from bs4 import BeautifulSoup
from datetime import datetime
from money_transfer.money_transfer.service.db import check_duplicate_payment, check_verification, save_status_req_db, save_verification_req_db, save_payment_req_db
from money_transfer.money_transfer.utils import console_print
from werkzeug.wrappers import Response
import money_transfer.money_transfer.service.const as const
def read_xml_verification(xml_string):
	bs_data = BeautifulSoup(xml_string, "xml")

	fp_header = bs_data.find('header:Fr').find('header:Id').text.strip() if bs_data.find('header:Fr') else ''
	bank_header_id = bs_data.find('header:To').find('header:Id').text.strip() if bs_data.find('header:To') else ''
	biz_msg_idr = bs_data.find('header:BizMsgIdr').text.strip() if bs_data.find('header:BizMsgIdr') else ''
	msg_def_idr = bs_data.find('header:MsgDefIdr').text.strip() if bs_data.find('header:MsgDefIdr') else ''
	req_bank_cre_dt = bs_data.find('header:CreDt').text.strip() if bs_data.find('header:CreDt') else ''

	bank_document_id = bs_data.find('document:Assgne').find('document:Id').text.strip() if bs_data.find('document:Assgne') else ''
	req_bank_id = bs_data.find('document:Assgnr').find('document:Id').text.strip() if bs_data.find('document:Assgnr') else ''
	req_bank_msg_id = bs_data.find('document:Vrfctn').find('document:Id', recursive=False).text.strip() if bs_data.find('document:Vrfctn') else ''
	party_type = bs_data.find('document:Prtry').text.strip() if bs_data.find('document:Prtry') else ''
	client_no = bs_data.find('document:PtyAndAcctId').find('document:Id').text.strip() if bs_data.find('document:PtyAndAcctId') else ''

	return fp_header, bank_header_id, bank_document_id, req_bank_id, req_bank_msg_id, biz_msg_idr, msg_def_idr, party_type, client_no, req_bank_cre_dt

def create_verification_res_xml(client_no, client_name, bank_header, req_bank_id, fp_header, bank_biz_msg_idr_serial, req_verification_biz_msg_idr, res_verification_biz_msg_idr, biz_msg_idr, req_bank_msg_id, req_prtry_type, reason_true_false, reason_msg, req_bank_creDt, customer_error, error_flg):
    today = datetime.today()
    start_date = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
    start_date_2 = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
    serial = today.strftime('%Y%m%d%H%M%S')

    doc_name = save_verification_req_db(client_no, bank_header, req_bank_id, bank_header + serial + bank_biz_msg_idr_serial, req_verification_biz_msg_idr, res_verification_biz_msg_idr, biz_msg_idr, req_bank_msg_id, req_prtry_type, reason_true_false, reason_msg, req_bank_creDt, start_date, customer_error, error_flg)

    if reason_msg == 'SUCC':
        with open("../apps/money_transfer/money_transfer/money_transfer/service/res_xml_files/Verification_RS.xml", "r") as f:
            xml_data = f.read()
            f.close()
        xml_args = {
            "header_fr": bank_header, "header_to": fp_header,"header_biz_msg": bank_header + serial + str(bank_biz_msg_idr_serial),
            "header_msg_def": res_verification_biz_msg_idr,"header_cre_dt":start_date ,
            "rltd_fr": fp_header,"rltd_to": bank_header,"rltd_biz_msg": biz_msg_idr,"rltd_msg_def": req_verification_biz_msg_idr,
            "rltd_cre_dt": req_bank_creDt,"document_msg_id": bank_header + serial + str(bank_biz_msg_idr_serial),
            "document_cre_dt_tm": start_date_2,"assgnr": bank_header,"assgne": req_bank_id,"orgnl_assgnmt": biz_msg_idr,
            "orgnl_assgnmt_cre_dt_tm": start_date_2,
            "orgnl_id": req_bank_msg_id,"vrfctn": reason_true_false,"rsn": reason_msg,
            "orgnl_acct_id": client_no, "orgnl_acct_prtry": req_prtry_type, "updtd_nm": client_name, "updtd_id": client_no, "updtd_prtry":req_prtry_type 
                }
    else:
        with open("../apps/money_transfer/money_transfer/money_transfer/service/res_xml_files/Verification_RS_fail.xml", "r") as f:
            xml_data = f.read()
            f.close()
        xml_args = {
            "header_fr": bank_header, "header_to": fp_header,"header_biz_msg": bank_header + serial + str(bank_biz_msg_idr_serial),
            "header_msg_def": res_verification_biz_msg_idr,"header_cre_dt":start_date ,
            "rltd_fr": fp_header,"rltd_to": bank_header,"rltd_biz_msg": biz_msg_idr,"rltd_msg_def": req_verification_biz_msg_idr,
            "rltd_cre_dt": req_bank_creDt,"document_msg_id": bank_header + serial + str(bank_biz_msg_idr_serial),
            "document_cre_dt_tm": start_date_2,"assgnr": bank_header,"assgne": req_bank_id,"orgnl_assgnmt": biz_msg_idr,
            "orgnl_assgnmt_cre_dt_tm": start_date_2,
            "orgnl_id": req_bank_msg_id,"vrfctn": reason_true_false,"rsn": reason_msg,
            "orgnl_acct_id": client_no, "orgnl_acct_prtry": req_prtry_type
            }
    
    xml_data = xml_data.format(**xml_args)    
    return xml_data, doc_name

