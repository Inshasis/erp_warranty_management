from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
import frappe
from frappe import _, throw
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, cstr, flt, formatdate, get_link_to_form, getdate, nowdate
from six import iteritems

import erpnext
from erpnext.accounts.deferred_revenue import validate_service_stop_date
from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
	check_if_return_invoice_linked_with_payment_entry,
	get_total_in_party_account_currency,
	is_overdue,
	unlink_inter_company_doc,
	update_linked_doc,
	validate_inter_company_party,
)
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
	get_party_tax_withholding_details,
)
from erpnext.accounts.general_ledger import (
	get_round_off_account_and_cost_center,
	make_gl_entries,
	make_reverse_gl_entries,
	merge_similar_entries,
)
from erpnext.accounts.party import get_due_date, get_party_account
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
from erpnext.assets.doctype.asset.asset import get_asset_account, is_cwip_accounting_enabled
from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account
from erpnext.buying.utils import check_on_hold_or_closed_status
from erpnext.controllers.accounts_controller import validate_account_head
from erpnext.controllers.buying_controller import BuyingController
from erpnext.stock import get_warehouse_account_map
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
	get_item_account_wise_additional_cost,
	update_billed_amount_based_on_po,
)

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}

class SerialNoPurchaseInvoice(PurchaseInvoice):
    def on_submit(self):
        super(PurchaseInvoice, self).on_submit()

        self.check_prev_docstatus()
        self.update_status_updater_args()
        self.update_prevdoc_status()

        frappe.get_doc("Authorization Control").validate_approving_authority(
            self.doctype, self.company, self.base_grand_total
        )

        if not self.is_return:
            self.update_against_document_in_jv()
            self.update_billing_status_for_zero_amount_refdoc("Purchase Receipt")
            self.update_billing_status_for_zero_amount_refdoc("Purchase Order")

        self.update_billing_status_in_pr()

        # Updating stock ledger should always be called after updating prevdoc status,
        # because updating ordered qty in bin depends upon updated ordered qty in PO
        if self.update_stock == 1:
            self.update_stock_ledger()
            self.set_consumed_qty_in_po()
            if self.company == "Husaingadh Enterprise LLP":
                from erpnext.stock.doctype.serial_no.serial_no import update_serial_nos_after_submit

                update_serial_nos_after_submit(self, "items")

        # this sequence because outstanding may get -negative
        self.make_gl_entries()

        if self.update_stock == 1:
            self.repost_future_sle_and_gle()

        self.update_project()
        update_linked_doc(self.doctype, self.name, self.inter_company_invoice_reference)
        self.update_advance_tax_references()

        self.process_common_party_accounting()