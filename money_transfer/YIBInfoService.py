import frappe
@frappe.whitelist(allow_guest=True)
def Verification():
	from werkzeug.wrappers import Response
	# response = Response()
	# response.mimetype = 'text/xml'
	# response.charset = 'utf-8'
	# response.data = '<xml>{ar}</xml>'.format(ar =args)
	print("*" * 100)
	print(frappe.request.data)
	print("*" * 100)
	return "test"

@frappe.whitelist(allow_guest=True)
def Payment():
	from werkzeug.wrappers import Response
	# response = Response()
	# response.mimetype = 'text/xml'
	# response.charset = 'utf-8'
	# response.data = '<xml>{ar}</xml>'.format(ar =args)
	print("*" * 100)
	print(frappe.request.data)
	print("*" * 100)
	return "test payment"

@frappe.whitelist(allow_guest=True)
def Status():
	from werkzeug.wrappers import Response
	# response = Response()
	# response.mimetype = 'text/xml'
	# response.charset = 'utf-8'
	# response.data = '<xml>{ar}</xml>'.format(ar =args)
	print("*" * 100)
	print(frappe.request.data)
	print("*" * 100)
	return "test status"