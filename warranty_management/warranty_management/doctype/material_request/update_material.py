import frappe
from frappe.utils import cint

@frappe.whitelist()
def update_warranty_parts(doc,method):
    material = frappe.db.get_value('Warranty Request',{'name':doc.name},['name'])
    if material:
        mr = frappe.get_doc('Warranty Request',material)

        if doc.items:  
            for i in doc.items:           
                mr.append("material_request_part",{
                    'item_code':i.item_code,
                    'item_name':i.item_name,
                    'qty':i.qty,
                    'rate':i.rate,
                    'amount':i.amount,
                    'uom':i.uom,
                    'schedule_date':i.schedule_date
                })
                mr.flags.ignore_permissions  = True
                mr.save()
                        
                               
    
    if doc.material_request_type == "Material Issue":
        scrap = frappe.new_doc("Scrap Warehouse")  
        for item in doc.items:      
            scrap.append("scrap_item",{
                'item_name':item.item_name,
                'qty':'1'
            })
        scrap.customer = doc.customer
        scrap.warranty_no = doc.against_warranty_request
        scrap.docstatus = 1
        scrap.flags.ignore_permissions = True
        scrap.submit()
        scrap.save()


                        

