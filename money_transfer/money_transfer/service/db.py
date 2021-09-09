from datetime import datetime
import frappe
from frappe.exceptions import RetryBackgroundJobError
import shutil

from money_transfer.money_transfer.utils import console_print


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
		"error_flg": error_flg,
		"creation_date_time": datetime.now()
	})
	vrfctn_doc.insert(ignore_permissions=True)
	frappe.db.commit()
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
	frappe.db.commit()

def save_payment_file_db(site_name, file_name, file_path, private_path, relative_path, doc_name):
	doc = 'Bank Payment Received'
	file = frappe.get_doc({
		"doctype":"File", 'file_url':  None, 'file_name': file_name,
		'is_private':1, 'attached_to_name':doc_name, "attached_to_doctype":doc  })
	file.insert(ignore_permissions=True)

	shutil.move(file_path, site_name + private_path + relative_path + '/' + file_name)
	new_url = private_path + relative_path + '/' + file_name
	
	frappe.db.sql('UPDATE tabFile SET file_url=%s WHERE name=%s', (new_url,file.name))
	frappe.db.commit()

def save_status_file_db(site_name, file_name, file_path, private_path, relative_path, doc_name):
	doc = 'Bank Status Received'
	file = frappe.get_doc({
		"doctype":"File", 'file_url':  None, 'file_name': file_name,
		'is_private':1, 'attached_to_name':doc_name, "attached_to_doctype":doc  })
	file.insert(ignore_permissions=True)

	shutil.move(file_path, site_name + private_path + relative_path + '/' + file_name)
	new_url = private_path + relative_path + '/' + file_name
	
	frappe.db.sql('UPDATE tabFile SET file_url=%s WHERE name=%s', (new_url,file.name))
	frappe.db.commit()

def check_duplicate_payment(req_bank_tx_id):
	tx_id = frappe.db.get_value("Bank Payment Received", {"req_bank_tx_id": req_bank_tx_id}, ["req_bank_tx_id"])
	return 1 if tx_id else 0

def check_verification(req_bank_tx_id):
	res = frappe.db.get_value("Bank Verification Received", {"req_bank_vrfctn_id": req_bank_tx_id}, ["req_bank_id", "req_bank_acct_id", "req_bank_prtry_id", "req_bank_cre_dt", "res_bank_rpt_vrfctn", "res_bank_rpt_prtry", "creation_date_time"])
	result = 1 if res else 0
	if result == 1:
		(req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_cre_dt, res_bank_rpt_vrfctn, 
		res_bank_rpt_prtry, creation) = res
	else:
		req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_cre_dt, res_bank_rpt_vrfctn, res_bank_rpt_prtry, creation = "", "", "", "", "", "", ""
	return result, req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_cre_dt, res_bank_rpt_vrfctn, res_bank_rpt_prtry, creation

def save_payment_req_db(req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, 
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy,  req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls,  req_bank_acct_id, req_bank_prtry_id,  req_bank_dbtr_acct_issr,
    req_bank_bldg_nb, req_bank_dbtr_agt_issr, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_ustrd, req_bank_debit_id, req_bank_debit_prt,
	res_bank_id, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, res_bank_tx_sts):
	payment_doc = frappe.get_doc({
		"doctype": 'Bank Payment Received',
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
		"req_bank_intr_bk_sttlm_amt_ccy": req_bank_intr_bk_sttlm_amt_ccy,
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
		"time_exceed_flg": "0",
		"status_recieved_flg": "0",
		"req_bank_debit_prt": req_bank_debit_prt,
		"req_bank_debit_id": req_bank_debit_id
	})
	payment_doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return payment_doc.name

def get_payment_status_flgs(doc_name):
	res = frappe.db.get_value("Bank Payment Received", doc_name, ["time_exceed_flg", "status_recieved_flg", "res_bank_tx_sts"])
	#res = frappe.get_doc( doctype="Bank Payment Received", filters={"name": doc_name})
	if res:
		timer_flg, status_flg, res_bank_tx_sts = res#res.time_exceed_flg, res.status_recieved_flg
		timer_flg = 0 if not timer_flg else int(timer_flg)
		status_flg = 0 if not status_flg else int(status_flg)
		res_bank_tx_sts = '' if not res_bank_tx_sts else res_bank_tx_sts
		return int(timer_flg), int(status_flg), res_bank_tx_sts
	else:
		return 0, 0, ''

