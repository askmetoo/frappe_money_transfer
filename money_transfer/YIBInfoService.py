from math import exp
import sys
import frappe
import threading
from frappe.database.database import enqueue_jobs_after_commit 
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from money_transfer.money_transfer.service.utils import background, get_service_files_names
from money_transfer.money_transfer.service.xml_handler import create_push_status_xml_doc, read_push_status_xml, read_status_xml, save_xml, read_xml_verification, create_verification_res_xml, get_xml_response, read_xml_payment, create_payment_res_xml, save_xml_prtfy, create_status_res_xml
from money_transfer.money_transfer.service.db import save_status_file_db, get_payment_status_data, get_psh_status_flg, get_status_data, save_payment_file_db, update_psh_status, update_status_flg, validate_req_bank, validate_account_type, save_verification_file_db, update_timer_flg, get_payment_status_flgs, get_fees_data, update_payment_fees_data
from money_transfer.money_transfer.service.socket_handler import get_customer_details, make_payment_for_customer

from money_transfer.money_transfer.db import get_table_serial_key
from money_transfer.money_transfer.xml_handler import create_fees_xml_doc, read_xml_fees_data
from money_transfer.money_transfer.utils import get_current_site_name, console_print

import money_transfer.money_transfer.service.const as const
from frappe.utils.background_jobs import enqueue, get_queue
import time
import json
@frappe.whitelist(allow_guest=True)
def Verification():
	# Get All Files Names & Paths
	req_file_name, res_file_name, req_xml_path, res_xml_path, site_name, private_path,  req_path, res_path = get_service_files_names('Verification', 'VerificationFileSerIn')
	if frappe.request.data:
		req_xml = frappe.request.data
		# Save Request Xml File to Server
		save_xml_prtfy(req_xml_path, req_xml)
		res_xml, doc_name = validate_verification_request(req_xml)
		# Save Request Xml File to Database
		save_verification_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	else:
		res_xml, doc_name = create_verification_res_xml(" ", " ", const.BANK_HEADER_NAME, " ", const.FP_HEADER, " ", " ", " ", " ", " ", " ", "false", const.TECHNICAL_ERROR, " ", " ", 1)
	# Save Response Xml File to Server & Database
	save_xml(res_xml_path, res_xml)
	save_verification_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)
	# Get Response Data
	response = get_xml_response(res_xml)

	return response

@frappe.whitelist(allow_guest=True)
def Payment():
	# Get All Files Names & Paths
	req_file_name, res_file_name, req_xml_path, res_xml_path, site_name, private_path,  req_path, res_path = get_service_files_names('Payment', 'PaymentFileSerIn')
	if frappe.request.data:
		req_xml = frappe.request.data
		# Save Request Xml File to Server
		save_xml_prtfy(req_xml_path, req_xml)
		res_xml, req_bank_tx_id, doc_name = validate_payment_request(req_xml)
		# Save Request Xml File to Database
		save_payment_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
		args = {"req_bank_tx_id": req_bank_tx_id, "doc_name":doc_name}
		status_timer = threading.Timer(10, on_time_event, kwargs=args)
		#status_timer = threading.Thread(target=on_time_event, name="Downloader", kwargs=args)
		status_timer.start()
		# on_time_event(req_bank_tx_id, doc_name)
	else:
		res_xml, doc_name = create_payment_res_xml(const.BANK_HEADER_NAME, const.FP_HEADER, " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " "," ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ")
	# Save Response Xml File to Server & Database
	save_xml(res_xml_path, res_xml)
	save_payment_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)
	# Get Response Data
	response = get_xml_response(res_xml)

	return response

@frappe.whitelist(allow_guest=True)
def Status2():
	# Get All Files Names & Paths
	req_file_name, res_file_name, req_xml_path, res_xml_path, site_name, private_path,  req_path, res_path = get_service_files_names('Status', 'StatusFileSerIn')
	if frappe.request.data:
		req_xml = frappe.request.data
		# Save Request Xml File to Server
		save_xml_prtfy(req_xml_path, req_xml)
		res_xml, doc_name = validate_status_request(req_xml)
		# Save Request Xml File to Database
		save_status_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	else:
		res_xml, doc_name = create_status_res_xml(" ",const.BANK_HEADER_NAME, const.FP_HEADER, " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", const.TECHNICAL_ERROR, "false", " ", " ", " ", " ", " ", " ", " ", " ")
	# Save Response Xml File to Server & Database
	save_xml(res_xml_path, res_xml)
	save_status_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)
	# Get Response Data
	response = get_xml_response(res_xml)

	return response

