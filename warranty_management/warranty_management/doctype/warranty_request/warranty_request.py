# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from __future__ import unicode_literals
from frappe.model.mapper import get_mapped_doc
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import now_datetime
from frappe.model.document import Document
import frappe


class WarrantyRequest(Document):

    def after_insert(self):
       pass       

    def on_submit(self):
        if self.status == 'Replacement':

            sales = frappe.new_doc("Sales Order")
            for i in self.warranty_request_purposes:
                sales.append("items", {
                    'item_code': i.item_code,
                    'item_name': i.item_name,
                    'is_free_item': 1,
                    'rate': 0.0,
                    'delivery_date': datetime.now(),
                    'qty': 1,
                    'uom': i.stock_uom,
                    # 'adr':i.adr,
                    'against_warranty_request' : self.name,
                    'against_warranty_serial_no':i.serial_no
                    # 'company': doc.company,
                    # 'ly_supplier': doc.supplier,
                    # 'item_status':'Not Available'
                })
                sales.customer = self.customer
                # sales.deal_number = self.order_number
                # sales.purchase_order_no = doc.name
                sales.company = self.company
                sales.warranty_claim = ""
                sales.set_warehouse = self.to_warehouse
                sales.staidentus = "Draft"
                sales.ignore_permissions = True
                sales.save()
                frappe.msgprint(msg='Sales Order Created Successfully',
                                title='Message',
                                indicator='green')

    def before_insert(self):
        if self.warranty_claim:
            update_status("Warranty Claim", self.warranty_claim, "Start Receiving")

    def before_submit(self):
        if self.status == 'Repairing Completed':
            sales = frappe.new_doc("Sales Invoice")
            if self.warranty_request_purposes:  
                for i in self.warranty_request_purposes:           
                    sales.append("items",{
                        'item_code':i.item_code,
                        'qty':'1',
                        'rate': 0,
                        'uom':i.stock_uom,
                                

                    })
                sales.customer = self.customer
                sales.posting_date = self.resolution_date
                sales.warranty_claim = ""
                sales.warranty_claim = ""
                sales.flags.ignore_permissions  = True
                sales.save()   

            
            wc_doc = frappe.get_doc('Warranty Claim', self.warranty_claim)
            wc_doc.status = "Closed"
            wc_doc.ignore_permissions = True
            wc_doc.save()
                
        elif self.status == 'Testing Completed' and self.to_warehouse == "Scrap Warehouse - HEL":
            scrap = frappe.new_doc("Scrap Warehouse")
            if self.warranty_request_purposes:
                    for i in self.warranty_request_purposes:           
                                    scrap.append("scrap_item",{
                                        'item_name':i.item_name,
                                        'qty':'1',
                                        'amount':i.amount,
                                        'serial_no':i.serial_no
                                    })
                                    scrap.customer = self.customer
                                    scrap.warranty_no = self.name
                                    scrap.flags.ignore_permissions  = True
                                    scrap.save()
        elif self.status == 'Repairing Completed' and self.to_warehouse == "Scrap Warehouse - HEL":
            scrap = frappe.new_doc("Scrap Warehouse")
            if self.material_request_part:
                    for i in self.material_request_part:           
                                    scrap.append("scrap_item",{
                                        'item_name':i.item_name,
                                        'qty':i.qty,
                                        'rate':i.rate,
                                        'amount':i.amount,
                                        'serial_no':self.serial_no
                                    })
                                    scrap.customer = self.customer
                                    scrap.warranty_no = self.name
                                    scrap.flags.ignore_permissions  = True
                                    scrap.save()   
        # else:
        #     update_status(self.doctype, self.name, "Closed")
        #     if self.warranty_claim:
        #         self.update_customer_issue()
        #     dn = make_delivery_note(self.name)
        #     dn.insert()
        #     frappe.msgprint("Delivery Note %s was created automatically" % dn.name)

    def update_customer_issue(self):
        for d in self.get("warranty_request_purposes"):
            resolution_date = self.resolution_date
            service_person = d.service_person
            work_done = d.work_done
            frappe.db.sql("update `tabWarranty Claim` set resolution_date=%s, resolved_by=%s, resolution_details=%s, status=%s where name =%s",(resolution_date,service_person,work_done,"Closed",self.warranty_claim))

    def confirm_receiving_item(self):
        if self.is_item_confirmed:
            frappe.throw("Item is already confirmed")

        frappe.db.set(self, "is_item_confirmed", 1)
        update_status(self.doctype, self.name, "Confirmed")
        if self.warranty_claim:
            update_status("Warranty Claim", self.warranty_claim, "Confirmed")
        self.get_doc().add_comment("Comment", _("Receiving Item has been confirmed"))
        se = make_stock_entry(self.name)
        se.insert()
        frappe.msgprint("Receiving Item has been confirmed")
        frappe.msgprint("Stock Entry %s was created automatically" % se.name)
        frappe.clear_cache(doctype="Warranty Request")

    def start_testing_item(self):
        if self.is_testing_started:
            frappe.throw("Testing is already started")

        frappe.db.set(self, "is_testing_started", 1)
        update_status(self.doctype, self.name, "Testing")
        if self.warranty_claim:
            update_status("Warranty Claim", self.warranty_claim, "Testing")
        self.get_doc().add_comment("Comment", _("Testing Item has been started"))
        frappe.msgprint("Testing Item has been started")
        frappe.clear_cache(doctype="Warranty Request")

    def start_repairing_item(self):
        if self.is_repairing_started:
            frappe.throw("Repairing is already started")

        frappe.db.set(self, "is_repairing_started", 1)
        update_status(self.doctype, self.name, "Repairing")
        if self.warranty_claim:
            update_status("Warranty Claim", self.warranty_claim, "Repairing")
        self.get_doc().add_comment("Comment", _("Repairing Item has been started"))
        frappe.msgprint("Repairing Item has been started")
        frappe.clear_cache(doctype="Warranty Request")

    def on_cancel(self):
        update_status(self.doctype, self.name, "Canceled")
        if self.warranty_claim:
            update_status("Warranty Claim", self.warranty_claim, "Canceled")

    def get_doc(self):
        if not getattr(self, "_doc", None):
            self._doc = frappe.get_doc(self.doctype, self.name)
        return self._doc

    