def get_psh_status_flg(req_bank_tx_id):
	flg = frappe.db.get_value("Bank Payment Received", {"req_bank_tx_id": req_bank_tx_id}, ["psh_sts_rcv_flg"])
	return int(flg) if flg else 99

def update_timer_flg(doc_name, timer):
	#frappe.db.set_value("Bank Payment Received", {"req_bank_tx_id": req_bank_tx_id}, {"time_exceed_flg": str(timer)})
	# payment_doc = frappe.get_doc(doctype="Bank Payment Received", filters={"req_bank_tx_id": req_bank_tx_id})
	# payment_doc.time_exceed_flg = str(timer)
	# payment_doc.save(ignore_permissions=True)
	frappe.db.set_value("Bank Payment Received", doc_name, {
		'time_exceed_flg': str(timer)
	})
	frappe.db.commit()

def update_psh_status(doc_name, flg, txt, error=''):
	#frappe.db.set_value("Bank Payment Received", {"req_bank_tx_id": req_bank_tx_id}, {"time_exceed_flg": str(timer)})
	# if doc_name is None:
	# 	payment_doc = frappe.get_doc(doctype="Bank Payment Received", filters={"req_bank_tx_id": req_bank_tx_id})
	# else:
	# 	payment_doc = frappe.get_doc(doctype="Bank Payment Received", filters={"name": doc_name})
	# payment_doc.psh_sts_rcv_flg = str(flg)
	# payment_doc.psh_sts_rcv_txt = str(txt)
	# if error != '':
	# 	payment_doc.sts_rcv_err_desc = error
	# payment_doc.save(ignore_permissions=True)
	frappe.db.set_value("Bank Payment Received", doc_name, {
		'psh_sts_rcv_flg': str(flg),
		'psh_sts_rcv_txt': str(txt),
		'sts_rcv_err_desc': error
	})
	frappe.db.commit()

def update_status_flg(doc_name, flg):
	frappe.db.set_value("Bank Payment Received", doc_name, {
		'status_recieved_flg': str(flg)
	})
	frappe.db.commit()

def get_payment_status_data(doc_name):
	res = frappe.db.get_value("Bank Payment Received", doc_name, ["res_bank_id", "res_bank_biz_msg_idr", "req_bank_biz_msg_idr"])
	if res:
		res_bank_id, res_bank_biz_msg, req_bank_biz_msg = res
	else:
		res_bank_id, res_bank_biz_msg, req_bank_biz_msg = '', '', ''
	res_bank_id = res_bank_id if res_bank_id else ""
	res_bank_biz_msg = res_bank_biz_msg if res_bank_biz_msg else ""
	req_bank_biz_msg = req_bank_biz_msg if req_bank_biz_msg else ""
	return res_bank_id, res_bank_biz_msg, req_bank_biz_msg

def get_fees_data(doc_name):
	res = frappe.db.get_value("Bank Payment Received", doc_name, ["res_bank_id", "req_bank_id", "req_bank_bldg_nb", "req_bank_acct_id", "req_bank_intr_bk_sttlm_amt"])
	try:
		res_bank_id, req_bank_id, req_bank_bldg, req_bank_acct, req_bank_amt = res
		currency = req_bank_acct[13:15]
		currency_code = frappe.db.get_value("Bank Currency", {"system_code": currency},["currency_code"] )
		
		bank_name, fees_password = frappe.db.get_value("Bank Company", {"system_code": req_bank_id}, ["name","fees_password"])
		
		branch_code = req_bank_acct[0:3]
		branch_region_id = frappe.db.get_value("Bank Branch", {"bank":bank_name, "branch_code":branch_code}, ["branch_region"])
		our_zone_code = frappe.db.get_value("Bank Region", branch_region_id, ["unique_code"])
		
		return res_bank_id, req_bank_id, req_bank_bldg, req_bank_acct, req_bank_amt, currency_code, fees_password, our_zone_code
	except:
		return "", "", "", "", "", "", "", ""

def update_payment_fees_data(doc_name, retail, switch, interchange, transaction_id, result, error_desc):
	# payment_doc = frappe.get_doc(doctype="Bank Payment Received", filters={"req_bank_tx_id": req_orgnl_tx_id})
	# payment_doc.retail_fees = retail
	# payment_doc.switch_fees = switch
	# payment_doc.interchange_fees = interchange
	# payment_doc.transaction_id_fees = transaction_id
	# payment_doc.result_fees = result
	# payment_doc.error_desc_fees = error_desc
	# payment_doc.save(ignore_permissions=True)
	frappe.db.set_value("Bank Payment Received", doc_name, {
		"retail_fees": retail,
		"switch_fees":switch,
		"interchange_fees":interchange,
		"transaction_id_fees":transaction_id,
		"result_fees":result,
		"error_desc_fees":error_desc,
	})
	frappe.db.commit()

