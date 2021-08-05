// Copyright (c) 2021, omar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bank Payment Order', {
	before_load: function(frm){
		frm.disable_save();
		
	},
	refresh: function(frm) {
		check_payment_type(frm);
		check_buttons(frm);
		// if(frm.doc.client_name == '_'){
		// 	frm.add_custom_button(__('Get Client Information'), function(){
		// 		get_client_info_on_click(frm)
		// 	});
		// }else{
		// 	if(frm.doc.beneficiary_name == '_'){
		// 		frm.set_df_property("payment_method", 'read_only', 1)
		// 		frm.add_custom_button(__('Verification'), function(){
		// 			verification_on_click(frm);
		// 		});
		// 	}else{
		// 		frm.set_df_property("payment_method", 'read_only', 1)
		// 		if(frm.doc.transaction_state_sequence == 'UnPost'){
		// 			frm.add_custom_button(__('Push Payment'), function(){
		// 				push_payment_on_click(frm);
		// 			});
		// 			frm.add_custom_button(__('Cancel The Operation'), function(){
		// 				cancel_on_click(frm);
		// 			});
		// 		}
		// 	}
				
		// }
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
	},
	on_load: function(frm){
		
	},
	after_save: function(frm){
		update_date_time(frm);
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
	},
	payment_method: function(frm){
		check_payment_type(frm);
		check_buttons(frm);
	}
});
function check_payment_type(frm){
	var payment_type = get_payment_type(frm.doc.payment_method);
	if (payment_type == 1 || payment_type == 2){
		frm.set_df_property('client_no','hidden',0);
		frm.set_df_property('account_sequence','hidden',0);
		frm.set_df_property('client_name','hidden',0);
		frm.set_df_property('region_code','hidden',0);
		frm.set_df_property('region','hidden',0);
		frm.set_df_property('card_type','hidden',1);
		frm.set_df_property('card_no','hidden',1);
		frm.remove_custom_button('Verification');
	}else{
		frm.set_df_property('client_no','hidden',1);
		frm.set_df_property('account_sequence','hidden',1);
		frm.set_df_property('client_name','hidden',1);
		frm.set_df_property('region_code','hidden',1);
		frm.set_df_property('region','hidden',1);
		frm.set_df_property('card_type','hidden',0);
		frm.set_df_property('card_no','hidden',0);
	}
}
function check_buttons(frm){
	remove_buttons(frm);
	var payment_type = get_payment_type(frm.doc.payment_method);
	if(frm.doc.transaction_state_sequence == 'Post' || frm.doc.transaction_state_sequence == 'Cancel') {
		frm.set_df_property("payment_method", 'read_only', 1)
		return;
	}
	if(frm.doc.transaction_state_sequence == 'UnPost'){
		frm.set_df_property("payment_method", 'read_only', 1)
		frm.add_custom_button(__('Push Payment'), function(){
			push_payment_on_click(frm);
		});
		if(payment_type == 1 || payment_type == 2){
			frm.add_custom_button(__('Cancel The Operation'), function(){
				cancel_on_click(frm);
			});
		}
		return;
	}
	if(frm.doc.transaction_state_sequence == '_'){
		if(payment_type == 1 || payment_type == 2){
			if(frm.doc.client_name == '_'){
				frm.add_custom_button(__('Get Client Information'), function(){
					get_client_info_on_click(frm)
				});
			}else{
				frm.set_df_property("payment_method", 'read_only', 1)
				frm.add_custom_button(__('Verification'), function(){
					verification_on_click(frm)
				});
			}
		}else{
			frm.add_custom_button(__('Verification'), function(){
				verification_on_click(frm)
			});
		}
	}
}
function remove_buttons(frm){
	frm.remove_custom_button('Get Client Information');
	frm.remove_custom_button('Verification');
	frm.remove_custom_button('Cancel The Operation');
	frm.remove_custom_button('Push Payment');
}
function get_payment_type(payment_method){
	if(payment_method == 'عميل - C') return 1; 
	if(payment_method == 'صندوق - C') return 3; 
	if(payment_method == 'عميل - CLIENT') return 2; 
	if(payment_method == 'صندوق - CASH') return 4;
}
function update_date_time(frm){
	var today = new Date();
	var date = today.getDate()+'/'+(today.getMonth()+1)+'/'+today.getFullYear();
	var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
	frm.set_value('date', date)
	frm.set_value('time', time)
}

