from . import __version__ as app_version

app_name = "warranty_management"
app_title = "Warranty Management"
app_publisher = "Matiyas Solutions LLP"
app_description = "Warranty Management Process"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "business@matiyas.com"
# app_version = "0.0.1"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/warranty_management/css/warranty_management.css"
# app_include_js = "/assets/warranty_management/js/warranty_management.js"

# include js, css files in header of web template
# web_include_css = "/assets/warranty_management/css/warranty_management.css"
# web_include_js = "/assets/warranty_management/js/warranty_management.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#   "Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "warranty_management.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]
# fixtures = [
#     {
#         "doctype": "Custom Field",
#         "filters": [
#             ["name", "in", (
#                "Stock Entry-warranty_claim",
#                 "Material Request-warranty_claim",
#                 "Delivery Note-warranty_claim", 
#                 "Sales Invoice-warranty_claim",
#                 "Warranty Claim-is_paid"
#             )]
#         ]
#     }
# ]
# Installation
# ------------

# before_install = "warranty_management.install.before_install"
# after_install = "warranty_management.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "warranty_management.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#   "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#   "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

override_doctype_class = {
	# "Purchase Receipt": "warranty_management.utils.purchase_receipt.SerialNoPurchaseReceipt",
    # "Purchase Invoice": "warranty_management.utils.purchase_invoice.SerialNoPurchaseInvoice",
    # "Delivery Note": "warranty_management.utils.delivery_note.SerialNoDeliveryNote",
    # "Sales Invoice": "warranty_management.utils.sales_invoice.SerialNoSalesInvoice",
    "Stock Ledger Entry": "warranty_management.utils.stock_ledger_entry.SerialNoStockLedgerEntry",
}

doc_events = {
    "Warranty Claim": {
        "before_save": "warranty_management.warranty_management.warranty_claim.before_save",
    },
    "Material Request": {
    	"on_submit":"warranty_management.warranty_management.doctype.material_request.update_material.update_warranty_parts",
    },
    "Delivery Note":{
        "on_submit":"warranty_management.utils.delivery_note.on_submit_set_data_in_serialno",
    },
    "Sales Invoice":{
        "on_submit":"warranty_management.utils.sales_invoice.on_submit_set_data_in_serialno"
    },
    "Stock Entry":{
        "on_submit":"warranty_management.utils.stock_entry.make_stock_entry_scrap",
    },
}
# doc_events = {
#   "*": {
#       "on_update": "method",
#       "on_cancel": "method",
#       "on_trash": "method"
#   }
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    # "all": [
    #     "warranty_management.tasks.all"
    # ],
    "daily": [
        "warranty_management.tasks.daily"
    ],
    #   "hourly": [
    #       "warranty_management.tasks.hourly"
    # ],
    # "weekly": [
    #    "warranty_management.tasks.weekly"
    # ]
    # "monthly": [
    #    "warranty_management.tasks.monthly"
    # ]
}

# Testing
# -------

# before_tests = "warranty_management.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
override_whitelisted_methods = {
	"erpnext.stock.doctype.material_request.material_request.make_stock_entry": "warranty_management.warranty_management.doctype.material_request.material_request.make_stock_entry",
    "erpnext.stock.doctype.serial_no.serial_no.auto_fetch_serial_number" : "warranty_management.utils.serial_no.auto_fetch_serial_number",
}
#
# override_whitelisted_methods = {
#   "frappe.desk.doctype.event.event.get_events": "warranty_management.event.get_events"
# }

doctype_js = {
    "Warranty Claim": ["custom_scripts/warranty_claim.js"]
}
