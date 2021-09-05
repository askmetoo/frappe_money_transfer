// Copyright (c) 2016, omar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Settlement Report"] = {
	"filters": [
		{
			"fieldname": "from",
			"label": __("من تاريخ"),
			"fieldtype": "Date",
			"width": 80,
			"reqd": 1,
			"default": dateutil.year_start()
		},
		{
			"fieldname": "to",
			"label": __("إلى تاريخ"),
			"fieldtype": "Date",
			"width": 80,
			"reqd": 1,
			"default": dateutil.year_end()
		},
		{
			"fieldname": "begin",
			"label": __("الرصيد الافتتاحي"),
			"fieldtype": "Data",
			"width": 80,
			"reqd": 0,
			"default": 0
		},
		{
			"fieldname": "currency",
			"label": __("العملة"),
			"fieldtype": "Link",
			"options": "Bank Currency",
			"width": 80,
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Bank Currency")
		},

	]
};
