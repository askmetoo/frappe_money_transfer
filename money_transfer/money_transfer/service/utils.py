from money_transfer.money_transfer.utils import mkdir, get_current_site_name
from money_transfer.money_transfer.db import get_table_serial_key
from datetime import datetime
import threading

def background(f):
    '''
    a threading decorator
    use @background above the function you want to run in the background
    '''
    def backgrnd_func(*a, **kw):
        threading.Thread(target=f, args=a, kwargs=kw).start()
    return backgrnd_func

def get_service_files_names(operation, file_serial):
	site_name = get_current_site_name()
	date = datetime.now()
	public_path = '/public/files/' 
	private_path = '/private/files/XMLOut/'
	req_path = operation + '/REQ/' + str(date.year) + '_' + str(date.month)
	res_path = operation +'/RES/' + str(date.year) + '_' + str(date.month)
	file_serial_req = get_table_serial_key(file_serial + '_RQ')
	file_serial_res = get_table_serial_key(file_serial + '_RS')

	req_file_name = operation + '_RQ_' + str(date.year) + str(date.month) + str(date.day) + '_' + file_serial_req + '.xml'
	res_file_name = operation + '_RS_' + str(date.year) + str(date.month) + str(date.day) + '_' + file_serial_res + '.xml'

	req_xml_path = site_name + public_path + req_file_name
	res_xml_path = site_name + public_path + res_file_name
	private_req_path = site_name + private_path + req_path
	private_res_path = site_name + private_path + res_path 

	mkdir([ private_req_path, private_res_path])
	return req_file_name, res_file_name, req_xml_path, res_xml_path, site_name , private_path , req_path, res_path