def save_xml_prtfy(xml_path, xml_string):
  with open(xml_path, "w") as f:
    soup = BeautifulSoup(xml_string, "xml")
    f.write(soup.prettify())
    f.close()

def save_xml(xml_path, xml_string):
  with open(xml_path, "w") as f:
    f.write(xml_string)
    f.close()

def get_xml_response(xml_string):
	response = Response()
	response.mimetype = 'text/xml'
	response.charset = 'utf-8'
	response.data = xml_string
	return response

def read_xml_payment(xml_string):
    bs_data = BeautifulSoup(xml_string, "xml")

    header_from = bs_data.find('header:Fr').find('header:Id').text.strip() if bs_data.find('header:Fr') else ''
    header_to = bs_data.find('header:To').find('header:Id').text.strip() if bs_data.find('header:To') else ''
    req_bank_biz_msg_idr = bs_data.find('header:BizMsgIdr').text.strip() if bs_data.find('header:BizMsgIdr') else '' 
    req_bank_msg_def_idr = bs_data.find('header:MsgDefIdr').text.strip() if bs_data.find('header:MsgDefIdr') else ''
    req_bank_cre_dt = bs_data.find('header:CreDt').text.strip() if bs_data.find('header:CreDt') else ''

    req_bank_cre_dt_tm = bs_data.find('document:CreDtTm').text.strip() if bs_data.find('document:CreDtTm') else ''
    req_bank_sttlm_mtd = bs_data.find('document:SttlmMtd').text.strip() if bs_data.find('document:SttlmMtd') else ''
    req_bank_lcl_instrm = bs_data.find('document:LclInstrm').find('document:Prtry').text.strip() if bs_data.find('document:LclInstrm') else ''
    req_bank_id = bs_data.find('document:InstgAgt').find('document:Id').text.strip() if bs_data.find('document:InstgAgt') else ''
    req_bank_tx_id = bs_data.find('document:TxId').text.strip() if bs_data.find('document:TxId') else ''
    req_bank_intr_bk_sttlm_amt = bs_data.find('document:IntrBkSttlmAmt').text.strip() if bs_data.find('document:IntrBkSttlmAmt') else ''
    req_bank_intr_bk_sttlm_amt_ccy = bs_data.find('document:IntrBkSttlmAmt').get('Ccy').strip() if bs_data.find('document:IntrBkSttlmAmt') else ''
    req_bank_accptnc_dt_tm = bs_data.find('document:AccptncDtTm').text.strip() if bs_data.find('document:AccptncDtTm') else ''
    req_bank_chrg_br = bs_data.find('document:ChrgBr').text.strip() if bs_data.find('document:ChrgBr') else ''

    req_bank_dbtr_name = bs_data.find('document:Dbtr').find('document:Nm').text.strip() if bs_data.find('document:Dbtr') else ''
    req_bank_pstl_adr = bs_data.find('document:AdrLine').text.strip() if bs_data.find('document:AdrLine') else ''
    req_bank_dbtr_ctct_dtls = bs_data.find('document:CtctDtls').find('document:Othr').text.strip() if bs_data.find('document:CtctDtls') else ''

    req_bank_debit_prt = bs_data.find('document:DbtrAcct').find('document:Prtry').text.strip() if bs_data.find('document:DbtrAcct') else ''
    req_bank_dbtr_acct_issr = bs_data.find('document:DbtrAcct').find('document:Issr').text.strip() if bs_data.find('document:DbtrAcct') else ''   
    req_bank_debit_id = bs_data.find('document:DbtrAcct').find('document:Othr').find('document:Id').text.strip() if bs_data.find('document:DbtrAcct') else ''

    req_bank_dbtr_agt_issr = bs_data.find('document:DbtrAgt').find('document:Issr').text.strip() if bs_data.find('document:DbtrAgt') else ''
    req_bank_bldg_nb = bs_data.find('document:BldgNb').text.strip() if bs_data.find('document:BldgNb') else ''
    req_bank_brnch_id = bs_data.find('document:BrnchId').find('document:Nm').text.strip() if bs_data.find('document:BrnchId') else ''

    req_bank_cdtr_nm = bs_data.find('document:Cdtr').find('document:Nm').text.strip() if bs_data.find('document:Cdtr') else ''

    req_bank_prtry_id = bs_data.find('document:CdtrAcct').find('document:Prtry').text.strip() if bs_data.find('document:CdtrAcct') else ''
    req_bank_acct_id = bs_data.find('document:CdtrAcct').find('document:Othr').find('document:Id').text.strip() if bs_data.find('document:CdtrAcct') else ''

    req_bank_ustrd = bs_data.find('document:Ustrd').text.strip() if bs_data.find('document:Ustrd') else ''

    return header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, req_bank_id, req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, req_bank_debit_prt, req_bank_dbtr_acct_issr, req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd
    
    