def validate_verification_request(verification_xml):
	fp_header, bank_header_id, bank_document_id, req_bank_id, req_bank_msg_id, biz_msg_idr, msg_def_idr, prtry_type, client_no, req_bank_cre_dt = read_xml_verification(verification_xml)
	our_biz_msg_idr_serial = get_table_serial_key('VerificationSerialIn_RS')	
	if not validate_req_bank(req_bank_id):
		verification_res, doc_name = create_verification_res_xml(client_no, "xxxxx", const.BANK_HEADER_NAME, req_bank_id, const.FP_HEADER, str(our_biz_msg_idr_serial), const.REQ_VERIFICATION_BIZ_MSG_IDR, const.RES_VERIFICATION_BIZ_MSG_IDR, biz_msg_idr, req_bank_msg_id, prtry_type, "false", const.WRONG_BIC, req_bank_cre_dt, " ", 1)
	else:
		if not validate_account_type(prtry_type):
			verification_res, doc_name = create_verification_res_xml(client_no, "xxxxx", const.BANK_HEADER_NAME, req_bank_id, const.FP_HEADER, str(our_biz_msg_idr_serial), const.REQ_VERIFICATION_BIZ_MSG_IDR, const.RES_VERIFICATION_BIZ_MSG_IDR, biz_msg_idr, req_bank_msg_id, prtry_type, "false", const.USER_NOT_FOUND, req_bank_cre_dt, " ", 1)
		else:
			customer_name, customer_add, customer_no, customer_brn, region_unique_code, customer_error, error_flg = get_customer_details(client_no)
			if error_flg == 1 and (customer_error == 'ca601' or customer_error == 'ca830' or customer_error == 'ca600'):
				verification_res, doc_name = create_verification_res_xml(client_no, "xxxxx", const.BANK_HEADER_NAME, req_bank_id, const.FP_HEADER, str(our_biz_msg_idr_serial), const.REQ_VERIFICATION_BIZ_MSG_IDR, const.RES_VERIFICATION_BIZ_MSG_IDR, biz_msg_idr, req_bank_msg_id, prtry_type, "false", const.USER_BLOCKED, req_bank_cre_dt, customer_error, error_flg)
			else:
				if error_flg == 1:
					verification_res, doc_name = create_verification_res_xml(client_no, "xxxxx", const.BANK_HEADER_NAME, req_bank_id, const.FP_HEADER, str(our_biz_msg_idr_serial), const.REQ_VERIFICATION_BIZ_MSG_IDR, const.RES_VERIFICATION_BIZ_MSG_IDR, biz_msg_idr, req_bank_msg_id, prtry_type, "false", const.USER_NOT_FOUND, req_bank_cre_dt, customer_error,error_flg )
				else:
					client_name = customer_name.strip() + '#' + customer_add.strip() + '#' + customer_brn.strip() + '#' + region_unique_code.strip()
					verification_res, doc_name= create_verification_res_xml(client_no, client_name, const.BANK_HEADER_NAME, req_bank_id, const.FP_HEADER, str(our_biz_msg_idr_serial), const.REQ_VERIFICATION_BIZ_MSG_IDR, const.RES_VERIFICATION_BIZ_MSG_IDR, biz_msg_idr, req_bank_msg_id, prtry_type, "true", const.REQ_SUCCESS, req_bank_cre_dt, customer_error, error_flg)
	return verification_res, doc_name

def validate_payment_request(payment_xml):
	(header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, 
	req_bank_id, req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, 
	req_bank_debit_prt, req_bank_dbtr_acct_issr, req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd) = read_xml_payment(payment_xml)

	our_biz_msg_idr_serial = get_table_serial_key('PaymentSerialIn_RS')
	
	payment_res, doc_name = create_payment_res_xml(header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, req_bank_id,
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, req_bank_debit_prt, req_bank_dbtr_acct_issr, 
    req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd, our_biz_msg_idr_serial)

	return payment_res, req_bank_tx_id, doc_name

def on_time_event(req_bank_tx_id, doc_name):
	frappe.init(site=get_current_site_name())
	frappe.connect()
	frappe.clear_cache()
	timer_exceed_flg, status_received_flg, res_tx_sts = get_payment_status_flgs(doc_name)
	if status_received_flg == 1 or timer_exceed_flg >= 1 or res_tx_sts != 'ACSC':
		frappe.db.commit()
		frappe.clear_cache()
		frappe.db.close()
		frappe.destroy()
		return
	update_timer_flg(doc_name, 1)
	push_status_loop(req_bank_tx_id, doc_name)
	frappe.db.commit()
	frappe.clear_cache()
	frappe.db.close()
	frappe.destroy()

def push_status_loop(req_bank_tx_id, doc_name):
	for counter in range(5):
		psh_sts_flg = get_psh_status_flg(req_bank_tx_id)
		if int(psh_sts_flg) == 99:
			push_status(req_bank_tx_id, doc_name)
		else:
			break

