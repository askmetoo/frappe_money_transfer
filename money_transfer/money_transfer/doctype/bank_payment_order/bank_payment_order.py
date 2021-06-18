# -*- coding: utf-8 -*-
# Copyright (c) 2021, omar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import socket

class BankPaymentOrder(Document):
	pass

@frappe.whitelist()
def getClientInfo(client_no, client_seril, branch_name, currency, amount):
	msg = ''
	branch_code, branch_ip, branch_port = frappe.db.get_value('Bank Branch',branch_name, ['branch_code', 'website', 'system_code'])
	currency_code = frappe.db.get_value('Bank Currency',currency, ['system_code'])
	for i in range(22):
		msg += 'z'
	msg += '820' + str(branch_code) + str(branch_code)
	for i in range(17):
		msg += 'z'
	amount = 0
	msg += str(branch_code) + str(client_no) + str(client_seril) + str(currency_code) + '1' + str("{:016d}".format(int(amount))) + '/'
	for i in range(59):
		msg += '#'
	for i in range(1907):
		msg += 'x'	
	msgAscii = msg.encode('ascii', 'replace')
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((branch_ip, int(branch_port)))
		s.sendall(msgAscii)
		data = s.recv(2052)
	dataUtf = data.decode("utf-8")
	errorFlag = dataUtf[0] == 'y' # 'y'
	errorMsg = ''
	if errorFlag:
		errorMsg = dataUtf[1:6]
	clientName = dataUtf[140:189]
	clientRegionCode = dataUtf[200:203]
	clientRegion = frappe.db.get_value('Bank Region',clientRegionCode, ['region_name'])
	result = {
		"error_msg": errorMsg, "client_name": clientName, "client_region_code":clientRegionCode, "client_region": clientRegion
	}
	return result

