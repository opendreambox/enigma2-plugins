#!/usr/bin/python
import sys
import os
import string
from xml.sax import make_parser
from xml.sax.handler import ContentHandler, property_lexical_handler
try:
	from _xmlplus.sax.saxlib import LexicalHandler
	no_comments = False
except ImportError:
	class LexicalHandler:
		pass
	no_comments = True

class parseXML(ContentHandler, LexicalHandler):
	def __init__(self, attrlist,file):
		self.isPointsElement, self.isReboundsElement = 0, 0
		self.currentFile = file
		self.attrlist = attrlist
		self.last_comment = None
		self.elements = []
		self.data = ""
		self.attributes = {}

	def comment(self, comment):
		if comment.find("TRANSLATORS:") != -1:
			self.last_comment = comment

	def startElement(self, name, attrs):
		#print "startElement", name
		self.elements.append(name)
		if name in ( "shortdescription", "description" ):
			self.data = ""

	def endElement(self, name):
		#print "endElement", name
		#print "self.elements:", self.elements
		self.elements.pop()

		if len(self.attributes) == 2:
			attrlist.add((self.attributes["shortdescription"], self.last_comment,self.currentFile))
			attrlist.add((self.attributes["description"], self.last_comment,self.currentFile))
			self.attributes = {}

	def characters(self, data):
		if self.elements[-1] == "shortdescription":
			self.attributes["shortdescription"] = str(data)
		if self.elements[-1] == "description":
			self.data += data.strip()
			self.attributes["description"] = str(self.data)


parser = make_parser()

attrlist = set()

if not no_comments:
	parser.setProperty(property_lexical_handler, contentHandler)

for arg in sys.argv[1:]:
	if os.path.isdir(arg):
		for file in os.listdir(arg):
			if (file.endswith(".xml")):
				contentHandler = parseXML(attrlist,file)
				parser.setContentHandler(contentHandler)
				parser.parse(os.path.join(arg, file))
	elif (arg.endswith(".xml")):
		contentHandler = parseXML(attrlist,arg)
		parser.setContentHandler(contentHandler)
		parser.parse(arg)

	attrlist = list(attrlist)
	attrlist.sort(key=lambda a: a[2])

	for (k,c,f) in attrlist:
		print
		print '#: ' + arg + f
		string.replace(k, "\\n", "\"\n\"")
		if c:
			for l in c.split('\n'):
				print "#. ", l
		if str(k).strip() != "":
			print 'msgid "' + str(k) + '"'
			print 'msgstr ""'

	attrlist = set()
