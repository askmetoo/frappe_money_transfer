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
from money_transfer.money_transfer.utils import dicttoxml, mkdir, console_print, make_socket_connection, get_current_site_name
from collections import OrderedDict
from datetime import datetime
import requests
from requests.api import head
from bs4 import BeautifulSoup, element
from xml.etree import ElementTree as et
import os
import shutil
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
def verification(client_no, client_seril, our_bank, user_branch, dest_bank, beneficiary_no, account_type, doc_name, amount, currency):
	site_name = get_current_site_name()
	date = datetime.now()
	public_path = '/public/files/' 
	private_path = '/private/files/'
	req_path = 'Verification/REQ/' + str(date.year) + '_' + str(date.month)
	res_path = 'Verification/RES/' + str(date.year) + '_' + str(date.month)
	BillVerification_Serial = get_table_serial_key('VerificationFileSerial')
	
	postfix = str(date.year) + str(date.month) + str(date.day) + '_' + BillVerification_Serial + '.xml'
	req_file_name = 'Verification_RQ_' + postfix
	res_file_name = 'Verification_RS_' + postfix
	req_xml_path = site_name + public_path + req_file_name
	res_xml_path = site_name + public_path + res_file_name
	acc_type = frappe.db.get_value('Bank Account Type', account_type, ['system_code'])
	mkdir([site_name + private_path + req_path , site_name + private_path + res_path ])

	xml_body, ourVefId = create_bv_xml_doc(req_xml_path, our_bank, dest_bank, beneficiary_no, acc_type)

	#------------------------------Sending REST request------------------------------
	api_point = frappe.db.get_value('Bank Service Control', "251", ['rec_text'])
	headers = {'Content-Type': 'application/xml'} 
	res_xml = requests.post(url= api_point, data=xml_body, headers=headers).text
	with open(res_xml_path, "w") as f:
		soup = BeautifulSoup(res_xml, "xml")
		f.write(soup.prettify())
		f.close()
	pv_Vrfctn, pv_Rsn, pv_Nm, pv_FPVrfctn = read_xml_verification_data(res_xml)

	#------------------------------Getting Transfer Fees------------------------------
	zone = pv_Nm[-2:]
	verification_file_serial = get_table_serial_key('VerificationFileSerial')

	postfix = str(date.year) + str(date.month) + str(date.day) + '_' + verification_file_serial + '.xml'
	lv_FeesRQFileName = "Fees_RQ_" + postfix
	lv_FeesRSFileName = "Fees_RS_" + postfix
	lv_FeesRQFilePath = site_name + public_path + lv_FeesRQFileName
	lv_FeesRSFilePath = site_name + public_path + lv_FeesRSFileName
	fees_xml = get_transfer_fees(lv_FeesRQFilePath, our_bank, user_branch, dest_bank, amount, zone, currency, pv_FPVrfctn)

	# Sending REST request
	fees_api_point = frappe.db.get_value('Bank Service Control', "260", ['rec_text'])
	headers = {'Content-Type': 'application/xml'} 
	fees_res_xml = requests.post(url= fees_api_point, data=fees_xml, headers=headers).text
	retail, switch, interchange, result, transactionid, errordesc = read_xml_fees_data(fees_res_xml)

	with open(lv_FeesRSFilePath, "w") as f:
		soup_fees = BeautifulSoup(fees_res_xml, "xml")
		f.write(soup_fees.prettify())
		f.close()
	
	#------------------------------Saving files to database------------------------------
	save_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	save_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)

	save_file_db(site_name, lv_FeesRQFileName, lv_FeesRQFilePath, private_path, req_path, doc_name)
	save_file_db(site_name, lv_FeesRSFileName, lv_FeesRSFilePath, private_path, res_path, doc_name)

	#------------------------------Reserving money------------------------------
	error_msg, client_name, client_address, client_region_code = '', '', '', ''

	if result == 'Success':
		res = check_client(client_no, client_seril, user_branch, currency, amount, rcv_fee= interchange, swift_fee=switch, snd_fee=retail, beneficiary_name=pv_Nm, fp_verification_id=pv_FPVrfctn)
		error_msg = res['error_msg']
		if res['res_status'] == 'true':
			client_name, client_address, client_region_code = res["client_name"], res['client_region'], res["client_region_code"]

	results = {
		'error_msg':error_msg,'pv_Vrfctn': pv_Vrfctn, 'pv_Rsn' : pv_Rsn, 'pv_Nm': pv_Nm, 'pv_FPVrfctn':pv_FPVrfctn, 'our_verf_id':ourVefId,
		'retail':retail, 'switch':switch, 'interchange': interchange, 'result': result, 'transactionid':transactionid, 'errordesc':errordesc,
		'client_name': client_name, 'client_address': client_address, 'client_region_code': client_region_code
	}
	return results

