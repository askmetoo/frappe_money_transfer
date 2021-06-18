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
					"name": "Bank Region",
					"label": _("Region"),
				},
                	{
					"type": "doctype",
					"name": "Bank Branch",
					"label": _("Branch"),
				},
                {
					"type": "doctype",
					"name": "Bank Currency",
					"label": _("Currency"),
				},		
			]
		}
	]
	return data
