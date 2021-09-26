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
		"fieldname": "trans_amount",
		"fieldtype": "Data",
		"label": "Transferred Amount",
	},
		{
		"fieldname": "trans_no",
		"fieldtype": "Data",
		"label": "Transferred No",
	},
		{
		"fieldname": "rcv_amount",
		"fieldtype": "Data",
		"label": "Received Amount",
	},
		{
		"fieldname": "rcv_no",
		"fieldtype": "Data",
		"label": "Received No",
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
	SELECT bank as participant, SUM(total_amount_fees_trans) as trans_amount, SUM(count_trans) as trans_no, SUM(total_amount_fees_rcv) as rcv_amount, SUM(count_rcv) as rcv_no, 
	(SUM(total_amount_fees_trans) - SUM(total_amount_fees_rcv)) as net_balance FROM(
		SELECT c.system_code as bank, count(receiver_bank) as count_trans, 
				(sum(amount) + sum(receiver_bank_fee + sender_bank_fee + swift_fee)) as total_amount_fees_trans,
				0 as count_rcv, 0 as total_amount_fees_rcv
			FROM `tabBank Payment Order` as bpo
			INNER JOIN `tabBank Company` as c ON receiver_bank=c.name
			WHERE transaction_state_sequence='Post' AND (bpo.creation BETWEEN %s AND %s ) AND bpo.currency=%s 
			GROUP BY receiver_bank
	UNION
	SELECT req_bank_id as bank,  0 as count_trans, 0 as total_amount_fees_trans, 
			count(req_bank_id) as count_rcv,
			(sum(req_bank_intr_bk_sttlm_amt) + sum(retail_fees + interchange_fees + switch_fees)) as total_amount_fees_rcv
			FROM `tabBank Payment Received` as bpr
			WHERE (bpr.creation BETWEEN %s AND %s ) AND (status_recieved_flg=1 OR (psh_sts_rcv_flg=1 AND psh_sts_rcv_txt='ACSC')) AND bpr.req_bank_intr_bk_sttlm_amt_ccy=%s
			GROUP BY req_bank_id
			) as master_table
	GROUP BY bank
			""",(from_date, to_date,currency, from_date, to_date, currency_code), as_dict=True)