# Bill Verification Xml Document
def create_bv_xml_doc(save_path_file, our_bank, dis_bank, beneficiary_no, account_type):
	header = "urn:iso:std:iso:20022:tech:xsd:head.001.001.01"
	document = "urn:iso:std:iso:20022:tech:xsd:acmt.023.001.02"
	FPXml = "urn:iso:std:iso:20022:tech:xsd:verification_request"
	gv_ReqBankId = frappe.db.get_value('Bank Company', our_bank, ['system_code'])
	gv_DisBankId = frappe.db.get_value('Bank Company', dis_bank, ['system_code'])

	gv_FPHeaderName = frappe.db.get_value('Bank Service Control', "101", ['rec_text'])
	gv_AcmtReq = frappe.db.get_value('Bank Service Control', "201", ['rec_text'])
	lv_CreDtForSerial = datetime.today().strftime('%Y%m%d%H%M%S')
	lv_CreDt = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
	lv_CreDtTm = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
	gv_VerificationSerial = get_table_serial_key('VerificationSerial')

	docObj = {
		"FPEnvelope":{
			"attr_names": ["xmlns","xmlns:document","xmlns:header"],
			"attr_values": [FPXml, document, header],
			"header:AppHdr":{
				"header:Fr":{
					"header:FIId":{
						"header:FinInstnId":{
							"header:Othr":{
								"header:Id": gv_ReqBankId
							}
						}
					}
				},
				"header:To":{
					"header:FIId":{
						"header:FinInstnId":{
							"header:Othr":{
								"header:Id": gv_FPHeaderName
							}
						}
					}
				},
				"header:BizMsgIdr": gv_ReqBankId + lv_CreDtForSerial + gv_VerificationSerial,
				"header:MsgDefIdr": gv_AcmtReq,
				"header:CreDt": lv_CreDt
			},
			"document:Document":{
				"document:IdVrfctnReq":{
					"document:Assgnmt":{
						"document:MsgId": gv_ReqBankId + lv_CreDtForSerial + gv_VerificationSerial,
						"document:CreDtTm": lv_CreDtTm,
						"document:Assgnr":{
							"document:Agt":{
								"document:FinInstnId":{
									"document:Othr":{
										"document:Id": gv_ReqBankId
									}
								}
							}
						},
						"document:Assgne":{
							"document:Agt":{
								"document:FinInstnId":{
									"document:Othr":{
										"document:Id": gv_DisBankId
									}
								}
							}
						}
					},
					"document:Vrfctn":{
						"document:Id": "ID",
						"document:PtyAndAcctId":{
							"document:Acct":{
								"document:Othr":{
									"document:Id": beneficiary_no,
									"document:SchmeNm":{
										"document:Prtry": account_type 
									}
								}
							}
						}
					}
				}
			}
		}
	}
	
	_, xml = dicttoxml(docObj)

	with open(save_path_file, "w") as f:
		f.write(xml)
		f.close()
	return xml,  gv_ReqBankId + lv_CreDtForSerial + gv_VerificationSerial