def get_status_data(req_bank_tx_id):
	res = frappe.db.get_value("Bank Payment Received", {"req_bank_tx_id":req_bank_tx_id}, ["name","req_bank_id", "req_bank_acct_id", "req_bank_prtry_id", "req_bank_intr_bk_sttlm_amt", "req_bank_intr_bk_sttlm_amt_ccy", "res_bank_tx_sts", "time_exceed_flg", "status_recieved_flg", "req_bank_debit_id", "req_bank_debit_prt"])
	if res:
		(doc_name, req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy,
		 res_bank_tx_sts, timer_exceed_flg, status_recieved_flg, req_bank_debit_id, req_bank_debit_prt) = res
		doc_name = doc_name if doc_name else ""
		req_bank_id = req_bank_id if req_bank_id else ""
		req_bank_acct_id = req_bank_acct_id if req_bank_acct_id else ""
		req_bank_prtry_id = req_bank_prtry_id if req_bank_prtry_id else ""
		req_bank_intr_bk_sttlm_amt = req_bank_intr_bk_sttlm_amt if req_bank_intr_bk_sttlm_amt else ""
		req_bank_intr_bk_sttlm_amt_ccy = req_bank_intr_bk_sttlm_amt_ccy if req_bank_intr_bk_sttlm_amt_ccy else ""
		res_bank_tx_sts = res_bank_tx_sts if res_bank_tx_sts else ""
		timer_exceed_flg = int(timer_exceed_flg) if timer_exceed_flg else 0
		status_recieved_flg = int(status_recieved_flg) if status_recieved_flg else 0
		req_bank_debit_id = req_bank_debit_id if req_bank_debit_id else ""
		req_bank_debit_prt = req_bank_debit_prt if req_bank_debit_prt else ""
		res_status = True
	else:
		(res_status, doc_name, req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy,
		 res_bank_tx_sts, timer_exceed_flg, status_recieved_flg, req_bank_debit_id, req_bank_debit_prt) = False, "","", "", "", "", "","", 0, 0, "", ""
	return res_status, doc_name, req_bank_id, req_bank_acct_id, req_bank_prtry_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy, res_bank_tx_sts, timer_exceed_flg, status_recieved_flg, req_bank_debit_id, req_bank_debit_prt


def save_status_req_db(header_form, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm, 
res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, req_tx_sts, req_sts_flg, req_intr_bk_sttlm_amt, req_intr_bk_sttl_amt_ccy,
req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id):
	status_doc = frappe.get_doc({
		"doctype": 'Bank Status Received',
		"owner": "Administrator",
		"modified_by": "Administrator",
		"header_from": header_form,
		"header_to": header_to,
		"req_bank_idr": req_bank_id,
		"req_bank_biz_msg_idr": req_bank_biz_msg_idr,
		"req_bank_msg_def_idr": req_bank_msg_def_idr,
		"req_bank_cre_dt": req_bank_cre_dt,
		"res_bank_biz_msg_idr": res_bank_biz_msg_idr,
		"res_bank_msg_def_idr": res_bank_msg_def_idr,
		"res_bank_cre_dt": res_bank_cre_dt,
		"req_bank_msg_id": req_bank_msg_id,
		"req_bank_cre_dt_tm": req_bank_cre_dt_tm,
		"req_bank_accptnc_dt_tm": req_bank_accptnc_dt_tm,
		"res_orgnl_msg_id": res_orgnl_msg_id,
		"res_orgnl_msg_nm_id": res_orgnl_msg_nm_id,
		"res_orgnl_cre_dt_tm": res_orgnl_cre_dt_tm,
		"req_orgnl_tx_id": req_orgnl_tx_id,
		"req_accptnc_dt_tm": req_accptnc_dt_tm,
		"req_tx_sts": req_tx_sts,
		"req_tx_sts_flg": req_sts_flg,
		"req_intr_bk_sttlm_amt": req_intr_bk_sttlm_amt,
		"req_intr_bk_sttlm_amt_ccy": req_intr_bk_sttl_amt_ccy,
		"req_adr_line": req_adr_line,
		"req_nm": req_nm,
		"req_bank_client_id": req_bank_client_id,
		"req_bank_prtry_id": req_bank_prtry_id,
	})
	status_doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return status_doc.name