@frappe.whitelist()
def add_testing_results(name, testing_results, is_testing_rejected=None):
    if frappe.db.get_value("Warranty Request", name, "is_testing_completed"):
        frappe.throw("Testing is already completed.")
    frappe.db.set_value("Warranty Request", name, "is_testing_completed", 1)
    update_status("Warranty Request", name, "Testing Completed")
    frappe.db.set_value("Warranty Request Purposes", {"parent": name}, "testing_results", testing_results)
    doc_warranty_request = frappe.get_doc("Warranty Request", name)
    doc_warranty_request.add_comment("Comment", _("Testing Item has been completed"))
    frappe.msgprint("Testing Item has been completed.")
    if is_testing_rejected:
        frappe.db.set_value("Warranty Request", name, "is_testing_rejected", 1)
        dn = make_delivery_note(name)
        dn.insert()
        frappe.db.set_value("Warranty Request", name, "delivery_note", dn.name)
        update_status("Warranty Request", name, "Closed")
        frappe.msgprint("Delivery Note %s was created automatically" % dn.name)
    warranty_claim = frappe.db.get_value("Warranty Request", name, "warranty_claim")
    if warranty_claim:
        update_status("Warranty Claim", warranty_claim, frappe.db.get_value("Warranty Request", name, "status"))
    frappe.clear_cache(doctype="Warranty Request")


@frappe.whitelist()
def add_repairing_results(name, repairing_results, is_item_to_be_replaced=None):
    if frappe.db.get_value("Warranty Request", name, "is_repairing_completed"):
        frappe.throw("Repairing is already completed")
    frappe.db.set_value("Warranty Request", name, "is_repairing_completed", 1)
    update_status("Warranty Request", name, "Repairing Completed")
    frappe.db.set_value("Warranty Request", name, "resolution_date", now_datetime())
    frappe.db.set_value("Warranty Request Purposes", {"parent": name}, "work_done", repairing_results)
    warranty_claim = frappe.db.get_value("Warranty Request", name, "warranty_claim")
    if warranty_claim:
        update_status("Warranty Claim", warranty_claim, "Repairing Completed")
    doc_warranty_request = frappe.get_doc("Warranty Request", name)
    doc_warranty_request.add_comment("Comment", _("Repairing Item has been completed"))
    if is_item_to_be_replaced:
        frappe.db.set_value("Warranty Request", name, "is_item_to_be_replaced", 1)
        so = make_sales_order(name)
        so.insert()
        frappe.db.set_value("Warranty Request", name, "sales_order", so.name)
        update_status("Warranty Request", name, "Closed")
        frappe.msgprint("sales Order %s was created automatically" % so.name)
    frappe.clear_cache(doctype="Warranty Request")


def update_status(doctype, name, status):
    frappe.db.set_value(doctype, name, "status", status)


