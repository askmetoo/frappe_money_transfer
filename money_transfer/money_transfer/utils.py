from xml.dom import minidom
from collections import OrderedDict
import os
import socket
import frappe
from frappe.utils import get_site_name

def make_socket_connection(ip, port, msg):
  error_msg = ''
  data = b''
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
      s.connect((ip, int(port)))
      s.sendall(msg)
      data = s.recv(2052)
      s.shutdown(socket.SHUT_RDWR)
    except socket.error:
      error_msg = 'Admin_ServerConnectionError'
    finally:
      s.close()
  return data, error_msg

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
  #return get_site_name(frappe.local.request.host)