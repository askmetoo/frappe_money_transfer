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
		"fieldname": "transaction_id",
		"fieldtype": "Data",
		"label": "Transaction ID",
	},
		{
		"fieldname": "trans_amount",
		"fieldtype": "Data",
		"label": "Transferred Amount",
	},
		{
		"fieldname": "trans_fees",
		"fieldtype": "Data",
		"label": "Transferred Fees",
	},
		{
		"fieldname": "rcv_amount",
		"fieldtype": "Data",
		"label": "Received Amount",
	},
		{
		"fieldname": "rcv_fees",
		"fieldtype": "Data",
		"label": "Received Fees",
	},
		{
		"fieldname": "total",
		"fieldtype": "Data",
		"label": "Total",
	},
	]

def get_data(filters=None):
	from_date, to_date, currency = filters.get('from'), filters.get('to'), filters.get('currency')
	currency_code = frappe.db.get_value("Bank Currency", currency, ["currency_code"])
	return frappe.db.sql("""
			select bictype , bic_id as transaction_id, snd_amount as trans_amount, rcv_amount + 0 as rcv_amount, trans_fees + 0 as trans_fees, rcv_fees , trxdate, trans_fees + rcv_fees as total  from (
			select 'sender' as bictype , bpo.fp_verification_id as bic_id , bpo.amount as snd_amount, 0 as rcv_amount  , swift_fee as  trans_fees , 0 as rcv_fees , modified as trxdate
			from `tabBank Payment Order` as bpo
			WHERE  bpo.transaction_state_sequence='Post' AND (bpo.creation BETWEEN %s AND %s ) AND bpo.currency=%s 
			UNION
			select  'receiver' as bictype , req_bank_tx_id as bic_id ,0 as snd_amount,req_bank_intr_bk_sttlm_amt as rcv_amount , 0 as trans_fees , 0 as rcv_fees , modified as trxdate
			from `tabBank Payment Received` bpr
			WHERE (bpr.creation BETWEEN %s AND %s ) AND (bpr.status_recieved_flg=1 OR (bpr.psh_sts_rcv_flg=1 AND bpr.psh_sts_rcv_txt='ACSC')) AND bpr.req_bank_intr_bk_sttlm_amt_ccy=%s
			) as  mastable
			order by trxdate desc
			""",(from_date, to_date,currency, from_date, to_date, currency_code), as_dict=True)
