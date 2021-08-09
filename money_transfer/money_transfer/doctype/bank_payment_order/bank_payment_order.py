# -*- coding: utf-8 -*-
# Copyright (c) 2021, omar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import exceptions, _
from frappe.model.document import Document
import socket
from xml.dom import minidom
from frappe.utils.data import unique
from money_transfer.money_transfer.utils import mkdir, console_print, get_current_site_name, get_total_amount, num2str, float2str
from money_transfer.money_transfer.socket_handler import make_socket_connection
from money_transfer.money_transfer.xml_handler import create_fees_xml_doc, create_pp_xml_doc, create_status_xml_doc, dicttoxml, create_bv_xml_doc, read_xml_payment_data, read_xml_verification_data, read_xml_fees_data
from money_transfer.money_transfer.db import get_fees_data, get_table_serial_key, get_verification_data, save_file_db
from collections import OrderedDict
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.api import head
from bs4 import BeautifulSoup, element



class BankPaymentOrder(Document):
	pass

@frappe.whitelist()
def get_client_info(client_no, client_seril, branch_name, currency):
	return check_client(client_no, client_seril, branch_name, currency)

def check_client(client_no, client_seril, branch_name, currency, amount=0, rcv_fee=0, swift_fee=0, snd_fee=0, beneficiary_name='', fp_verification_id=''):
	msg = ''
	branch_code, branch_ip, branch_port = frappe.db.get_value('Bank Branch',branch_name, ['branch_code', 'ip_address', 'port_number'])
	currency_code = frappe.db.get_value('Bank Currency',currency, ['system_code'])
	for i in range(22):
		msg += 'z'
	msg += '820' + str(branch_code) + str(branch_code)
	for i in range(17):
		msg += 'z'

	wnote = fp_verification_id + '/' + beneficiary_name[:30]
	for i in range(60):
		wnote += '#'

	total_amount_str = get_total_amount(amount, rcv_fee, swift_fee, snd_fee)

	msg += str(branch_code) + str(client_no) + str(client_seril) + str(currency_code) + '1' + total_amount_str + wnote[:60]

	for i in range(1908):
		msg += 'x'

	msg_ascii = msg.encode('ascii', 'replace')

	data, socket_error_msg = make_socket_connection(branch_ip, branch_port, msg_ascii)

	if socket_error_msg == '':
		error_flag = data[0] == 121 # 'y'
		error_msg = ''
		if error_flag:
			error_code = data[1:6].decode("utf-8").strip()
			error_msg = frappe.db.get_value('Bank System Error', error_code, ['a_name'])
		client_name = data[140:189].decode("iso8859_6")
		client_region_code = data[200:203].decode("utf-8")
		client_region = frappe.db.get_value('Bank Region',{'region_code':client_region_code}, ['a_name'])
		res_status = 'true'
		result = {
			"res_status":res_status, "error_msg": error_msg, "client_name": client_name, "client_region_code":client_region_code, "client_region": client_region
		}
	else:
		error_msg = socket_error_msg
		res_status = 'false'
		result = {
			"res_status":res_status, "error_msg": error_msg
		}
	return result

