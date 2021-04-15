# -*- coding: utf-8 -*-
from Components.Sources.Source import Source
from glob import glob
from os import statvfs
from os.path import basename, isfile, join
from shutil import move


class PkgConfList(Source):
	LIST = 0
	SWITCH = 1
	MEM = 2

	sources_list_d = '/etc/apt/sources.list.d'

	def __init__(self, session, func=LIST, wap=False):
		Source.__init__(self)
		self.func = func
		self.wap = wap
		self.session = session
		self.res = (False, "Missing or Wrong Argument")
			
	def handleCommand(self, cmd):
		if cmd is not None:
			if self.func is self.SWITCH:
				self.res = self.switch(cmd)
			if self.func is self.MEM:
				self.res = self.getMem()
			elif self.func is self.LIST:
				pass
			
	def switch(self, cmd):
		if cmd:
			filename = cmd.get('file')
			if not filename or filename != basename(filename):
				return (False, 'Invalid filename')

			filename = join(self.sources_list_d, filename)
			backup = filename + '.off'
			if isfile(filename):
				move(filename, backup)
				return (True, backup)
			elif isfile(backup):
				move(backup, filename)
				return (True, filename)

	def getMem(self):
		try:
			stat = statvfs(self.sources_list_d)
		except OSError:
			return (False, "statvfs() failed")
		freespace = stat.f_bfree / 1000 * stat.f_bsize / 1000
		return (True, '%d' % freespace)
			
	def getList(self):
		sources = []
		for filename in sorted(glob('%s/*.list*' % self.sources_list_d)):
			if filename.endswith(".list") or filename.endswith(".list.off"):
				print "[PkgConfList] file ", filename
				with open(filename) as f:
					text = f.read()
					print "[PkgConfList] text ", text
					sources.append((basename(filename), text))
		return sources

	def getResult(self):
		if self.func is not self.LIST:
			return self.res
		return (False, "illegal call")

	result = property(getResult)
	
	list = property(getList)
	lut = {"Name": 0			, "Text": 1
		}
