# -*- coding: UTF-8 -*-
# Zap Statistic by AliAbdul
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eServiceReference, gFont, RT_VALIGN_CENTER
from os import environ
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.Screen import Screen
from ServiceReference import ServiceReference
from time import gmtime, localtime, strftime, time
from Tools.Directories import fileExists
from xml.etree.cElementTree import parse
from skin import TemplatedListFonts, componentSizes

def decode_charset(str, charset):
	try:
		uni = unicode(str, charset, 'strict')
	except:
		uni = str
	return uni

###########################################################

def deformXml(xml):
	xml = xml.replace("&", "&amp;")
	xml = xml.replace("'", "&apos;")
	xml = xml.replace("<", "&lt;")
	xml = xml.replace(">", "&gt;")
	xml = xml.replace('"', "&quot;")
	return xml

def reformXml(xml):
	xml = xml.replace("&amp;", "&")
	xml = xml.replace("&apos;", "'")
	xml = xml.replace("&lt;", "<")
	xml = xml.replace("&gt;", ">")
	xml = xml.replace("&quot;", '"')
	return xml

###########################################################

class ZapEntry:
	def __init__(self, ref, begin=None, end=None):
		self.ref = ref
		self.name = ServiceReference(eServiceReference(ref)).getServiceName()
		if begin:
			self.begin = begin
		else:
			self.begin = time()
		self.end = end

	def stop(self):
		self.end = time()

###########################################################

class DurationZapEntry:
	def __init__(self, zapentry):
		self.ref = zapentry.ref
		self.name = zapentry.name
		duration = zapentry.end - zapentry.begin
		self.duration = strftime("%H:%M:%S", gmtime(duration))
		t = localtime(zapentry.begin)
		self.begin = "%02d.%02d. %02d:%02d:%02d" % (t[2], t[1], t[3], t[4], t[5])

###########################################################

class CombinedZapEntry:
	def __init__(self, zapentry):
		self.ref = zapentry.ref
		self.name = zapentry.name
		self.duration = zapentry.end - zapentry.begin

	def addDuration(self, zapentry):
		self.duration = self.duration + zapentry.end - zapentry.begin

	def getDurationText(self):
		return strftime("%H:%M:%S", gmtime(self.duration))

###########################################################

class ZapStatistic:
	def __init__(self):
		self.xmlFile = "/etc/zapstatistic.xml"
		self.zapEntries = []
		self.currentEntry = None

	def loadZapEntries(self):
		if fileExists(self.xmlFile):
			try:
				menu = parse(self.xmlFile).getroot()
				for item in menu.findall("entry"):
					ref = item.get("ref") or None
					if ref:
						ref = decode_charset(ref, "UTF-8").encode("UTF-8")
						ref = reformXml(ref)
					begin = item.get("begin") or None
					end = item.get("end") or None
					if ref and begin and end:
						self.zapEntries.append(ZapEntry(ref, float(begin), float(end)))
			except:
				print "[ZapStatistic] Error while reading xml file"

	def saveZapEntries(self):
		xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<zapstatistic>\n'
		for x in self.zapEntries:
			if not x.end:
				x.end = time()
			xml += '\t<entry ref="%s" begin="%s" end ="%s" />\n' % (decode_charset(deformXml(x.ref), "UTF-8"), str(x.begin), str(x.end))
		xml += '</zapstatistic>'
		try:
			f = open(self.xmlFile, "w")
			f.write(xml.encode("UTF-8"))
			f.close()
		except:
			print "[ZapStatistic] Error while writing xml file"

	def handlePlayServiceCommand(self, ref):
		self.handleStopServiceCommand()
		if ref:
			self.currentEntry = ZapEntry(ref.toString())

	def handleStopServiceCommand(self):
		if self.currentEntry:
			self.currentEntry.stop()
			self.zapEntries.append(self.currentEntry)
			self.currentEntry = None

zapstatistic = ZapStatistic()

###########################################################

