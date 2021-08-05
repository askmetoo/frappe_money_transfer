from bs4 import BeautifulSoup
from datetime import datetime
from money_transfer.money_transfer.service.db import check_duplicate_payment, check_verification, save_verification_req_db, save_payment_req_db
from werkzeug.wrappers import Response
from money_transfer.money_transfer.xml_handler import dicttoxml
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
    start_date = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
    start_date_2 = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
    serial = datetime.today().strftime('%Y%m%d%H%M%S')
    doc_name = save_verification_req_db(client_no, bank_header, req_bank_id, bank_header + serial + bank_biz_msg_idr_serial, req_verification_biz_msg_idr, res_verification_biz_msg_idr, biz_msg_idr, req_bank_msg_id, req_prtry_type, reason_true_false, reason_msg, req_bank_creDt, start_date, customer_error, error_flg)
    header = "urn:iso:std:iso:20022:tech:xsd:head.001.001.01"
    document = "urn:iso:std:iso:20022:tech:xsd:acmt.024.001.02"
    fp_xml = "urn:iso:std:iso:20022:tech:xsd:verification_response"
    xml_obj = {
        "FPEnvelope":{
			"attr_names": ["xmlns","xmlns:document","xmlns:header"],
			"attr_values": [fp_xml, document, header],
			"header:AppHdr": {
				"header:Fr":{
					"header:FIId":{
						"header:FinInstnId":{
							"header:Othr":{
								"header:Id": bank_header
							}
						}
					}
				},
				"header:To": {
					"header:FIId": {
						"header:FinInstnId": {
							"header:Othr": {
								"header:Id": fp_header
							}
						}
					}
				},
				"header:BizMsgIdr": bank_header + serial + str(bank_biz_msg_idr_serial),
				"header:MsgDefIdr": res_verification_biz_msg_idr,
				"header:CreDt": start_date,
                "header:Rltd": {
                    "header:Fr":{
                        "header:FIId":{
                            "header:FinInstnId":{
                               "header:Othr":{
                                   "header:Id": fp_header
                               } 
                            }
                        }
                    },
                    "header:To":{
                        "header:FIId":{
                            "header:FinInstnId":{
                                "header:Othr":{
                                    "header:Id": bank_header
                                }
                            }
                        }
                    },
                    "header:BizMsgIdr": biz_msg_idr,
                    "header:MsgDefIdr": req_verification_biz_msg_idr,
                    "header:CreDt": req_bank_creDt
                }
			},
            "document:Document":{
                "document:IdVrfctnRpt":{
                    "document:Assgnmt":{
                        "document:MsgId": bank_header + serial + str(bank_biz_msg_idr_serial),
                        "document:CreDtTm": start_date_2,
                        "document:Assgnr":{
                            "document:Agt":{
                                "document:FinInstnId":{
                                    "document:Othr":{
                                        "document:Id": bank_header
                                    }
                                }
                            }
                        },
                        "document:Assgne":{
                            "document:Agt":{
                                "document:FinInstnId":{
                                    "document:Othr":{
                                        "document:Id": req_bank_id
                                    }
                                }
                            }
                        }
                    },
                    "document:OrgnlAssgnmt":{
                        "document:MsgId": biz_msg_idr,
                        "document:CreDtTm": start_date_2
                    },
                    "document:Rpt": {
                        "document:OrgnlId": req_bank_msg_id,
                        "document:Vrfctn": reason_true_false,
                        "document:Rsn":{
                            "document:Prtry": reason_msg
                        },
                        "document:OrgnlPtyAndAcctId":{
                            "document:Acct":{
                                "document:Othr":{
                                    "document:Id": client_no,
                                    "document:SchmeNm": {
                                        "document:Prtry": req_prtry_type
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    acct_id_obj = {
            "document:Pty":{
                "document:Nm": client_name
            },
           "document:Acct":{
               "document:Othr":{
                   "document:Id": client_no,
                   "document:SchmeNm":{
                       "document:Prtry": req_prtry_type
                   }
               }
           } 
    }
    if reason_msg == 'SUCC':
        xml_obj["FPEnvelope"]["document:Document"]["document:IdVrfctnRpt"]["document:Rpt"]["document:UpdtdPtyAndAcctId"] = acct_id_obj
        
    i, xml_string = dicttoxml(xml_obj)
    return xml_string, doc_name

def save_xml(xml_path, xml_string):
  with open(xml_path, "w") as f:
    soup = BeautifulSoup(xml_string, "xml")
    f.write(soup.prettify())
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

    return header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, req_bank_id, req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, req_bank_debit_prt, req_bank_dbtr_acct_issr, req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd
    
    
def create_payment_res_xml(header_from, header_to, req_bank_biz_msg_idr, req_bank_msg_def_idr, req_bank_cre_dt, req_bank_cre_dt_tm, req_bank_sttlm_mtd, req_bank_lcl_instrm, req_bank_id,
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt, req_bank_accptnc_dt_tm, req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls, req_bank_debit_prt, req_bank_dbtr_acct_issr, 
    req_bank_debit_id, req_bank_dbtr_agt_issr, req_bank_bldg_nb, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_prtry_id, req_bank_acct_id, req_bank_ustrd, our_biz_msg_idr_serial):

    start_date = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + 'Z'
    start_date_2 = datetime.today().strftime('%Y-%m-%dT%H:%M:%S.%f')[:23] + "+03:00"
    serial = datetime.today().strftime('%Y%m%d%H%M%S')

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
	req_bank_tx_id, req_bank_intr_bk_sttlm_amt,  req_bank_chrg_br, req_bank_dbtr_name, req_bank_pstl_adr, req_bank_dbtr_ctct_dtls,  req_bank_acct_id, req_bank_prtry_id,  req_bank_dbtr_acct_issr,
    req_bank_bldg_nb, req_bank_dbtr_agt_issr, req_bank_brnch_id, req_bank_cdtr_nm, req_bank_ustrd, req_bank_debit_id, req_bank_debit_prt,
    header_to, header_to + serial + our_biz_msg_idr_serial, const.RES_PAYMENT_BIZ_MSG_IDR, start_date, tx_sts)

    header = "urn:iso:std:iso:20022:tech:xsd:head.001.001.01"
    document = "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.05"
    fp_xml = "urn:iso:std:iso:20022:tech:xsd:payment_response"

    xml_obj = {
        "FPEnvelope":{
			"attr_names": ["xmlns","xmlns:document","xmlns:header"],
			"attr_values": [fp_xml, document, header],
			"header:AppHdr": {
				"header:Fr":{
					"header:FIId":{
						"header:FinInstnId":{
							"header:Othr":{
								"header:Id": header_to
							}
						}
					}
				},
				"header:To": {
					"header:FIId": {
						"header:FinInstnId": {
							"header:Othr": {
								"header:Id": header_from
							}
						}
					}
				},
				"header:BizMsgIdr": header_to + serial + str(our_biz_msg_idr_serial),
				"header:MsgDefIdr": const.RES_PAYMENT_BIZ_MSG_IDR,
				"header:CreDt": start_date,
                "header:Rltd": {
                    "header:Fr":{
                        "header:FIId":{
                            "header:FinInstnId":{
                               "header:Othr":{
                                   "header:Id": header_from
                               } 
                            }
                        }
                    },
                    "header:To":{
                        "header:FIId":{
                            "header:FinInstnId":{
                                "header:Othr":{
                                    "header:Id": header_to
                                }
                            }
                        }
                    },
                    "header:BizMsgIdr": req_bank_biz_msg_idr,
                    "header:MsgDefIdr": req_bank_msg_def_idr,
                    "header:CreDt": req_bank_cre_dt
                }
			},
            "document:Document":{
                "document:FIToFIPmtStsRpt":{
                    "document:GrpHdr": {
                        "document:MsgId": header_to + serial + our_biz_msg_idr_serial,
                        "document:CreDtTm": start_date_2,
                        "document:InstgAgt":{
                            "document:FinInstnId":{
                                "document:Othr":{
                                    "document:Id": header_to
                                }
                            }
                        },
                        "document:InstdAgt":{
                            "document:FinInstnId":{
                                "document:Othr":{
                                    "document:Id": req_bank_id
                                }
                            }
                        }
                    },
                    "document:OrgnlGrpInfAndSts":{
                        "document:OrgnlMsgId": req_bank_biz_msg_idr,
                        "document:OrgnlMsgNmId": req_bank_msg_def_idr,
                        "document:OrgnlCreDtTm": req_bank_cre_dt_tm,
                    },
                    "document:TxInfAndSts":{
                        "document:OrgnlEndToEndId": "-",
                        "document:OrgnlTxId": req_bank_tx_id,
                        "document:TxSts": tx_sts,
                        "document:AccptncDtTm": req_bank_accptnc_dt_tm,
                        "document:OrgnlTxRef":{
                            "document:IntrBkSttlmAmt":{
                            "attr_names": ["Ccy"],
							"attr_values": ["YER"],
							'node_value': req_bank_intr_bk_sttlm_amt
                            },
                            "document:Amt":{
                                "document:InstdAmt":{
                                    "attr_names": ["Ccy"],
                                    "attr_values": ["YER"],
                                    'node_value': req_bank_intr_bk_sttlm_amt
                                }
                            },
                            "document:Dbtr":{
                                "document:Nm": req_bank_dbtr_name,
                                "ocument:PstlAdr":{
                                    "document:AdrLine": req_bank_pstl_adr
                                }
                            },
                            "document:DbtrAcct":{
                                "document:Id":{
                                    "document:Othr":{
                                        "document:Id": req_bank_debit_id,
                                        "document:SchmeNm":{
                                            "document:Prtry": req_bank_debit_prt
                                        }
                                    }
                                }
                            },
                            "document:CdtrAcct":{
                                "document:Id":{
                                    "document:Othr":{
                                        "document:Id": req_bank_acct_id,
                                        "document:SchmeNm":{
                                            "document:Prtry": req_bank_prtry_id
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    i, xml_string = dicttoxml(xml_obj)
    return xml_string, doc_name