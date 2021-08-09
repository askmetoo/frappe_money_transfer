import frappe
from money_transfer.money_transfer.db import get_service_control
from money_transfer.money_transfer.utils import console_print, get_total_amount, num2str
from money_transfer.money_transfer.socket_handler import make_socket_connection

def get_customer_details(client_no):
    customer_name, customer_add, customer_no, customer_brn, region_unique_code, customer_error, error_flag = "NA", "NA", "NA", "", "", "", 0
    client_no = client_no.strip().zfill(15)
    cli_brn, cli_no, cli_ser, cli_cur = client_no[:3], client_no[3:10], client_no[10:13], client_no[13:15]
    
    our_header_name = get_service_control(102)
    our_bank_id = frappe.db.get_value("Bank Company", {"system_code":our_header_name}, "name")
    customer_brn, branch_region_id, branch_ip, branch_port = frappe.db.get_value("Bank Branch", {"branch_code":cli_brn, "bank":our_bank_id}, ["a_name","branch_region","ip_address", "port_number"] )
    region_unique_code = frappe.db.get_value("Bank Region", branch_region_id, "unique_code")

    msg = ''
    for i in range(22): msg += 'z'
    msg += '822' + str(cli_brn) + str(cli_brn)
    for i in range(17): msg += 'z'
    wnote = ''.join(['#' for i in range(60)])
    msg += client_no + '1' + get_total_amount() + wnote[:60]
    for i in range(len(msg), 2052): msg += "x"

    msg_ascii = msg.encode('ascii', 'replace')

    data, socket_error_msg = make_socket_connection(branch_ip, branch_port, msg_ascii)

    if socket_error_msg == '':
        error_msg = data[1:6].decode("utf-8").strip()
        if error_msg != 'zzzzz':
            error_flag = 1
            customer_error = error_msg
        customer_name = data[140:200].decode("iso8859_6")
        client_region_code = data[200:203].decode("utf-8")
        customer_add = frappe.db.get_value('Bank Region',{'region_code':client_region_code}, ['a_name'])
        customer_no = client_no
    else:
        customer_error = "Can not connect to our bank server"
        error_flag = 1

    return customer_name, customer_add, customer_no, customer_brn, region_unique_code, customer_error, error_flag


def make_payment_for_customer(customer_no, req_intr_bk_sttlm_amt, req_orgnl_tx_id, req_bank_prtry_id, req_bank_id, snd_fees, swf_fees, rcv_fees):
    if not customer_no:
        return customer_no, 'Error in customer no', 1
    client_no = customer_no.strip().zfill(15)
    cli_brn, cli_no, cli_ser, cli_cur = client_no[:3], client_no[3:10], client_no[10:13], client_no[13:15]
    our_header_name = get_service_control(102)
    our_bank_id = frappe.db.get_value("Bank Company", {"system_code":our_header_name}, "name")
    customer_brn, branch_region_id, branch_ip, branch_port = frappe.db.get_value("Bank Branch", {"branch_code":cli_brn, "bank":our_bank_id}, ["a_name","branch_region","ip_address", "port_number"] )
    msg = ''
    for i in range(22): msg += 'z'
    msg += '824' + str(cli_brn) + str(cli_brn)
    for i in range(17): msg += 'z'
    wnote = req_orgnl_tx_id + '/' + req_bank_prtry_id + '/' + req_bank_id
    for i in range(60): wnote += "x"
    msg += client_no + '2' + num2str(req_intr_bk_sttlm_amt) + num2str(snd_fees) + num2str(swf_fees) +num2str(rcv_fees) + wnote[:60]
    for i in range(len(msg), 2052): msg += "x"

    msg_ascii = msg.encode('ascii', 'replace')
    data, socket_error_msg = make_socket_connection(branch_ip, branch_port, msg_ascii)
    if socket_error_msg == '':
        customer_error = data[1:6].decode("utf-8").strip()
        # if error_msg != 'zzzzz':
        #     error_flag = 1
        #     customer_error = error_msg
        error_flag = 0
        # customer_name = data[140:200].decode("iso8859_6")
        # client_region_code = data[200:203].decode("utf-8")
        # customer_add = frappe.db.get_value('Bank Region',{'region_code':client_region_code}, ['a_name'])
        customer_no = client_no
    else:
        customer_error = "Can not connect to our bank server"
        error_flag = 1

    return customer_no, customer_error, error_flag