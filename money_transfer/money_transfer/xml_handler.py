import frappe
from datetime import datetime
from xml.dom import minidom
from collections import OrderedDict
from bs4 import BeautifulSoup
from money_transfer.money_transfer.db import get_payment_data, get_status_data
from xml.etree import ElementTree as et

from money_transfer.money_transfer.utils import console_print, float2str

def getXmlElement(root, element, attributeNames=[], attributes=[]):
    elementChild = root.createElement(element)
    for name, attribute in zip(attributeNames, attributes):
        elementChild.setAttribute(name, attribute)
    return elementChild

def dicttoxml(obj, root=None, parentNode = None):
  if parentNode is None:
    root = minidom.Document()
  xml_str = ''
  for key, value in obj.items():
    if type(value) == dict or type(value) == OrderedDict:
      if 'attr_names' in value.keys():
        if 'node_value' in value.keys():
          node = getXmlElement(root, key, value['attr_names'], value['attr_values'])
          node.appendChild(root.createTextNode(str(value['node_value'])))
          parentNode.appendChild(node)
          continue
        else:
          node = getXmlElement(root, key, value['attr_names'], value['attr_values'])
      else:
        node = getXmlElement(root, key)
      node, _ = dicttoxml(value, root, node)
      if parentNode is not None:
        parentNode.appendChild(node)
    elif type(value) != list:
      node = getXmlElement(root, key)
      node.appendChild(root.createTextNode(str(value)))
      parentNode.appendChild(node)
  if parentNode is None:
    root.appendChild(node)
    xml_str = root.toprettyxml(encoding='utf-8',indent ="\t").decode('utf-8')
  return parentNode, xml_str


# Bill Verification Xml Document
def create_bv_xml_doc(save_path_file, req_bank_id, dis_bank_id, fp_header_name, acmt_req, verification_serial, beneficiary_no, account_type):
  cre_dt_serial = datetime.today().strftime('%Y%m%d%H%M%S')
  cre_dt = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
  cre_dt_tm = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"

  with open("../apps/money_transfer/money_transfer/money_transfer/req_xml_files/Verification_RQ.xml", "r") as f:
    xml_data = f.read()
    f.close()

  header_biz_msg = req_bank_id + cre_dt_serial + verification_serial
  xml_args = {
  "header_fr": req_bank_id, "header_to": fp_header_name, "header_biz_msg": header_biz_msg, "header_msg_def": acmt_req, "heder_cre_dt":cre_dt,
  "document_msg_id": header_biz_msg, "document_cre_dt_tm": cre_dt_tm, "assgnr_id": req_bank_id, "assgne_id": dis_bank_id, "vrfctn_id": "ID",
  "acct_id": beneficiary_no, "acct_prtry": account_type
  }
  xml_data = xml_data.format(**xml_args)

  with open(save_path_file, "w") as f:
    f.write(xml_data)
    f.close()

  return xml_data,  header_biz_msg

def read_xml_verification_data(xml):
	Bs_data = BeautifulSoup(xml, "xml")
	pv_Vrfctn = Bs_data.find('document:Vrfctn').text if Bs_data.find('document:Vrfctn') else ''
	pv_Rsn = Bs_data.find('document:Rsn').find('document:Prtry').text if  Bs_data.find('document:Rsn') else ''
	pv_Nm = Bs_data.find('document:Nm').text if Bs_data.find('document:Nm') else ''
	pv_FPVrfctn = Bs_data.find('document:OrgnlId').text if Bs_data.find('document:OrgnlId') else ''

	return pv_Vrfctn, pv_Rsn, pv_Nm, pv_FPVrfctn


# Bill Verification Xml Document
def create_fees_xml_doc(save_path_file, req_bank_id, fees_password, amount, dest_bank_id, unique_code, zone, currency_code, fp_verification_id):
  with open("../apps/money_transfer/money_transfer/money_transfer/req_xml_files/Fees_RQ.xml", "r") as f:
    xml_data = f.read()
    f.close()
  if not amount:
    amount = 0
  xml_args = {
    "user_id": req_bank_id, "user_pass": fees_password, "amount": float2str(amount), "dest_bank": dest_bank_id, 
    "from_zone": unique_code, "to_zone": zone, "currency": currency_code, "trans_id": fp_verification_id}
  xml_data = xml_data.format(**xml_args)

  with open(save_path_file, "w") as f:
    f.write(xml_data)
    f.close()

  return xml_data