function verification_on_click(frm){
	var payment_method = get_payment_type(frm.doc.payment_method);
	var client_no = ''
	if(payment_method == 1 || payment_method == 2){
		client_no = frm.doc.client_no;
		verification_call(client_no, frm);
	}
	else{
		frm.save().then(()=>{
			frm.set_value('serial_no', frm.doc.name);
			verification_call(client_no, frm);
		})
	}
}
function verification_call(client_no, frm){
	frappe.call({
		"method": "money_transfer.money_transfer.doctype.bank_payment_order.bank_payment_order.verification",
		"args": {
			'client_no': client_no, 
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
				frm.set_value('verification_status', r.message.pv_Vrfctn)
				frm.set_value('reason', r.message.pv_Rsn)
				frm.set_value('beneficiary_name', r.message.pv_Nm)
				frm.set_value('fp_verification_id', r.message.pv_FPVrfctn)
				frm.set_value('our_verification_id', r.message.our_verf_id)
				frm.set_value('zone', r.message.pv_Nm.substring(r.message.pv_Nm.length - 2))
				frm.remove_custom_button('Verification');
				
			}else{
				frm.set_value('verification_status', r.message.pv_Vrfctn)
				frm.set_value('reason', r.message.pv_Rsn)
				frm.set_value('transaction_notes', r.message.errordesc)
				frm.set_value('transaction_state_sequence', 'Cancel')
				frm.save()
				return;
			}
			if(r.message.result == 'Success'){
				frm.set_value('transaction_status', r.message.result)
				frm.set_value('sender_bank_fee', r.message.retail)
				frm.set_value('swift_fee', r.message.switch)
				frm.set_value('receiver_bank_fee', r.message.interchange)

			}else{
				frm.set_value('transaction_status', r.message.result)
				frm.set_value('transaction_notes', r.message.errordesc)
				frm.set_value('transaction_state_sequence', 'Cancel')
				frm.save()
				return;
			}
			if(r.message.error_msg != ''){
				frm.set_value('transaction_state_sequence', 'Idle')
				frm.set_value('transaction_status', 'false')
				frm.set_value('transaction_notes', r.message.error_msg)
			}else{
				frm.set_value('transaction_state_sequence', 'UnPost')
				frm.set_value('client_name', r.message.client_name)
				frm.set_value('region_code', r.message.client_region_code)
				frm.set_value('region', r.message.client_address)
			}
			frm.save()
		}
	})
}
function get_client_info_on_click(frm){
	var missed_fields = show_missed_fields(frm, ['sender_bank','client_no', 'account_sequence', 'branch', 'currency'])
	if(missed_fields) return;
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

function push_payment_on_click(frm){
	var payment_method = get_payment_type(frm.doc.payment_method);
	var client_no = ''
	var card_no = ''
	var card_type = ''
	if(payment_method == 1 || payment_method == 2){
		client_no = frm.doc.client_no;
	}else{
		card_no = frm.doc.card_no;
		card_type = frm.doc.card_type;
	}
	frappe.call({
		"method": "money_transfer.money_transfer.doctype.bank_payment_order.bank_payment_order.push_payment",
		"args":{
			'doc_name': frm.doc.name,
			'payment_method': payment_method,
			'client_no':client_no,
			'client_serial': frm.doc.account_sequence, 
			'our_client_name': frm.doc.client_name, 
			'our_client_address': frm.doc.region, 
			'our_bank': frm.doc.sender_bank, 
			'our_branch': frm.doc.branch, 
			'region_code': frm.doc.region_code,
			'dest_bank': frm.doc.receiver_bank, 
			'fp_verification_id': frm.doc.fp_verification_id, 
			'amount': frm.doc.amount,
			'rcv_fee': frm.doc.receiver_bank_fee,
			'snd_fee': frm.doc.sender_bank_fee, 
			'swift_fee': frm.doc.swift_fee,
			'currency': frm.doc.currency, 
			'beneficiary_name': frm.doc.beneficiary_name, 
			'beneficiary_no': frm.doc.beneficiary_no, 
			'account_type': frm.doc.account_type, 
			'op_type': frm.doc.type,
			'card_no': card_no,
			'card_type': card_type
		},
		callback: function(r) {
			frm.set_value('payment_status', r.message.res_status)
			frm.set_value('transaction_status', r.message.journal_status)
			if(r.message.cancellation_msg != ''){
				frm.set_value('transaction_notes', r.message.cancellation_msg)
				frm.set_value('transaction_state_sequence', 'UnPost')
			}
			else if(r.message.journal_msg != ''){
				frm.set_value('transaction_notes', r.message.journal_msg)
				frm.set_value('transaction_state_sequence', 'Cancel')
			}else{
				if(r.message.res_status == 'ACSC')
					frm.set_value('transaction_state_sequence', 'Post')
				else
					frm.set_value('transaction_state_sequence', 'Cancel')
			}
			frm.save()
		}
	})
}

function show_missed_fields(frm, fields){
	
	for(let field of fields){

		if(frm.doc[field] == '-' || frm.doc[field] == '_' || frm.doc[field] == '' || !frm.doc[field]){
			frappe.msgprint(__('Please fill ') + __(field))
			return true
		}
	}
	return false
}
	