@frappe.whitelist()
def verification(client_no, client_seril, our_bank, user_branch, dest_bank, beneficiary_no, account_type, doc_name, amount, currency, payment_method):
	site_name = get_current_site_name()
	date = datetime.now()
	public_path = '/public/files/' 
	private_path = '/private/files/'
	req_path = 'XMLIN/Verification/REQ/' + str(date.year) + '_' + str(date.month)
	res_path = 'XMLIN/Verification/RES/' + str(date.year) + '_' + str(date.month)
	BillVerification_Serial = get_table_serial_key('VerificationFileSerial')
	
	postfix = str(date.year) + str(date.month) + str(date.day) + '_' + BillVerification_Serial + '.xml'
	req_file_name = 'Verification_RQ_' + postfix
	res_file_name = 'Verification_RS_' + postfix
	req_xml_path = site_name + public_path + req_file_name
	res_xml_path = site_name + public_path + res_file_name
	acc_type = frappe.db.get_value('Bank Account Type', account_type, ['system_code'])
	mkdir([site_name + private_path + req_path , site_name + private_path + res_path ])

	req_bank_id, dis_bank_id, fp_header_name, acmt_req, verification_serial, currency_prefix = get_verification_data(our_bank, dest_bank, currency)
	xml_body, our_verf_id = create_bv_xml_doc(req_xml_path, req_bank_id, dis_bank_id, fp_header_name, acmt_req, verification_serial, currency_prefix + str(beneficiary_no), acc_type)

	#------------------------------Sending REST request------------------------------
	try:
		api_point = frappe.db.get_value('Bank Service Control', "251", ['rec_text'])
		headers = {'Content-Type': 'application/xml'}
		session = requests.Session()
		retry = Retry(connect=3, backoff_factor=0.5)
		adapter = HTTPAdapter(max_retries=retry)
		session.mount('http://', adapter)
		session.mount('https://', adapter)
		res_xml = session.post(url= api_point, data=xml_body.encode("utf-8"), headers=headers).text

		with open(res_xml_path, "w") as f:
			soup = BeautifulSoup(res_xml, "xml")
			f.write(soup.prettify())
			f.close()
		rpt_vrfctn, rpt_rsn, pty_nm, fp_vrfctn = read_xml_verification_data(res_xml)
	except requests.exceptions.ConnectionError:
		results = {
		'error_msg':'', 'pv_Vrfctn': 'false', 'pv_Rsn' : '', 'pv_Nm': '', 'pv_FPVrfctn':'', 'our_verf_id': '',
		'retail': 0, 'switch': 0, 'interchange': 0, 'result': 'false', 'transactionid': '', 'errordesc': 'System connection error in verification request',
		'client_name': '', 'client_address': '', 'client_region_code': ''
		}
		return results
	except:
		results = {
		'error_msg':'', 'pv_Vrfctn': 'false', 'pv_Rsn' : '', 'pv_Nm': '', 'pv_FPVrfctn':'', 'our_verf_id': '',
		'retail': 0, 'switch': 0, 'interchange': 0, 'result': 'false', 'transactionid': '', 'errordesc': 'An error occurred while requesting verification',
		'client_name': '', 'client_address': '', 'client_region_code': ''
		}
		return results
	#------------------------------Saving files to database------------------------------
	save_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	save_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)
	if rpt_vrfctn != 'true' and rpt_rsn != 'SUCC':
		results = {
		'error_msg':'', 'pv_Vrfctn': rpt_vrfctn, 'pv_Rsn' : rpt_rsn, 'pv_Nm': pty_nm, 'pv_FPVrfctn':fp_vrfctn, 'our_verf_id':our_verf_id,
		'retail': 0, 'switch': 0, 'interchange': 0, 'result': 'false', 'transactionid': '', 'errordesc': '',
		'client_name': '', 'client_address': '', 'client_region_code': ''
		}
		return results
	zone = pty_nm[-2:]
	#----------------------------get fees if enabled----------------------------------
	retail, switch, interchange, result, transactionid, errordesc = push_transfer_fees(site_name, public_path, private_path, req_path, res_path, doc_name, our_bank, user_branch, dest_bank, amount, zone, currency, fp_vrfctn)
	#------------------------------Reserving money------------------------------
	error_msg, client_name, client_address, client_region_code = '', '', '', ''

	if result == 'Success':
		if int(payment_method) == 1 or int(payment_method) == 2:
			res = check_client(client_no, client_seril, user_branch, currency, amount, rcv_fee= interchange, swift_fee=switch, snd_fee=retail, beneficiary_name=pty_nm, fp_verification_id=fp_vrfctn)
			error_msg = res['error_msg']
			if res['res_status'] == 'true':
				client_name, client_address, client_region_code = res["client_name"], res['client_region'], res["client_region_code"]
	results = {
		'error_msg':error_msg,'pv_Vrfctn': rpt_vrfctn, 'pv_Rsn' : rpt_rsn, 'pv_Nm': pty_nm, 'pv_FPVrfctn':fp_vrfctn, 'our_verf_id':our_verf_id,
		'retail':retail, 'switch':switch, 'interchange': interchange, 'result': result, 'transactionid':transactionid, 'errordesc':errordesc,
		'client_name': client_name, 'client_address': client_address, 'client_region_code': client_region_code
	}
	return results


