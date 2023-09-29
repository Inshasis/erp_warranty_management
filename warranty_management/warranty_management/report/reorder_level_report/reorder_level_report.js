frappe.query_reports["Reorder Level Report"] = { 
    "filters": [{ 
            "fieldname": "warehouse", 
            "label": __("Warehouse"), 
            "fieldtype": "Link", 
            "options": "Warehouse", 
 
        }, 
        { 
            "fieldname": "item_code", 
            "label": __("Item"), 
            "fieldtype": "Link", 
            "options": "Item", 
 
        }, 
 
 
    ] 
};