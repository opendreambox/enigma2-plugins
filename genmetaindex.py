# usage: genmetaindex.py <xml-files>  > index.xml
import sys, os
from xml.etree.ElementTree import ElementTree, Element

root = Element("index")

for file in sys.argv[1:]:
	p = ElementTree()
	p.parse(file)
	
	package = Element("package")
	package.set("details", os.path.basename(file))
	
	# we need all prerequisites
	prerequisites = p.find("prerequisites")
	if prerequisites is None:
		continue
	package.append(prerequisites)
	
	# we need some of the info, but not all
	info = p.find("info")
	if info is None:
		continue
	
	for i in info:
		if i.tag in ("name", "packagename", "packagetype", "shortdescription"):
			package.set(i.tag, i.text)

	root.append(package)

def indent(elem, level=0):
	i = "\n" + level*"\t"
	if elem != None and len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "\t"
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

indent(root)

ElementTree(root).write(sys.stdout)
