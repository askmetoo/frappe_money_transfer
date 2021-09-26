# Copyright (c) 2013, omar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data


def get_columns():
	return [
		{
		"fieldname": "participant",
		"fieldtype": "Data",
		"label": "Participant",
	},
		{
		"fieldname": "trans_rcv",
		"fieldtype": "Data",
		"label": "Transferred YIB Received",
	},
		{
		"fieldname": "trans_paid",
		"fieldtype": "Data",
		"label": "Transferred YIB Paid",
	},
		{
		"fieldname": "rcv_rcv",
		"fieldtype": "Data",
		"label": "Received YIB Received",
	},
		{
		"fieldname": "rcv_paid",
		"fieldtype": "Data",
		"label": "Received YIB Paid",
	},
		{
		"fieldname": "net_balance",
		"fieldtype": "Data",
		"label": "Net Balance",
	},
	]

def get_data(filters=None):
	from_date, to_date, currency = filters.get('from'), filters.get('to'), filters.get('currency')
	currency_code = frappe.db.get_value("Bank Currency", currency, ["currency_code"])
	return frappe.db.sql("""
	SELECT bank as participant, SUM(trans_rcv) as trans_rcv, SUM(trans_paid) as trans_paid, 
	SUM(rcv_rcv) as rcv_rcv, SUM(rcv_paid) as rcv_paid, 
	(SUM(trans_rcv + rcv_rcv -  trans_paid - rcv_paid)) as net_balance FROM(
		SELECT c.system_code as bank,  sum(bpo.sender_bank_fee) as trans_rcv, SUM(bpo.receiver_bank_fee) as trans_paid, 0 as rcv_rcv, 0 as rcv_paid
			FROM `tabBank Payment Order` as bpo
			INNER JOIN `tabBank Company` as c ON receiver_bank=c.name
			WHERE transaction_state_sequence='Post' AND (bpo.creation BETWEEN %s AND %s ) AND bpo.currency=%s 
			GROUP BY receiver_bank
	UNION
	SELECT req_bank_id as bank,  0 as trans_rcv, 0 as trans_paid, 0 as rcv_rcv, 0 as rcv_paid
			FROM `tabBank Payment Received` as bpr
			WHERE (bpr.creation BETWEEN %s AND %s ) AND (status_recieved_flg=1 OR (psh_sts_rcv_flg=1 AND psh_sts_rcv_txt='ACSC')) AND bpr.req_bank_intr_bk_sttlm_amt_ccy=%s
			GROUP BY req_bank_id
			) as master_table
	GROUP BY bank
			""",(from_date, to_date,currency, from_date, to_date, currency_code), as_dict=True)
