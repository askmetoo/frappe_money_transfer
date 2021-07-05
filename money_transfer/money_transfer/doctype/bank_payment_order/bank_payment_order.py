# -*- coding: utf-8 -*-
# Copyright (c) 2021, omar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
import socket
from xml.dom import minidom
from money_transfer.money_transfer.utils import dicttoxml, mkdir
from collections import OrderedDict
from datetime import datetime
import requests
from requests.api import head
from frappe.utils import get_site_name
from bs4 import BeautifulSoup
import os
import shutil
class BankPaymentOrder(Document):
	pass

@frappe.whitelist()
def getClientInfo(client_no, client_seril, branch_name, currency, amount):
	msg = ''
	branch_code, branch_ip, branch_port = frappe.db.get_value('Bank Branch',branch_name, ['branch_code', 'ip_address', 'port_number'])
	currency_code = frappe.db.get_value('Bank Currency',currency, ['system_code'])
	for i in range(22):
		msg += 'z'
	msg += '820' + str(branch_code) + str(branch_code)
	for i in range(17):
		msg += 'z'
	amount = 0
	msg += str(branch_code) + str(client_no) + str(client_seril) + str(currency_code) + '1' + str("{:016d}".format(int(amount))) 
	for i in range(60):
		msg += '#'
	for i in range(1907):
		msg += 'x'
	msgAscii = msg.encode('ascii', 'replace')
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((branch_ip, int(branch_port)))
		s.sendall(msgAscii)
		data = s.recv(2052)
		s.shutdown(socket.SHUT_RDWR)
		s.close()
	dataUtf = data #.decode("utf-8")
	errorFlag = dataUtf[0] == 121 # 'y'
	errorMsg = ''
	if errorFlag:
		errorCode = dataUtf[1:6].decode("utf-8").strip()
		print("*" * 100)
		print(errorCode)
		print("*" * 100)
		errorMsg = frappe.db.get_value('Bank System Error', errorCode, ['a_name'])
	clientName = dataUtf[140:189].decode("iso8859_6")
	clientRegionCode = dataUtf[200:203].decode("utf-8")
	clientRegion = frappe.db.get_value('Bank Region',{'region_code':clientRegionCode}, ['region_name'])
	result = {
		"error_msg": errorMsg, "client_name": clientName, "client_region_code":clientRegionCode, "client_region": clientRegion
	}
	return result

@frappe.whitelist()
def sendVerificationDoc(our_bank, dis_bank, beneficiary_no, account_type, doc_name):
	site_name = get_site_name(frappe.local.request.host)
	public_path = '/public/files/'
	private_path = '/private/files/'
	req_path = 'Verification/REQ'
	res_path = 'Verification/RES'
	BillVerification_Serial = frappe.db.get_value('Bank CSSRLCOD', "VerificationFileSerial", ['table_serial'])
	date = datetime.now()
	postfix = str(date.year) + str(date.month) + str(date.day) + '_' + BillVerification_Serial + '.xml'
	req_file_name = 'Verification_RQ_' + postfix
	res_file_name = 'Verification_RS_' + postfix
	req_xml_path = site_name + public_path + req_file_name
	res_xml_path = site_name + public_path + res_file_name
	acc_type = frappe.db.get_value('Bank Account Type', account_type, ['system_code'])
	mkdir([site_name + private_path + req_path , site_name + private_path + res_path ])

	xml_body, ourVefId = createBVXmlDoc(req_xml_path, our_bank, dis_bank, beneficiary_no, acc_type)

	# Sending REST request
	api_point = frappe.db.get_value('Bank Service Control', "251", ['rec_text'])
	headers = {'Content-Type': 'application/xml'} 
	res_xml = requests.post(url= api_point, data=xml_body, headers=headers).text
	with open(res_xml_path, "w") as f:
		f.write(res_xml)

	pv_Vrfctn, pv_Rsn, pv_Nm, pv_FPVrfctn = read_xml_verification_data(res_xml)

	# Saving files to database
	doc = 'Bank Payment Order'
	cwd = os.getcwd()
	
	file1 = frappe.get_doc({
		"doctype":"File", 'file_url':  None, 'file_name': req_file_name,
		'is_private':1, 'attached_to_name':doc_name, "attached_to_doctype":doc  })
	file1.insert()

	file2 = frappe.get_doc({
		"doctype":"File", 'file_url':  None, 'file_name': res_file_name,
		'is_private':1, 'attached_to_name':doc_name, "attached_to_doctype":doc  })
	file2.insert()

	shutil.move(req_xml_path, site_name + private_path + req_path + '/' + req_file_name)
	shutil.move(res_xml_path, site_name + private_path + res_path + '/' + res_file_name)
	new_req_url = private_path + req_path + '/' + req_file_name
	new_res_url = private_path + res_path + '/' + res_file_name
	
	frappe.db.sql('UPDATE tabFile SET file_url=%s WHERE name=%s', (new_req_url,file1.name))
	frappe.db.sql('UPDATE tabFile SET file_url=%s WHERE name=%s', (new_res_url,file2.name))
	result = {
		'pv_Vrfctn': pv_Vrfctn, 'pv_Rsn' : pv_Rsn, 'pv_Nm': pv_Nm, 'pv_FPVrfctn':pv_FPVrfctn, 'our_verf_id':ourVefId
	}
	return result

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
	gv_VerificationSerial = frappe.db.get_value('Bank CSSRLCOD', "VerificationSerial", ['table_serial'])
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

	return xml,  gv_ReqBankId + lv_CreDtForSerial + gv_VerificationSerial

def read_xml_verification_data(xml):
	Bs_data = BeautifulSoup(xml, "xml")
	pv_Vrfctn = Bs_data.find('document:Vrfctn').text
	pv_Rsn = Bs_data.find('document:Rsn').find('document:Prtry').text
	pv_Nm = Bs_data.find('document:Nm').text
	pv_FPVrfctn = Bs_data.find('document:OrgnlId').text

	return pv_Vrfctn, pv_Rsn, pv_Nm, pv_FPVrfctn
