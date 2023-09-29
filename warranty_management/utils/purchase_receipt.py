from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt, update_billed_amount_based_on_po, update_billing_percentage
import frappe
from frappe import _, throw
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt, getdate, nowdate
from six import iteritems

import erpnext
from erpnext.accounts.utils import get_account_currency
from erpnext.assets.doctype.asset.asset import get_asset_account, is_cwip_accounting_enabled
from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account
from erpnext.buying.utils import check_on_hold_or_closed_status
from erpnext.controllers.buying_controller import BuyingController
from erpnext.stock.doctype.delivery_note.delivery_note import make_inter_company_transaction

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}

class SerialNoPurchaseReceipt(PurchaseReceipt):
    def on_submit(self):
        super(PurchaseReceipt, self).on_submit()

        # Check for Approving Authority
        frappe.get_doc("Authorization Control").validate_approving_authority(
            self.doctype, self.company, self.base_grand_total
        )

        self.update_prevdoc_status()
        if flt(self.per_billed) < 100:
            self.update_billing_status()
        else:
            self.db_set("status", "Completed")

        # Updating stock ledger should always be called after updating prevdoc status,
        # because updating ordered qty, reserved_qty_for_subcontract in bin
        # depends upon updated ordered qty in PO
        self.update_stock_ledger()

        if self.company == "Husaingadh Enterprise LLP":
            from erpnext.stock.doctype.serial_no.serial_no import update_serial_nos_after_submit
            update_serial_nos_after_submit(self, "items")
        else:
            from warranty_management.warranty_management.doctype.distributor_serial_no.distributor_serial_no import update_serial_no_after_submit
            update_serial_no_after_submit(self, "items")

        self.make_gl_entries()
        self.repost_future_sle_and_gle()
        self.set_consumed_qty_in_po()

    