def create_payment_res_xml(header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, req_bank_id,
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, req_bank_debit_prt, req_bank_dbtr_acct_issr, 
    req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd, our_biz_msg_idr_serial):
    today = datetime.today()
    start_date = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
    start_date_2 = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
    serial = today.strftime('%Y%m%d%H%M%S')

    tx_sts = "ACSC"
    result = check_duplicate_payment(req_bank_tx_id)
    if result == 1:
        tx_sts = "DTID"
    else:
        client_no, bic, dte, prtry, ver_status, ver_mess = " ", " ", " ", " ", " ", " "
        if req_bank_acct_id == "123":
            tx_sts = "NOVF"
        else:
            if req_bank_acct_id == "223547860":
                tx_sts = "TNFN"
            else:
                result, bic, client_no, prtry, dte, ver_status, ver_mess = check_verification(req_bank_tx_id)
                if result == 0:
                    tx_sts = "TNFN"
                else:
                    if ver_status == "false":
                        tx_sts = "MISS"
                    else:
                        if client_no != req_bank_acct_id:
                            tx_sts = "MISS"
                        else:
                            if prtry != "ACCT":
                                tx_sts = "MISS"
                            else:
                                if bic != req_bank_id:
                                    tx_sts = "MISS"

    doc_name = save_payment_req_db(req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, 
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_intr_bk_sttlm_amt_ccy,  req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls,  req_bank_acct_id, req_bank_prtry_id,  req_bank_dbtr_acct_issr,
    req_bank_bldg_nb, req_bank_dbtr_agt_issr, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_ustrd, req_bank_debit_id, req_bank_debit_prt,
    header_to, header_to + serial + our_biz_msg_idr_serial, const.RES_PAYMENT_BIZ_MSG_IDR, start_date, tx_sts)

    with open("../apps/money_transfer/money_transfer/money_transfer/service/res_xml_files/Payment_RS.xml", "r") as f:
            xml_data = f.read()
            f.close()

    xml_args = {
        "header_fr": header_to, "header_to": header_from, "header_biz_msg": header_to + serial + str(our_biz_msg_idr_serial),
         "header_msg_def": const.RES_PAYMENT_BIZ_MSG_IDR, "header_cre_dt": start_date,
        "rltd_fr": header_from, "rltd_to": header_to, "rltd_biz_msg": req_bank_biz_msg_idr , "rltd_msg_def": req_bank_msg_def_idr, "rltd_cre_dt": req_bank_cre_dt,
        "document_msg_id": header_to + serial + str(our_biz_msg_idr_serial), "document_cre_dt_tm": start_date_2, 
        "instg_agt": header_to, "instd_agt": req_bank_id, "orgnl_msg_id": req_bank_biz_msg_idr,
        "orgnl_msg_nm": req_bank_msg_def_idr, "orgnl_cre_dt_tm": req_bank_cre_dt_tm,
         "orgnl_end_to_end":  "-", "orgnl_tx_id":req_bank_tx_id , "tx_sts": tx_sts,
        "accptnc_dt_tm": req_bank_accptnc_dt_tm, "intr_bk_sttlm_amt_ccy": req_bank_intr_bk_sttlm_amt_ccy, "intr_bk_sttlm_amt": req_bank_intr_bk_sttlm_amt, "instd_amt_ccy": req_bank_intr_bk_sttlm_amt_ccy, "instd_amt": req_bank_intr_bk_sttlm_amt,
        "dbtr_nm": req_bank_dbtr_name, "adr_line": req_bank_pstl_adr, "dbtr_acct_id": req_bank_debit_id,
         "dbtr_acct_prtry": req_bank_debit_prt, "cdtr_acct_id": req_bank_acct_id,
        "cdtr_acct_prtry": req_bank_prtry_id
    }

    xml_data = xml_data.format(**xml_args)
    return xml_data, doc_name


