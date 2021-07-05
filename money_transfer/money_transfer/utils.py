from xml.dom import minidom
from collections import OrderedDict
import os

def getSocket():
    pass

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
        node = getXmlElement(root, key, value['attr_names'], value['attr_values'])
      else:
        node = getXmlElement(root, key)
      node, _ = dicttoxml(value, root, node)
      if parentNode is not None:
        parentNode.appendChild(node)
    elif type(value) != list:
      node = getXmlElement(root, key)
      node.appendChild(root.createTextNode(value))
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