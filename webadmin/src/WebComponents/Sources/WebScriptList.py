# -*- coding: utf-8 -*-
from Components.Sources.Source import Source
from glob import glob
from os.path import basename


class WebScriptList(Source):
	LIST = 0

	def __init__(self, session, func=LIST, wap=False):
		Source.__init__(self)
		self.func = func
		self.wap = wap
		self.session = session
		self.res = (False, "Missing or Wrong Argument")

	def handleCommand(self, cmd):
		pass

	def getList(self):
		scripts = []
		for filename in sorted(glob('/usr/script/*.sh')):
			print "[WebScriptList] filename ", filename
			with open(filename) as f:
				text = f.read()
				print "[WebScriptList] text ", text
				scripts.append((basename(filename), text))
		return scripts

	def getResult(self):
		return self.res

	result = property(getResult)
	list = property(getList)
	lut = {"Name": 0			, "Text": 1
		}