def read_xml_verification_data(xml):
	Bs_data = BeautifulSoup(xml, "xml")
	pv_Vrfctn = Bs_data.find('document:Vrfctn').text if Bs_data.find('document:Vrfctn') else ''
	pv_Rsn = Bs_data.find('document:Rsn').find('document:Prtry').text if  Bs_data.find('document:Rsn') else ''
	pv_Nm = Bs_data.find('document:Nm').text if Bs_data.find('document:Nm') else ''
	pv_FPVrfctn = Bs_data.find('document:OrgnlId').text if Bs_data.find('document:OrgnlId') else ''

	return pv_Vrfctn, pv_Rsn, pv_Nm, pv_FPVrfctn

def get_transfer_fees(save_path_file, user_bank, user_branch, dest_bank, amount, zone, currency, fp_verification_id):
	# gv_FPHeaderName = frappe.db.get_value('Bank Service Control', "101", ['rec_text'])
	# gv_AcmtReq = frappe.db.get_value('Bank Service Control', "201", ['rec_text'])
	# verification_serial = get_table_serial_key('VerificationSerial')

	gv_ReqBankId, fees_password = frappe.db.get_value('Bank Company', user_bank, ['system_code', 'fees_password'])
	gv_DestBankId = frappe.db.get_value('Bank Company', dest_bank, ['system_code'])

	branch_region = frappe.db.get_value('Bank Branch',user_branch, ['branch_region'])
	unique_code = frappe.db.get_value('Bank Region',branch_region, ['unique_code'])

	currency_code = frappe.db.get_value('Bank Currency', currency, ['currency_code'])
	xml_object = {
		"root":{
			"UserId":gv_ReqBankId,
			"UserPass":fees_password,
			"AMOUNT": amount,
			"DEST_BANK": gv_DestBankId,
			"FROM_ZONE": unique_code,
			"TO_ZONE": zone,
			"CURRENCY": currency_code,
			"TransactionID": fp_verification_id
		}
	}


	_, xml = dicttoxml(xml_object)

	with open(save_path_file, "w") as f:
		f.write(xml)
		f.close()
	return xml

def get_table_serial_key(table_name):
	table_serial = frappe.db.get_value('Bank CSSRLCOD', table_name, ['table_serial'])
	frappe.db.set_value('Bank CSSRLCOD', table_name, {"table_serial" : str(int(table_serial) + 1)})
	return table_serial

def save_file_db(site_name, file_name, file_path, private_path, relative_path, doc_name):
	doc = 'Bank Payment Order'
	file = frappe.get_doc({
		"doctype":"File", 'file_url':  None, 'file_name': file_name,
		'is_private':1, 'attached_to_name':doc_name, "attached_to_doctype":doc  })
	file.insert()

	shutil.move(file_path, site_name + private_path + relative_path + '/' + file_name)
	new_url = private_path + relative_path + '/' + file_name
	
	frappe.db.sql('UPDATE tabFile SET file_url=%s WHERE name=%s', (new_url,file.name))

def read_xml_fees_data(xml):
	xml_data = et.fromstring(xml)
	elements ={elem.tag:elem.text for elem in xml_data.iter()}
	retail =  elements['Retail'] if 'Retail' in elements.keys() else ''
	switch =  elements['Switch'] if 'Switch' in elements.keys() else ''
	interchange =  elements['interchange'] if 'interchange' in elements.keys() else ''
	result =  elements['Result'] if 'Result' in elements.keys() else ''
	transactionid =  elements['TransactionId'] if 'TransactionId' in elements.keys() else ''
	errordesc =  elements['ErrorDesc'] if 'ErrorDesc' in elements.keys() else ''

	return retail, switch, interchange, result, transactionid, errordesc

@frappe.whitelist()
def cancel_reservation(client_no, client_seril, currency, user_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id):
	error_msg, cancellation_status = do_cancel_reservation(client_no, client_seril, currency, user_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id)
	return {'error_msg': error_msg, 'cancellation_status': cancellation_status}

def do_cancel_reservation(client_no, client_seril, currency, user_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id):
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
		error_msg = _(socket_error_msg)
		res_status = "false"
	#results = {"error_msg": error_msg, "res_stats":res_status}
	return error_msg, res_status


def get_total_amount(amount, rcv_fee, swift_fee, snd_fee):
	total_amount = float(amount) + float(rcv_fee) + float(swift_fee) + float(snd_fee)
	total_amount_int = int(total_amount * 1000) 
	return str("{:016d}".format(total_amount_int))