def push_status(req_bank_tx_id, doc_name):
	res_bank_id, res_bank_biz_msg, req_bank_biz_msg, req_bank_acct_id = get_payment_status_data(doc_name)
	status_req_xml = create_push_status_xml_doc(req_bank_biz_msg, res_bank_id, res_bank_biz_msg, req_bank_tx_id)
	req_file_name, res_file_name, req_xml_path, res_xml_path, site_name, private_path,  req_path, res_path = get_service_files_names('PushStatus', 'StatusFileSerIn')
	save_xml(req_xml_path, status_req_xml)
	save_payment_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)

	push_status_url = frappe.db.get_value("Bank Service Control", "253", ["rec_text"])
	try:
		headers = {'Content-Type': 'application/xml'}
		res_xml = requests.post(url= push_status_url, data=status_req_xml.encode('utf-8'), headers=headers, timeout=15).text
		save_xml_prtfy(res_xml_path, res_xml)
		save_payment_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)
		validate_push_status_res(res_xml, doc_name, req_bank_acct_id, req_bank_tx_id)
	except requests.Timeout:
		try:
			update_psh_status(doc_name, '99', 'pushstatus time out')
		except:
			update_psh_status(doc_name, '99', '')
	except:
		try:
			update_psh_status(doc_name, '99', sys.exc_info()[0])
		except:
			update_psh_status(doc_name, '99', '')

def validate_push_status_res(status_res_xml, doc_name, rv_req_bank_acct_id, req_bank_tx_id):
	(header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt,
            req_bank_cre_dt_tm, req_bank_msg_id, req_bank_id, res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_tx_sts, 
            req_intr_bk_sttl_amt, req_nm, req_adr_line, req_bank_client_id, req_bank_prtry_id) = read_push_status_xml(status_res_xml)
	print(req_bank_tx_id ,req_orgnl_tx_id)
	if rv_req_bank_acct_id == req_bank_client_id and req_bank_tx_id == req_orgnl_tx_id:
		if req_tx_sts == 'ACSC':
			customer_no, customer_error, error_flg = req_bank_client_id, '', 0
			snd_fee, swf_fee, rcv_fee = "0", get_transfer_fee(req_orgnl_tx_id, doc_name),"0"

			customer_no, customer_error, error_flg = make_payment_for_customer(customer_no, req_intr_bk_sttl_amt, req_orgnl_tx_id, req_bank_prtry_id, req_bank_id, snd_fee, swf_fee, rcv_fee)
			if int(error_flg) == 1:
				update_psh_status(doc_name, '0', req_tx_sts, customer_error)
			else:
				update_psh_status(doc_name, '1', req_tx_sts)

		else:
			update_psh_status(doc_name, '0', req_tx_sts)
	else:
		update_psh_status(doc_name, '0', req_tx_sts)

def get_transfer_fee(req_orgnl_tx_id, doc_name):
	return "0"
	ret_fees, our_zone_code = "0", "00"
	#doc_name = frappe.db.get_value("Bank Payment Received", {"req_bank_tx_id":req_orgnl_tx_id}, ["name"])
	req_file_name, res_file_name, req_xml_path, res_xml_path, site_name, private_path,  req_path, res_path = get_service_files_names('Fees', 'StatusFileSerIn')
	res_bank_id, req_bank_id, req_bank_bldg, req_bank_acct, req_bank_amt, currency_code, fees_password, our_zone_code = get_fees_data(doc_name)
	fees_xml_req = create_fees_xml_doc(req_xml_path, req_bank_id, fees_password, str(req_bank_amt).strip(), res_bank_id, req_bank_bldg, our_zone_code, currency_code, req_orgnl_tx_id)
	save_payment_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	
	req_fees_url = frappe.db.get_value("Bank Service Control", "260", ["rec_text"])
	
	try:
		headers = {'Content-Type': 'application/xml'}
		session = requests.Session()
		retry = Retry(connect=3, backoff_factor=0.5)
		adapter = HTTPAdapter(max_retries=retry)
		session.mount('http://', adapter)
		session.mount('https://', adapter)
		res_xml = session.post(url= req_fees_url, data=fees_xml_req.encode("utf-8"), headers=headers).text
		with open(res_xml_path, "w") as f:
				f.write(res_xml)
				f.close()
		save_payment_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)
		retail, switch, interchange, result, transactionid, errordesc = read_xml_fees_data(res_xml)
		update_payment_fees_data(doc_name, retail, switch, interchange, transactionid, result, errordesc)
		ret_fees = interchange
	except:
		try:
			update_payment_fees_data(doc_name, "0", "0", "0", "", "error", sys.exc_info()[0])
		except:
			update_payment_fees_data(doc_name, "0", "0", "0", "", "error", '')

	return ret_fees