def create_push_status_xml_doc(req_bank_biz_msg, res_bank_id, res_bank_biz_msg, req_bank_tx_id):
    today = datetime.today()
    start_date = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
    start_date_2 = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"

    with open("../apps/money_transfer/money_transfer/money_transfer/service/res_xml_files/PushStatus_RQ.xml", "r") as f:
        xml_data = f.read()
        f.close()
    
    xml_args = { 
        "header_fr": res_bank_id, "header_to": "FP", "header_biz_msg": res_bank_biz_msg, "header_msg_def": "pacs.028.001.02",
        "header_cre_dt": start_date, "document_msg_id": req_bank_biz_msg, "document_cre_dt_tm": start_date_2, "orgnl_tx_id": req_bank_tx_id}

    xml_data = xml_data.format(**xml_args)

    return xml_data

def read_push_status_xml(xml_string):
    bs_data = BeautifulSoup(xml_string, "xml")

    header_from = bs_data.find('header:AppHdr').find('header:Fr', recursive=False).find('header:Id').text.strip() if bs_data.find('header:AppHdr') else ''
    header_to = bs_data.find('header:AppHdr').find('header:To', recursive=False).find('header:Id').text.strip() if bs_data.find('header:AppHdr') else ''
    req_bank_biz_msg_idr = bs_data.find('header:AppHdr').find('header:BizMsgIdr', recursive=False).text.strip() if bs_data.find('header:AppHdr') else ''
    req_bank_msg_def_idr = bs_data.find('header:AppHdr').find('header:MsgDefIdr', recursive=False).text.strip() if bs_data.find('header:AppHdr') else ''
    req_bank_cre_dt = bs_data.find('header:AppHdr').find('header:MsgDefIdr', recursive=False).text.strip() if bs_data.find('header:AppHdr') else ''
    
    res_bank_biz_msg_idr = bs_data.find('header:Rltd').find('header:BizMsgIdr').text.strip() if bs_data.find('header:Rltd') else '' 
    res_bank_msg_def_idr = bs_data.find('header:Rltd').find('header:MsgDefIdr').text.strip() if bs_data.find('header:Rltd') else ''
    res_bank_cre_dt = bs_data.find('header:Rltd').find('header:CreDt').text.strip() if bs_data.find('header:Rltd') else ''

    req_bank_cre_dt_tm = bs_data.find('document:CreDtTm').text.strip() if bs_data.find('document:CreDtTm') else ''
    req_bank_msg_id = bs_data.find('document:MsgId').text.strip() if bs_data.find('document:MsgId') else ''

    req_bank_id = bs_data.find('document:InstdAgt').find('document:Id').text.strip() if bs_data.find('document:InstdAgt') else ''

    res_orgnl_msg_id = bs_data.find('document:OrgnlMsgId').text.strip() if bs_data.find('document:OrgnlMsgId') else ''
    res_orgnl_msg_nm_id = bs_data.find('document:OrgnlMsgNmId').text.strip() if bs_data.find('document:OrgnlMsgNmId') else ''
    res_orgnl_cre_dt_tm = bs_data.find('document:OrgnlCreDtTm').text.strip() if bs_data.find('document:OrgnlCreDtTm') else ''

    req_orgnl_tx_id = bs_data.find('document:OrgnlTxId').text.strip() if bs_data.find('document:OrgnlTxId') else ''
    req_tx_sts = bs_data.find('document:TxSts').text.strip() if bs_data.find('document:TxSts') else ''
    req_intr_bk_sttl_amt = bs_data.find('document:IntrBkSttlmAmt').text.strip() if bs_data.find('document:IntrBkSttlmAmt') else ''
    req_nm = bs_data.find('document:Nm').text.strip() if bs_data.find('document:Nm') else ''
    req_adr_line = bs_data.find('document:AdrLine').text.strip() if bs_data.find('document:AdrLine') else ''

    req_bank_client_id = bs_data.find('document:DbtrAcct').find('document:Othr').find('document:Id').text.strip() if bs_data.find('document:DbtrAcct') else ''
    req_bank_prtry_id = bs_data.find('document:DbtrAcct').find('document:Prtry').text.strip() if bs_data.find('document:DbtrAcct') else ''

    return (header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt,
            req_bank_cre_dt_tm, req_bank_msg_id, req_bank_id, res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_tx_sts, 
            req_intr_bk_sttl_amt, req_nm, req_adr_line, req_bank_client_id, req_bank_prtry_id)