global PlayService
global StopService
PlayService = None
StopService = None

def playService(ref, checkParentalControl=True, forceRestart=False):
	if PlayService:
		zapstatistic.handlePlayServiceCommand(ref)
		PlayService(ref, checkParentalControl, forceRestart)

def stopService():
	if StopService:
		zapstatistic.handleStopServiceCommand()
		StopService()

###########################################################

class ZapStatisticBrowserList(MenuList):
	SKIN_COMPONENT_KEY = "ZapStatisticBrowserList"
	SKIN_COMPONENT_TEXT1_WIDTH = "text1Width"
	SKIN_COMPONENT_TEXT2_WIDTH = "text2Width"
	SKIN_COMPONENT_TEXT3_WIDTH = "text3Width"
	SKIN_COMPONENT_TEXT_HEIGHT = "textHeight"

	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setItemHeight(componentSizes.itemHeight(self.SKIN_COMPONENT_KEY, 30))
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))

def ZapStatisticBrowserListEntry(entry):
	sizes = componentSizes[ZapStatisticBrowserList.SKIN_COMPONENT_KEY]
	text1Width = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT1_WIDTH, 300)
	text2Width = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT2_WIDTH, 500)
	textHeight = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT_HEIGHT, 30)

	res = [entry]
	t_begin = localtime(entry.begin)
	t_end = localtime(entry.end)
	res.append(MultiContentEntryText(pos=(5, 0), size=(text1Width, textHeight), font=0, flags=RT_VALIGN_CENTER, text="%02d.%02d. %02d:%02d:%02d - %02d:%02d:%02d" % (t_begin[2], t_begin[1], t_begin[3], t_begin[4], t_begin[5], t_end[3], t_end[4], t_end[5])))
	res.append(MultiContentEntryText(pos=(text1Width, 0), size=(text2Width, textHeight), font=0, flags=RT_VALIGN_CENTER, text=entry.name))
	return res

def ZapStatisticBrowserDurationListEntry(entry):
	sizes = componentSizes[ZapStatisticBrowserList.SKIN_COMPONENT_KEY]
	text1Width = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT1_WIDTH, 300)
	text2Width = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT2_WIDTH, 500)
	textHeight = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT_HEIGHT, 30)

	res = [entry]
	res.append(MultiContentEntryText(pos=(5, 0), size=(text1Width, textHeight), font=0, flags=RT_VALIGN_CENTER, text="%s (%s)" % (entry.duration, entry.begin)))
	res.append(MultiContentEntryText(pos=(text1Width, 0), size=(text2Width, textHeight), font=0, flags=RT_VALIGN_CENTER, text=entry.name))
	return res

def ZapStatisticBrowserCombinedListEntry(entry):
	sizes = componentSizes[ZapStatisticBrowserList.SKIN_COMPONENT_KEY]
	text3Width = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT3_WIDTH, 120)
	text2Width = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT2_WIDTH, 500)
	textHeight = sizes.get(ZapStatisticBrowserList.SKIN_COMPONENT_TEXT_HEIGHT, 30)

	res = [entry]
	res.append(MultiContentEntryText(pos=(5, 0), size=(text3Width, textHeight), font=0, flags=RT_VALIGN_CENTER, text="%s" % (entry.getDurationText())))
	res.append(MultiContentEntryText(pos=(text3Width, 0), size=(text2Width, textHeight), font=0, flags=RT_VALIGN_CENTER, text=entry.name))
	return res

###########################################################

