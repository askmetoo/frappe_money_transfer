import os
from frappe.utils import get_site_name
import datetime

def get_total_amount(amount=0, rcv_fee=0, swift_fee=0, snd_fee=0):
	total_amount = float(amount) + float(rcv_fee) + float(swift_fee) + float(snd_fee)
	total_amount_int = int(total_amount * 1000) 
	return str("{:016d}".format(total_amount_int))

def mkdir(pathList):
  for path in pathList:
    paths = path.split('/')

    #for p in paths:
    nPaths = []
    for i in range(len(paths)):
      if i == 0:
        nPaths.append(paths[i])
      else:
        nPaths.append(nPaths[i - 1] + '/' + paths[i])
      if not os.path.exists(nPaths[i]):
        os.mkdir(nPaths[i])

def console_print(stm):
  print("*" * 100)
  print(stm)
  print("*" * 100)

def get_current_site_name():
  return 'yibbank.com'
  #return 'islah.erp'
  #return get_site_name(frappe.local.request.host)


def num2str(num):
	num_int = int(float(num) * 1000)
	return str("{:016d}".format(num_int))

def float2str(num):
	return "{0:.2f}".format(float(num))

def validate_expiration(creation_date: datetime.datetime, expiration_seconds: float):
  now = datetime.datetime.now()
  delta = now - creation_date
  expired = delta.total_seconds() > expiration_seconds
  return expired