def read_status_xml(xml_string):
    bs_data = BeautifulSoup(xml_string, "xml")
    header_from = bs_data.find('header:AppHdr').find('header:Fr', recursive=False).find('header:Id').text.strip() if bs_data.find('header:AppHdr') else ''
    header_to = bs_data.find('header:AppHdr').find('header:To', recursive=False).find('header:Id').text.strip() if bs_data.find('header:AppHdr') else ''
    req_bank_biz_msg_idr = bs_data.find('header:AppHdr').find('header:BizMsgIdr', recursive=False).text.strip() if bs_data.find('header:AppHdr') else ''
    req_bank_msg_def_idr = bs_data.find('header:AppHdr').find('header:MsgDefIdr', recursive=False).text.strip() if bs_data.find('header:AppHdr') else ''
    req_bank_cre_dt = bs_data.find('header:AppHdr').find('header:MsgDefIdr', recursive=False).text.strip() if bs_data.find('header:AppHdr') else ''
    
    res_bank_biz_msg_idr = bs_data.find('header:Rltd').find('header:BizMsgIdr').text.strip() if bs_data.find('header:Rltd') else '' 
    res_bank_msg_def_idr = bs_data.find('header:Rltd').find('header:MsgDefIdr').text.strip() if bs_data.find('header:Rltd') else ''
    res_bank_cre_dt = bs_data.find('header:Rltd').find('header:CreDt').text.strip() if bs_data.find('header:Rltd') else ''

    req_bank_msg_id = bs_data.find('document:MsgId').text.strip() if bs_data.find('document:MsgId') else ''
    req_bank_cre_dt_tm = bs_data.find('document:CreDtTm').text.strip() if bs_data.find('document:CreDtTm') else ''

    res_orgnl_msg_id = bs_data.find('document:OrgnlMsgId').text.strip() if bs_data.find('document:OrgnlMsgId') else ''
    res_orgnl_msg_nm_id = bs_data.find('document:OrgnlMsgNmId').text.strip() if bs_data.find('document:OrgnlMsgNmId') else ''
    res_orgnl_cre_dt_tm = bs_data.find('document:OrgnlCreDtTm').text.strip() if bs_data.find('document:OrgnlCreDtTm') else ''

    req_orgnl_tx_id = bs_data.find('document:OrgnlTxId').text.strip() if bs_data.find('document:OrgnlTxId') else ''
    req_accptnc_dt_tm = bs_data.find('document:AccptncDtTm').text.strip() if bs_data.find('document:AccptncDtTm') else ''
    req_tx_sts = bs_data.find('document:TxSts').text.strip() if bs_data.find('document:TxSts') else ''
    req_intr_bk_sttl_amt = bs_data.find('document:IntrBkSttlmAmt').text.strip() if bs_data.find('document:IntrBkSttlmAmt') else ''
    req_intr_bk_sttl_amt_ccy = bs_data.find('document:IntrBkSttlmAmt').get('Ccy').strip() if bs_data.find('document:IntrBkSttlmAmt') else ''

    req_nm = bs_data.find('document:Nm').text.strip() if bs_data.find('document:Nm') else ''
    req_adr_line = bs_data.find('document:AdrLine').text.strip() if bs_data.find('document:AdrLine') else ''

    req_bank_client_id = bs_data.find('document:CdtrAcct').find('document:Othr').find('document:Id').text.strip() if bs_data.find('document:DbtrAcct') else ''
    req_bank_prtry_id = bs_data.find('document:CdtrAcct').find('document:Prtry').text.strip() if bs_data.find('document:DbtrAcct') else ''

    req_bank_id = bs_data.find('document:InstdAgt').find('document:Id').text.strip() if bs_data.find('document:InstdAgt') else ''

    return (header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt,
            req_bank_cre_dt_tm, req_bank_msg_id, req_bank_id, res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_tx_sts, 
            req_intr_bk_sttl_amt, req_intr_bk_sttl_amt_ccy, req_nm, req_adr_line, req_bank_client_id, req_bank_prtry_id, req_accptnc_dt_tm)


