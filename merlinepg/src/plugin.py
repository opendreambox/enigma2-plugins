#######################################################################
#
#	Merlin Programm Guide for Dreambox-Enigma2
#	Coded by Vali (c)2010-2011
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Property GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#
#######################################################################



from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.EventView import EventViewSimple
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.TimerEntry import TimerEntry
from Screens.TimerEdit import TimerSanityConflict
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, Rect
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigInteger, getConfigListEntry
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, fileExists
from Tools.LoadPixmap import LoadPixmap
from enigma import eServiceReference, eServiceCenter, getDesktop, eTimer, gFont, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_VALIGN_TOP, RT_WRAP, eEPGCache
from RecordTimer import RecordTimerEntry, parseEvent, AFTEREVENT
from ServiceReference import ServiceReference
from ShowMe import ShowMe
from skin import TemplatedListFonts, componentSizes
from time import localtime
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/AutoTimer/AutoTimerEditor.pyo"):
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import addAutotimerFromEvent
	from Plugins.Extensions.AutoTimer.plugin import main as AutoTimerView
	AutoTimerPresent=True
else:
	AutoTimerPresent=False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo"):
	from Plugins.Extensions.IMDb.plugin import IMDB
	IMDbPresent=True
else:
	IMDbPresent=False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/AdvancedMovieSelection/plugin.pyo"):
	from Plugins.Extensions.AdvancedMovieSelection.plugin import tmdbInfo
	TMDbPresent=True
else:
	TMDbPresent=False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/AdvancedMovieSelection/plugin.pyo"):
	from Plugins.Extensions.AdvancedMovieSelection.plugin import tvdbInfo
	TVDbPresent=True
else:
	TVDbPresent=False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/SeriesPlugin/plugin.pyo"):
	from Plugins.Extensions.SeriesPlugin.SeriesPluginInfoScreen import SeriesPluginInfoScreen
	SeriesPluginPresent=True
else:
	SeriesPluginPresent=False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EPGSearch/EPGSearch.pyo"):
	from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearchList, EPGSearch
	epgSpresent=True
else:
	epgSpresent=False



config.plugins.MerlinEPG = ConfigSubsection()
config.plugins.MerlinEPG.Columns = ConfigYesNo(default=True)
config.plugins.MerlinEPG.StartFirst = ConfigYesNo(default=False)
config.plugins.MerlinEPG.Primetime  = ConfigInteger(default=20, limits=(0, 23))
config.plugins.MerlinEPG.PTlow  = ConfigInteger(default=10, limits=(0, 59))
config.plugins.MerlinEPG.PThi  = ConfigInteger(default=20, limits=(0, 59))
config.plugins.MerlinEPG.AutoPT  = ConfigYesNo(default=False)
config.plugins.MerlinEPG.ZapOnOK  = ConfigYesNo(default=False)
config.plugins.MerlinEPG.PageUDonBouquets  = ConfigYesNo(default=True)



def Plugins(**kwargs):
 	list = [(PluginDescriptor(name="Merlin Programm Guide", description="Merlin Programm Guide", where=PluginDescriptor.WHERE_EVENTINFO, fnc=startMerlinPG))]
	list.append(PluginDescriptor(name="Merlin Programm Guide", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=startMerlinPGnew))
	return list



def startMerlinPG(session, servicelist, **kwargs):
	if config.plugins.MerlinEPG.Columns.value:
		session.open(Merlin_PGII, servicelist)
	else:
		session.open(Merlin_PGd, servicelist)



def startMerlinPGnew(session, **kwargs):
	if "servicelist" in kwargs:
		if config.plugins.MerlinEPG.Columns.value:
			session.open(Merlin_PGII, kwargs["servicelist"])
		else:
			session.open(Merlin_PGd, kwargs["servicelist"])
	else:
		if config.plugins.MerlinEPG.Columns.value:
			session.open(Merlin_PGII)
		else:
			session.open(Merlin_PGd)



class MerlinPGsetup(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="660,340" title="Merlin Programm Guide">
			<widget name="config" position="10,10" size="640,320" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		clist = []
		clist.append(getConfigListEntry(_("Show EPG in columns:"), config.plugins.MerlinEPG.Columns))
		clist.append(getConfigListEntry(_("Start allways on channel 1:"), config.plugins.MerlinEPG.StartFirst))
		clist.append(getConfigListEntry(_("Primetime (h):"), config.plugins.MerlinEPG.Primetime))
		clist.append(getConfigListEntry(_("Primetime from (m):"), config.plugins.MerlinEPG.PTlow))
		clist.append(getConfigListEntry(_("Primetime to (m):"), config.plugins.MerlinEPG.PThi))
		clist.append(getConfigListEntry(_("Auto-Primetime:"), config.plugins.MerlinEPG.AutoPT))
		clist.append(getConfigListEntry(_("Zap with OK button (false=EventInfo):"), config.plugins.MerlinEPG.ZapOnOK))
		clist.append(getConfigListEntry(_("Page-up/down with bouquet+/- :"), config.plugins.MerlinEPG.PageUDonBouquets))
		ConfigListScreen.__init__(self, clist)
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.set, "cancel": self.exit}, -2)

	def set(self):
		if not config.plugins.MerlinEPG.PThi.value > config.plugins.MerlinEPG.PTlow.value:
			return
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()



