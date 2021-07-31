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
		}
	]
	return data
