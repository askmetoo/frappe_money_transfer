# Copyright (c) 2013, omar and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from typing import Dict

import frappe
# import frappe

def execute(filters=None):
	columns = get_columns()

	data = get_data(filters)
	return columns, data

def get_columns():
  return [{
   "fieldname": "bank",
   "fieldtype": "Data",
   "label": "البنوك",
  },

  {
   "fieldname": "snd_total_amount",
   "fieldtype": "Data",
   "label": "اجمالي الحركات الصادرة",
  },
  {
   "fieldname": "snd_count",
   "fieldtype": "Data",
   "label": "عدد الحركات الصادرة",
  },
   {
   "fieldname": "snd_total_fees",
   "fieldtype": "Data",
   "label": "اجمالي العمولات الصادرة",
  },
   {
   "fieldname": "snd_total_amount_fees",
   "fieldtype": "Data",
   "label": "اجمالي الصادر",
  },

  {
   "fieldname": "rcv_total_amount",
   "fieldtype": "Data",
   "label": "اجمالي الحركات الواردة",
  },
  {
   "fieldname": "rcv_count",
   "fieldtype": "Data",
   "label": "عدد الحركات الواردة",
  },
   {
   "fieldname": "rcv_total_fees",
   "fieldtype": "Data",
   "label": "اجمالي العمولات الواردة",
  },
   {
   "fieldname": "rcv_total_amount_fees",
   "fieldtype": "Data",
   "label": "اجمالي الوارد",
  }
  ]

def get_data(filters=None):
  data = []
  data_obj = dict()
  from_date, to_date, currency = filters.get('from'), filters.get('to'), filters.get('currency')
  currency_code = frappe.db.get_value("Bank Currency", currency, ["currency_code"])
  snd_data = frappe.db.sql("""
          SELECT c.system_code as bank, sum(amount) as total_amount,  
          sum(receiver_bank_fee + sender_bank_fee + swift_fee) as total_fees, count(receiver_bank) as count,
            (sum(amount) + sum(receiver_bank_fee + sender_bank_fee + swift_fee)) as total_amount_fees
          FROM `tabBank Payment Order` as p
          INNER JOIN `tabBank Company` as c ON receiver_bank=c.name
          WHERE transaction_state_sequence='Post' AND (p.creation BETWEEN %s AND %s ) AND currency=%s
          GROUP BY receiver_bank
  """, (from_date, to_date, currency))
  rcv_data = frappe.db.sql("""
          SELECT req_bank_id as bank, sum(req_bank_intr_bk_sttlm_amt) as total_amount, 
            sum( IFNULL(retail_fees, "0")+ IFNULL(interchange_fees, "0") + IFNULL(switch_fees, "0") ) as total_fees, 
            count(req_bank_id) as count, 
            (sum(req_bank_intr_bk_sttlm_amt) + sum(retail_fees + interchange_fees + switch_fees)) as total_amount_fees
          FROM `tabBank Payment Received` as p
          WHERE (p.creation BETWEEN %s AND %s ) AND (status_recieved_flg=1 OR (psh_sts_rcv_flg=1 AND psh_sts_rcv_txt='ACSC')) AND req_bank_intr_bk_sttlm_amt_ccy=%s
          GROUP BY req_bank_id
  """, (from_date, to_date, currency_code))
  for d in snd_data:
    obj = {
      "bank": d[0],
      "snd_total_amount": d[1],
      "snd_total_fees": d[2],
      "snd_count": d[3],
      "snd_total_amount_fees": float(d[1]) + float(d[2]),
      "rcv_total_amount": 0,
      "rcv_total_fees": 0,
      "rcv_count": 0,
      "rcv_total_amount_fees": 0
    }
    data_obj[d[0]] = obj
  for d in rcv_data:
    if d[0] in data_obj.keys():
      obj = {
      "rcv_total_amount": d[1],
      "rcv_total_fees": d[2],
      "rcv_count": d[3],
      "rcv_total_amount_fees": float(d[1]) + float(d[2])
    }
      data_obj[d[0]].update(obj)
    else:
      obj = {
        "bank":d[0],
      "snd_total_amount":0,
      "snd_total_fees": 0,
      "snd_count": 0,
      "snd_total_amount_fees":0,
      "rcv_total_amount": d[1],
      "rcv_total_fees": d[2],
      "rcv_count": d[3],
      "rcv_total_amount_fees": float(d[1]) + float(d[2])
    }
      data_obj[d[0]] = obj
  for d in data_obj.values():
    data.append(d)
  return data