class MerlinEPGList(EPGList):
	SKIN_COMPONENT_KEY = "MerlinEPGList"
	SKIN_COMPONENT_ICON_HEIGHT = "iconHeight"
	SKIN_COMPONENT_ICON_WIDTH = "iconWidth"
	SKIN_COMPONENT_ITEM_MARGIN = "itemMargin"
	SKIN_COMPONENT_TEXT_HEIGHT = "textHeight"

	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None):
		EPGList.__init__(self, type, selChangedCB, timer)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.SMALL), tlf.size(tlf.SMALL)))
		self.PTpicture = LoadPixmap(cached=True, path="/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPG/primetime.svg")
		self.evCnt = 0

		sizes = componentSizes[MerlinEPGList.SKIN_COMPONENT_KEY]
		self._textHeight = sizes.get(MerlinEPGList.SKIN_COMPONENT_TEXT_HEIGHT, 40)
		self._iconWidth = sizes.get(MerlinEPGList.SKIN_COMPONENT_ICON_WIDTH, 21)
		self._iconHeight = sizes.get(MerlinEPGList.SKIN_COMPONENT_ICON_HEIGHT, 21)
		self._itemMargin = sizes.get(MerlinEPGList.SKIN_COMPONENT_ITEM_MARGIN, 100)

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		width = esize.width()
		height = esize.height()
		self.datetime_rect = Rect(5,2, width * 0.80, self._iconHeight)
		self.descr_rect = Rect(5, self._iconHeight +5, width-10, self._textHeight)
		self.evCnt = 0

	def buildSingleEntry(self, service, eventId, beginTime, duration, EventName):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		r2=self.datetime_rect
		r3=self.descr_rect
		t = localtime(beginTime)
		self.evCnt = self.evCnt + 1
		if (t[3]==config.plugins.MerlinEPG.Primetime.value) and (t[4]>=config.plugins.MerlinEPG.PTlow.value) and (t[4]<config.plugins.MerlinEPG.PThi.value):
			res = [
				None,
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r2.left() +self._itemMargin, 1, self._iconWidth, self._iconHeight, self.PTpicture),
				(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r2.height(), 0, RT_HALIGN_LEFT, (("%02d:%02d"%(t[3],t[4]))+" - "+self.days[t[6]]))
			]
		else:
			res = [
				None,
				(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r2.height(), 0, RT_HALIGN_LEFT, (("%02d:%02d"%(t[3],t[4]))+" - "+self.days[t[6]]))
			]
		if rec:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r2.left() +self._itemMargin*1.9, r2.top(), self._iconWidth, self._iconHeight, clock_pic),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_WRAP, EventName)
			))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_WRAP, EventName))
		return res

	def getBgTime(self):
		tmp = self.l.getCurrentSelection()
		if tmp is None:
			return ( None )
		bt = localtime(tmp[2])
		return ( bt[3], bt[4] )

	def foudPrimetime(self):
		for OneLine in range(0,self.evCnt):
			evBgTime, evBgMin = self.getBgTime()
			if evBgTime is not None:
				if (evBgTime==config.plugins.MerlinEPG.Primetime.value) and (evBgMin>=config.plugins.MerlinEPG.PTlow.value) and (evBgMin<config.plugins.MerlinEPG.PThi.value):
					break
				self.moveDown()
			else:
				break



