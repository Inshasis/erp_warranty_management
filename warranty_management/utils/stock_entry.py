import frappe

def make_stock_entry_scrap(self,method):
    if self.against_warranty_request and self.stock_entry_type == "Material Issue":
        stock = frappe.new_doc("Stock Entry")    
        for item in self.items:    
            stock.append("items",{
                'item_code':item.item_code,
                'qty':'1',
                'is_scrap_item' : 1,
                'transfer_qty': '0',
                't_warehouse' : "Scrap Warehouse - HEL",
                'uom':item.uom,
                'conversion_factor' : '1',
                'basic_rate':0,
                
            })
        # stock.customer = doc.customer
        stock.stock_entry_type = "Material Receipt"
        stock.to_warehouse = "Scrap Warehouse - HEL"
        stock.warranty_claim = ""
        stock.docstatus = 1
        stock.flags.ignore_permissions = True
        stock.submit()
        stock.save()