def create_status_res_xml(our_biz_msg_idr_serial, header_form, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm, 
res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, req_tx_sts, req_sts_flg, req_intr_bk_sttlm_amt, req_intr_bk_sttl_amt_ccy,
req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id, req_bank_debit_id, req_bank_debit_prt):
    today = datetime.today()
    start_date = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
    start_date_2 = today.strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
    serial = today.strftime('%Y%m%d%H%M%S')

    doc_name = save_status_req_db(header_form, header_to, req_bank_id, req_bank_biz_msg_idr, req_bank_msg_def_idr, 
req_bank_cre_dt, res_bank_biz_msg_idr, res_bank_msg_def_idr, res_bank_cre_dt, req_bank_msg_id, req_bank_cre_dt_tm, req_bank_accptnc_dt_tm, 
res_orgnl_msg_id, res_orgnl_msg_nm_id, res_orgnl_cre_dt_tm, req_orgnl_tx_id, req_accptnc_dt_tm, req_tx_sts, req_sts_flg, req_intr_bk_sttlm_amt, req_intr_bk_sttl_amt_ccy,
req_adr_line, req_nm, req_bank_client_id, req_bank_prtry_id)

    with open("../apps/money_transfer/money_transfer/money_transfer/service/res_xml_files/Status_RS.xml", "r") as f:
        xml_data = f.read()
        f.close()
    xml_args = {
        "header_fr": header_to, "header_to": header_form, "header_biz_msg": header_to + serial + our_biz_msg_idr_serial, 
        "header_msg_def": "pacs.002.001.05", "header_cre_dt": start_date, "rltd_fr": header_form, "rltd_to": header_to,
        "rltd_biz_msg": req_bank_biz_msg_idr, "rltd_msg_def":" pacs.002.001.05", "rltd_cre_dt": req_bank_cre_dt, 
        "document_msg_id": header_to + serial+ our_biz_msg_idr_serial, "document_cre_dt_tm": start_date_2, "instg_agt": header_to, "instd_agt": req_bank_id, "orgnl_msg_id": req_bank_msg_id,
        "orgnl_msg_nm_id": "pacs.002.001.05", "ognl_cre_dt_tm": start_date_2, "orgnl_end_to_end_id": "-", "orgnl_tx_id": req_orgnl_tx_id, 
        "tx_sts": req_tx_sts, "accptnc_dt_tm": start_date_2, "intr_bk_sttlm_amt_ccy": req_intr_bk_sttl_amt_ccy, 
        "intr_bk_sttlm_amt": req_intr_bk_sttlm_amt, "instd_amt_ccy": req_intr_bk_sttl_amt_ccy, "instd_amt": req_intr_bk_sttlm_amt, "dbtr_nm": req_nm, 
        "adr_line": req_adr_line, "dbtr_acct_id": req_bank_debit_id, "dbtr_acct_prtry": req_bank_debit_prt, "cdtr_acct": req_bank_client_id, "cdtr_prtry": req_bank_prtry_id
    }

    xml_data = xml_data.format(**xml_args)

    return xml_data, doc_name