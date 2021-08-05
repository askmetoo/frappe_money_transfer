import frappe
from frappe.exceptions import RetryBackgroundJobError
import shutil


def validate_req_bank(bank_id):
	bank_code = frappe.db.get_value("Bank Company", {"system_code":bank_id, "is_active":1, "is_local":0}, ["company_code"])
	return True if bank_code else False

def save_verification_req_db(client_no, bank_header, req_bank_id, bank_biz_msg_idr_serial, req_verification_biz_msg_idr, res_verification_biz_msg_idr, biz_msg_idr, req_bank_msg_id, req_prtry_type, reason_true_false, reason_msg, req_bank_start_date, res_bank_start_date, customer_error, error_flg):
	vrfctn_doc = frappe.get_doc({
		"doctype": 'Bank Verification Received',
		"owner": "Administrator",
		"modified_by": "Administrator",
		"req_bank_id": req_bank_id,
		"req_bank_vrfctn_id": req_bank_msg_id,
		"req_bank_acct_id": client_no,
		"req_bank_prtry_id": req_prtry_type,
		"req_bank_biz_msg_idr": biz_msg_idr,
		"req_bank_msg_def_idr": req_verification_biz_msg_idr,
		"req_bank_cre_dt": req_bank_start_date,
		"res_bank_id": bank_header,
		"res_bank_biz_msg_idr": bank_biz_msg_idr_serial,
		"res_bank_msg_def_idr": res_verification_biz_msg_idr,
		"res_bank_cre_dt": res_bank_start_date,
		"res_bank_rpt_vrfctn": reason_true_false,
		"res_bank_rpt_prtry": reason_msg,
		"customer_error": customer_error,
		"error_flg": error_flg
	})
	vrfctn_doc.insert(ignore_permissions=True)
	return vrfctn_doc.name

def validate_account_type(account_type):
	system_code = frappe.db.get_value("Bank Account Type", {"system_code":account_type, "is_active":1}, ["system_code"])
	return True if system_code else False


def save_verification_file_db(site_name, file_name, file_path, private_path, relative_path, doc_name):
	doc = 'Bank Verification Received'
	file = frappe.get_doc({
		"doctype":"File", 'file_url':  None, 'file_name': file_name,
		'is_private':1, 'attached_to_name':doc_name, "attached_to_doctype":doc  })
	file.insert(ignore_permissions=True)

	shutil.move(file_path, site_name + private_path + relative_path + '/' + file_name)
	new_url = private_path + relative_path + '/' + file_name
	
	frappe.db.sql('UPDATE tabFile SET file_url=%s WHERE name=%s', (new_url,file.name))

def check_duplicate_payment(req_bank_tx_id):
	tx_id = frappe.db.get_value("Bank Payment Received", {"req_bank_tx_id": req_bank_tx_id}, ["req_bank_tx_id"])
	return 1 if tx_id else 0

def check_verification(req_bank_tx_id):
	(req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_cre_dt, res_bank_rpt_vrfctn, 
	res_bank_rpt_prtry) = frappe.db.get_value("Bank Verification Received", {"req_bank_vrfctn_id": req_bank_tx_id}, ["req_bank_id", "req_bank_acct_id", "req_bank_prtry_id", "req_bank_cre_dt", "res_bank_rpt_vrfctn", "res_bank_rpt_prtry"])
	result = 1 if req_bank_id else 0
	return result, req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_cre_dt, res_bank_rpt_vrfctn, res_bank_rpt_prtry

def save_payment_req_db(req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, 
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt,  req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls,  req_bank_acct_id, req_bank_prtry_id,  req_bank_dbtr_acct_issr,
    req_bank_bldg_nb, req_bank_dbtr_agt_issr, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_ustrd, req_bank_debit_id, req_bank_debit_prt,
	res_bank_id, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, res_bank_tx_sts):
	payment_doc = frappe.get_doc({
		"doctype": 'Bank Verification Received',
		"owner": "Administrator",
		"modified_by": "Administrator",
		"req_bank_id": req_bank_id,
		"req_bank_biz_msg_idr": req_bank_biz_msg_idr,
		"req_bank_msg_def_idr": req_bank_msg_def_idr,
		"req_bank_cre_dt": req_bank_cre_dt,
		"req_bank_cre_dt_tm": req_bank_cre_dt_tm,
		"req_bank_accptnc_dt_tm": req_bank_accptnc_dt_tm,
		"req_bank_sttlm_mtd": req_bank_sttlm_mtd,
		"req_bank_lcl_instrm": req_bank_lcl_instrm,
		"req_bank_tx_id": req_bank_tx_id,
		"req_bank_intr_bk_sttlm_amt": req_bank_intr_bk_sttlm_amt,
		"req_bank_chrg_br": req_bank_chrg_br,
		"req_bank_dbtr": req_bank_dbtr_name,
		"req_bank_pstl_adr": req_bank_pstl_adr,
		"req_bank_ctct_dtls": req_bank_dbtr_ctct_dtls,
		"req_bank_acct_id": req_bank_acct_id,
		"req_bank_prtry_id": req_bank_prtry_id,
		"req_bank_dbtr_acct_issr": req_bank_dbtr_acct_issr,
		"req_bank_bldg_nb": req_bank_bldg_nb,
		"req_bank_dbtr_agt_issr": req_bank_dbtr_agt_issr,
		"req_bank_brnch_id": req_bank_brnch_id,
		"req_bank_cdtr_nm": req_bank_cdtr_nm,
		"req_bank_ustrd": req_bank_ustrd,
		"res_bank_id": res_bank_id,
		"res_bank_biz_msg_idr": res_bank_biz_msg_idr,
		"res_bank_msg_def_idr": res_bank_msg_def_idr,
		"res_bank_cre_dt": res_bank_cre_dt,
		"res_bank_tx_sts": res_bank_tx_sts,
		"timer_exceed_flg": "0",
		"status_received_flg": "0",
		"req_bank_debit_prt": req_bank_debit_prt,
		"req_bank_debit_id": req_bank_debit_id
	})
	payment_doc.insert(ignore_permissions=True)
	return payment_doc.name