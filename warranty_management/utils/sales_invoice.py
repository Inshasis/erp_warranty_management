
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice, update_linked_doc
import frappe
from frappe import _, msgprint, throw
from frappe.contacts.doctype.address.address import get_address_display
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import (
	add_days,
	add_months,
	cint,
	cstr,
	flt,
	formatdate,
	get_link_to_form,
	getdate,
	nowdate,
)
from six import iteritems

import erpnext
from erpnext.accounts.deferred_revenue import validate_service_stop_date
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
	get_loyalty_program_details_with_points,
	validate_loyalty_points,
)
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
	get_party_tax_withholding_details,
)
from erpnext.accounts.general_ledger import get_round_off_account_and_cost_center
from erpnext.accounts.party import get_due_date, get_party_account, get_party_details
from erpnext.accounts.utils import get_account_currency
from erpnext.assets.doctype.asset.depreciation import (
	get_disposal_account_and_cost_center,
	get_gl_entries_on_asset_disposal,
	get_gl_entries_on_asset_regain,
	make_depreciation_entry,
)
from erpnext.controllers.accounts_controller import validate_account_head
from erpnext.controllers.selling_controller import SellingController
from erpnext.healthcare.utils import manage_invoice_submit_cancel
from erpnext.projects.doctype.timesheet.timesheet import get_projectwise_timesheet_data
from erpnext.setup.doctype.company.company import update_company_current_month_sales
from erpnext.stock.doctype.batch.batch import set_batch_nos
from erpnext.stock.doctype.delivery_note.delivery_note import update_billed_amount_based_on_so
from erpnext.stock.doctype.serial_no.serial_no import (
	get_delivery_note_serial_no,
	get_serial_nos,
	update_serial_nos_after_submit,
)



class SerialNoSalesInvoice(SalesInvoice):
    def on_submit(self):
        self.validate_pos_paid_amount()

        if not self.auto_repeat:
            frappe.get_doc("Authorization Control").validate_approving_authority(
                self.doctype, self.company, self.base_grand_total, self
            )

        self.check_prev_docstatus()

        if self.is_return and not self.update_billed_amount_in_sales_order:
            # NOTE status updating bypassed for is_return
            self.status_updater = []

        self.update_status_updater_args()
        self.update_prevdoc_status()
        self.update_billing_status_in_dn()
        self.clear_unallocated_mode_of_payments()

        # Updating stock ledger should always be called after updating prevdoc status,
        # because updating reserved qty in bin depends upon updated delivered qty in SO
        if self.update_stock == 1:
            self.update_stock_ledger()
        if self.is_return and self.update_stock and self.company == "Husaingadh Enterprise LLP":
            update_serial_nos_after_submit(self, "items")

        # this sequence because outstanding may get -ve
        self.make_gl_entries()

        if self.update_stock == 1:
            self.repost_future_sle_and_gle()

        if not self.is_return:
            self.update_billing_status_for_zero_amount_refdoc("Delivery Note")
            self.update_billing_status_for_zero_amount_refdoc("Sales Order")
            self.check_credit_limit()

        self.update_serial_no()

        if not cint(self.is_pos) == 1 and not self.is_return:
            self.update_against_document_in_jv()

        self.update_time_sheet(self.name)

        if (
            frappe.db.get_single_value("Selling Settings", "sales_update_frequency") == "Each Transaction"
        ):
            update_company_current_month_sales(self.company)
            self.update_project()
        update_linked_doc(self.doctype, self.name, self.inter_company_invoice_reference)

        # create the loyalty point ledger entry if the customer is enrolled in any loyalty program
        if not self.is_return and not self.is_consolidated and self.loyalty_program:
            self.make_loyalty_point_entry()
        elif (
            self.is_return and self.return_against and not self.is_consolidated and self.loyalty_program
        ):
            against_si_doc = frappe.get_doc("Sales Invoice", self.return_against)
            against_si_doc.delete_loyalty_point_entry()
            against_si_doc.make_loyalty_point_entry()
        if self.redeem_loyalty_points and not self.is_consolidated and self.loyalty_points:
            self.apply_loyalty_points()

        # Healthcare Service Invoice.
        domain_settings = frappe.get_doc("Domain Settings")
        active_domains = [d.domain for d in domain_settings.active_domains]

        if "Healthcare" in active_domains:
            manage_invoice_submit_cancel(self, "on_submit")

        self.process_common_party_accounting()


