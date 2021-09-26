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
		"fieldname": "bictype",
		"fieldtype": "Data",
		"label": "Transaction Type",
	},
		{
		"fieldname": "orgnl_id",
		"fieldtype": "Data",
		"label": "Original ID",
	},
		{
		"fieldname": "trxdate",
		"fieldtype": "Data",
		"label": "Time",
	},
		{
		"fieldname": "dest",
		"fieldtype": "Data",
		"label": "Destination",
	},
		{
		"fieldname": "src",
		"fieldtype": "Data",
		"label": "Source",
	},
		{
		"fieldname": "debtor_act",
		"fieldtype": "Data",
		"label": "Debtor Account",
	},
		{
		"fieldname": "debtor_adrs",
		"fieldtype": "Data",
		"label": "Debtor Address",
	},
		{
		"fieldname": "creditor_act",
		"fieldtype": "Data",
		"label": "Creditor Account",
	},
		{
		"fieldname": "op_amount",
		"fieldtype": "Data",
		"label": "Operation Amount",
	},
		{
		"fieldname": "interchange_amount",
		"fieldtype": "Data",
		"label": "Interchange Amount",
	},
		{
		"fieldname": "setl_amount",
		"fieldtype": "Data",
		"label": "Settlement Amount",
	},
		{
		"fieldname": "service_fee",
		"fieldtype": "Data",
		"label": "Service Fee",
	},
	]

def get_data(filters=None):
	from_date, to_date, currency = filters.get('from'), filters.get('to'), filters.get('currency')
	currency_code = frappe.db.get_value("Bank Currency", currency, ["currency_code"])
	return frappe.db.sql("""
					SELECT bictype, orgnl_id, trxdate, dest, src, debtor_act, debtor_adrs, creditor_act, (op_amount + 0) as op_amount, interchange_amount, 
					(op_amount + interchange_amount) as setl_amount, (service_fee + 0) as service_fee from
					(select 'Sending' as bictype , bpo.fp_verification_id as orgnl_id , bpo.modified as trxdate, c.system_code as dest, '' as src, 
					CONCAT(b.branch_code, client_no, account_sequence, cur.system_code) as debtor_act,  CONCAT(bpo.region, "#", b.a_name) as debtor_adrs,
					bpo.beneficiary_no as creditor_act,
					bpo.amount as op_amount, (sender_bank_fee + receiver_bank_fee) as interchange_amount, swift_fee as  service_fee
					from `tabBank Payment Order` as bpo
					INNER JOIN `tabBank Company` as c ON bpo.receiver_bank=c.name
					INNER JOIN `tabBank Branch` as b ON bpo.branch=b.name
					INNER JOIN `tabBank Currency` as cur ON bpo.currency=cur.name
					WHERE  bpo.transaction_state_sequence='Post' AND (bpo.creation BETWEEN %s AND %s ) AND bpo.currency=%s 
					UNION
					select  'Receiving' as bictype , bpr.req_bank_tx_id as bic_id ,  bpr.modified as trxdate, '' as dest, bpr.req_bank_id as src,
					bpr.req_bank_debit_id as debtor_act, bpr.req_bank_pstl_adr as debtor_adrs, req_bank_acct_id as creditor_act,
					req_bank_intr_bk_sttlm_amt as op_amount , 0 as interchange_amount, 0 as  service_fee
					from `tabBank Payment Received` bpr
					WHERE (bpr.creation BETWEEN %s AND %s ) AND (bpr.status_recieved_flg=1 OR (bpr.psh_sts_rcv_flg=1 AND bpr.psh_sts_rcv_txt='ACSC')) AND bpr.req_bank_intr_bk_sttlm_amt_ccy=%s
					) as mastable
					order by trxdate
					""",(from_date, to_date,currency, from_date, to_date, currency_code), as_dict=True)
