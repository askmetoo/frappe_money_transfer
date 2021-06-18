// Copyright (c) 2021, omar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bank Payment Order', {
	refresh: function(frm) {
		frm.add_custom_button(__('Get Client Information'), function(){
			frappe.call({
				"method": "money_transfer.money_transfer.doctype.bank_payment_order.bank_payment_order.getClientInfo",
				"args": {
					'client_no': frm.doc.client_no, 
					'client_seril': frm.doc.client_serial, 
					'branch_name': frm.doc.branch, 
					'currency': frm.doc.currency,
					'amount': frm.doc.amount
				},
				callback: function(r) {
					if(r.message.error_msg != ''){
						frm.set_value('transaction_notes', r.message.error_msg)
						console.log(r.message.error_msg);
					}else{
						frm.set_value('client_name', r.message.client_name)
						frm.set_value('region_code', r.message.client_region_code)
						frm.set_value('region', r.message.client_region)
						frm.remove_custom_button('Get Client Information');
						frm.add_custom_button(__('Verification'), function(){})
					}

				}
			});

		});
	 }
});
