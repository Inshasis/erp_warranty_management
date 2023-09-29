frappe.ui.form.on("Warranty Claim", {
	onload:function(frm) {
		frm.toggle_reqd("warranty_amc_status", 1);
	},
	refresh:function(frm) {
		if(!cur_frm.doc.__islocal &&
			(cur_frm.doc.status=='Open' || cur_frm.doc.status == 'Work In Progress')) {
			// cur_frm.add_custom_button(__('Warranty Request'),
			// 	make_warranty_management_request(frm), __("Make"))
			// cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			frm.add_custom_button(__("Warranty Request"), function() {
				make_warranty_management_request(frm)
            });
           
		}
		cur_frm.set_df_property("customer", "label", "Dealer")
		cur_frm.set_df_property("status", "options", "\nOpen\nClosed\nWork In Progress\nStart Receiving\nConfirmed\nTesting\nTesting Completed\nRepairing\nRepairing Completed\nCancelled");
	},
	
});

cur_frm.cscript.custom_warranty_amc_status = function(doc, dt, dn) {
	cur_frm.toggle_reqd("is_paid", doc.warranty_amc_status=="Out of Warranty" || doc.warranty_amc_status=="Out of AMC");
	cur_frm.set_value("is_paid", doc.warranty_amc_status=="Out of Warranty" || doc.warranty_amc_status=="Out of AMC");
	cur_frm.refresh_fields();
}

var make_warranty_management_request = function(frm) {
		frappe.model.open_mapped_doc({
			method: "warranty_management.warranty_management.warranty_claim.make_warranty_management_request",
			frm: cur_frm
		})
	}