def get_transfer_fees(save_path_file, user_bank, user_branch, dest_bank, amount, zone, currency, fp_verification_id):
	req_bank_id, fees_password, dest_bank_id, unique_code, currency_code = get_fees_data(user_bank, dest_bank, user_branch, currency)
	xml_data = create_fees_xml_doc(save_path_file, req_bank_id, fees_password, amount, dest_bank_id, unique_code, zone, currency_code, fp_verification_id)
	
	return xml_data

def push_transfer_fees(site_name, public_path, private_path, req_path, res_path, doc_name, our_bank, user_branch, dest_bank, amount, zone, currency, fp_vrfctn):
	fetch_fees = frappe.db.get_value('Bank Currency', currency, ['fetch_fees'])
	if 	int(fetch_fees) == 1:
		#fees_api_point = frappe.db.get_value('Bank Service Control', "260", ['rec_text'])
		fees_api_point = frappe.db.get_value('Bank Currency', currency, ['system_url'])
		if fees_api_point:
			#------------------------------Getting Transfer Fees------------------------------
			
			verification_file_serial = get_table_serial_key('VerificationFileSerial')
			date = datetime.now()
			postfix = str(date.year) + str(date.month) + str(date.day) + '_' + verification_file_serial + '.xml'
			fees_rq_file_name = "Fees_RQ_" + postfix
			fees_rs_file_name = "Fees_RS_" + postfix
			fees_rq_file_path = site_name + public_path + fees_rq_file_name
			fees_rs_file_path = site_name + public_path + fees_rs_file_name
			fees_xml = get_transfer_fees(fees_rq_file_path, our_bank, user_branch, dest_bank, amount, zone, currency, fp_vrfctn)
			console_print(fees_xml)
			# Sending REST request
			try:
				session = requests.Session()
				retry = Retry(connect=3, backoff_factor=0.5)
				adapter = HTTPAdapter(max_retries=retry)
				session.mount('http://', adapter)
				session.mount('https://', adapter)
				headers = {'Content-Type': 'application/xml'} 
				fees_res_xml = session.post(url= fees_api_point, data=fees_xml.encode('utf-8'), headers=headers).text
			except requests.exceptions.ConnectionError:
				return 0, 0, 0, "false", "", "System connection error in fees request"
			except:
				return 0, 0, 0, "false", "", "An error occurred while requesting fees"
			retail, switch, interchange, result, transactionid, errordesc = read_xml_fees_data(fees_res_xml)
			

			with open(fees_rs_file_path, "w") as f:
				f.write(fees_res_xml)
				f.close()

			save_file_db(site_name, fees_rq_file_name, fees_rq_file_path, private_path, req_path, doc_name)
			save_file_db(site_name, fees_rs_file_name, fees_rs_file_path, private_path, res_path, doc_name)
		else:
			retail, switch, interchange, result, transactionid, errordesc = 0, 0, 0, "false", "", "Fees url not defined"
	else:
		retail, switch, interchange, result, transactionid, errordesc = 0, 0, 0, "Success", "", ""
	return retail, switch, interchange, result, transactionid, errordesc
	

@frappe.whitelist()
def cancel_reservation(payment_method, client_no, client_seril, currency, user_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id):
	error_msg, cancellation_status = do_cancel_reservation(payment_method, client_no, client_seril, currency, user_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id)
	return {'error_msg': error_msg, 'cancellation_status': cancellation_status}

def do_cancel_reservation(payment_method, client_no, client_seril, currency, user_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id):
	if int(payment_method) == 3 or int(payment_method) == 4:
		return  '', 'true'
	msg = ''
	branch_code, branch_ip, branch_port = frappe.db.get_value('Bank Branch',user_branch, ['branch_code', 'ip_address', 'port_number'])
	currency_code = frappe.db.get_value('Bank Currency',currency, ['system_code'])
	total_amount_str = get_total_amount(amount, rcv_fee, swift_fee, snd_fee)
	
	ii = len(beneficiary_name)
	if ii > 30:
		ii = 30
	wnote = fp_verification_id + '/' + beneficiary_name[:ii]
	for i in range(60):
		wnote += '#'

	for i in range(22):
		msg += 'z'
	msg += '821' + str(branch_code) + str(branch_code)
	for i in range(17):
		msg += 'z'
	msg += str(branch_code) + str(client_no) + str(client_seril) + str(currency_code) + '1' + total_amount_str + wnote[:60]

	for i in range(1908):
		msg += 'x'
	msg_ascii = msg.encode('ascii', 'replace')

	data, socket_error_msg = make_socket_connection(branch_ip, branch_port, msg_ascii)
	if socket_error_msg == '':
		error_flag = data[0] == 121 # 'y'
		error_msg = ''
		if error_flag:
			error_code = data[1:6].decode("utf-8").strip()
			error_msg = frappe.db.get_value('Bank System Error', error_code, ['a_name'])
		res_status = "true"
	else:
		error_msg = socket_error_msg
		res_status = "false"
	#results = {"error_msg": error_msg, "res_stats":res_status}
	return error_msg, res_status