def validate_status_request(status_xml):
	(header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt,
            req_bank_cre_dt_tm, req_bank_msg_id, req_bank_id, res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_tx_sts, 
            req_intr_bk_sttl_amt, req_intr_bk_sttl_amt_ccy, req_nm, req_adr_line, req_bank_client_id, req_bank_prtry_id, req_accptnc_dt_tm) = read_status_xml(status_xml)

	our_biz_msg_idr_serial = get_table_serial_key('StatusSerialIn_RS')
	(res_status, payment_doc_name, rv_req_bank_id, rv_req_bank_acct_id, rv_req_bank_prtry_id, rv_req_bank_intr_bk_sttlm_amt, rv_req_bank_intr_bk_sttlm_amt_ccy,
	rv_res_bank_tx_sts, rv_timer_exceed_flg, rv_status_recieved_flg, rv_req_bank_debit_id, rv_req_bank_debit_prt) = get_status_data(req_orgnl_tx_id)
	req_bank_accptnc_dt_tm = ''
	# print(res_status, payment_doc_name, rv_req_bank_id, rv_req_bank_acct_id, rv_req_bank_prtry_id, rv_req_bank_intr_bk_sttlm_amt, rv_req_bank_intr_bk_sttlm_amt_ccy,
	# rv_res_bank_tx_sts, rv_timer_exceed_flg, rv_status_recieved_flg, rv_req_bank_debit_id, rv_req_bank_debit_prt)
	#or req_bank_prtry_id != rv_req_bank_prtry_id or req_bank_id != rv_req_bank_id or req_bank_client_id != rv_req_bank_acct_id
	if not validate_req_bank(req_bank_id) or not res_status or rv_res_bank_tx_sts != 'ACSC' or req_bank_prtry_id != rv_req_bank_prtry_id or req_bank_id != rv_req_bank_id or req_bank_client_id != rv_req_bank_acct_id or rv_req_bank_intr_bk_sttlm_amt_ccy != req_intr_bk_sttl_amt_ccy or float(rv_req_bank_intr_bk_sttlm_amt) != float(req_intr_bk_sttl_amt):
		status_res_xml, doc_name = create_status_res_xml(str(our_biz_msg_idr_serial), header_from, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
		req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm,
		res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, "TNFN", "false", req_intr_bk_sttl_amt, req_intr_bk_sttl_amt_ccy,
		req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id, rv_req_bank_debit_id, rv_req_bank_debit_prt)
	else:
		if int(rv_timer_exceed_flg) > 0:
			status_res_xml, doc_name = create_status_res_xml(str(our_biz_msg_idr_serial), header_from, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
			req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm,
			res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, "LTXD", "false", req_intr_bk_sttl_amt, req_intr_bk_sttl_amt_ccy,
			req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id, rv_req_bank_debit_id, rv_req_bank_debit_prt)
		else:
			if int(rv_status_recieved_flg > 0):
				status_res_xml, doc_name = create_status_res_xml(str(our_biz_msg_idr_serial), header_from, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
				req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm,
				res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, "DTID", "false", req_intr_bk_sttl_amt, req_intr_bk_sttl_amt_ccy,
				req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id, rv_req_bank_debit_id, rv_req_bank_debit_prt)
			else:
				customer_no, customer_error, error_flg = req_bank_client_id, '', 0
				snd_fee, swf_fee, rcv_fee = "0", get_transfer_fee(req_orgnl_tx_id, payment_doc_name),"0"

				customer_no, customer_error, error_flg = make_payment_for_customer(customer_no, req_intr_bk_sttl_amt, req_orgnl_tx_id, rv_req_bank_debit_id, req_bank_id, snd_fee, swf_fee, rcv_fee)
				if error_flg == 1:
					update_psh_status(payment_doc_name, '0', 'Server Error', customer_error)
					status_res_xml, doc_name = create_status_res_xml(str(our_biz_msg_idr_serial), header_from, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
					req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm,
					res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, customer_error, "false", req_intr_bk_sttl_amt, req_intr_bk_sttl_amt_ccy,
					req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id, rv_req_bank_debit_id, rv_req_bank_debit_prt)
				else:
					update_status_flg(payment_doc_name, '1')
					status_res_xml, doc_name = create_status_res_xml(str(our_biz_msg_idr_serial), header_from, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
					req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm,
					res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, "ACSC", "true", req_intr_bk_sttl_amt, req_intr_bk_sttl_amt_ccy,
					req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id, rv_req_bank_debit_id, rv_req_bank_debit_prt)

	return status_res_xml, doc_name