def has_active_dn(warranty_claim):
    if warranty_claim:
        for dn in frappe.get_all("Delivery Note", fields=["docstatus"], filters={"warranty_claim": warranty_claim}):
            if dn.get("docstatus") in (0, 1):
                return True
    return False


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source, target, source_parent):
        target.qty = 1

    if has_active_dn(frappe.db.sql("""select warranty_claim from `tabWarranty Request` where name=%s""", source_name, as_dict=1)[0].warranty_claim):
        frappe.throw("Cannot make new Delivery Note: Delivery Note is already created and its docstatus is not canceled.")

    target_doc = get_mapped_doc("Warranty Request", source_name, {
        "Warranty Request": {
            "doctype": "Delivery Note",
            "field_map": {
                "warranty_claim": "warranty_claim",
            },
        },
        "Warranty Request Purposes": {
            "doctype": "Delivery Note Item",

            "postprocess": update_item,
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "add_if_empty": True
        }
    }, target_doc, set_missing_values)

    return target_doc


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.stock_entry_type = "Material Receipt"

    def update_item(source, target, source_parent):
        target.qty = 1
        target.uom = source.stock_uom
        target.stock_uom = source.stock_uom
        # target.stock_entry_type = "Material Issue"

    target_doc = get_mapped_doc("Warranty Request", source_name, {
        "Warranty Request": {
            "doctype": "Stock Entry",
            "validation": {
                "is_item_confirmed": ["=", 1]
            },
            "field_map": {
                "warranty_claim": "warranty_claim",
                "to_warehouse": "to_warehouse"
            },
        },
        "Warranty Request Purposes": {
            "doctype": "Stock Entry Detail",
            "postprocess": update_item,
        }
    }, target_doc, set_missing_values)

    return target_doc


@frappe.whitelist()
def make_material_request(source_name, target_doc=None):

    # def set_missing_values(source, target_doc):
    #     target_doc.schedule_date = datetime.now()

    def postprocess(source, doc):
        doc.material_request_type = "Material Issue"
        doc.warranty_request_name = source_name
        
    def update_item(source_doc, target_doc, source_parent):
        target_doc.price_list_rate = 0
        target_doc.rate = 0 
        # target_doc.schedule_date = datetime.now()


    target_doc = get_mapped_doc("Warranty Request", source_name, {
        "Warranty Request": {
            "doctype": "Material Request",
            "validation": {
                "status": ["=", 'Testing Completed']
                },
        },        
        "Material Request Part": {
            "doctype": "Material Request Item",
            "field_map": {
                
            },
            "postprocess": update_item,
        },
        "field_map": {
            "warranty_claim": "warranty_claim"
        },
        
    }, target_doc, postprocess)

    return target_doc


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.customer = source.customer
        target.customer_name = source.customer_name
        target.ignore_pricing_rule = 1
        target.flags.ignore_permissions = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.price_list_rate = 0
        target_doc.rate = 0
        target_doc.qty = 1

    target_doc = get_mapped_doc("Warranty Request", source_name, {
        "Warranty Request": {
            "doctype": "Sales Order",
            "validation": {
            },
        },
        "Warranty Request Purposes": {
            "doctype": "Sales Order Item",
            "field_map": {
            },
            "postprocess": update_item,
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "add_if_empty": True
        }
    }, target_doc, set_missing_values, ignore_permissions=1)

    return target_doc
#sales invoice function
@frappe.whitelist()
def make_sales_invoices(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.customer = source.customer
        target.customer_name = source.customer_name
        target.ignore_pricing_rule = 1
        target.flags.ignore_permissions = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.price_list_rate = 0
        target_doc.rate = 0
        target_doc.qty = 1

    target_doc = get_mapped_doc("Warranty Request", source_name, {
        "Warranty Request": {
            "doctype": "Sales Invoice",
            "validation": {
                "status": ["=", 'Repairing Completed']
            },
        },
        "Warranty Request Purposes": {
            "doctype": "Sales Invoice Item",
            "field_map": {
            },
            "postprocess": update_item,
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "add_if_empty": True
        }
    }, target_doc, set_missing_values, ignore_permissions=1)

    return target_doc


@frappe.whitelist()
def make_sales_invoice(source_name):
    si = make_sales_invoice_main(source_name)
    si.insert()
    frappe.msgprint("Sales Invoice %s was created automatically" % si.name)


@frappe.whitelist()
def make_sales_invoice_main(source_name, target_doc=None):
    def postprocess(source, target):
        set_missing_values(source, target)
        target.get_advances()

    def set_missing_values(source, target):
        target.is_pos = 0
        # target.customer = source.customer
        # target.customer_name = source.customer_name
        # target.ignore_pricing_rule = 1
        target.flags.ignore_permissions = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        # target_doc.price_list_rate = 0
        # target_doc.rate = 0
        target_doc.qty = source_doc.qty

    target_doc = get_mapped_doc("Material Request", source_name, {
        "Material Request": {
            "doctype": "Sales Invoice",
            "validation": {
                "is_paid": ["=", 1]
            }
        },
        "Material Request Item": {
            "doctype": "Sales Invoice Item",
            "field_map": {
            },
            "postprocess": update_item,
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "add_if_empty": True
        }
    }, target_doc, postprocess, ignore_permissions=1)

    return target_doc
   

    