class Merlin_PGII(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 1920:
		skin = """
		<screen flags="wfNoBorder" name="Merlin_PG" position="0,0" size="1920,1080" title="Merlin Program Guide">
		<!-- DO NOT CHANGE THIS LINE !!!!!!!!!!!!!!! --><widget enableWrapAround="0" itemHeight="25" name="prg_list" position="-200,-200" size="50,125"/>
			<widget font="Regular;34" halign="center" name="currCh1" position="30,20" size="360,40"/>
			<widget font="Regular;34" halign="center" name="currCh2" position="405,20" size="360,40"/>
			<widget font="Regular;34" halign="center" name="currCh3" position="780,20" size="360,40"/>
			<widget font="Regular;34" halign="center" name="currCh4" position="1155,20" size="360,40"/>
			<widget font="Regular;34" halign="center" name="currCh5" position="1530,20" size="360,40"/>
			<widget backgroundColor="#888888" name="Active1" position="25,70" size="350,10"/>
			<widget backgroundColor="#888888" name="Active2" position="400,70" size="350,10"/>
			<widget backgroundColor="#888888" name="Active3" position="775,70" size="350,10"/>
			<widget backgroundColor="#888888" name="Active4" position="1150,70" size="350,10"/>
			<widget backgroundColor="#888888" name="Active5" position="1525,70" size="350,10"/>
			<widget itemHeight="110" name="epg_list1" position="25,100" scrollbarMode="showOnDemand" size="370,770"/>
			<widget itemHeight="110" name="epg_list2" position="400,100" scrollbarMode="showOnDemand" size="370,770"/>
			<widget itemHeight="110" name="epg_list3" position="775,100" scrollbarMode="showOnDemand" size="370,770"/>
			<widget itemHeight="110" name="epg_list4" position="1150,100" scrollbarMode="showOnDemand" size="370,770"/>
			<widget itemHeight="110" name="epg_list5" position="1525,100" scrollbarMode="showOnDemand" size="370,770"/>
			<widget font="Regular;28" name="fullEventInfo" position="50,885" size="1820,132"/>
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPG/buttons.png" position="60,1030" size="800,40"/>
			<widget backgroundColor="background" font="Regular;32" foregroundColor="#ffc000" position="900,1030" render="Label" size="600,40" source="global.CurrentTime">
				<convert type="ClockToText">Format:%H:%M  %a %d. %b</convert>
			</widget>
		</screen>"""
	else:
		skin = """
		<screen name="Merlin_PG" position="center,60" size="1260,650" title="Merlin Program Guide">
		<!-- DO NOT CHANGE THIS LINE !!!!!!!!!!!!!!! --><widget enableWrapAround="0" itemHeight="25" name="prg_list" position="-200,-200" size="50,125"/>
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
			<eLabel text="Zap" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel text="Timer" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel text="Primetime" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"  shadowColor="black" shadowOffset="-2,-2" />
			<eLabel text="Refresh" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="820,12" size="60,30" alphatest="on" />
			<widget source="global.CurrentTime" render="Label" position="1130,12" size="80,22" font="Regular;22" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="910,12" size="210,25" font="Regular;22" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Format:%A %d. %B</convert>
			</widget>
			<eLabel position="10,50" size="1240,1" backgroundColor="grey" />
			<widget font="Regular;20" halign="center" name="currCh1" position="10,60" size="235,24" />
			<widget font="Regular;20" halign="center" name="currCh2" position="260,60" size="235,24" />
			<widget font="Regular;20" halign="center" name="currCh3" position="510,60" size="235,24" />
			<widget font="Regular;20" halign="center" name="currCh4" position="760,60" size="235,24" />
			<widget font="Regular;20" halign="center" name="currCh5" position="1010,60" size="235,24" />
			<widget backgroundColor="grey" name="Active1" position="5,87" size="245,6" />
			<widget backgroundColor="grey" name="Active2" position="255,87" size="245,6" />
			<widget backgroundColor="grey" name="Active3" position="505,87" size="245,6" />
			<widget backgroundColor="grey" name="Active4" position="755,87" size="245,6" />
			<widget backgroundColor="grey" name="Active5" position="1005,87" size="245,6" />
			<widget itemHeight="75" name="epg_list1" position="5,110" scrollbarMode="showOnDemand" size="245,450" />
			<widget itemHeight="75" name="epg_list2" position="255,110" scrollbarMode="showOnDemand" size="245,450" />
			<widget itemHeight="75" name="epg_list3" position="505,110" scrollbarMode="showOnDemand" size="245,450" />
			<widget itemHeight="75" name="epg_list4" position="755,110" scrollbarMode="showOnDemand" size="245,450" />
			<widget itemHeight="75" name="epg_list5" position="1005,110" scrollbarMode="showOnDemand" size="245,450" />
			<eLabel position="10,566" size="1240,1" backgroundColor="grey" />
			<widget font="Regular;19" name="fullEventInfo" position="10,575" size="1240,65"/>
		</screen>"""

	def __init__(self, session, servicelist=None):
		Screen.__init__(self, session)
		self.session = session
		self.srvList = servicelist
		self.myServices = []
		self.myBqts = []
		self.list = []
		self.chCount = 0
		self.ActiveEPG = 1
		self.Fields = 6
		self.CheckForEPG = eTimer()
		self.CheckForEPG_conn = self.CheckForEPG.timeout.connect(self.CheckItNow)
		self.AutoPrime = eTimer()
		self.AutoPrime_conn = self.AutoPrime.timeout.connect(self.go2Primetime)
		self["prg_list"] = MenuList(self.getChannels())
		self["fullEventInfo"] = Label(" ")
		self["currCh1"] = Label(" ")
		self["currCh2"] = Label(" ")
		self["currCh3"] = Label(" ")
		self["currCh4"] = Label(" ")
		self["currCh5"] = Label(" ")
		self["Active1"] = Label(" ")
		self["Active2"] = Label(" ")
		self["Active3"] = Label(" ")
		self["Active4"] = Label(" ")
		self["Active5"] = Label(" ")
		self["epg_list1"] = MerlinEPGList(type=EPG_TYPE_SINGLE, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self["epg_list2"] = MerlinEPGList(type=EPG_TYPE_SINGLE, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self["epg_list3"] = MerlinEPGList(type=EPG_TYPE_SINGLE, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self["epg_list4"] = MerlinEPGList(type=EPG_TYPE_SINGLE, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self["epg_list5"] = MerlinEPGList(type=EPG_TYPE_SINGLE, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self["actions"] = ActionMap(["OkCancelActions", "EPGSelectActions", "DirectionActions", "ColorActions", "MenuActions", "NumberActions", "HelpActions", "InfobarActions"], {
						"ok": self.UserOK,
						"cancel": self.close,
						"nextBouquet": self.AllUp,
						"prevBouquet": self.AllDown,
						"nextService": self.NextPage,
						"prevService": self.PrevPage,
						"right": self.right,
						"rightRepeated": self.right,
						"left": self.left,
						"leftRepeated": self.left,
						"up": self.up,
						"upRepeated": self.up,
						"down": self.down,
						"downRepeated": self.down,
						"info": self.showEventInfo,
						"red": self.ZapTo,
						"green": self.timerAdd,
						"blue": self.ZapForRefresh,
						"yellow": self.go2Primetime,
						"menu": self.menuClicked,
						"displayHelp": self.myhelp,
						"0": self.go2now,
						"1": self.go2first,
						"7": self.findPrvBqt,
						"9": self.findNextBqt,
						"showMovies": self.editCurTimer,
						"showTv": self.fullEPGlist,
						"showRadio": self.runEpgSeartch
						},-2)
		self.onLayoutFinish.append(self.onLayoutReady)

	def getChannels(self):
		indx = 0
		serviceHandler = eServiceCenter.getInstance()
		services = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET "bouquets.tv" ORDER BY bouquet'))
		bouquets = services and services.getContent("SN", True)
		for bouquet in bouquets:
			services = serviceHandler.list(eServiceReference(bouquet[0]))
			channels = services and services.getContent("SN", True)
			for channel in channels:
				if not channel[0].startswith("1:64:"):
					indx = indx + 1
					self.list.append(str(indx) + ". " + channel[1].replace('\xc2\x86', '').replace('\xc2\x87', ''))
					self.myServices.append(channel)
					self.myBqts.append(bouquet)
		self.chCount = indx - 1
		return self.list

	def onLayoutReady(self):
		#service = self.session.nav.getCurrentService()
		#info = service and service.info()
		#if (info is not None) and not(config.plugins.MerlinEPG.StartFirst.value):
			#nameROH = info.getName().replace('\xc2\x86', '').replace('\xc2\x87', '')
		if self.srvList:
			service = ServiceReference(self.srvList.getCurrentSelection())
			info = service and service.info()
			nameROH = info and info.getName(service.ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
		else:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			nameROH = info and info.getName().replace('\xc2\x86', '').replace('\xc2\x87', '')
		if (nameROH is not None) and not(config.plugins.MerlinEPG.StartFirst.value):
		#
			for idx in range(1, len(self.list)):
				name = str(idx) + ". " + nameROH
				if name == self.list[idx-1]:
					break
			self["prg_list"].moveToIndex(idx-1)
		else:
			self["prg_list"].moveToIndex(0)
		self.updateInfos()

	def updateInfos(self):
		if self.AutoPrime.isActive():
			self.AutoPrime.stop()
		self.displayActiveEPG()
		prgIndex = self["prg_list"].getSelectionIndex()
		CurrentPrg = self.myServices[prgIndex]
		self["currCh1"].setText(str(CurrentPrg[1]))
		l = self["epg_list1"]
		l.recalcEntrySize()
		myService = ServiceReference(CurrentPrg[0])
		l.fillSingleEPG(myService)
		prgIndex = prgIndex + 1
		if prgIndex < (self.chCount+1):
			self["epg_list2"].show()
			CurrentPrg = self.myServices[prgIndex]
			self["currCh2"].setText(str(CurrentPrg[1]))
			l = self["epg_list2"]
			l.recalcEntrySize()
			myService = ServiceReference(CurrentPrg[0])
			l.fillSingleEPG(myService)
		else:
			self["currCh2"].setText(str(" "))
			self["epg_list2"].hide()
		prgIndex = prgIndex + 1
		if prgIndex < (self.chCount+1):
			self["epg_list3"].show()
			CurrentPrg = self.myServices[prgIndex]
			self["currCh3"].setText(str(CurrentPrg[1]))
			l = self["epg_list3"]
			l.recalcEntrySize()
			myService = ServiceReference(CurrentPrg[0])
			l.fillSingleEPG(myService)
		else:
			self["currCh3"].setText(str(" "))
			self["epg_list3"].hide()
		prgIndex = prgIndex + 1
		if prgIndex < (self.chCount+1):
			self["epg_list4"].show()
			CurrentPrg = self.myServices[prgIndex]
			self["currCh4"].setText(str(CurrentPrg[1]))
			CurrentPrg = self.myServices[prgIndex]
			self["currCh4"].setText(str(CurrentPrg[1]))
			l = self["epg_list4"]
			l.recalcEntrySize()
			myService = ServiceReference(CurrentPrg[0])
			l.fillSingleEPG(myService)
		else:
			self["currCh4"].setText(str(" "))
			self["epg_list4"].hide()
		if self.Fields == 6:
			prgIndex = prgIndex + 1
			if prgIndex < (self.chCount+1):
				self["epg_list5"].show()
				CurrentPrg = self.myServices[prgIndex]
				self["currCh5"].setText(str(CurrentPrg[1]))
				l = self["epg_list5"]
				l.recalcEntrySize()
				myService = ServiceReference(CurrentPrg[0])
				l.fillSingleEPG(myService)
			else:
				self["currCh5"].setText(str(" "))
				self["epg_list5"].hide()
		if config.plugins.MerlinEPG.AutoPT.value:
			 self.AutoPrime.start(500)

	def onSelectionChanged(self):
		curEV = self["epg_list"+str(self.ActiveEPG)].getCurrent()
		event = curEV[0]
		ext = event and event.getExtendedDescription() or ""
		self["fullEventInfo"].setText(str(ext))

	def NextPage(self):
		self["prg_list"].pageDown()
		self.ActiveEPG = 1
		self.updateInfos()

	def PrevPage(self):
		self["prg_list"].pageUp()
		self.ActiveEPG = 1
		self.updateInfos()

	def displayActiveEPG(self):
		for xA in range(1,self.Fields):
			if xA == self.ActiveEPG:
				self["Active"+str(xA)].show()
			else:
				self["Active"+str(xA)].hide()

	def getActivePrg(self):
		return self["prg_list"].getSelectionIndex()+(self.ActiveEPG-1)

	def ZapTo(self):
		if (self.getActivePrg() > self.chCount) or (self.srvList==None):
			return
		CurrentPrg = self.myServices[self.getActivePrg()]
		CurrentBqt = self.myBqts[self.getActivePrg()]
		myService = ServiceReference(CurrentPrg[0])
		myB = ServiceReference(CurrentBqt[0])
		self.srvList.clearPath()
		if self.srvList.bouquet_root != myB.ref:
			self.srvList.enterPath(self.srvList.bouquet_root)
		self.srvList.enterPath(myB.ref)
		self.srvList.setCurrentSelection(myService.ref)
		self.srvList.zap()
		self.close()

	def ZapForRefresh(self):
		if (self.getActivePrg() > self.chCount) or (self.srvList==None):
			return
		CurrentPrg = self.myServices[self.getActivePrg()]
		myService = ServiceReference(CurrentPrg[0])
		self.session.nav.playService(myService.ref)
		self.CheckForEPG.start(4000, True)

	def CheckItNow(self):
		self.CheckForEPG.stop()
		CurrentPrg = self.myServices[self.getActivePrg()]
		l = self["epg_list"+str(self.ActiveEPG)]
		l.recalcEntrySize()
		myService = ServiceReference(CurrentPrg[0])
		l.fillSingleEPG(myService)

	def up(self):
		self["epg_list"+str(self.ActiveEPG)].moveUp()

	def down(self):
		self["epg_list"+str(self.ActiveEPG)].moveDown()

	def AllUp(self):
		if config.plugins.MerlinEPG.PageUDonBouquets.value:
			for xU in range(1,self.Fields):
				self["epg_list"+str(xU)].instance.moveSelection(self["epg_list"+str(xU)].instance.pageUp)
		else:
			for xU in range(1,self.Fields):
				self["epg_list"+str(xU)].moveUp()

	def AllDown(self):
		if config.plugins.MerlinEPG.PageUDonBouquets.value:
			for xU in range(1,self.Fields):
				self["epg_list"+str(xU)].instance.moveSelection(self["epg_list"+str(xU)].instance.pageDown)
		else:
			for xD in range(1,self.Fields):
				self["epg_list"+str(xD)].moveDown()

	def go2now(self):
		for xD in range(1,self.Fields):
			self["epg_list"+str(xD)].instance.moveSelection(self["epg_list"+str(xD)].instance.moveTop)

	def go2first(self):
		self["prg_list"].moveToIndex(0)
		self.ActiveEPG = 1
		self.updateInfos()

	def left(self):
		if self.ActiveEPG > 1:
			self.ActiveEPG = self.ActiveEPG - 1
			self.displayActiveEPG()
		else:
			self["prg_list"].pageUp()
			self.ActiveEPG = (self.Fields-1)
			self.updateInfos()
		self.onSelectionChanged()

	def right(self):
		if self.ActiveEPG < (self.Fields-1):
			self.ActiveEPG = self.ActiveEPG + 1
			self.displayActiveEPG()
		else:
			self.NextPage()
		self.onSelectionChanged()

	def showEventInfo(self):
		if not IMDbPresent:
			self.showConfirmedInfo([None,"Ei"])
		elif not TMDbPresent:
			self.showConfirmedInfo([None,"Ei"])
		elif not TVDbPresent:
			self.showConfirmedInfo([None,"Ei"])
		else:
			self.session.openWithCallback(self.showConfirmedInfo, ChoiceBox, title=_("Select Info type..."), list=[(_("Standard EPG info"), "Ei"),(_("IMDb info"), "Ii"),(_("TMDb info"), "Tm"),(_("TVDb info"), "Tv"),(_("SeriesPlugin"), "Sp")])

	def showConfirmedInfo(self,answer):
		curEV = self["epg_list"+str(self.ActiveEPG)].getCurrent()
		event = curEV[0]
		service = curEV[1]
		answer = answer and answer[1]
		if answer == "Ei":
			if event is not None:
				self.session.open(EventViewSimple, event, service)
		if answer == "Ii":
			if event is not None:
				IeventName=event.getEventName()
				self.session.open(IMDB, IeventName)
		if answer == "Tm":
			if event is not None:
				IeventName=event.getEventName()
				tmdbInfo(self.session, IeventName)
		if answer == "Tv":
			if event is not None:
				IeventName=event.getEventName()
				tvdbInfo(self.session, IeventName)
		if answer == "Sp":
			if event is not None:
				IeventName=event.getEventName()
				self.session.open(SeriesPluginInfoScreen, service, event)

	def timerAdd(self):
		if not AutoTimerPresent:
			self.AddConfirmedTimer([None,"NT"])
		else:
			self.session.openWithCallback(self.AddConfirmedTimer, ChoiceBox, title=_("Select timer type..."), list=[(_("Standard timer"), "NT"),(_("AutoTimer"), "AT"),(_("View AutoTimers"), "ATV")])

	def AddConfirmedTimer(self, answer):
		cur = self["epg_list"+str(self.ActiveEPG)].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event is None:
			return
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		answer = answer and answer[1]
		if answer == "AT":
			addAutotimerFromEvent(self.session,evt=event,service=serviceref)
		elif answer == "NT":
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
					cb_func = lambda ret : not ret or self.removeTimer(timer)
					self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
					break
			else:
				newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *parseEvent(event))
				self.session.openWithCallback(self.finishedAdd, TimerEntry, newEntry)
		elif answer == "ATV":
			AutoTimerView(self.session)

	def removeTimer(self, timer):
		timer.afterEvent = AFTEREVENT.NONE
		self.session.nav.RecordTimer.removeEntry(timer)

	def finishedAdd(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList is not None:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)
				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

	def menuClicked(self):
		self.session.open(MerlinPGsetup)

	def findNextBqt(self):
		CurrIdx = 0
		CurrBqt = self.myBqts[self.getActivePrg()]
		self.ActiveEPG = 1
		for CurrIdx in range(self.getActivePrg(),self.chCount):
			NewBqt = self.myBqts[CurrIdx]
			if NewBqt != CurrBqt:
				break
		self["prg_list"].moveToIndex(CurrIdx)
		self.updateInfos()

	def findPrvBqt(self):
		CurrIdx = 0
		CurrBqt = self.myBqts[self.getActivePrg()]
		self.ActiveEPG = 1
		for CurrIdx in range(self.getActivePrg(),-1,-1):
			NewBqt = self.myBqts[CurrIdx]
			if NewBqt != CurrBqt:
				break
		self["prg_list"].moveToIndex(CurrIdx)
		self.updateInfos()

	def go2Primetime(self):
		if self.AutoPrime.isActive():
			self.AutoPrime.stop()
		for xFL in range(1, self.Fields):
			self["epg_list"+str(xFL)].instance.moveSelection(self["epg_list"+str(xFL)].instance.moveTop)
			for i in range(0,(self.Fields*3)):
				self["epg_list"+str(xFL)].foudPrimetime()

	def myhelp(self):
		self.session.open(ShowMe, "/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPG/help.jpg")

	def UserOK(self):
		if config.plugins.MerlinEPG.ZapOnOK.value:
			self.ZapTo()
		else:
			self.showConfirmedInfo([None,"Ei"])

	def editCurTimer(self):
		cur = self["epg_list"+str(self.ActiveEPG)].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event is None:
			return
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				self.session.open(TimerEntry, timer)

	def fullEPGlist(self):
		if epgSpresent:
			self.session.open(myEPGSearch)
		else:
			self.session.open(MessageBox, text=_('EPGsearch is not installed!'), type=MessageBox.TYPE_ERROR)

	def runEpgSeartch(self):
		if epgSpresent:
			cur = self["epg_list"+str(self.ActiveEPG)].getCurrent()
			epg_event = cur[0]
			epg_name = epg_event and epg_event.getEventName() or ''
			self.session.open(EPGSearch, epg_name, False)
		else:
			self.session.open(MessageBox, text=_('EPGsearch is not installed!'), type=MessageBox.TYPE_ERROR)



class Merlin_PGd(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 1920:
		skin = """
		<screen flags="wfNoBorder" name="Merlin_PG" position="0,0" size="1920,1080" title="Merlin Program Guide">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,10" size="300,60" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="310,10" size="300,60" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,10" size="300,60" alphatest="on" />
			<eLabel text="Zap/Exit" position="10,10" size="300,60" zPosition="1" font="Regular;28" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel text="Timer" position="310,10" size="300,60" zPosition="1" font="Regular;28" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel text="Zap" position="610,10" size="300,60" zPosition="1" font="Regular;28" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<ePixmap pixmap="skin_default/icons/left.png" position="920,25" size="70,40" alphatest="on" />
			<ePixmap pixmap="skin_default/icons/right.png" position="1000,25" size="70,40" alphatest="on" />
			<widget source="global.CurrentTime" render="Label" position="1780,20" size="100,38" font="Regular;32" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="1450,20" size="300,38" font="Regular;32" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Format:%A %d. %B</convert>
			</widget>
			<eLabel position="10,80" size="1900,2" backgroundColor="grey" />
			<eLabel text="ChannelList" position="30,115" size="560,75" zPosition="1" font="Regular;65" halign="center" transparent="1" backgroundColor="background" shadowColor="black" shadowOffset="-4,-4" />
			<eLabel position="610,95" size="2,970" backgroundColor="grey" />
			<ePixmap position="20,100" size="580,955" pixmap="skin_default/menu.png" zPosition="-1"/>
			<widget itemHeight="45" name="prg_list" position="50,210" enableWrapAround="1" scrollbarMode="showOnDemand" size="520,810" transparent="1"/>
			<widget itemHeight="40" name="epg_list" position="630,160" enableWrapAround="1" scrollbarMode="showOnDemand" size="1250,880" />
			<widget font="Regular;50" foregroundColor="#fcc000" halign="center" transparent="1" backgroundColor="background" shadowColor="black" shadowOffset="-4,-4" name="currCh" position="640,90" size="1230,60"/>
		</screen>"""
	else:
		skin = """
		<screen name="Merlin_PG" position="center,60" size="1260,650" title="Merlin Program Guide">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="410,5" size="200,40" alphatest="on" />
			<eLabel text="Zap/Exit" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel text="Timer" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel text="Zap" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<ePixmap pixmap="skin_default/icons/left.png" position="620,12" size="60,30" alphatest="on" />
			<ePixmap pixmap="skin_default/icons/right.png" position="690,12" size="60,30" alphatest="on" />
			<widget source="global.CurrentTime" render="Label" position="1130,12" size="80,22" font="Regular;22" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="910,12" size="210,25" font="Regular;22" halign="right" backgroundColor="background" shadowColor="black" shadowOffset="-2,-2" transparent="1">
				<convert type="ClockToText">Format:%A %d. %B</convert>
			</widget>
			<eLabel position="10,50" size="1240,1" backgroundColor="grey" />
			<eLabel text="ChannelList" position="30,70" size="360,40" zPosition="1" font="Regular;35" halign="center" transparent="1" backgroundColor="background" shadowColor="black" shadowOffset="-4,-4" />
			<eLabel position="420,55" size="1,585" backgroundColor="grey" />
			<ePixmap position="10,60" size="400,580" pixmap="skin_default/menu.png" zPosition="-1"/>
			<widget itemHeight="30" name="prg_list" position="30,130" enableWrapAround="1" scrollbarMode="showOnDemand" size="360,480" transparent="1"/>
			<widget itemHeight="27" name="epg_list" position="430,100" enableWrapAround="1" scrollbarMode="showOnDemand" size="820,540" />
			<widget font="Regular;28" foregroundColor="#fcc000" halign="center" transparent="1" backgroundColor="background" shadowColor="black" shadowOffset="-4,-4" name="currCh" position="440,60" size="800,32"/>
		</screen>"""

	def __init__(self, session, servicelist=None):
		Screen.__init__(self, session)
		self.session = session
		self.myServices = []
		self.myBqts = []
		self.list = []
		self.srvList = servicelist
		self.CheckForEPG = eTimer()
		self.CheckForEPG_conn = self.CheckForEPG.timeout.connect(self.CheckItNow)
		self["currCh"] = Label(_("Channel"))
		self["fullEventInfo"] = Label(" ")
		self["prg_list"] = MenuList(self.getChannels())
		self["epg_list"] = EPGList(type=EPG_TYPE_SINGLE, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
		self["actions"] = ActionMap(["OkCancelActions", "EPGSelectActions", "ColorActions", "DirectionActions", "MenuActions", "HelpActions", "InfobarActions"], {
									"ok": self.ok,
									"cancel": self.close,
									"nextBouquet": self.prgDown,
									"prevBouquet": self.prgUp,
									"nextService": self.prgPlus,
									"prevService": self.prgMinus,
									"red": self.ZapTo,
									"green": self.timerAdd,
									"blue": self.ZapForRefresh,
									"yellow": self.go2now,
									"info": self.ok,
									"menu": self.menuClicked,
									"displayHelp": self.myhelp,
									"right": self.right,
									"rightRepeated": self.right,
									"left": self.left,
									"leftRepeated": self.left,
									"up": self.up,
									"upRepeated": self.up,
									"down": self.down,
									"downRepeated": self.down,
									"showMovies": self.editCurTimer,
									"showTv": self.fullEPGlist,
									"showRadio": self.runEpgSeartch
									},-2)
		self.onLayoutFinish.append(self.onLayoutReady)

	def onLayoutReady(self):
		#service = self.session.nav.getCurrentService()
		#info = service and service.info()
		#if (info is not None) and not(config.plugins.MerlinEPG.StartFirst.value):
			#nameROH = info.getName().replace('\xc2\x86', '').replace('\xc2\x87', '')
		if self.srvList:
			service = ServiceReference(self.srvList.getCurrentSelection())
			info = service and service.info()
			nameROH = info and info.getName(service.ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
		else:
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			nameROH = info and info.getName().replace('\xc2\x86', '').replace('\xc2\x87', '')
		if (nameROH is not None) and not(config.plugins.MerlinEPG.StartFirst.value):
		#
			for idx in range(1, len(self.list)):
				name = str(idx) + ". " + nameROH
				if name == self.list[idx-1]:
					break
			self["prg_list"].moveToIndex(idx-1)
		else:
			self["prg_list"].moveToIndex(0)
		self.updateInfos()

	def onSelectionChanged(self):
		curEV = self["epg_list"].getCurrent()
		event = curEV[0]
		ext = event and event.getExtendedDescription() or ""
		self["fullEventInfo"].setText(str(ext))

	def prgUp(self):
		self["prg_list"].down()
		self.updateInfos()

	def prgDown(self):
		self["prg_list"].up()
		self.updateInfos()

	def prgPlus(self):
		self["prg_list"].pageDown()
		self.updateInfos()

	def prgMinus(self):
		self["prg_list"].pageUp()
		self.updateInfos()

	def getChannels(self):
		indx = 0
		serviceHandler = eServiceCenter.getInstance()
		services = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET "bouquets.tv" ORDER BY bouquet'))
		bouquets = services and services.getContent("SN", True)
		for bouquet in bouquets:
			services = serviceHandler.list(eServiceReference(bouquet[0]))
			channels = services and services.getContent("SN", True)
			for channel in channels:
				if not channel[0].startswith("1:64:"):
					indx = indx + 1
					self.list.append(str(indx) + ". " + channel[1].replace('\xc2\x86', '').replace('\xc2\x87', ''))
					self.myServices.append(channel)
					self.myBqts.append(bouquet)
		return self.list

	def updateInfos(self):
		l = self["epg_list"]
		l.recalcEntrySize()
		CurrentPrg = self.myServices[self["prg_list"].getSelectionIndex()]
		self["currCh"].setText(str(CurrentPrg[1]))
		myService = ServiceReference(CurrentPrg[0])
		l.fillSingleEPG(myService)

	def ok(self):
		curEV = self["epg_list"].getCurrent()
		event = curEV[0]
		service = curEV[1]
		if event is not None:
			self.session.open(EventViewSimple, event, service)

	def ZapTo(self):
		if self.srvList==None:
			return
		CurrentPrg = self.myServices[self["prg_list"].getSelectionIndex()]
		CurrentBqt = self.myBqts[self["prg_list"].getSelectionIndex()]
		myService = ServiceReference(CurrentPrg[0])
		myB = ServiceReference(CurrentBqt[0])
		self.srvList.clearPath()
		if self.srvList.bouquet_root != myB.ref:
			self.srvList.enterPath(self.srvList.bouquet_root)
		self.srvList.enterPath(myB.ref)
		self.srvList.setCurrentSelection(myService.ref)
		self.srvList.zap()
		self.close()

	def ZapForRefresh(self):
		if self.srvList==None:
			return
		CurrentPrg = self.myServices[self["prg_list"].getSelectionIndex()]
		myService = ServiceReference(CurrentPrg[0])
		self.session.nav.playService(myService.ref)
		self.CheckForEPG.start(4000, True)

	def CheckItNow(self):
		self.CheckForEPG.stop()
		self.updateInfos()

	def timerAdd(self):
		if not AutoTimerPresent:
			self.AddConfirmedTimer([None,"NT"])
		else:
			self.session.openWithCallback(self.AddConfirmedTimer, ChoiceBox, title=_("Select timer type..."), list=[(_("Standard timer"), "NT"),(_("AutoTimer"), "AT"),(_("View AutoTimers"), "ATV")])

	def AddConfirmedTimer(self, answer):
		cur = self["epg_list"].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event is None:
			return
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		answer = answer and answer[1]
		if answer == "AT":
			addAutotimerFromEvent(self.session,evt=event,service=serviceref)
		elif answer == "NT":
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
					cb_func = lambda ret : not ret or self.removeTimer(timer)
					self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
					break
			else:
				newEntry = RecordTimerEntry(serviceref, checkOldTimers=True, *parseEvent(event))
				self.session.openWithCallback(self.finishedAdd, TimerEntry, newEntry)
		elif answer == "ATV":
			AutoTimerView(self.session)

	def removeTimer(self, timer):
		timer.afterEvent = AFTEREVENT.NONE
		self.session.nav.RecordTimer.removeEntry(timer)
		self["epg_list"+str(self.ActiveEPG)].rebuild()

	def finishedAdd(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList is not None:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)
				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

	def menuClicked(self):
		self.session.open(MerlinPGsetup)

	def go2now(self):
		self["epg_list"].instance.moveSelection(self["epg_list"].instance.moveTop)

	def myhelp(self):
		self.session.open(ShowMe, "/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPG/help.jpg")

	def up(self):
		self["epg_list"].moveUp()

	def down(self):
		self["epg_list"].moveDown()

	def left(self):
		self["epg_list"].instance.moveSelection(self["epg_list"].instance.pageUp)

	def right(self):
		self["epg_list"].instance.moveSelection(self["epg_list"].instance.pageDown)

	def editCurTimer(self):
		cur = self["epg_list"].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event is None:
			return
		eventid = event.getEventId()
		refstr = serviceref.ref.toString()
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				self.session.open(TimerEntry, timer)

	def fullEPGlist(self):
		if epgSpresent:
			self.session.open(myEPGSearch)
		else:
			self.session.open(MessageBox, text=_('EPGsearch is not installed!'), type=MessageBox.TYPE_ERROR)

	def runEpgSeartch(self):
		if epgSpresent:
			cur = self["epg_list"].getCurrent()
			epg_event = cur[0]
			epg_name = epg_event and epg_event.getEventName() or ''
			self.session.open(EPGSearch, epg_name, False)
		else:
			self.session.open(MessageBox, text=_('EPGsearch is not installed!'), type=MessageBox.TYPE_ERROR)



if epgSpresent:
	class myEPGSearchList(EPGSearchList):
		def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None):
			EPGSearchList.__init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None)
			EPGList.__init__(self, type, selChangedCB, timer)
			self.l.setBuildFunc(self.buildEPGSearchEntry)

		def buildEPGSearchEntry(self, service, eventId, beginTime, duration, EventName):
			r2 = self.datetime_rect
			r3 = self.descr_rect
			t = localtime(beginTime)
			serviceref = ServiceReference(service)
			res = [
				None,
				(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r2.height(), 0, RT_HALIGN_LEFT, self.days[t[6]]),
				(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width()-20, r2.height(), 0, RT_HALIGN_LEFT, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
			]
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName + " <" + serviceref.getServiceName()))
			return res



if epgSpresent:
	class myEPGSearch(EPGSearch):
		def __init__(self, session, *args):
			EPGSearch.__init__(self, session)
			Screen.__init__(self, session)
			self.skinName = ["EPGSearch", "EPGSelection"]
			self["list"] = myEPGSearchList(type=EPG_TYPE_SINGLE, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)
			self.onLayoutFinish.append(self.fillMe)

		def fillMe(self):
			self["key_yellow"].hide()
			self["key_green"].hide()
			self["key_blue"].hide()
			self.searchEPG("")

		def searchEPG(self, searchString=None, searchSave=True):
			self.currSearch = ""
			encoding = config.plugins.epgsearch.encoding.value
			epgcache = eEPGCache.getInstance()
			ret = epgcache.search(('RIBDT', 2000, eEPGCache.PARTIAL_TITLE_SEARCH, "", eEPGCache.NO_CASE_CHECK)) or []
			ret.sort(key=lambda x: x[4])
			l = self["list"]
			l.recalcEntrySize()
			l.list = ret
			l.l.setList(ret)

		def blueButtonPressed(self):
			pass

		def yellowButtonPressed(self):
			pass

		def timerAdd(self):
			pass

		def menu(self):
			pass

		def zapTo(self):
			pass

		def timerAdd(self):
			pass
