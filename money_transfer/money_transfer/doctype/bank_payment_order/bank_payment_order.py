# -*- coding: utf-8 -*-
# Copyright (c) 2021, omar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import socket
from xml.dom import minidom
from frappe.utils.data import unique
from money_transfer.money_transfer.utils import dicttoxml, mkdir
from collections import OrderedDict
from datetime import datetime
import requests
from requests.api import head
from frappe.utils import get_site_name
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
	for _ in range(22):
		msg += 'z'
	msg += '820' + str(branch_code) + str(branch_code)
	for _ in range(17):
		msg += 'z'

	wnote = fp_verification_id + '/' + beneficiary_name[:30]
	for _ in range(60):
		wnote += '#'

	total_amount_str = get_total_amount(amount, rcv_fee, swift_fee, snd_fee)

	msg += str(branch_code) + str(client_no) + str(client_seril) + str(currency_code) + '1' + total_amount_str + wnote[:60]

	for _ in range(1908):
		msg += 'x'

	msg_ascii = msg.encode('ascii', 'replace')
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((branch_ip, int(branch_port)))
		s.sendall(msg_ascii)
		data = s.recv(2052)
		s.shutdown(socket.SHUT_RDWR)
		s.close()
	error_flag = data[0] == 121 # 'y'
	error_msg = ''
	if error_flag:
		error_code = data[1:6].decode("utf-8").strip()
		error_msg = frappe.db.get_value('Bank System Error', error_code, ['a_name'])
	client_name = data[140:189].decode("iso8859_6")
	client_region_code = data[200:203].decode("utf-8")
	client_region = frappe.db.get_value('Bank Region',{'region_code':client_region_code}, ['a_name'])
	result = {
		"error_msg": error_msg, "client_name": client_name, "client_region_code":client_region_code, "client_region": client_region
	}
	return result

@frappe.whitelist()
def sendVerificationDoc(client_no, client_seril, our_bank, user_branch, dest_bank, beneficiary_no, account_type, doc_name, amount, currency):
	site_name = get_site_name(frappe.local.request.host)
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

	xml_body, ourVefId = createBVXmlDoc(req_xml_path, our_bank, dest_bank, beneficiary_no, acc_type)

	#------------------------------Sending REST request------------------------------
	api_point = frappe.db.get_value('Bank Service Control', "251", ['rec_text'])
	headers = {'Content-Type': 'application/xml'} 
	res_xml = requests.post(url= api_point, data=xml_body, headers=headers).text
	with open(res_xml_path, "w") as f:
		f.write(res_xml)
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
	print(fees_res_xml)
	retail, switch, interchange, result, transactionid, errordesc = read_xml_fees_data(fees_res_xml)

	with open(lv_FeesRSFilePath, "w") as f:
		f.write(fees_res_xml)
		f.close()
	
	#------------------------------Saving files to database------------------------------
	save_file_db(site_name, req_file_name, req_xml_path, private_path, req_path, doc_name)
	save_file_db(site_name, res_file_name, res_xml_path, private_path, res_path, doc_name)

	save_file_db(site_name, lv_FeesRQFileName, lv_FeesRQFilePath, private_path, req_path, doc_name)
	save_file_db(site_name, lv_FeesRSFileName, lv_FeesRSFilePath, private_path, res_path, doc_name)

	#------------------------------Reserving money------------------------------
	error_msg = ''
	if result == 'Success':
		res = check_client(client_no, client_seril, user_branch, currency, amount, rcv_fee= interchange, swift_fee=switch, snd_fee=retail, beneficiary_name=pv_Nm, fp_verification_id=pv_FPVrfctn)
		error_msg = res['error_msg']

	
	results = {
		'error_msg':error_msg,'pv_Vrfctn': pv_Vrfctn, 'pv_Rsn' : pv_Rsn, 'pv_Nm': pv_Nm, 'pv_FPVrfctn':pv_FPVrfctn, 'our_verf_id':ourVefId,
		'retail':retail, 'switch':switch, 'interchange': interchange, 'result': result, 'transactionid':transactionid, 'errordesc':errordesc
	}
	return results

def createBVXmlDoc(save_path_file, our_bank, dis_bank, beneficiary_no, account_type):
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
	data = ''
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((branch_ip, int(branch_port)))
		s.sendall(msg_ascii)
		data = s.recv(2052)
		s.shutdown(socket.SHUT_RDWR)
		s.close()

	error_flag = data[0] == 121 # 'y'
	error_msg = ''
	if error_flag:
		error_code = data[1:6].decode("utf-8").strip()
		error_msg = frappe.db.get_value('Bank System Error', error_code, ['a_name'])
	return {'error_msg': error_msg}


def get_total_amount(amount, rcv_fee, swift_fee, snd_fee):
	total_amount = float(amount) + float(rcv_fee) + float(swift_fee) + float(snd_fee)
	total_amount_int = int(total_amount) * 1000
	return str("{:016d}".format(total_amount_int))