class ZapStatisticDurationScreen(Screen):
	SORT_NAME_ASCENDING = 0
	SORT_NAME_DESCENDING = 1
	SORT_DURATION_ASCENDING = 2
	SORT_DURATION_DESCENDING = 3
	skin = """
		<screen position="center,120" size="820,520" title="%s" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
	    	<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<eLabel position="10,50" size="800,1" backgroundColor="grey" />
	    	<widget name="list" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>""" % _("Zap Statistic")

	def __init__(self, session):
		Screen.__init__(self, session)

		self.sortType = self.SORT_NAME_ASCENDING

		self["key_red"] = Label(_("Sort (name+)"))
		self["key_green"] = Label(_("Sort (name-)"))
		self["key_yellow"] = Label(_("Sort (duration+)"))
		self["key_blue"] = Label(_("Sort (duration-)"))
		self["list"] = ZapStatisticBrowserList([])

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.play,
				"cancel": self.close,
				"red": self.sortByNameAscending,
				"green": self.sortByNameDescending,
				"yellow": self.sortByDurationAscending,
				"blue": self.sortByDurationDescending
			}, prio=-1)

		self.onLayoutFinish.append(self.buildList)

	def sortList(self, l):
		if self.sortType == self.SORT_NAME_ASCENDING:
			return l.sort(key=self.buildSortNameKey, reverse=False)
		elif self.sortType == self.SORT_NAME_DESCENDING:
			return l.sort(key=self.buildSortNameKey, reverse=True)
		elif self.sortType == self.SORT_DURATION_ASCENDING:
			return l.sort(key=self.buildSortDurationKey, reverse=False)
		elif self.sortType == self.SORT_DURATION_DESCENDING:
			return l.sort(key=self.buildSortDurationKey, reverse=True)
		else:
			return l

	def buildSortNameKey(self, x):
		try:
			name = x.name
		except:
			name = ""
		return (name and name.lower() or "")

	def buildSortDurationKey(self, x):
		try:
			name = str(x.duration)
		except:
			name = ""
		return (name and name.lower() or "")

	def buildList(self):
		list = []
		l = []
		for x in zapstatistic.zapEntries:
			l.append(DurationZapEntry(x))
		self.sortList(l)
		for x in l:
			list.append(ZapStatisticBrowserDurationListEntry(x))
		self["list"].setList(list)

	def play(self):
		cur = self["list"].getCurrent()
		if cur:
			entry = cur[0]
			self.session.nav.playService(eServiceReference(entry.ref))

	def sortByNameAscending(self):
		self.sortType = self.SORT_NAME_ASCENDING
		self.buildList()

	def sortByNameDescending(self):
		self.sortType = self.SORT_NAME_DESCENDING
		self.buildList()

	def sortByDurationAscending(self):
		self.sortType = self.SORT_DURATION_ASCENDING
		self.buildList()

	def sortByDurationDescending(self):
		self.sortType = self.SORT_DURATION_DESCENDING
		self.buildList()

###########################################################