@frappe.whitelist()
def push_payment(doc_name, payment_method, client_no, client_serial, our_client_name, our_client_address, our_bank, our_branch, region_code,
dest_bank, fp_verification_id, amount, rcv_fee, snd_fee, swift_fee, currency, beneficiary_name, beneficiary_no, account_type, op_type):
	site_name = get_current_site_name()
	date = datetime.now()
	public_path = '/public/files/' 
	private_path = '/private/files/'
	req_path = 'Payment/REQ/' + str(date.year) + '_' + str(date.month)
	res_path = 'Payment/RES/' + str(date.year) + '_' + str(date.month)
	BillVerification_Serial = get_table_serial_key('PaymentFileSerial')
	
	postfix = str(date.year) + str(date.month) + str(date.day) + '_' + BillVerification_Serial + '.xml'
	req_file_name = 'Payment_RQ_' + postfix
	res_file_name = 'Payment_RS_' + postfix
	req_xml_path = site_name + public_path + req_file_name
	res_xml_path = site_name + public_path + res_file_name
	mkdir([site_name + private_path + req_path , site_name + private_path + res_path ])

	xml_body = create_pp_xml_doc(req_xml_path, payment_method, client_no, client_serial, our_client_name, our_client_address, our_bank, our_branch, region_code, dest_bank, fp_verification_id, amount, currency, beneficiary_name, beneficiary_no, account_type, op_type)
	xml_body = xml_body.encode('utf-8')
	#------------------------------Sending REST request------------------------------
	api_point = frappe.db.get_value('Bank Service Control', "252", ['rec_text'])
	headers = {'Content-Type': 'application/xml'}
	is_push_payment = True
	try:
		res_xml = requests.post(url= api_point, data=xml_body, headers=headers, timeout=10).text
		with open(res_xml_path, "w") as f:
			soup = BeautifulSoup(res_xml, "xml")
			f.write(soup.prettify())
			f.close()
	except requests.exceptions.Timeout:
		is_push_payment = False
		res_xml = push_status(doc_name, our_bank, fp_verification_id)
	except requests.exceptions.ConnectionError:
		is_push_payment = False
		

	res_status = read_xml_payment_data(res_xml)

	#------------------------------Saving files to database------------------------------
	save_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	if is_push_payment:
		save_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)


	results = {"cancellation_msg": '', "cancellation_status": 'false', "journal_msg": '', "journal_status": 'false', 'res_status': res_status}
	if res_status == 'ACSC':
		results['cancellation_msg'], results['cancellation_status'] = do_cancel_reservation(client_no, client_serial, currency, our_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id)
		results['journal_msg'], results['journal_status'] = do_journal(payment_method, client_no, client_serial, our_branch, dest_bank, beneficiary_no, amount, currency, rcv_fee, swift_fee, snd_fee, fp_verification_id)
	else: 
		results['cancellation_msg'], results['cancellation_status'] = do_cancel_reservation(client_no, client_serial, currency, our_branch, amount, rcv_fee, swift_fee, snd_fee, beneficiary_name, fp_verification_id)
	return results