@frappe.whitelist()
def on_submit_set_data_in_serialno(doc,handler=""):
    if doc.update_stock == 1:
        for item in doc.items:
            if item.against_warranty_serial_no and item.serial_no:
                data_old_serialno = frappe.db.sql("""select * from `tabSerial No` where name ="{0}" """.format(item.against_warranty_serial_no), as_dict=1)[0]
                # frappe.msgprint("data_old_serialno--- {0} item--- {1}".format(data_old_serialno.item_code,item))

                name = frappe.db.get_value(
                    'Serial No', {'name': item.serial_no}, ['name'])
                if name:
                    serial_no = frappe.get_doc('Serial No', name)
                    
                    serial_no.delivery_document_type = "Sales Invoice" 
                    serial_no.delivery_document_no= doc.name 
                    serial_no.delivery_date= doc.posting_date 
                    serial_no.delivery_time= doc.posting_time 
                    serial_no.customer= data_old_serialno.customer
                    serial_no.customer_name= data_old_serialno.customer_name
                    # serial_no.sales_invoice= data_old_serialno.sales_invoice, 
                    serial_no.warranty_expiry_date= data_old_serialno.warranty_expiry_date 
                    serial_no.amc_expiry_date= data_old_serialno.amc_expiry_date
                    serial_no.maintenance_status= data_old_serialno.maintenance_status
                    serial_no.warranty_period= data_old_serialno.warranty_period
                    # serial_no.serial_no_details= data_old_serialno.serial_no_details, 
                    # serial_no.company= data_old_serialno.company, 
                    serial_no.status= data_old_serialno.status
                    # serial_no.work_order= data_old_serialno.work_order,
                    serial_no.ignore_permissions = True
                    serial_no.save()
                frappe.msgprint(msg='Serial No has been Updated Successfully',
                                title='Message',
                                indicator='green')


            
            if item.against_warranty_request:
                warranty_claim = frappe.db.get_value(
                        'Warranty Request', {'name': item.against_warranty_request}, ['warranty_claim'])  

                if warranty_claim:
                    wc_doc = frappe.get_doc('Warranty Claim', warranty_claim)
                    wc_doc.status = "Closed"
                    wc_doc.ignore_permissions = True
                    wc_doc.save()


                old_rate = frappe.db.sql("""select rate from `tabSales Invoice Item` where serial_no ="{0}" """.format(item.against_warranty_serial_no))[0][0]
    
                scrap = frappe.new_doc("Scrap Warehouse")        
                scrap.append("scrap_item",{
                    'item_name':item.item_name,
                    'qty':'1',
                    'amount':old_rate,
                    'serial_no':item.against_warranty_serial_no
                })
                scrap.customer = doc.customer
                scrap.warranty_no = item.against_warranty_request
                scrap.flags.ignore_permissions = True
                scrap.submit()
                scrap.save()    


                #create Stock Entry For Scrap Warehouse
                scrap_warehouse = frappe.db.get_value(
                        'Warranty Request', {'name': item.against_warranty_request}, ['scrap_warehouse'])  

                stock = frappe.new_doc("Stock Entry")        
                stock.append("items",{
                    'item_code':item.item_code,
                    'qty':'1',
                    'is_scrap_item' : 1,
                    'transfer_qty': '0',
                    't_warehouse' : scrap_warehouse,
                    'uom':item.uom,
                    'conversion_factor' : '1',
                    'basic_rate':old_rate,
                    'serial_no':item.against_warranty_serial_no
                })
                # stock.customer = doc.customer
                stock.stock_entry_type = "Material Receipt"
                stock.to_warehouse = scrap_warehouse
                stock.warranty_claim = ""
                stock.flags.ignore_permissions = True
                stock.submit()
                stock.save()

