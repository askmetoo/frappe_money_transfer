import frappe
import shutil

def get_table_serial_key(table_name):
	#table_serial = frappe.db.get_value('Bank CSSRLCOD', table_name, ['table_serial'])
  serial_doc = frappe.get_doc('Bank CSSRLCOD', table_name)
  table_serial = serial_doc.table_serial
	#frappe.db.set_value('Bank CSSRLCOD', table_name, {"table_serial" : str(int(table_serial) + 1)})
  serial_doc.table_serial = str(int(table_serial) + 1)
  serial_doc.save(ignore_permissions=True)
  return table_serial

def get_service_control(rec_control):
  return frappe.db.get_value("Bank Service Control", rec_control, "rec_text")

def save_file_db(site_name, file_name, file_path, private_path, relative_path, doc_name):
	doc = 'Bank Payment Order'
	file = frappe.get_doc({
		"doctype":"File", 'file_url':  None, 'file_name': file_name,
		'is_private':1, 'attached_to_name':doc_name, "attached_to_doctype":doc  })
	file.insert(ignore_permissions=True)

	shutil.move(file_path, site_name + private_path + relative_path + '/' + file_name)
	new_url = private_path + relative_path + '/' + file_name
	
	frappe.db.sql('UPDATE tabFile SET file_url=%s WHERE name=%s', (new_url,file.name))

def get_verification_data(our_bank, dis_bank, currency):
	req_bank_id = frappe.db.get_value('Bank Company', our_bank, ['system_code'])
	dis_bank_id = frappe.db.get_value('Bank Company', dis_bank, ['system_code'])

	fp_header_name = frappe.db.get_value('Bank Service Control', "101", ['rec_text'])
	acmt_req = frappe.db.get_value('Bank Service Control', "201", ['rec_text'])
	verification_serial = get_table_serial_key('VerificationSerial')
	currency_prefix = frappe.db.get_value('Bank Currency', currency, ['currency_prefix'])
	currency_prefix = currency_prefix if currency_prefix else ''
	return req_bank_id, dis_bank_id, fp_header_name, acmt_req, verification_serial, currency_prefix

def get_fees_data(user_bank, dest_bank, user_branch, currency):
	req_bank_id, fees_password = frappe.db.get_value('Bank Company', user_bank, ['system_code', 'fees_password'])
	dest_bank_id = frappe.db.get_value('Bank Company', dest_bank, ['system_code'])

	branch_region = frappe.db.get_value('Bank Branch',user_branch, ['branch_region'])
	unique_code = frappe.db.get_value('Bank Region',branch_region, ['unique_code'])

	currency_code = frappe.db.get_value('Bank Currency', currency, ['currency_code'])

	return req_bank_id, fees_password, dest_bank_id, unique_code, currency_code
	

def get_payment_data(our_bank, dest_bank, our_branch, region_code, currency, account_type, sender_region):
	our_bank_id = frappe.db.get_value('Bank Company', our_bank, ['system_code'])
	dest_bank_id = frappe.db.get_value('Bank Company', dest_bank, ['system_code'])
	our_branch_code, our_branch_name = frappe.db.get_value('Bank Branch', our_branch, ['branch_code', 'a_name'])

	fp_region_code = frappe.db.get_value('Bank Region', {"region_code":region_code}, ['service_code'])
	currency_code, currency_system_code, currency_prefix =frappe.db.get_value('Bank Currency', currency, ['currency_code', 'system_code', 'currency_prefix'])
	currency_prefix = currency_prefix if currency_prefix else ''

	fp_header_name = frappe.db.get_value('Bank Service Control', "101", ['rec_text'])
	pacs_req = frappe.db.get_value('Bank Service Control', "202", ['rec_text'])
	acc_type = frappe.db.get_value('Bank Account Type', account_type, ['system_code'])
	payment_serial = get_table_serial_key('PaymentSerial')
	username = frappe.db.get_value('User', frappe.session.user, ['username'])
	if sender_region != '':
		sender_address, sender_region_code = frappe.db.get_value('Bank Region', sender_region, ["a_name","service_code"])
	else:
		sender_address, sender_region_code = '',''
	return (our_bank_id, dest_bank_id, our_branch_code, our_branch_name, fp_region_code, currency_code, 
	currency_system_code, fp_header_name, pacs_req, acc_type, payment_serial, username, currency_prefix, sender_address, sender_region_code)

def get_status_data(our_bank):
	req_bank = frappe.db.get_value('Bank Company', our_bank, ['system_code'])
	fp_header_name = frappe.db.get_value('Bank Service Control', "101", ['rec_text'])
	status_serial = get_table_serial_key('StatusSerial')

	return req_bank, fp_header_name, status_serial