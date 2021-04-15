#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Property GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Property GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Property GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Components.Sources.List import List
from Components.Element import cached

class InternetRadioList(List):
	def buildEntry(self, item):
		text1 = ""
		text2 = ""
		if self.mode == 0: # GENRELIST
			text1 = item.name
		elif self.mode == 1: # STATIONLIST
			if len(item.country) != 0:
				display = "%s (%s)" % (item.name, item.country)
			else:
				display = item.name
			text1 = display
			text2 = item.genre
		elif self.mode == 2: # FAVORITELIST
			if len(item.configItem.country.value) != 0:
				display = "%s (%s)" % (item.configItem.name.value, item.configItem.country.value)
			else:
				display = item.configItem.name.value
				
			if item.configItem.type.value > 0:
				if item.configItem.type.value == 1:
					filtername = _("Genres")
				else:
					filtername = _("Countries")
				display2 = "%s %s" % (_("Filter:"), filtername)
			else:
				display2 = item.configItem.tags.value
			text1 = display
			text2 = display2
		return (text1, text2)

	def __init__(self):
		List.__init__(self, enableWrapAround=True, item_height=28, buildfunc=self.buildEntry)
		self.mode = 0
		self.list = []

	def setMode(self, mode):
		self.mode = mode
		if mode == 0: # GENRELIST
			self.style = "default"
		elif mode == 1 or mode == 2: # STATIONLIST OR FAVORITELIST
			self.style = "favorite"

	def moveToIndex(self, index):
		if self.master is not None:
			self.master.index = index

	def getCurrentIndex(self):
		if self.master is not None:
			return self.master.getIndex()
		else:
			return 0
			
	@cached
	def getCurrentSelection(self):
		data = self.current and self.current[0]
		if data:
			return data
		return None			

	def setList(self, list):
		self.list = list
		List.setList(self, list)

	def moveToFavorite(self, name, text):
		if self.mode == 2: # FAVORITELIST
			i = 0
			for favs in self.list:
				if favs[0].configItem.name.value == name and favs[0].configItem.text.value == text:
					self.moveToIndex(i)
					break
				i += 1