@frappe.whitelist()
def push_payment(doc_name, payment_method, client_no, client_serial, our_client_name, our_client_address, our_bank, our_branch, region_code,
dest_bank, fp_verification_id, amount, rcv_fee, snd_fee, swift_fee, currency, beneficiary_name, beneficiary_no, account_type, op_type, card_no, card_type, sender_name, sender_region):
	site_name = get_current_site_name()
	date = datetime.now()
	public_path = '/public/files/' 
	private_path = '/private/files/'
	req_path = 'XMLIN/Payment/REQ/' + str(date.year) + '_' + str(date.month)
	res_path = 'XMLIN/Payment/RES/' + str(date.year) + '_' + str(date.month)
	BillVerification_Serial = get_table_serial_key('PaymentFileSerial')
	
	postfix = str(date.year) + str(date.month) + str(date.day) + '_' + BillVerification_Serial + '.xml'
	req_file_name = 'Payment_RQ_' + postfix
	res_file_name = 'Payment_RS_' + postfix
	req_xml_path = site_name + public_path + req_file_name
	res_xml_path = site_name + public_path + res_file_name
	mkdir([site_name + private_path + req_path , site_name + private_path + res_path ])
	currency_prefix =frappe.db.get_value('Bank Currency', currency, ['currency_prefix'])
	currency_prefix = currency_prefix if currency_prefix else ''
	xml_body = create_pp_xml_doc(req_xml_path, payment_method, client_no, client_serial, our_client_name, our_client_address, our_bank, our_branch, region_code, dest_bank, fp_verification_id, amount, currency, beneficiary_name, beneficiary_no, account_type, op_type, card_no, card_type, sender_name, sender_region)
	xml_body = xml_body.encode('utf-8')
	results = {"cancellation_msg": '', "cancellation_status": 'false', "journal_msg": '', "journal_status": 'false', 'res_status': 'false'}
	#------------------------------Sending REST request------------------------------
	api_point = frappe.db.get_value('Bank Service Control', "252", ['rec_text'])
	headers = {'Content-Type': 'application/xml'}
	is_push_payment = True
	status_error = ""
	try:
		res_xml = requests.post(url= api_point, data=xml_body, headers=headers, timeout=10).text
		with open(res_xml_path, "w") as f:
			soup = BeautifulSoup(res_xml, "xml")
			f.write(soup.prettify())
			f.close()
	except requests.exceptions.Timeout:
		is_push_payment = False
		res_xml, status_error = push_status(doc_name, our_bank, fp_verification_id)
		if status_error != '':
			results['cancellation_msg'], results['cancellation_status'] = do_cancel_reservation(payment_method, client_no, client_serial, currency, our_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id)
			return results
	except requests.exceptions.ConnectionError:
		is_push_payment = False
		

	res_status = read_xml_payment_data(res_xml)
	results['res_status'] = res_status
	#------------------------------Saving files to database------------------------------
	save_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	if is_push_payment:
		save_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)

	if res_status == 'ACSC':
		results['cancellation_msg'], results['cancellation_status'] = do_cancel_reservation(payment_method, client_no, client_serial, currency, our_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id)
		if results['cancellation_msg'] == '':
			results['journal_msg'], results['journal_status'] = do_journal(payment_method, client_no, client_serial, our_branch, dest_bank, currency_prefix+beneficiary_no, amount, currency, rcv_fee, swift_fee, snd_fee, fp_verification_id)
	else: 
		results['cancellation_msg'], results['cancellation_status'] = do_cancel_reservation(payment_method, client_no, client_serial, currency, our_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id)
	return results



