# -*- coding: utf-8 -*-
from Components.Sources.Source import Source
from subprocess import check_output

class PkgList(Source):
	def __init__(self, session, wap=False):
		Source.__init__(self)

	def handleCommand(self, cmd):
		pass

	def getOpkgfeed(self):
		PKG_NAME = 0
		PKG_VERSION = 1
		PKG_DESCRIPTION = 2
		PKG_INSTALLED = 3
		PKG_UPGRADABLE = 4

		pkglist = {}
		try:
			for line in check_output(['opkg', 'list']).splitlines():
				package, version, description = line.split(' - ', 2)
				pkglist[package] = (package, version, description, "0", "0")

			for line in check_output(['opkg', 'list-installed']).splitlines():
				package, version, description = line.split(' - ', 2)
				pkglist[package] = (package, version, description, "1", "0")

			for line in check_output(['opkg', 'list-upgradable']).splitlines():
				package, oldver, newver = line.split(' - ', 2)
				pkglist[package] = (package, "%s -> %s" % (oldver, newver), pkglist[package][PKG_DESCRIPTION], "1", "1")

			return sorted(pkglist.values())
		except Exception, e:
			print "[PkgList] except: ",str(e)
			return []

	list = property(getOpkgfeed)
	lut = {"Packagename": 0,
		"Release": 1,
		"Info": 2,
		"State": 3,
		"Update": 4,
	}
