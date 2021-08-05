import frappe

from money_transfer.money_transfer.service.utils import get_service_files_names
from money_transfer.money_transfer.service.xml_handler import save_xml, read_xml_verification, create_verification_res_xml, get_xml_response, read_xml_payment, create_payment_res_xml
from money_transfer.money_transfer.service.db import validate_req_bank, validate_account_type, save_verification_file_db
from money_transfer.money_transfer.service.socket_handler import get_customer_details

from money_transfer.money_transfer.db import get_table_serial_key
from money_transfer.money_transfer.utils import get_current_site_name, console_print

import money_transfer.money_transfer.service.const as const


@frappe.whitelist(allow_guest=True)
def Verification():
	# Get All Files Names & Paths
	req_file_name, res_file_name, req_xml_path, res_xml_path, site_name, private_path,  req_path, res_path = get_service_files_names('Verification', 'VerificationFileSerIn')
	if frappe.request.data:
		req_xml = frappe.request.data
		# Save Request Xml File to Server
		save_xml(req_xml_path, req_xml)
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
		save_xml(req_xml_path, req_xml)
		res_xml, doc_name = validate_payment_request(req_xml)

	return "test payment"

@frappe.whitelist(allow_guest=True)
def Status():
	# response = Response()
	# response.mimetype = 'text/xml'
	# response.charset = 'utf-8'
	# response.data = '<xml>{ar}</xml>'.format(ar =args)
	print("*" * 100)
	print(frappe.request.data)
	print("*" * 100)
	return "test status"



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
	req_bank_id, req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, 
	req_bank_debit_prt, req_bank_dbtr_acct_issr, req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd) = read_xml_payment(payment_xml)

	our_biz_msg_idr_serial = get_table_serial_key('PaymentSerialIn_RS')
	
	payment_res, doc_name = create_payment_res_xml(header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, req_bank_id,
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, req_bank_debit_prt, req_bank_dbtr_acct_issr, 
    req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd, our_biz_msg_idr_serial)

	return payment_res, req_bank_tx_id, doc_name

	
	