from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote
from warranty_management.warranty_management.doctype.distributor_serial_no.distributor_serial_no import get_delivery_note_serial_no
import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_company_address
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import cint, flt

from erpnext.controllers.accounts_controller import get_taxes_and_charges
from erpnext.controllers.selling_controller import SellingController
from erpnext.stock.doctype.batch.batch import set_batch_nos


form_grid_templates = {"items": "templates/form_grid/item_grid.html"}

class SerialNoDeliveryNote(DeliveryNote):
    def update_item(source_doc, target_doc, source_parent):
        to_make_invoice_qty_map = {}
        target_doc.qty = to_make_invoice_qty_map[source_doc.name]

        if source_parent.company == "Husaingadh Enterprise LLP":

            if source_doc.serial_no and source_parent.per_billed > 0 and not source_parent.is_return:
                target_doc.serial_no = get_delivery_note_serial_no(
                    source_doc.item_code, target_doc.qty, source_parent.name
                )


@frappe.whitelist()
def on_submit_set_data_in_serialno(doc,handler=""):
    for item in doc.items:
        if item.against_warranty_serial_no and item.serial_no:
            data_old_serialno = frappe.db.sql("""select * from `tabSerial No` where name ="{0}" """.format(item.against_warranty_serial_no), as_dict=1)[0]
            # frappe.msgprint("data_old_serialno--- {0} item--- {1}".format(data_old_serialno.item_code,item))

            name = frappe.db.get_value(
                'Serial No', {'name': item.serial_no}, ['name'])
            if name:
                serial_no = frappe.get_doc('Serial No', name)
                # serial_no.item_code = data_old_serialno.item_code,
                # serial_no.warehouse = data_old_serialno.warehouse, 
                # serial_no.batch_no= data_old_serialno.batch_no, 
                # serial_no.item_name= data_old_serialno.item_name, 
                # serial_no.description= data_old_serialno.description, 
                # serial_no.item_group= data_old_serialno.item_group, 
                # serial_no.brand= data_old_serialno.brand, 
                # serial_no.sales_order= data_old_serialno.sales_order, 
                # serial_no.purchase_document_type= data_old_serialno.purchase_document_type, 
                # serial_no.purchase_document_no= data_old_serialno.purchase_document_no, 
                # serial_no.purchase_date= data_old_serialno.purchase_date, 
                # serial_no.purchase_time= data_old_serialno.purchase_time, 
                # serial_no.purchase_rate= data_old_serialno.purchase_rate, 
                # serial_no.supplier= data_old_serialno.supplier, 
                # serial_no.supplier_name= data_old_serialno.supplier_name, 
                # serial_no.asset= data_old_serialno.asset,
                # serial_no.asset_status= data_old_serialno.asset_status, 
                # serial_no.location= data_old_serialno.location,
                # serial_no.employee= data_old_serialno.employee, 
                serial_no.delivery_document_type = "Delivery Note" 
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


            old_rate = frappe.db.sql("""select rate from `tabSales Invoice Item` where serial_no ="{0}" """.format(item.against_warranty_serial_no))
    
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
            stock.save()




# @frappe.whitelist()
# def check_rate(against_warranty_serial_no):
#     old_rate = frappe.db.sql("""select rate from `tabSales Invoice Item` where serial_no ="{0}" """.format(against_warranty_serial_no))[0][0]
            
#     return old_rate