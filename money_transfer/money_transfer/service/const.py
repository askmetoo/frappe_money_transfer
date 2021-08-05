BANK_HEADER_NAME = "YIB-B"
FP_HEADER = 'FP'
REQ_VERIFICATION_BIZ_MSG_IDR = 'acmt.023.001.02'
RES_VERIFICATION_BIZ_MSG_IDR = 'acmt.024.001.02'

REQ_PAYMENT_BIZ_MSG_IDR = 'pacs.008.001.04'
RES_PAYMENT_BIZ_MSG_IDR = 'pacs.002.001.05'

 # success reason msg
REQ_SUCCESS = "SUCC"
# failed reason msg
USER_NOT_FOUND = "UNFN" #UserID was not found in the payee’s bank 
USER_BLOCKED = "BLCK" # The given UserID is blocked in the payee’s bank and cannot be used in transactions 
MISSING = "MISS" # SVIP did not receive a response from the payee’s bank 
NOT_PERFORMED = "NOVF" # SVIP failed to send a request to the payee’s bank 
TECHNICAL_ERROR = "ERRR" # Technical error (for example, invalid XSD) 
WRONG_BIC = "WBIC" # Bank BIC was not found in SVIP  