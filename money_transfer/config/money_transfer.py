from __future__ import unicode_literals
import frappe
from frappe import _

def get_data():
	data = [
		{
			"label": _("Transactions"),
			"icon": "fa fa-wrench",
			"items": [
				{
					"type": "doctype",
					"name": "Bank Payment Order",
					"label": _("Payment Order"),
				},	
				
			]
		},
        {
			"label": _("Portal"),
			"icon": "fa fa-wrench",
			"items": [
				{
					"type": "doctype",
					"name": "Bank Company",
					"label": _("Banks"),
				},
				{
					"type": "doctype",
					"name": "Bank Branch",
					"label": _("Branches"),
				},
				{
					"type": "doctype",
					"name": "Bank Region",
					"label": _("Regions"),
				},
                	
                {
					"type": "doctype",
					"name": "Bank Currency",
					"label": _("Currencies"),
				},		
			]
		},
		{
			
			"label": _("Settings"),
			"icon": "fa fa-wrench",
			"items": [
					{
					"type": "doctype",
					"name": "Bank Service Control",
					"label": _("Serivce Control"),
				},
					{
					"type": "doctype",
					"name": "Bank CSSRLCOD",
					"label": _("CSSRLCOD"),
				},
					{
					"type": "doctype",
					"name": "Bank System Error",
					"label": _("System Errors"),
				}
			]
		},
		{
			
			"label": _("Transaction Types"),
			"icon": "fa fa-wrench",
			"items": [
					{
					"type": "doctype",
					"name": "Bank Account Type",
					"label": _("Account Type"),
				},
					{
					"type": "doctype",
					"name": "Bank Card Type",
					"label": _("Card Type"),
				}
			]
		},
		{
			
			"label": _("YIB Info Service"),
			"icon": "fa fa-wrench",
			"items": [
					{
					"type": "doctype",
					"name": "Bank Verification Received",
					"label": _("Received Verification Requests"),
				},
				{
					"type": "doctype",
					"name": "Bank Payment Received",
					"label": _("Received Payment Requests"),
				},
				{
					"type": "doctype",
					"name": "Bank Status Received",
					"label": _("Received Status Requests"),
				}
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-wrench",
			"items":[
				{
					"type": "report",
					"name": "Settlement Report",
					"is_query_report": True,
					"doctype": "Bank Payment Order",
					"label": _("Settlement Report"),
				},	
				{
					"type": "report",
					"name": "Daily Settlement Report",
					"is_query_report": True,
					"doctype": "Bank Payment Order",
					"label": _("Daily Settlement Report"),
				},	
				{
					"type": "report",
					"name": "Switching Fees",
					"is_query_report": True,
					"doctype": "Bank Payment Order",
					"label": _("Switching Fees"),
				},	
				{
					"type": "report",
					"name": "Interchange Fees",
					"is_query_report": True,
					"doctype": "Bank Payment Order",
					"label": _("Interchange Fees"),
				},	
				{
					"type": "report",
					"name": "Reconciliation",
					"is_query_report": True,
					"doctype": "Bank Payment Order",
					"label": _("Reconciliation"),
				},	
				{
					"type": "report",
					"name": "Transaction By Member",
					"is_query_report": True,
					"doctype": "Bank Payment Order",
					"label": _("Transaction By Member"),
				},	
			]
		}
	]
	return data
