// Copyright (c) 2016, omar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Interchange Fees"] = {
	"filters": [
		{
			"fieldname": "from",
			"label": __("من تاريخ"),
			"fieldtype": "Datetime",
			"width": 80,
			"reqd": 1,
			"default": moment().format('YYYY-MM-DD 00:00:00')
		},
		{
			"fieldname": "to",
			"label": __("إلى تاريخ"),
			"fieldtype": "Datetime",
			"width": 80,
			"reqd": 1,
			"default": moment().format('YYYY-MM-DD 23:59:59')
		},
		{
			"fieldname": "currency",
			"label": __("العملة"),
			"fieldtype": "Link",
			"options": "Bank Currency",
			"width": 80,
			"reqd": 1,
			on_change: () => {
				var currency = frappe.query_report.get_filter_value('currency');
				frappe.model.get_value("Bank Currency", currency, ["name", "currency_code"], (val)=>{
					frappe.currency_code = val.currency_code;
					frappe.query_report.refresh();
				})

			}
		},
	]
};