# Push payment xml document
def create_pp_xml_doc(save_path_file, payment_method, client_no, client_serial, our_client_name, our_client_address, our_bank, our_branch, region_code,
dest_bank, fp_verification_id, amount, currency, beneficiary_name, beneficiary_no, account_type, op_type, card_no='', card_type='', sender_name='', sender_region=''):
  (our_bank_id, dest_bank_id, our_branch_code, our_branch_name, fp_region_code, currency_code, 
  currency_system_code, fp_header_name, pacs_req, acc_type, payment_serial, username, currency_prefix, sender_address, sender_region_code) = get_payment_data(our_bank, dest_bank, our_branch, region_code, currency, account_type, sender_region)
  cre_dt_serial = datetime.today().strftime('%Y%m%d%H%M%S')
  cre_dt = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
  cre_dt_tm = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"

  if int(payment_method) == 1 or int(payment_method) == 2:
    cli_name = '#'
    cli_id_no = '#'
    cli_id_type = '#'
  else:
    cli_name = sender_name
    our_client_name = sender_name
    our_client_address = sender_address
    fp_region_code = sender_region_code
    cli_id_no = card_no
    cli_id_type = card_type
    client_no = '00001'

  with open("../apps/money_transfer/money_transfer/money_transfer/req_xml_files/Payment_RQ.xml", "r") as f:
    xml_data = f.read()
    f.close()
  biz_msg = our_bank_id + cre_dt_serial + payment_serial
  dbtr_acct_id = our_branch_code + str(client_no) + str(client_serial) + str(currency_system_code)
  xml_args = {
    "header_fr": str(our_bank_id), "header_to": str(fp_header_name), "header_biz_msg": biz_msg, "header_msg_def":str(pacs_req),
    "header_cre_dt": cre_dt, "document_msg_id": biz_msg, "document_cre_dt_tm":cre_dt_tm , "nb_of_txs": "1", "sttlm_mtd": "CLRG", 
    "clr_sys": fp_header_name, "lcl_instrm_prtry": "C2C", "instg_agt_id":  str(our_bank_id), "instd_agt_id": str(dest_bank_id), 
    "end_to_end_id": "-", "tx_id": str(fp_verification_id), "intr_bksttlm_amt_ccy": str(currency_code), "intr_bksttlm_amt": float2str(amount), 
    "accptnc_dt_tm": cre_dt_tm, "instd_amt_ccy": str(currency_code), "instd_amt": float2str(amount), "chrg_br": "SLEV", "ultmt_dbtr_nm": cli_name, 
    "ultmt_dbtr_id": str(cli_id_no), "ultmt_dbtr_prtry": str(cli_id_type), "dbtr_nm": our_client_name.strip(), "dbtr_adr_line": our_client_address + '#' + our_branch_name, 
    "dbtr_othr": fp_region_code, "dbtr_acct_id": dbtr_acct_id, "dbtr_acct_prtry": str(acc_type),"dbtr_acct_issr": "C", 
    "dbtr_agt_bldg_nb": "01", "dbtr_agt_id": our_bank_id, "dbtr_agt_issr": "TELER-" + username, "dbtr_agt_nm": our_branch_code, 
    "cdtr_agt_id": str(dest_bank_id), "cdtr_nm": beneficiary_name.strip(), "cdtr_acct_id": currency_prefix + str(beneficiary_no), "cdtr_prtry": str(acc_type), "ustrd": str(op_type)}

  xml_data = xml_data.format(**xml_args)

  with open(save_path_file, "w") as f:
    f.write(xml_data)
    f.close()

  return xml_data


def create_status_xml_doc(save_path_file, our_bank, fp_verification_id):
  req_bank, fp_header_name, status_serial = get_status_data(our_bank)

  cre_dt_serial = datetime.today().strftime('%Y%m%d%H%M%S')
  cre_dt = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
  cre_dt_tm = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
  
  with open("../apps/money_transfer/money_transfer/money_transfer/req_xml_files/BillStatus_RQ.xml", "r") as f:
    xml_data = f.read()
    f.close()
  biz_msg = req_bank + cre_dt_serial + str(status_serial)
  xml_args = {"header_fr": req_bank, "header_to": fp_header_name, "header_biz_msg": biz_msg, "header_def_idr": "pacs.028.001.02", 
  "header_cre_dt":cre_dt, "document_msg_id": biz_msg, "document_cre_dt_tm": cre_dt_tm, "orgnl_tx_id": fp_verification_id}

  xml_data = xml_data.format(**xml_args)

  with open(save_path_file, "w") as f:
    f.write(xml_data)
    f.close()

  return xml_data

def read_xml_payment_data(xml_data):
	bs_data = BeautifulSoup(xml_data, "xml")
	result = bs_data.find('document:TxSts').text if bs_data.find('document:TxSts') else ''
	return result

def read_xml_fees_data(xml_string):
	xml_data = et.fromstring(xml_string)
	elements ={elem.tag:elem.text for elem in xml_data.iter()}
	retail =  elements['Retail'] if 'Retail' in elements.keys() else ''
	switch =  elements['Switch'] if 'Switch' in elements.keys() else ''
	interchange =  elements['interchange'] if 'interchange' in elements.keys() else ''
	result =  elements['Result'] if 'Result' in elements.keys() else ''
	transactionid =  elements['TransactionId'] if 'TransactionId' in elements.keys() else ''
	errordesc =  elements['ErrorDesc'] if 'ErrorDesc' in elements.keys() else ''

	return retail, switch, interchange, result, transactionid, errordesc