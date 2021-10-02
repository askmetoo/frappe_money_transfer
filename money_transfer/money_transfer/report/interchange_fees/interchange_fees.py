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
		"fieldname": "trans_rcv",
		"fieldtype": "Data",
		"label": "Receiver Bank Fee",
	},
		{
		"fieldname": "trans_swft",
		"fieldtype": "Data",
		"label": "Swift Fee",
	},
		{
		"fieldname": "trans_snd",
		"fieldtype": "Data",
		"label": "Sender Bank Fee",
	},
		{
		"fieldname": "rcv_amount",
		"fieldtype": "Data",
		"label": "Received Amount",
	},
		{
		"fieldname": "rcv_rcv",
		"fieldtype": "Data",
		"label": "Receiver Bank Fee",
	},
		{
		"fieldname": "rcv_swft",
		"fieldtype": "Data",
		"label": "Swift Fee",
	},
		{
		"fieldname": "rcv_snd",
		"fieldtype": "Data",
		"label": "Sender Bank Fee",
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
	SELECT bank as participant, 
	SUM(trans_amount) as trans_amount, SUM(trans_rcv) as trans_rcv, SUM(trans_swft) as trans_swft,SUM(trans_snd) as trans_snd, 
	SUM(rcv_amount) as rcv_amount, SUM(rcv_rcv) as rcv_rcv, SUM(rcv_swft) as rcv_swft,SUM(rcv_snd) as rcv_snd, 
	(SUM( trans_rcv + trans_swft + trans_snd  - rcv_rcv - rcv_swft - rcv_snd)) as net_balance FROM(
		SELECT c.system_code as bank,  sum(bpo.amount) as trans_amount, sum(bpo.receiver_bank_fee) as trans_rcv, 
		SUM(bpo.swift_fee) as trans_swft, SUM(bpo.sender_bank_fee) as trans_snd, 0 as rcv_amount, 0 as rcv_rcv, 0 as rcv_swft, 0 as rcv_snd
			FROM `tabBank Payment Order` as bpo
			INNER JOIN `tabBank Company` as c ON receiver_bank=c.name
			WHERE transaction_state_sequence='Post' AND (bpo.creation BETWEEN %s AND %s ) AND bpo.currency=%s 
			GROUP BY receiver_bank
	UNION
	SELECT req_bank_id as bank,  0 as trans_amount, 0 as trans_rcv, 0 as trans_swft, 0 as trans_snd, 
			SUM(bpr.req_bank_intr_bk_sttlm_amt) as rcv_amount , SUM(bpr.retail_fees) as rcv_rcv, SUM(bpr.switch_fees) as rcv_swft, SUM(bpr.interchange_fees) as rcv_snd
			FROM `tabBank Payment Received` as bpr
			WHERE (bpr.creation BETWEEN %s AND %s ) AND (status_recieved_flg=1 OR (psh_sts_rcv_flg=1 AND psh_sts_rcv_txt='ACSC')) AND bpr.req_bank_intr_bk_sttlm_amt_ccy=%s
			GROUP BY req_bank_id
			) as master_table
	GROUP BY bank
			""",(from_date, to_date,currency, from_date, to_date, currency_code), as_dict=True)