class ZapStatisticCombinedScreen(Screen):
	SORT_NAME_ASCENDING = 0
	SORT_NAME_DESCENDING = 1
	SORT_DURATION_ASCENDING = 2
	SORT_DURATION_DESCENDING = 3
	skin = """
		<screen position="center,120" size="820,520" title="%s" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
	    	<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<eLabel position="10,50" size="800,1" backgroundColor="grey" />
	    	<widget name="list" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>""" % _("Zap Statistic")

	def __init__(self, session):
		Screen.__init__(self, session)

		self.list = []
		self.sortType = self.SORT_DURATION_DESCENDING

		self["key_red"] = Label(_("Sort (name+)"))
		self["key_green"] = Label(_("Sort (name-)"))
		self["key_yellow"] = Label(_("Sort (duration+)"))
		self["key_blue"] = Label(_("Sort (duration-)"))
		self["list"] = ZapStatisticBrowserList([])

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.play,
				"cancel": self.close,
				"red": self.sortByNameAscending,
				"green": self.sortByNameDescending,
				"yellow": self.sortByDurationAscending,
				"blue": self.sortByDurationDescending
			}, prio=-1)

		self.onLayoutFinish.append(self.buildList)

	def sortList(self, l):
		if self.sortType == self.SORT_NAME_ASCENDING:
			return l.sort(key=self.buildSortNameKey, reverse=False)
		elif self.sortType == self.SORT_NAME_DESCENDING:
			return l.sort(key=self.buildSortNameKey, reverse=True)
		elif self.sortType == self.SORT_DURATION_ASCENDING:
			return l.sort(key=self.buildSortDurationKey, reverse=False)
		elif self.sortType == self.SORT_DURATION_DESCENDING:
			return l.sort(key=self.buildSortDurationKey, reverse=True)
		else:
			return l

	def buildSortNameKey(self, x):
		try:
			name = x.name
		except:
			name = ""
		return (name and name.lower() or "")

	def buildSortDurationKey(self, x):
		try:
			name = x.getDurationText()
		except:
			name = ""
		return (name and name.lower() or "")

	def buildList(self):
		list = []
		if len(self.list) == 0:
			for x in zapstatistic.zapEntries:
				added = False
				for y in self.list:
					if x.ref == y.ref:
						y.addDuration(x)
						added = True
						break
				if added == False:
					self.list.append(CombinedZapEntry(x))
		self.sortList(self.list)
		for x in self.list:
			list.append(ZapStatisticBrowserCombinedListEntry(x))
		self["list"].setList(list)

	def play(self):
		cur = self["list"].getCurrent()
		if cur:
			entry = cur[0]
			self.session.nav.playService(eServiceReference(entry.ref))

	def sortByNameAscending(self):
		self.sortType = self.SORT_NAME_ASCENDING
		self.buildList()

	def sortByNameDescending(self):
		self.sortType = self.SORT_NAME_DESCENDING
		self.buildList()

	def sortByDurationAscending(self):
		self.sortType = self.SORT_DURATION_ASCENDING
		self.buildList()

	def sortByDurationDescending(self):
		self.sortType = self.SORT_DURATION_DESCENDING
		self.buildList()

###########################################################

