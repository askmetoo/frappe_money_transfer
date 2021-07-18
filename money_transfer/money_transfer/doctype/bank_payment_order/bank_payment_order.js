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
				if(frm.doc.transaction_state_sequence == 'UnPost'){
					frm.add_custom_button(__('Push Payment'), function(){
					});
					frm.add_custom_button(__('Cancel The Operation'), function(){
						cancel_on_click(frm);
					});
				}
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
			'client_no': frm.doc.client_no, 
			'client_seril': frm.doc.account_sequence, 
			'our_bank': frm.doc.sender_bank,
			'dest_bank': frm.doc.receiver_bank,
			'beneficiary_no': frm.doc.beneficiary_no,
			'account_type': frm.doc.account_type,
			'doc_name': frm.doc.name,
			'user_branch': frm.doc.branch,
			'amount': frm.doc.amount,
			'currency': frm.doc.currency
		},
		callback: function(r) {
			if(r.message.pv_Vrfctn == "true"){
				frm.set_value('payment_status', r.message.pv_Vrfctn)
				frm.set_value('reason', r.message.pv_Rsn)
				frm.set_value('beneficiary_name', r.message.pv_Nm)
				frm.set_value('fp_verification_id', r.message.pv_FPVrfctn)
				frm.set_value('our_verification_id', r.message.our_verf_id)
				frm.set_value('zone', r.message.pv_Nm.substring(r.message.pv_Nm.length - 2))
				frm.remove_custom_button('Verification');
				frm.set_value('transaction_state_sequence', 'UnPost')
				
			}else{
				frm.set_value('payment_status', r.message.pv_Vrfctn)
				frm.set_value('reason', r.message.pv_Rsn)
			}
			if(r.message.result == 'Success'){
				frm.set_value('transaction_status', r.message.result)
				frm.set_value('sender_bank_fee', r.message.retail)
				frm.set_value('swift_fee', r.message.switch)
				frm.set_value('receiver_bank_fee', r.message.interchange)

			}else{
				frm.set_value('transaction_status', r.message.result)
				frm.set_value('transaction_notes', r.message.errordesc)
			}
			if(r.message.error_msg != ''){
				frm.set_value('transaction_state_sequence', 'Idle')
				frm.set_value('transaction_status', 'false')
				frm.set_value('transaction_notes', r.message.error_msg)
			}
			frm.save()
		}
	})
}

function get_client_info_on_click(frm){
	frappe.call({
		"method": "money_transfer.money_transfer.doctype.bank_payment_order.bank_payment_order.get_client_info",
		"args": {
			'client_no': frm.doc.client_no, 
			'client_seril': frm.doc.account_sequence, 
			'branch_name': frm.doc.branch, 
			'currency': frm.doc.currency
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
				frm.set_value('transaction_notes', __('Client information fetched successfully'))
				frm.set_value('transaction_status', __('True'))
			}
			frm.save().then(()=>frm.set_value('serial_no', frm.doc.name))
			
		}
	});	

}

function cancel_on_click(frm){
	frappe.call({
		"method": "money_transfer.money_transfer.doctype.bank_payment_order.bank_payment_order.cancel_reservation",
		"args": {
			'client_no': frm.doc.client_no, 
			'client_seril': frm.doc.account_sequence, 
			'user_branch': frm.doc.branch, 
			'currency': frm.doc.currency,
			'amount': frm.doc.amount,
			'rcv_fee': frm.doc.receiver_bank_fee , 
			'swift_fee': frm.doc.swift_fee, 
			'snd_fee': frm.doc.sender_bank_fee, 
			'beneficiary_name': frm.doc.beneficiary_name,
			'fp_verification_id': frm.doc.fp_verification_id
		},
		callback: function(r) {
			if(r.message.error_msg != ''){
				frm.set_value('transaction_notes', r.message.error_msg)
				frm.set_value('transaction_status', __('False'))
			}else{
				frm.remove_custom_button('Push Payment');
				frm.remove_custom_button('Cancel The Operation');

				frm.set_value('transaction_notes', __('The operation canceled successfully'))
				frm.set_value('transaction_status', __('True'))
				frm.set_value('transaction_state_sequence', 'Cancel')
				
			}
			frm.save()	
		}
	});	
}