# Push payment xml document
def create_pp_xml_doc(save_path_file, payment_method, client_no, client_serial, our_client_name, our_client_address, our_bank, our_branch, region_code,
dest_bank, fp_verification_id, amount, currency, beneficiary_name, beneficiary_no, account_type, op_type, card_no='', card_type=''):
	header = "urn:iso:std:iso:20022:tech:xsd:head.001.001.01"
	document = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.04"
	fp_xml = "urn:iso:std:iso:20022:tech:xsd:payment_request"
	our_bank_id = frappe.db.get_value('Bank Company', our_bank, ['system_code'])
	dest_bank_id = frappe.db.get_value('Bank Company', dest_bank, ['system_code'])
	our_branch_code, our_branch_name = frappe.db.get_value('Bank Branch', our_branch, ['branch_code', 'a_name'])

	fp_region_code = frappe.db.get_value('Bank Region', {"region_code":region_code}, ['service_code'])
	currency_code, currency_system_code =frappe.db.get_value('Bank Currency', currency, ['currency_code', 'system_code'])

	fp_header_name = frappe.db.get_value('Bank Service Control', "101", ['rec_text'])
	pacs_req = frappe.db.get_value('Bank Service Control', "202", ['rec_text'])

	cre_dt_serial = datetime.today().strftime('%Y%m%d%H%M%S')
	cre_dt = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
	cre_dt_tm = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
	acc_type = frappe.db.get_value('Bank Account Type', account_type, ['system_code'])
	payment_serial = get_table_serial_key('PaymentSerial')

	username = frappe.db.get_value('User', frappe.session.user, ['username'])
	if int(payment_method) == 1 or int(payment_method) == 2:
		cli_name = '#'
		cli_id_no = '#'
		cli_id_type = '#'
	else:
		cli_name = our_client_name
		cli_id_no = card_no
		cli_id_type = card_type
		client_no = '00001'
	doc_obj = {
		"FPEnvelope":{
			"attr_names": ["xmlns","xmlns:document","xmlns:header"],
			"attr_values": [fp_xml, document, header],
			"header:AppHdr":{
				"header:Fr":{
					"header:FIId":{
						"header:FinInstnId":{
							"header:Othr":{
								"header:Id": str(our_bank_id)
							}
						}
					}
				},
				"header:To":{
					"header:FIId":{
						"header:FinInstnId":{
							"header:Othr":{
								"header:Id": str(fp_header_name)
							}
						}
					}
				},
				"header:BizMsgIdr": our_bank_id + cre_dt_serial + payment_serial,
				"header:MsgDefIdr": str(pacs_req),
				"header:CreDt": cre_dt
			},
			"document:Document":{
				"document:FIToFICstmrCdtTrf":{
					"document:GrpHdr":{
						"document:MsgId": our_bank_id + cre_dt_serial + payment_serial,
						"document:CreDtTm": cre_dt_tm,
						"document:NbOfTxs": "1",
						"document:SttlmInf":{
							"document:SttlmMtd": "CLRG",
							"document:ClrSys": {
								"document:Prtry": fp_header_name
							}
						},
						"document:PmtTpInf":{
							"document:LclInstrm":{
								"document:Prtry": "C2C"
							}
						},
						"document:InstgAgt":{
							"document:FinInstnId":{
								"document:Othr":{
									"document:Id": str(our_bank_id)
								}
							}
						},
						"document:InstdAgt":{
							"document:FinInstnId":{
								"document:Othr":{
									"document:Id": str(dest_bank_id)
								}
							}
						}
					},
					"document:CdtTrfTxInf":{
						"document:PmtId":{
							"document:EndToEndId": "-",
							"document:TxId": str(fp_verification_id)
						},
						"document:IntrBkSttlmAmt":{
							"attr_names": ["Ccy"],
							"attr_values": [str(currency_code)],
							'node_value': str(amount)
						},
						"document:AccptncDtTm": cre_dt_tm,
						"document:InstdAmt": {
							"attr_names": ["Ccy"],
							"attr_values": [str(currency_code)],
							'node_value': str(amount)
						},
						"document:ChrgBr": "SLEV",
						"document:UltmtDbtr": {
							"document:Nm": cli_name,
							"document:Id": {
								"document:OrgId": {
									"document:Othr":{
										"document:Id": str(cli_id_no),
										"document:SchmeNm": {
											"document:Prtry": str(cli_id_type)
										}
									}
								}
							}
						},
						"document:Dbtr": {
							"document:Nm": our_client_name.strip(),
							"document:PstlAdr":{
								"document:AdrLine": our_client_address + '#' + our_branch_name
							},
							"document:CtctDtls":{
								"document:Othr": fp_region_code
							}
						},
						"document:DbtrAcct": {
							"document:Id":{
								"document:Othr":{
									"document:Id": our_branch_code + str(client_no) + str(client_serial) + str(currency_system_code),
									"document:SchmeNm":{
										"document:Prtry": str(acc_type)
									},
									"document:Issr": "C"
								}
							}
						},
						"document:DbtrAgt": {
							"document:FinInstnId":{
								"document:PstlAdr":{
									"document:BldgNb": "01"
								},
								"document:Othr": {
									"document:Id": our_bank_id,
									"document:Issr": "TELER-" + username
								}
							},
							"document:BrnchId": {
								"document:Nm": our_branch_code
							}
						},
						"document:CdtrAgt": {
							"document:FinInstnId":{
								"document:Othr":{
									"document:Id": str(dest_bank_id)
								}
							}
						},
						"document:Cdtr": {
							"document:Nm": beneficiary_name.strip()
						},
						"document:CdtrAcct":{
							"document:Id":{
								"document:Othr":{
									"document:Id": str(beneficiary_no),
									"document:SchmeNm":{
										"document:Prtry": str(acc_type)
									}
								}
							}
						},
						"document:RmtInf":{
							"document:Ustrd": str(op_type)
						}
					}
				}
			}
		}
	}
	
	_, xml = dicttoxml(doc_obj)

	with open(save_path_file, "w") as f:
		f.write(xml)
		f.close()
	return xml#,  gv_ReqBankId + lv_CreDtForSerial + gv_VerificationSerial