class ZapStatisticScreen(Screen, ProtectedScreen):
	SORT_NAME_ASCENDING = 0
	SORT_NAME_DESCENDING = 1
	SORT_DATE_ASCENDING = 2
	SORT_DATE_DESCENDING = 3
	skin = """
		<screen position="center,120" size="820,520" title="%s" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
	    	<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
	    	<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
	    	<eLabel position="10,50" size="800,1" backgroundColor="grey" />
	    	<widget name="list" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>""" % _("Zap Statistic")

	def __init__(self, session):
		Screen.__init__(self, session)
		ProtectedScreen.__init__(self)

		self.session = session
		self.sortType = self.SORT_DATE_ASCENDING

		self["key_red"] = Label(_("Delete"))
		self["key_green"] = Label(" ")
		self["key_yellow"] = Label(" ")
		self["key_blue"] = Label(_("Durations"))
		self["list"] = ZapStatisticBrowserList([])

		self["actions"] = ActionMap(["ColorActions", "OkCancelActions", "InfobarMenuActions"],
			{
				"ok": self.play,
				"cancel": self.close,
				"red": self.delete,
				"green": self.sortByName,
				"yellow": self.sortByDate,
				"blue": self.duration,
				"mainMenu": self.menu
			}, prio=-1)

		self.onLayoutFinish.append(self.buildList)

	def updateLabels(self):
		self["key_green"].setText(_("Sort (name+)"))
		self["key_yellow"].setText(_("Sort (date+)"))
		if self.sortType == self.SORT_NAME_ASCENDING:
			self["key_green"].setText(_("Sort (name-)"))
		if self.sortType == self.SORT_DATE_ASCENDING:
			self["key_yellow"].setText(_("Sort (date-)"))

	def sortList(self, l):
		if self.sortType == self.SORT_NAME_ASCENDING:
			return l.sort(key=self.buildSortNameKey, reverse=False)
		elif self.sortType == self.SORT_NAME_DESCENDING:
			return l.sort(key=self.buildSortNameKey, reverse=True)
		elif self.sortType == self.SORT_DATE_ASCENDING:
			return l.sort(key=self.buildSortDateKey, reverse=False)
		elif self.sortType == self.SORT_DATE_DESCENDING:
			return l.sort(key=self.buildSortDateKey, reverse=True)
		else:
			return l

	def buildSortNameKey(self, x):
		try:
			name = x.name
		except:
			name = ""
		return (name and name.lower() or "")

	def buildSortDateKey(self, x):
		try:
			name = str(x.begin)
		except:
			name = ""
		return (name and name.lower() or "")

	def buildList(self):
		list = []
		l = zapstatistic.zapEntries
		self.sortList(l)
		for x in l:
			list.append(ZapStatisticBrowserListEntry(x))
		self["list"].setList(list)
		self.updateLabels()

	def isProtected(self):
		return config.ParentalControl.setuppinactive.value and config.ParentalControl.configured.value

	def pinEntered(self, result):
		if result is None:
			self.close()
		elif not result:
			self.close()

	def play(self):
		cur = self["list"].getCurrent()
		if cur:
			entry = cur[0]
			self.session.nav.playService(eServiceReference(entry.ref))

	def delete(self):
		cur = self["list"].getCurrent()
		if cur:
			entry = cur[0]
			idx = 0
			for x in zapstatistic.zapEntries:
				if x == entry:
					del zapstatistic.zapEntries[idx]
					break
				else:
					idx += 1
			self.buildList()

	def deleteAll(self):
		if len(zapstatistic.zapEntries):
			del zapstatistic.zapEntries
			zapstatistic.zapEntries = []
			self.buildList()

	def sortByName(self):
		if self["key_green"].getText() == _("Sort (name-)"):
			self.sortType = self.SORT_NAME_DESCENDING
		else:
			self.sortType = self.SORT_NAME_ASCENDING
		self.buildList()

	def sortByNameAscending(self):
		self.sortType = self.SORT_NAME_ASCENDING
		self.buildList()

	def sortByNameDescending(self):
		self.sortType = self.SORT_NAME_DESCENDING
		self.buildList()

	def sortByDate(self):
		if self["key_yellow"].getText() == _("Sort (date-)"):
			self.sortType = self.SORT_DATE_DESCENDING
		else:
			self.sortType = self.SORT_DATE_ASCENDING
		self.buildList()

	def sortByDateAscending(self):
		self.sortType = self.SORT_DATE_ASCENDING
		self.buildList()

	def sortByDateDescending(self):
		self.sortType = self.SORT_DATE_DESCENDING
		self.buildList()

	def duration(self):
		self.session.open(ZapStatisticDurationScreen)

	def combined(self):
		self.session.open(ZapStatisticCombinedScreen)

	def menu(self):
		list = []
		list.append((_("Play entry"), self.play))
		list.append((_("Delete entry"), self.delete))
		list.append((_("Delete all entries"), self.deleteAll))
		list.append((_("Sort by name (ascending)"), self.sortByNameAscending))
		list.append((_("Sort by name (descending)"), self.sortByNameDescending))
		list.append((_("Sort by date (ascending)"), self.sortByDateAscending))
		list.append((_("Sort by date (descending)"), self.sortByDateDescending))
		list.append((_("Show duration window"), self.duration))
		list.append((_("Show combined duration window"), self.combined))
		list.append((_("Close plugin"), self.close))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Please choose a function..."), list=list)

	def menuCallback(self, callback=None):
		if callback is not None:
			callback[1]()

###########################################################

def main(session, **kwargs):
	session.open(ZapStatisticScreen)

def sessionstart(reason, **kwargs):
	if reason == 0:
		zapstatistic.loadZapEntries()
		session = kwargs["session"]
		global PlayService
		global StopService
		PlayService = session.nav.playService
		StopService = session.nav.stopService
		session.nav.playService = playService
		session.nav.stopService = stopService

def autostart(reason, **kwargs):
	if reason == 1:
		zapstatistic.saveZapEntries()

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Zap Statistic"), description=_("Shows the watched services with some statistic"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart),
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart)]