def do_journal(payment_method, client_no, client_serial, user_branch, dest_bank, beneficiary_no, amount, currency, rcv_fee, swift_fee, snd_fee, fp_verficication_id):
	if int(payment_method) == 1 or int(payment_method) == 2:
		mas_account = client_no
		sub_account = client_serial
		tcppid = "823"
		pletter = 'c'
		padding_size = 1843
	else:
		mas_account, sub_account = frappe.db.get_value('User', frappe.session.user, ['mas_account', 'sub_account'])
		if not mas_account:
			return _('Admin_UserCashNotDefine'), 'false'
		tcppid = "825"
		pletter = 'a'
		padding_size = 1841

	branch_code, branch_ip, branch_port = frappe.db.get_value('Bank Branch',user_branch, ['branch_code', 'ip_address', 'port_number'])
	currency_code = frappe.db.get_value('Bank Currency',currency, ['system_code'])
	dest_bank_code = frappe.db.get_value('Bank Company',dest_bank, ['system_code'])

	wnote = fp_verficication_id + '/' + beneficiary_no + '/' + dest_bank_code
	for i in range(60): wnote += '#'
	
	msg = ''
	for i in range(22): msg += 'z'
	msg += tcppid + str(branch_code) + str(branch_code)
	for i in range(17): msg += 'z'
	msg += str(branch_code) + str(mas_account) + str(sub_account) + str(currency_code) + "1" + pletter + num2str(amount)+ num2str(amount) + num2str(snd_fee) + num2str(swift_fee) + num2str(rcv_fee) + wnote[:60]
	for i in range(padding_size): msg += 'x'

	msg_ascii = msg.encode('ascii', 'replace')
	
	data, socket_error_msg = make_socket_connection(branch_ip, branch_port, msg_ascii)
	if socket_error_msg == '':
		error_flag = data[0] == 121 # 'y'
		error_msg = ''
		if error_flag:
			error_code = data[1:6].decode("utf-8").strip()
			error_msg = frappe.db.get_value('Bank System Error', error_code, ['a_name'])
		res_status = "true"
	else:
		error_msg = socket_error_msg
		res_status = "false"
	#results = {"error_msg": error_msg, "res_stats":res_status}
	return error_msg, res_status

# @frappe.whitelist()
# def push_status_click(doc_name, our_bank, fp_verification_id):
# 	res_xml = push_status(doc_name, our_bank, fp_verification_id)
# 	res_status = read_xml_payment_data(res_xml)

def push_status(doc_name, our_bank, fp_verification_id):
	site_name = get_current_site_name()
	date = datetime.now()
	public_path = '/public/files/' 
	private_path = '/private/files/'
	req_path = 'XMLIN/Status/REQ/' + str(date.year) + '_' + str(date.month)
	res_path = 'XMLIN/Status/RES/' + str(date.year) + '_' + str(date.month)
	BillStatus_Serial = get_table_serial_key('StatusFileSerial')
	
	postfix = str(date.year) + str(date.month) + str(date.day) + '_' + BillStatus_Serial + '.xml'
	req_file_name = 'BillStatus_RQ_' + postfix
	res_file_name = 'BillStatus_RS_' + postfix
	req_xml_path = site_name + public_path + req_file_name
	res_xml_path = site_name + public_path + res_file_name
	mkdir([site_name + private_path + req_path , site_name + private_path + res_path ])

	xml_body = create_status_xml_doc(req_xml_path, our_bank, fp_verification_id)
	xml_body = xml_body.encode('utf-8')
	
	#------------------------------Sending REST request------------------------------
	api_point = frappe.db.get_value('Bank Service Control', "253", ['rec_text'])
	session = requests.Session()
	retry = Retry(connect=3, backoff_factor=0.5)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount('http://', adapter)
	session.mount('https://', adapter)
	headers = {'Content-Type': 'application/xml'}
	done = False
	for i in range(5):
		try:
			res_xml = session.post(url= api_point, data=xml_body, headers=headers, timeout=10).text
			done = True
			break
		except requests.Timeout:
			continue
		except requests.exceptions.ConnectionError:
			return "", "System connection error in status request"
		except:
			return "", "An error occurred while requesting status"	
	if not done:
		return "", "The system does not respond to the status request"
	with open(res_xml_path, "w") as f:
		soup = BeautifulSoup(res_xml, "xml")
		f.write(soup.prettify())
		f.close()

	#------------------------------Saving files to database------------------------------
	save_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)
	save_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)

	return res_xml, ""



