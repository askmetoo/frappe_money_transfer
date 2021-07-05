// Copyright (c) 2021, omar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bank Payment Order', {
	before_load: function(frm){
		frm.disable_save();
		
	},
	refresh: function(frm) {
		if(frm.doc.client_name == '_'){
			frm.add_custom_button(__('Get Client Information'), function(){
				get_client_info_on_click(frm)
			});
		}else{
			if(frm.doc.beneficiary_name == '_'){
				frm.add_custom_button(__('Verification'), function(){
					verification_on_click(frm);
				});
			}else{
				frm.add_custom_button(__('Push Payment'), function(){
				});
			}
				
		}
	 },
	 setup: function(frm) {
		frm.set_df_property('branch','read_only',1);
		frm.set_query("sender_bank", function() {
			return {
				filters: [
					["Bank Company","is_local", "=", 1]
				]
			}
		});
		frm.set_query("receiver_bank", function() {
			return {
				filters: [
					["Bank Company","is_local", "=", 0]
				]
			}
		});
		update_date_time(frm);
		
	},
	on_load: function(frm){
		
	},
	sender_bank: function(frm){
		if(frm.doc.sender_bank){
			frm.set_df_property('branch','read_only',0);
			frm.set_query("branch", function(){
				return {
					filters:[
						["Bank Branch", "Bank" , "=", frm.doc.sender_bank]
					]
				}
			})
		}else{
			frm.set_df_property('branch','read_only',1);
			frm.set_value('branch',null)
		}
	}
});

function update_date_time(frm){
	var today = new Date();
	var date = today.getDate()+'/'+(today.getMonth()+1)+'/'+today.getFullYear();
	var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
	frm.set_value('date', date)
	frm.set_value('time', time)
}

function verification_on_click(frm){
	frappe.call({
		"method": "money_transfer.money_transfer.doctype.bank_payment_order.bank_payment_order.sendVerificationDoc",
		"args": {
			'our_bank': frm.doc.sender_bank,
			'dis_bank': frm.doc.receiver_bank,
			'beneficiary_no': frm.doc.beneficiary_no,
			'account_type': frm.doc.account_type,
			'doc_name': frm.doc.name
		},
		callback: function(r) {
			
			if(r.message.pv_Vrfctn == "true"){
				frm.set_value('payment_status', r.message.pv_Vrfctn)
				frm.set_value('reason', r.message.pv_Rsn)
				frm.set_value('beneficiary_name', r.message.pv_Nm)
				frm.set_value('fp_verificaion_id', r.message.pv_FPVrfctn)
				frm.set_value('our_verification_id', r.message.our_verf_id)
				frm.set_value('zone', r.message.pv_Nm.substring(r.message.pv_Nm.length - 2))
				frm.remove_custom_button('Verification');
			}else{
				frm.set_value('payment_status', r.message.pv_Vrfctn)
				frm.set_value('reason', r.message.pv_Rsn)
			}
			frm.save()
		}
	})
}

function get_client_info_on_click(frm){
	frappe.call({
		"method": "money_transfer.money_transfer.doctype.bank_payment_order.bank_payment_order.getClientInfo",
		"args": {
			'client_no': frm.doc.client_no, 
			'client_seril': frm.doc.account_sequence, 
			'branch_name': frm.doc.branch, 
			'currency': frm.doc.currency,
			'amount': frm.doc.amount
		},
		callback: function(r) {
			if(r.message.error_msg != ''){
				frm.set_value('transaction_notes', r.message.error_msg)
				frm.set_value('transaction_status', __('False'))
			}else{
				frm.set_value('client_name', r.message.client_name)
				frm.set_value('region_code', r.message.client_region_code)
				frm.set_value('region', r.message.client_region)
				frm.remove_custom_button('Get Client Information');
				frm.add_custom_button(__('Verification'), function(){
					verification_on_click(frm);
				})
				frm.set_value('transaction_notes', __('Client information has been fetched'))
				frm.set_value('transaction_status', __('True'))
			}
			frm.save()	
		}
	});	

}