def num2str(num):
	num_int = int(float(num) * 1000)
	return str("{:016d}".format(num_int))

def read_xml_payment_data(xml):
	bs_data = BeautifulSoup(xml, "xml")
	result = bs_data.find('document:TxSts').text if bs_data.find('document:TxSts') else ''
	return result

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
		error_msg = _(socket_error_msg)
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
	req_path = 'Status/REQ/' + str(date.year) + '_' + str(date.month)
	res_path = 'Status/RES/' + str(date.year) + '_' + str(date.month)
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
	headers = {'Content-Type': 'application/xml'} 
	res_xml = requests.post(url= api_point, data=xml_body, headers=headers).text
	with open(res_xml_path, "w") as f:
		soup = BeautifulSoup(res_xml, "xml")
		f.write(soup.prettify())
		f.close()

	#------------------------------Saving files to database------------------------------
	save_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	save_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)

	return res_xml

def create_status_xml_doc(save_path_file, our_bank, fp_verification_id):
	header = 'urn:iso:std:iso:20022:tech:xsd:head.001.001.01'
	document = 'urn:iso:std:iso:20022:tech:xsd:pacs.028.001.02'
	fp_xml = 'urn:iso:std:iso:20022:tech:xsd:paymentStatus_request'

	req_bank = frappe.db.get_value('Bank Company', our_bank, ['system_code'])
	fp_header_name = frappe.db.get_value('Bank Service Control', "101", ['rec_text'])
	status_serial = get_table_serial_key('StatusSerial')

	cre_dt_serial = datetime.today().strftime('%Y%m%d%H%M%S')
	cre_dt = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
	cre_dt_tm = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"

	doc_obj = {
		"FPEnvelope":{
			"attr_names": ["xmlns","xmlns:document","xmlns:header"],
			"attr_values": [fp_xml, document, header],
			"header:AppHdr": {
				"header:Fr":{
					"header:FIId":{
						"header:FinInstnId":{
							"header:Othr":{
								"header:Id": req_bank
							}
						}
					}
				},
				"header:To": {
					"header:FIId": {
						"header:FinInstnId": {
							"header:Othr": {
								"header:Id": fp_header_name
							}
						}
					}
				},
				"header:BizMsgIdr": req_bank + cre_dt_serial + str(status_serial),
				"header:MsgDefIdr": "pacs.028.001.02",
				"header:CreDt": cre_dt
			},
			"document:Document": {
				"document:FIToFIPmtStsReq":{
					"document:GrpHdr":{
						"document:MsgId": req_bank + cre_dt_serial + str(status_serial),
						"document:CreDtTm": cre_dt_tm
					},
					"document:TxInf": {
						"document:OrgnlTxId": fp_verification_id
					}
				}
			}
		}
	}

	_, xml = dicttoxml(doc_obj)

	with open(save_path_file, "w") as f:
		f.write(xml)
		f.close()
	return xml