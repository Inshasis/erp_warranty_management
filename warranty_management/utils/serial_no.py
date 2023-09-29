import json
from typing import List, Optional, Union

from erpnext.stock.doctype.serial_no.serial_no import clean_serial_no_string, fetch_serial_numbers, get_pos_reserved_serial_nos, get_serial_nos

import frappe
from frappe import ValidationError, _
from frappe.model.naming import make_autoname
from frappe.query_builder.functions import Coalesce
from frappe.utils import (
	add_days,
	cint,
	cstr,
	flt,
	get_link_to_form,
	getdate,
	nowdate,
	safe_json_loads,
)

from erpnext.controllers.stock_controller import StockController
from erpnext.stock.get_item_details import get_reserved_qty_for_so

@frappe.whitelist()
def auto_fetch_serial_number(
	qty: float,
	item_code: str,
	warehouse: str,
	posting_date: Optional[str] = None,
	batch_nos: Optional[Union[str, List[str]]] = None,
	for_doctype: Optional[str] = None,
	exclude_sr_nos: Optional[List[str]] = None,
) -> List[str]:

    doc_wh = frappe.get_doc('Warehouse', warehouse)
    if doc_wh.company == 'Husaingadh Enterprise LLP':
    
        filters = frappe._dict({"item_code": item_code, "warehouse": warehouse})

        if exclude_sr_nos is None:
            exclude_sr_nos = []
        else:
            exclude_sr_nos = safe_json_loads(exclude_sr_nos)
            exclude_sr_nos = get_serial_nos(clean_serial_no_string("\n".join(exclude_sr_nos)))

        if batch_nos:
            batch_nos_list = safe_json_loads(batch_nos)
            if isinstance(batch_nos_list, list):
                filters.batch_no = batch_nos_list
            else:
                filters.batch_no = [batch_nos]

        if posting_date:
            filters.expiry_date = posting_date

        serial_numbers = []
        if for_doctype == "POS Invoice":
            exclude_sr_nos.extend(get_pos_reserved_serial_nos(filters))

        serial_numbers = fetch_serial_numbers(filters, qty, do_not_include=exclude_sr_nos)

        return sorted([d.get("name") for d in serial_numbers])

    else:
        frappe.msgprint("List of Data {0}".format(doc_wh.company))
        # from warranty_management.warranty_management.doctype.distributor_serial_no.distributor_serial_no import auto_fetch_serial_number_dis

        # auto_fetch_serial_number_dis(qty,item_code,warehouse,posting_date,batch_nos,for_doctype,exclude_sr_nos)
        filters = frappe._dict({"item_code": item_code, "warehouse": warehouse})

        if exclude_sr_nos is None:
            exclude_sr_nos = []
        else:
            exclude_sr_nos = safe_json_loads(exclude_sr_nos)
            exclude_sr_nos = get_serial_nos(clean_serial_no_string("\n".join(exclude_sr_nos)))

        if batch_nos:
            batch_nos_list = safe_json_loads(batch_nos)
            if isinstance(batch_nos_list, list):
                filters.batch_no = batch_nos_list
            else:
                filters.batch_no = [batch_nos]

        if posting_date:
            filters.expiry_date = posting_date

        serial_numbers = []
        if for_doctype == "POS Invoice":
            exclude_sr_nos.extend(get_pos_reserved_serial_nos(filters))

        serial_numbers = fetch_serial_numbers_dis(filters, qty, do_not_include=exclude_sr_nos)
        
        return sorted([d.get("name") for d in serial_numbers])


def fetch_serial_numbers_dis(filters, qty, do_not_include=None):
	if do_not_include is None:
		do_not_include = []

	batch_nos = filters.get("batch_no")
	expiry_date = filters.get("expiry_date")
	serial_no = frappe.qb.DocType("Distributor Serial No")

	query = (
		frappe.qb.from_(serial_no)
		.select(serial_no.name)
		.where(
			(serial_no.item_code == filters["item_code"])
			& (serial_no.warehouse == filters["warehouse"])
			& (Coalesce(serial_no.sales_invoice, "") == "")
			& (Coalesce(serial_no.delivery_document_no, "") == "")
		)
		.orderby(serial_no.creation)
		.limit(qty or 1)
	)

	if do_not_include:
		query = query.where(serial_no.name.notin(do_not_include))

	if batch_nos:
		query = query.where(serial_no.batch_no.isin(batch_nos))

	if expiry_date:
		batch = frappe.qb.DocType("Batch")
		query = (
			query.left_join(batch)
			.on(serial_no.batch_no == batch.name)
			.where(Coalesce(batch.expiry_date, "4000-12-31") >= expiry_date)
		)

	serial_numbers = query.run(as_dict=True)
	return serial_numbers
