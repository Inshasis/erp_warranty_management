# Copyright (c) 2013, Matiyas Solutions LLP and contributors
# For license information, please see license.txt



import frappe 
 
def execute(filters=None): 
 conditions, filters = get_conditions(filters) 
 columns = get_columns(filters) 
 # columns2 = get_columns2(filters) 
 # test = get_mapped_pri_records(conditions,filters) 
 data = get_data(conditions,filters) 
 
 return columns,data 
 
 
def get_data(conditions,filters): 
         
   
  item = frappe.db.sql("""  
  select item.item_code,item.item_name,ir.warehouse,ir.warehouse_reorder_level,ir.warehouse_reorder_qty,bin.actual_qty,bin.reserved_qty, bin.projected_qty from `tabItem`item 
 
LEFT JOIN 
`tabItem Reorder`ir on ir.parent = item.item_name 
 
LEFT JOIN 
`tabBin`bin on  bin.item_code = item.item_code and  
ir.warehouse_reorder_level >= bin.actual_qty 

WHERE bin.actual_qty and  ir.warehouse_reorder_level >= bin.actual_qty IS NOT NULL; 
 
 """.format(conditions=conditions), filters, as_dict=1) 
   
  return item 
 
 
def get_conditions(filters): 
        conditions = "" 
         
        if filters.get("so_company"): conditions += " and so.company = %(so_company)s" 
 
        return conditions,filters    
 
 
def get_columns(filters): 
 
 return  [ 
  { 
   "label": ("Item Name"), 
   "fieldname": "item_code", 
   "fieldtype": "Link", 
   "options": "Item", 
   "width": 100 
  }, 
  { 
   "label": ("Warehouse"), 
   "fieldname": "warehouse", 
   "fieldtype": "Link", 
   "options": "Warehouse", 
   "width": 100 
  }, 
  { 
   "label": ("Actual Qty"), 
   "fieldname": "actual_qty", 
   "width": 120 
  }, 
  { 
   "label": ("Reserved Qty"), 
   "fieldname": "reserved_qty", 
   "width": 120 
  }, 
  { 
   "label": ("Project Qty"), 
   "fieldname": "projected_qty", 
   "width": 120 
  }, 
  { 
   "label": ("Reorder Level"), 
   "fieldname": "warehouse_reorder_level", 
   "width": 120 
  }, 
  { 
   "label": ("Reorder Qty"), 
   "fieldname": "warehouse_reorder_qty", 
   "width": 120 
  } 
 
 
         
        ]
