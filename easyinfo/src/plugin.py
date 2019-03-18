#######################################################################
#
#    EasyInfo for Dreambox-Enigma2
#    Coded by Vali (c)2011
#    Re-worked by dre (c) 2019
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
from Screens.MessageBox import MessageBox
from Screens.InfoBarGenerics import InfoBarPlugins
from Screens.TimerEdit import TimerEditList
from Screens.EpgSelection import EPGSelection
from Screens.EventView import EventViewSimple, EventViewBase
from Screens.ServiceInfo import ServiceInfo
from Screens.ChannelSelection import BouquetSelector
from Screens.TimeDateInput import TimeDateInput
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.EpgList import EPGList, EPG_TYPE_MULTI
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigClock, ConfigYesNo
from Components.Sources.StaticText import StaticText
from Tools.Directories import fileExists, pathExists
from Tools.LoadPixmap import LoadPixmap
from Tools.PiconResolver import PiconResolver
from ServiceReference import ServiceReference
from enigma import eListboxPythonMultiContent, gFont, eTimer, eServiceReference, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP, RT_HALIGN_RIGHT, RT_VALIGN_TOP
from time import localtime, time, mktime
from skin import TemplatedListFonts, componentSizes

EasyInfoBaseInfoBarPlugins__init__ = None
EasyInfoStartOnlyOnce = False
EasyInfoSession = None
EINposition = 0
InfoBar_instance = None

CHOICELIST=[("no", _("Disabled")),
			("eventinfo", _("Event info")),
			("singleepg", _("Single EPG")),
			("multiepg", _("Multi EPG")),
			("easypg", _("EasyPG")),
			("easysel", _("EasySelection")),
			("graphepg", _("Graphik multi-EPG")),
			("merlinepg", _("Merlin EPG")),
			("cooltv", _("Cool-TV")),
			("timers", _("Timerlist")),
			("epgsearch", _("EPG search")),
			("autotimer", _("Autotimer")),
			("channelinfo", _("Channel info")),
			("imdbinfo", _("IMDB info")),
			("epgrefresh", _("EPG refresh")),
			("sleep", _("Sleep timer")),
			]

COLORCHOICELIST = [("singleepg", _("Single EPG")),("multiepg", _("Multi EPG")),("easypg", _("Easy-PG")),("graphepg", _("Graphik multi-EPG")),("merlinepg", _("Merlin EPG")),("cooltv", _("Cool-TV")),("imdbinfo", _("IMDB info"))]
config.plugins.EasyInfo  = ConfigSubsection()
config.plugins.EasyInfo.pos1 = ConfigSelection(default="eventinfo", choices = CHOICELIST)
config.plugins.EasyInfo.pos2 = ConfigSelection(default="singleepg", choices = CHOICELIST)
config.plugins.EasyInfo.pos3 = ConfigSelection(default="merlinepg", choices = CHOICELIST)
config.plugins.EasyInfo.pos4 = ConfigSelection(default="timers", choices = CHOICELIST)
config.plugins.EasyInfo.pos5 = ConfigSelection(default="channelinfo", choices = CHOICELIST)
config.plugins.EasyInfo.pos6 = ConfigSelection(default="no", choices = CHOICELIST)
config.plugins.EasyInfo.pos7 = ConfigSelection(default="no", choices = CHOICELIST)
config.plugins.EasyInfo.pos8 = ConfigSelection(default="no", choices = CHOICELIST)
config.plugins.EasyInfo.pos9 = ConfigSelection(default="no", choices = CHOICELIST)
config.plugins.EasyInfo.pos10 = ConfigSelection(default="no", choices = CHOICELIST)
config.plugins.EasyInfo.pos11 = ConfigSelection(default="no", choices = CHOICELIST)
config.plugins.EasyInfo.showEventInfoFirst = ConfigYesNo(default=False)
config.plugins.EasyInfo.eventViewYellow = ConfigSelection(default="singleepg", choices= COLORCHOICELIST)
config.plugins.EasyInfo.eventViewBlue = ConfigSelection(default="multiepg", choices= COLORCHOICELIST)
config.plugins.EasyInfo.piconPath = ConfigSelection(default="/data/picon_50x30/", choices = [("/data/picon_50x30/", "/data/picon_50x30/"), ("/usr/share/enigma2/picon_50x30/", "/usr/share/enigma2/picon_50x30/"),("/data/picon/", "/data/picon/"), ("/usr/share/enigma2/picon/", "/usr/share/enigma2/picon/")])
config.plugins.EasyInfo.easyPGOK = ConfigSelection(default="info", choices = [("info", _("Event info")), ("zap", _("Just zap")),("exitzap", _("Zap and Exit"))])
config.plugins.EasyInfo.primeTime1 = ConfigClock(default = 63000)
config.plugins.EasyInfo.primeTime2 = ConfigClock(default = 69300)
config.plugins.EasyInfo.primeTime3 = ConfigClock(default = 75600)
config.plugins.EasyInfo.buttonTV = ConfigSelection(default="easysel", choices = [("no", _("Disabled")), ("easysel", _("Easy-Selection")), ("easypg", _("Easy-PG"))])



def Plugins(**kwargs):
	return [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = EasyInfoAutostart)]

def EasyInfoAutostart(reason, **kwargs):
	global EasyInfoBaseInfoBarPlugins__init__
	if "session" in kwargs:
		global EasyInfoSession
		EasyInfoSession = kwargs["session"]
		if EasyInfoBaseInfoBarPlugins__init__ is None:
			EasyInfoBaseInfoBarPlugins__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.__init__ = InfoBarPlugins__init__
		InfoBarPlugins.showInfo = showInfo
		if config.plugins.EasyInfo.buttonTV.value != "no":
			InfoBarPlugins.buttonTV = buttonTV

def InfoBarPlugins__init__(self):
	global EasyInfoStartOnlyOnce
	if not EasyInfoStartOnlyOnce: 
		EasyInfoStartOnlyOnce = True
		global InfoBar_instance
		InfoBar_instance = self
		if config.plugins.EasyInfo.buttonTV.value != "no":
			self["EasyInfoActions"] = ActionMap(["EasyInfoActions"],
				{"info_but": self.showInfo, "tv_but": self.buttonTV}, -1)
		else:
			self["EasyInfoActions"] = ActionMap(["EasyInfoActionsALT"],
				{"info_but": self.showInfo}, -1)
	else:
		InfoBarPlugins.__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.info = None
		if config.plugins.EasyInfo.buttonTV.value != "no":
			InfoBarPlugins.buttonTV = None
	EasyInfoBaseInfoBarPlugins__init__(self)

def showInfo(self):
	if not config.plugins.EasyInfo.showEventInfoFirst.value:
		epglist = [ ]
		service = self.session.nav.getCurrentService()
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		info = service.info()
		ptr=info.getEvent(0)
		if ptr:
			epglist.append(ptr)
		ptr=info.getEvent(1)
		if ptr:
			epglist.append(ptr)
		if epglist:
			self.session.open(EasyInfoEventView, epglist[0], ServiceReference(ref))
		else:
			self.session.open(EasyInfo)
	else:
		self.session.open(EasyInfo)

def buttonTV(self):
	currentService = self.session.nav.getCurrentService()
	currentServiceTimeShift = currentService and currentService.timeshift()
	if currentServiceTimeShift is not None:
		if currentServiceTimeShift.isTimeshiftActive():
			InfoBar_instance.stopTimeshift()
			return
	if InfoBar_instance.servicelist.mode == 1:
		del currentService
		del currentServiceTimeShift
		InfoBar_instance.showTv()
		return
	bouquets = InfoBar_instance.servicelist.getBouquetList()
	if bouquets is None:
		cnt = 0
	else:
		cnt = len(bouquets)
		InfoBarServices = InfoBar_instance.getBouquetServices(InfoBar_instance.servicelist.getRoot())
	if cnt > 1:
		if config.plugins.EasyInfo.buttonTV.value == "easysel":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, InfoBarServices, EasyInfoZapTo, None, EasyInfoChangeBouquetCB))
		elif config.plugins.EasyInfo.buttonTV.value == "easypg":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, InfoBarServices, EasyInfoZapTo, None, EasyInfoChangeBouquetCB))
	elif cnt == 1:
		if config.plugins.EasyInfo.buttonTV.value == "easysel":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, InfoBarServices, EasyInfoZapTo, None, None))
		if config.plugins.EasyInfo.buttonTV.value == "easypg":
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, InfoBarServices, EasyInfoZapTo, None, EasyInfoChangeBouquetCB))

def getPluginByName(sstr):
	sret = " "
	for xs in CHOICELIST:
		if sstr == xs[0]:
			sret = xs[1]
			break
	return sret

class EasyInfoPanelList(MenuList):
	SKIN_COMPONENT_KEY = "EasyInfoPanelList"
	SKIN_COMPONENT_ITEM_HEIGHT = "itemHeight"
	SKIN_COMPONENT_TEXT_WIDTH = "textWidth"
	SKIN_COMPONENT_TEXT_HEIGHT = "textHeight"
	SKIN_COMPONENT_TEXT_XOFFSET = "textXOffset"
	SKIN_COMPONENT_TEXT_YOFFSET = "textYOffset"
	SKIN_COMPONENT_ICON_WIDTH = "iconWidth"
	SKIN_COMPONENT_ICON_HEIGHT = "iconHeight"
	SKIN_COMPONENT_ICON_XOFFSET = "iconXOffset"
	SKIN_COMPONENT_ICON_YOFFSET = "iconYOffset"
	SKIN_COMPONENT_KEYICON_WIDTH = "keyIconWidth"
	SKIN_COMPONENT_KEYICON_HEIGHT = "keyIconHeight"
	SKIN_COMPONENT_KEYICON_XOFFSET = "keyIconXOffset"
	SKIN_COMPONENT_KEYICON_YOFFSET = "keyIconYOffset"
			
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)

		if pathExists('/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/icons/'):
			self.easyInfoIconsPath = '/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/icons/'
		else:
			self.easyInfoIconsPath = '/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/'
		
		sizes = componentSizes[EasyInfoPanelList.SKIN_COMPONENT_KEY]
		self.itemHeight = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_ITEM_HEIGHT, 60)
		self.textWidth = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_TEXT_WIDTH, 300)
		self.textHeight = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_TEXT_HEIGHT, 60)
		self.textXOffset = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_TEXT_XOFFSET, 115)
		self.textYOffset = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_TEXT_YOFFSET, 0)		
		self.iconWidth = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_ICON_WIDTH, 100)
		self.iconHeight = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_ICON_HEIGHT, 50)
		self.iconXOffset = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_ICON_XOFFSET, 5)
		self.iconYOffset = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_ICON_YOFFSET, 5)
		self.keyIconWidth = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_KEYICON_WIDTH, 5)
		self.keyIconHeight = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_KEYICON_HEIGHT, 50)
		self.keyIconXOffset = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_KEYICON_XOFFSET, 0)
		self.keyIconYOffset = sizes.get(EasyInfoPanelList.SKIN_COMPONENT_KEYICON_YOFFSET, 5)
		
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setItemHeight(self.itemHeight)
		self.l.setBuildFunc(self.buildEntry)
		
	def buildEntry(self, func, key):
		res = [ None ]
		
		text = getPluginByName(func)
		
		bpng = LoadPixmap(self.easyInfoIconsPath + "key-" + key + ".png")
		if bpng is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, self.keyIconXOffset, self.keyIconYOffset, self.keyIconWidth, self.keyIconHeight, bpng))
		png = LoadPixmap(self.easyInfoIconsPath + func + ".png")
		if png is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, self.iconXOffset, self.iconYOffset, self.iconWidth, self.iconHeight, png))		
		if not config.plugins.EasyInfo.showEventInfoFirst.value:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.textXOffset, self.textYOffset, self.textWidth, self.textHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, getPluginByName(text)))
		return res	

class EasyInfoConfig(ConfigListScreen, Screen):
	skin = """
		<screen name="EasyInfoConfig" position="center,center" size="700,530" title="EasyInfo settings...">
			<widget name="config" position="5,5" scrollbarMode="showOnDemand" size="690,475"/>
			<eLabel font="Regular;20" foregroundColor="#00ff4A3C" halign="center" position="20,490" size="140,26" text="Cancel"/>
			<eLabel font="Regular;20" foregroundColor="#0056C856" halign="center" position="165,490" size="140,26" text="Save"/>
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("EasyInfo settings..."))
		self.session = session
		self.oldsetting = [config.plugins.EasyInfo.showEventInfoFirst.value, config.plugins.EasyInfo.buttonTV.value]
		list = []
		list.append(getConfigListEntry(_("Replace event info with EasyInfo:"), config.plugins.EasyInfo.showEventInfoFirst ))
		list.append(getConfigListEntry(_("Replace TV-button function:"), config.plugins.EasyInfo.buttonTV ))
		list.append(getConfigListEntry(_("EventInfo yellow button:"), config.plugins.EasyInfo.eventViewYellow ))
		list.append(getConfigListEntry(_("EventInfo blue button:"), config.plugins.EasyInfo.eventViewBlue ))
		list.append(getConfigListEntry(_("OK function in Easy-PG:"), config.plugins.EasyInfo.easyPGOK))
		list.append(getConfigListEntry(_("Easy-PG picons path:"), config.plugins.EasyInfo.piconPath))
		list.append(getConfigListEntry(_("Easy-PG Primetime 1:"), config.plugins.EasyInfo.primeTime1))
		list.append(getConfigListEntry(_("Easy-PG Primetime 2 (main):"), config.plugins.EasyInfo.primeTime2))
		list.append(getConfigListEntry(_("Easy-PG Primetime 3:"), config.plugins.EasyInfo.primeTime3))
		list.append(getConfigListEntry(_("Position 1 (info button):"), config.plugins.EasyInfo.pos1))
		list.append(getConfigListEntry(_("Position 2 (red button):"), config.plugins.EasyInfo.pos2))
		list.append(getConfigListEntry(_("Position 3 (green button):"), config.plugins.EasyInfo.pos3))
		list.append(getConfigListEntry(_("Position 4 (yellow button):"), config.plugins.EasyInfo.pos4))
		list.append(getConfigListEntry(_("Position 5 (blue button):"), config.plugins.EasyInfo.pos5))
		list.append(getConfigListEntry(_("Position 6:"), config.plugins.EasyInfo.pos6))
		list.append(getConfigListEntry(_("Position 7:"), config.plugins.EasyInfo.pos7))
		list.append(getConfigListEntry(_("Position 8:"), config.plugins.EasyInfo.pos8))
		list.append(getConfigListEntry(_("Position 9:"), config.plugins.EasyInfo.pos9))
		list.append(getConfigListEntry(_("Position 10:"), config.plugins.EasyInfo.pos10))
		list.append(getConfigListEntry(_("Position 11:"), config.plugins.EasyInfo.pos11))
		ConfigListScreen.__init__(self, list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {"green": self.save, "red": self.exit, "cancel": self.exit, "yellow": self.exit}, -1)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		if self.oldsetting != [config.plugins.EasyInfo.showEventInfoFirst.value, config.plugins.EasyInfo.buttonTV.value]:
			self.session.open(MessageBox, text = _('You need GUI-restart to load the new settings!'), type = MessageBox.TYPE_INFO)
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

class EasyInfo(Screen):
	if not config.plugins.EasyInfo.showEventInfoFirst.value:
		skin = """
		<screen name="EasyInfo" flags="wfNoBorder" position="center,center" size="500,740" title="Easy Info">
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/bg.png" position="0,0" size="500,740"/>
			<widget name="list" position="70,40" size="360,660" scrollbarMode="showNever" transparent="1" zPosition="2"/>
		</screen>"""
	else:
		skin = """
		<screen name="EventViewWithEasyInfo" backgroundColor="background" flags="wfNoBorder" position="center,0" size="1280,720" title="Easy Info">
			<widget name="list" position="55,30" size="110,660" scrollbarMode="showNever" transparent="1" zPosition="2"/>
			<eLabel backgroundColor="#666666" position="250,359" size="1280,2"/>
			<widget font="Regular;24" foregroundColor="#fcc000" position="630,50" render="Label" size="600,30" source="session.CurrentService" transparent="1" zPosition="1">
				<convert type="ServiceName">Name</convert>
			</widget>
			<widget font="Regular;24" position="250,50" render="Label" size="100,30" source="session.Event_Now" transparent="1" zPosition="1">
				<convert type="EventTime">StartTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget font="Regular;24" noWrap="1" position="250,90" render="Label" size="900,30" source="session.Event_Now" transparent="1" zPosition="1">
				<convert type="EventName">Name</convert>
			</widget>
			<widget font="Regular;22" foregroundColor="#fcc000" position="350,50" halign="right" render="Label" size="130,30" source="session.Event_Now" transparent="1" zPosition="1">
				<convert type="EventTime">Remaining</convert>
				<convert type="RemainingToText">InMinutes</convert>
			</widget>
			<widget font="Regular;24" position="250,400" render="Label" size="100,30" source="session.Event_Next" transparent="1" zPosition="1">
				<convert type="EventTime">StartTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget font="Regular;24" foregroundColor="#aaaaaa" noWrap="1" position="250,370" render="Label" size="900,30" source="session.Event_Next" transparent="1" zPosition="1">
				<convert type="EventName">Name</convert>
			</widget>
			<widget font="Regular;24" foregroundColor="#aaaaaa" position="350,400" render="Label" size="130,30" source="session.Event_Next" transparent="1" zPosition="1">
				<convert type="EventTime">Duration</convert>
				<convert type="ClockToText">InMinutes</convert>
			</widget>
			<widget backgroundColor="#555555" borderColor="#555555" borderWidth="4" position="490,57" render="Progress" size="120,14" source="session.Event_Now" zPosition="2">
				<convert type="EventTime">Progress</convert>
			</widget>
			<widget font="Regular;22" position="250,127" render="Label" size="950,225" source="session.Event_Now" transparent="1" valign="top" zPosition="5">
				<convert type="EventName">ExtendedDescription</convert>
			</widget>
			<widget font="Regular;22" foregroundColor="#aaaaaa" position="250,437" render="Label" size="950,225" source="session.Event_Next" transparent="1" valign="top" zPosition="5">
				<convert type="EventName">ExtendedDescription</convert>
			</widget>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.list = []
		self.__keys = []
		EasyInfoPluginsList = []
		
		if not config.plugins.EasyInfo.showEventInfoFirst.value:
			self.skinName = "EasyInfo"
		else:
			self.skinName = "EventViewWithEasyInfo"
		

		self["key_info"] = StaticText(" ")
		self["key_yellow"] = StaticText(" ")
		self["key_green"] = StaticText(" ")
		self["key_red"] = StaticText(" ")
		self["key_blue"] = StaticText(" ")
		
		self["list"] = EasyInfoPanelList(self.getMenuItems())
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.okPressed,
			"back": self.cancel,
			"menu": self.openConfig,
			"green": self.greenPressed,
			"red": self.redPressed,
			"blue": self.bluePressed,
			"yellow": self.yellowPressed,
			"info": self.infoPressed
		}, -1)

	def getMenuItems(self):
		list = []
		if config.plugins.EasyInfo.pos1.value != "no":
			self["key_info"].setText(_(getPluginByName(config.plugins.EasyInfo.pos1.value)))
			list.append((config.plugins.EasyInfo.pos1.value,"info"))
		if config.plugins.EasyInfo.pos2.value != "no":
			self["key_red"].setText(_(getPluginByName(config.plugins.EasyInfo.pos2.value)))
			list.append((config.plugins.EasyInfo.pos2.value,"red"))
		if config.plugins.EasyInfo.pos3.value != "no":
			self["key_green"].setText(_(getPluginByName(config.plugins.EasyInfo.pos3.value)))
			list.append((config.plugins.EasyInfo.pos3.value,"green"))
		if config.plugins.EasyInfo.pos4.value != "no":
			self["key_yellow"].setText(_(getPluginByName(config.plugins.EasyInfo.pos4.value)))
			list.append((config.plugins.EasyInfo.pos4.value,"yellow"))			
		if config.plugins.EasyInfo.pos5.value != "no":
			self["key_blue"].setText(_(getPluginByName(config.plugins.EasyInfo.pos5.value)))
			list.append((config.plugins.EasyInfo.pos5.value,"blue"))
		if config.plugins.EasyInfo.pos6.value != "no":
			list.append((config.plugins.EasyInfo.pos6.value,"x"))
		if config.plugins.EasyInfo.pos7.value != "no":
			list.append((config.plugins.EasyInfo.pos7.value,"x"))
		if config.plugins.EasyInfo.pos8.value != "no":
			list.append((config.plugins.EasyInfo.pos8.value,"x"))
		if config.plugins.EasyInfo.pos9.value != "no":
			list.append((config.plugins.EasyInfo.pos9.value,"x"))
		if config.plugins.EasyInfo.pos10.value != "no":
			list.append((config.plugins.EasyInfo.pos10.value,"x"))
		if config.plugins.EasyInfo.pos11.value != "no":
			list.append((config.plugins.EasyInfo.pos11.value,"x"))	
			
		return list

	def cancel(self):
		self.close(None)

	def okPressed(self):
		currentSelection = self["list"].l.getCurrentSelection()
		print "answer", currentSelection
		if currentSelection:
			EasyInfoCallbackFunc(currentSelection[0])

	def openConfig(self):
		self.session.openWithCallback(self.configCallback, EasyInfoConfig)

	def configCallback(self):
		self["list"].setList(self.getMenuItems())

	def infoPressed(self):
		self["list"].moveToIndex(0)
		self.okPressed()

	def redPressed(self):
		self["list"].moveToIndex(1)
		self.okPressed()

	def greenPressed(self):
		self["list"].moveToIndex(2)
		self.okPressed()

	def yellowPressed(self):
		self["list"].moveToIndex(3)
		self.okPressed()

	def bluePressed(self):
		self["list"].moveToIndex(4)
		self.okPressed()

def EasyInfoChangeBouquetCB(direction, epg):
	global EINposition
	IBbouquets = InfoBar_instance.servicelist.getBouquetList()
	if EINposition>0 and direction<0:
		EINposition = EINposition - 1
	elif EINposition==0 and direction<0:
		EINposition = len(IBbouquets) - 1
	elif EINposition<(len(IBbouquets)-1) and direction>0:
		EINposition = EINposition + 1
	elif EINposition==(len(IBbouquets)-1) and direction>0:
		EINposition = 0
	InfoBarServices = InfoBar_instance.getBouquetServices(IBbouquets[EINposition][1])
	if InfoBarServices:
		epg.setServices(InfoBarServices)

def EasyInfoZapTo(NewService):
	IBbouquets = InfoBar_instance.servicelist.getBouquetList()
	NewBbouquet = IBbouquets[EINposition][1]
	InfoBar_instance.servicelist.clearPath()
	if InfoBar_instance.servicelist.bouquet_root != NewBbouquet:
		InfoBar_instance.servicelist.enterPath(InfoBar_instance.servicelist.bouquet_root)
	InfoBar_instance.servicelist.enterPath(NewBbouquet)
	InfoBar_instance.servicelist.setCurrentSelection(NewService)
	InfoBar_instance.servicelist.zap()

def EasyInfoCallbackFunc(answer):
	if answer is None: return
	
	if EasyInfoSession is None: return
	
	if not InfoBar_instance: return
	
	if answer == "singleepg":
		ref=InfoBar_instance.servicelist.getCurrentSelection()
		if ref:
			InfoBar_instance.servicelist.savedService = ref
			EasyInfoSession.openWithCallback(InfoBar_instance.servicelist.SingleServiceEPGClosed, EPGSelection, ref, serviceChangeCB = InfoBar_instance.servicelist.changeServiceCB)
	elif answer == "easypg":
		bouquets = InfoBar_instance.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
			InfoBarServices = InfoBar_instance.getBouquetServices(InfoBar_instance.servicelist.getRoot())
		if cnt > 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, InfoBarServices, EasyInfoZapTo, None, EasyInfoChangeBouquetCB))
		elif cnt == 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasyPG, InfoBarServices, EasyInfoZapTo, None, None))
	elif answer == "easysel":
		bouquets = InfoBar_instance.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
			InfoBarServices = InfoBar_instance.getBouquetServices(InfoBar_instance.servicelist.getRoot())
		if cnt > 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, InfoBarServices, EasyInfoZapTo, None, EasyInfoChangeBouquetCB))
		elif cnt == 1:
			InfoBar_instance.dlg_stack.append(InfoBar_instance.session.open(EasySelection, InfoBarServices, EasyInfoZapTo, None, None))
	elif answer == "timers":
		EasyInfoSession.open(TimerEditList)
	elif answer == "multiepg":
		bouquets = InfoBar_instance.servicelist.getBouquetList()
		if bouquets is None:
			cnt = 0
		else:
			cnt = len(bouquets)
		if cnt > 1:
			InfoBar_instance.bouquetSel = EasyInfoSession.openWithCallback(InfoBar_instance.closed, BouquetSelector, bouquets, InfoBar_instance.openBouquetEPG, enableWrapAround=True)
			InfoBar_instance.dlg_stack.append(InfoBar_instance.bouquetSel)
		elif cnt == 1:
			InfoBar_instance.openBouquetEPG(bouquets[0][1], True)
	elif answer == "eventinfo":
		epglist = [ ]
		InfoBar_instance.epglist = epglist
		service = EasyInfoSession.nav.getCurrentService()
		ref = EasyInfoSession.nav.getCurrentlyPlayingServiceReference()
		info = service.info()
		ptr=info.getEvent(0)
		if ptr:
			epglist.append(ptr)
		ptr=info.getEvent(1)
		if ptr:
			epglist.append(ptr)
		if epglist:
			EasyInfoSession.open(EventViewSimple, epglist[0], ServiceReference(ref), InfoBar_instance.eventViewCallback)
	elif answer == "merlinepg":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPG/plugin.pyo"):
			from Plugins.Extensions.MerlinEPG.plugin import Merlin_PGII, Merlin_PGd
			if config.plugins.MerlinEPG.Columns.value:
				EasyInfoSession.open(Merlin_PGII, InfoBar_instance.servicelist)
			else:
				EasyInfoSession.open(Merlin_PGd, InfoBar_instance.servicelist)
		else:
			EasyInfoSession.open(MessageBox, text = _('MerlinEPG is not installed!'), type = MessageBox.TYPE_INFO)
	elif answer == "autotimer":
		try:
			from Plugins.Extensions.AutoTimer.plugin import main as AutoTimerView
			AutoTimerView(EasyInfoSession)
		except ImportError as ie:
			EasyInfoSession.open(MessageBox, text = _('Autotimer is not installed!'), type = MessageBox.TYPE_INFO)
	elif answer == "epgsearch":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EPGSearch/plugin.pyo"):
			from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
			service = EasyInfoSession.nav.getCurrentService()
			info = service.info()
			epg_event=info.getEvent(0)
			if epg_event:
				epg_name = epg_event and epg_event.getEventName() or ''
				EasyInfoSession.open(EPGSearch, epg_name, False)
		else:
			EasyInfoSession.open(MessageBox, text = _('EPGsearch is not installed!'), type = MessageBox.TYPE_INFO)
	elif answer == "channelinfo":
		EasyInfoSession.open(ServiceInfo, InfoBar_instance.servicelist.getCurrentSelection())
	elif answer == "imdbinfo":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo"):
			from Plugins.Extensions.IMDb.plugin import IMDB
			service = EasyInfoSession.nav.getCurrentService()
			info = service.info()
			epg_event=info.getEvent(0)
			if epg_event:
				IeventName = epg_event.getEventName()
				EasyInfoSession.open(IMDB, IeventName)
		else:
			EasyInfoSession.open(MessageBox, text = _('IMDB is not installed!'), type = MessageBox.TYPE_INFO)
	elif answer == "graphepg":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/GraphMultiEPG/plugin.pyo"):
			from Plugins.Extensions.GraphMultiEPG.plugin import main as gmepgmain
			gmepgmain(EasyInfoSession, InfoBar_instance.servicelist)
		else:
			EasyInfoSession.open(MessageBox, text = _('GraphMultiEPG is not installed!'), type = MessageBox.TYPE_INFO)
	elif answer == "epgrefresh":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EPGRefresh/plugin.pyo"):
			from Plugins.Extensions.EPGRefresh.plugin import main as epgrefmain
			epgrefmain(EasyInfoSession)
		else:
			EasyInfoSession.open(MessageBox, text = _('EPGRefresh is not installed!'), type = MessageBox.TYPE_INFO)
	elif answer == "cooltv":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/CoolTVGuide/plugin.pyo"):
			from Plugins.Extensions.CoolTVGuide.plugin import main as ctvmain
			ctvmain(EasyInfoSession, InfoBar_instance.servicelist)
		else:
			EasyInfoSession.open(MessageBox, text = _('CoolTVGuide is not installed!'), type = MessageBox.TYPE_INFO)
	elif answer == "sleep":
		from Screens.SleepTimerEdit import SleepTimerEdit
		EasyInfoSession.open(SleepTimerEdit)
	else:
		EasyInfoSession.open(MessageBox, text = _('This function is yet not available!'), type = MessageBox.TYPE_INFO)

class EasyInfoEventView(Screen, EventViewBase):
	def __init__(self, session, Event, Ref, callback=None, singleEPGCB=None, multiEPGCB=None):
		Screen.__init__(self, session)
		self.session = session
		self.skinName = "EventView"
		
		EventViewBase.__init__(self, Event, Ref, callback=InfoBar_instance.eventViewCallback)
		
		self["key_yellow"].setText(_(getPluginByName(config.plugins.EasyInfo.eventViewYellow.value)))
		self["key_blue"].setText(_(getPluginByName(config.plugins.EasyInfo.eventViewBlue.value)))
		self["key_red"].setText(_("Similar"))
		
		self["epgactions"] = ActionMap(["EventViewEPGActions", "EPGSelectActions",  "EventViewActions"],
			{
				"openSingleServiceEPG": self.singleEPGCB,
				"openMultiServiceEPG": self.multiEPGCB,
				"openSimilarList": self.openSimilarList,
				"info": self.exit,
				"pageUp": self.pageUp,
				"pageDown": self.pageDown,
				"prevEvent": self.prevEvent,
				"nextEvent": self.nextEvent
			},-1)

	def openSimilarList(self):
		self.hide()
		EasyInfoCallbackFunc("epgsearch")
		self.close()

	def singleEPGCB(self):
		self.hide()
		EasyInfoCallbackFunc(config.plugins.EasyInfo.eventViewYellow.value)
		self.close()

	def multiEPGCB(self):
		self.hide()
		EasyInfoCallbackFunc(config.plugins.EasyInfo.eventViewBlue.value)
		self.close()

	def setEvent(self, event):
		self.event = event
		if event is None:
			return
		text = event.getEventName()
		short = event.getShortDescription()
		ext = event.getExtendedDescription()
		if short and short != text:
			text += '\n\n' + short
		if ext:
			if text:
				text += '\n\n'
			text += ext
		self.setTitle(event.getEventName())
		self["epg_description"].setText(text)
		self["datetime"].setText(event.getBeginTimeString())
		self["duration"].setText(_("%d min")%(event.getDuration()/60))
		self["key_red"].setText(_("Similar"))
		serviceref = self.currentService
		eventid = self.event.getEventId()
		refstr = serviceref.ref.toString()
		isRecordEvent = False
		for timer in self.session.nav.RecordTimer.timer_list:
			if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				isRecordEvent = True
				break
		if isRecordEvent and self.key_green_choice != self.REMOVE_TIMER:
			self["key_green"].setText(_("Remove timer"))
			self.key_green_choice = self.REMOVE_TIMER
		elif not isRecordEvent and self.key_green_choice != self.ADD_TIMER:
			self["key_green"].setText(_("Add timer"))
			self.key_green_choice = self.ADD_TIMER

	def exit(self):
		self.hide()
		self.session.open(EasyInfo)
		self.close()

class EasyInfoEventList(EPGList):
	SKIN_COMPONENT_KEY = "EasyInfoEventList"
	SKIN_COMPONENT_CHANNEL_WIDTH = "ChannelWidth" # width for the first column with channelname or picon
	SKIN_COMPONENT_TIME_WIDTH = "TimeWidth" # width for the time information
	SKIN_COMPONENT_TIME_FUTURE_INDICATOR_WIDTH = "TimeFutureIndicatorWidth" # width for the ">"
	SKIN_COMPONENT_TIME_OFFSET = "TimeOffset" # y position of time information including indicator
	SKIN_COMPONENT_REMAINING_TIME_WIDTH = "RemainingTimeWidth" # width of remaining time information (below progress bar)
	SKIN_COMPONENT_EVENTNAME_WIDTH = "EventNameWidth" # width of eventname
	SKIN_COMPONENT_EVENTNAME_OFFSET = "EventNameOffset" # y position of eventname
	SKIN_COMPONENT_ITEM_HEIGHT = "ItemHeight" # height of row
	SKIN_COMPONENT_PROGRESSBAR_WIDTH = "ProgressBarWidth" # width of progress bar
	SKIN_COMPONENT_PROGRESSBAR_HEIGHT = "ProgressBarHeight" # height of progress bar
	SKIN_COMPONENT_CHANNEL_OFFSET = "ChannelOffset" # offset applied to the first event column
	SKIN_COMPONENT_REC_OFFSET = "RecOffset" # offset applied when a timer exists for the event
	SKIN_COMPONENT_REC_ICON_SIZE = "RecIconSize" # size of record icon

	def __init__(self, type=EPG_TYPE_MULTI, selChangedCB=None, timer = None, hasChannelInfo=True):
		EPGList.__init__(self, type, selChangedCB, timer)
		
		sizes = componentSizes[EasyInfoEventList.SKIN_COMPONENT_KEY]
		self.channelWidth = sizes.get(EasyInfoEventList.SKIN_COMPONENT_CHANNEL_WIDTH, 120)
		self.timeWidth = sizes.get(EasyInfoEventList.SKIN_COMPONENT_TIME_WIDTH, 70)
		self.timeIndicatorWidth = sizes.get(EasyInfoEventList.SKIN_COMPONENT_TIME_FUTURE_INDICATOR_WIDTH, 10)
		self.eventNameWidth = sizes.get(EasyInfoEventList.SKIN_COMPONENT_EVENTNAME_WIDTH, 460)
		self.eventNameYOffset = sizes.get(EasyInfoEventList.SKIN_COMPONENT_EVENTNAME_OFFSET, 1)
		self.timeYOffset = sizes.get(EasyInfoEventList.SKIN_COMPONENT_TIME_OFFSET, 3)
		self.itemHeight = sizes.get(EasyInfoEventList.SKIN_COMPONENT_ITEM_HEIGHT, 50)
		self.recOffset = sizes.get(EasyInfoEventList.SKIN_COMPONENT_REC_OFFSET, 25)
		self.channelOffset = sizes.get(EasyInfoEventList.SKIN_COMPONENT_CHANNEL_OFFSET, 120)
		self.progressBarWidth = sizes.get(EasyInfoEventList.SKIN_COMPONENT_PROGRESSBAR_WIDTH, 40)
		self.progressBarHeight = sizes.get(EasyInfoEventList.SKIN_COMPONENT_PROGRESSBAR_HEIGHT, 8)
		self.remainingTimeWidth = sizes.get(EasyInfoEventList.SKIN_COMPONENT_REMAINING_TIME_WIDTH, 70)
		self.recIconSize = sizes.get(EasyInfoEventList.SKIN_COMPONENT_REC_ICON_SIZE, 16)
		self.piconWidth = 0
		self.piconHeight = 0

		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setFont(1, gFont(tlf.face(tlf.SMALL), tlf.size(tlf.SMALL)))
		self.l.setFont(2, gFont(tlf.face(tlf.SMALLER), tlf.size(tlf.SMALLER)))
		
		self.l.setItemHeight(self.itemHeight)
		self.l.setBuildFunc(self.buildMultiEntry)
		
		self.hasChannelInfo = hasChannelInfo
		self.nameCache = { }

	def getPicon(self, sRef):
		pngname = PiconResolver.getPngName(sRef, self.nameCache, self.findPicon)
		if fileExists(pngname):
			return LoadPixmap(cached = True, path = pngname)
		else:
			return None
			
	def findPicon(self, sRef):
		pngname = "%s%s.png" % (config.plugins.EasyInfo.piconPath.value, sRef)
		if not fileExists(pngname):
			pngname = ""
		return pngname

	def buildMultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name):
		(clock_pic, rec) = self.getPixmapForEntry(service, eventId, beginTime, duration)
		res = [ None ]
		
		channelOffset = 0
		recOffset = 0
		
		flagValue = RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP
		if self.hasChannelInfo:
			channelOffset = self.channelOffset
			
		if EventName is not None and len(EventName) > 60:
			flagValue = RT_HALIGN_LEFT|RT_VALIGN_TOP|RT_WRAP
		
		if self.hasChannelInfo:
			picon = self.getPicon(service)
			if picon is not None:
				if self.piconWidth == 0:
					self.piconWidth = picon.size().width()
				if self.piconHeight == 0:
					self.piconHeight = picon.size().height()
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, (self.channelWidth-self.piconWidth)/2, (self.itemHeight-self.piconHeight)/2, self.piconWidth, self.piconHeight, picon))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, self.channelWidth, self.itemHeight, 1, RT_HALIGN_CENTER|RT_VALIGN_CENTER|RT_WRAP, service_name))
		
		if rec:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, self.timeIndicatorWidth+self.timeWidth+channelOffset, (self.itemHeight-self.recIconSize)/2, self.recIconSize, self.recIconSize, clock_pic)) 
			recOffset = self.recOffset
				
		if beginTime is not None:
			if nowTime < beginTime:
				begin = localtime(beginTime)
				end = localtime(beginTime+duration)
				
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, channelOffset, self.timeYOffset, self.timeIndicatorWidth, self.itemHeight-2*self.timeYOffset, 1, RT_HALIGN_RIGHT, '>'),
					(eListboxPythonMultiContent.TYPE_TEXT, self.timeIndicatorWidth+channelOffset, self.timeYOffset, self.timeWidth, self.itemHeight-2*self.timeYOffset, 1, RT_HALIGN_LEFT, "%02d.%02d\n%02d.%02d"%(begin[3],begin[4],end[3],end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, self.timeIndicatorWidth+self.timeWidth+channelOffset+recOffset, self.eventNameYOffset, self.eventNameWidth-recOffset, self.itemHeight-2*self.eventNameYOffset, 0, flagValue, EventName)
				))
			else:
				percent = (nowTime - beginTime)*100/duration
				remaining = ((beginTime+duration)-nowTime)
				
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, (self.remainingTimeWidth-self.progressBarWidth)/2+channelOffset, (self.itemHeight/2-self.progressBarHeight)/2, self.progressBarWidth, self.progressBarHeight, percent),
					(eListboxPythonMultiContent.TYPE_TEXT, self.timeIndicatorWidth+channelOffset, self.itemHeight/2, self.remainingTimeWidth, self.itemHeight/2, 1, RT_HALIGN_LEFT, "+%d:%02d" % (remaining/3600, (remaining/60)-((remaining /3600)*60))),
					(eListboxPythonMultiContent.TYPE_TEXT, self.timeIndicatorWidth+self.timeWidth+channelOffset+recOffset, self.eventNameYOffset, self.eventNameWidth-recOffset, self.itemHeight-2*self.eventNameYOffset, 0, flagValue, EventName)
				))
		return res

	def moveToService(self,serviceref):
		if not serviceref:
			return
		index = 0
		refstr = serviceref.toString()
		for x in self.list:
			if x[1] == refstr:
				self.instance.moveSelectionTo(index)
				break
			index += 1
		if x[1] != refstr:
			self.instance.moveSelectionTo(0)
			
class EasyPG(EPGSelection, Screen):
	skin = """
		<screen name="NewEasyPG" backgroundColor="#101220" flags="wfNoBorder" position="center,0" size="1280,720" title="Easy PG">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="60,35" size="660,650" zPosition="-1"/>
			<widget font="Regular;20" position="785,30" render="Label" size="202,25" source="global.CurrentTime" transparent="1" zPosition="1">
				<convert type="ClockToText">Format:%a %d. %b   %H:%M</convert>
			</widget>
			<widget backgroundColor="#ff000000" position="755,125" render="Pig" size="497,280" source="session.VideoPicture" zPosition="1"/>
			<widget foregroundColor="#fcc000" font="Regular;20" name="date" position="755,415" size="100,25" transparent="1"/>
			<widget name="list" position="60,35" scrollbarMode="showNever" size="660,650" transparent="1"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-red.png" position="785,65" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-green.png" position="785,90" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-yellow.png" position="1005,65" size="5,20"/>
			<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/key-blue.png" position="1005,90" size="5,20"/>
			<eLabel font="Regular;18" position="800,63" size="150,25" text="Similar" transparent="1"/>
			<eLabel font="Regular;18" position="800,90" size="150,25" text="Timer" transparent="1"/>
			<eLabel font="Regular;18" position="1015,63" size="150,25" text="Back" transparent="1"/>
			<eLabel font="Regular;18" position="1015,90" size="150,25" text="Next" transparent="1"/>
			<widget font="Regular;20" halign="right" position="870,415" render="Label" size="70,25" source="Event" transparent="1" zPosition="1">
				<convert type="EventTime">StartTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<eLabel font="Regular;18" position="945,415" size="10,25" text="-" transparent="1"/>
			<widget font="Regular;20" position="955,415" render="Label" size="70,25" source="Event" transparent="1" zPosition="1">
				<convert type="EventTime">EndTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget font="Regular;20" position="1050,415" render="Label" size="171,25" source="Event" transparent="1" zPosition="1">
			<convert type="EventTime">Duration</convert>
				<convert type="ClockToText">InMinutes</convert>
			</widget>
			<widget font="Regular;20" position="755,445" render="Label" size="480,25" source="Event" transparent="1" zPosition="2" noWrap="1">
				<convert type="EventName">ShortDescription</convert>
			</widget>
			<widget font="Regular;18" position="755,475" render="Label" size="480,210" source="Event" transparent="1" zPosition="3">
				<convert type="EventName">ExtendedDescription</convert>
			</widget>
		</screen>"""

	def __init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
		Screen.__init__(self, session)
		EPGSelection.__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
		EPGSelection.skinName = "NewEasyPG"
		self.skinName = "NewEasyPG"
		
		global EINposition
		EINposition = 0
		allbouq = InfoBar_instance.servicelist.getBouquetList()
		for newpos in range(0, len(allbouq)):
			if InfoBar_instance.servicelist.getRoot() == allbouq[newpos][1]:
				EINposition = newpos
				break
		
		self.initPrimeTime = False
		self.session = session

		self.primeTimeHour = config.plugins.EasyInfo.primeTime2.value[0]
		self.primeTimeMinute = config.plugins.EasyInfo.primeTime2.value[1]
		
		self["list"] = EasyInfoEventList(type = EPG_TYPE_MULTI, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer)

		self.refreshTimer = eTimer()
		self.refreshTimer_conn = self.refreshTimer.timeout.connect(self.refreshEPG)
		
		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions", "NumberActions", "InfobarActions"],
			{
				"cancel": self.closeScreen,
				"ok": self.okPressed,
				"timerAdd": self.timerAdd,
				"yellow": self.yellowButtonPressed,
				"blue": self.blueButtonPressed,
				"info": self.infoKeyPressed,
				"red": self.redButtonPressed,
				"input_date_time": self.openContextMenu,
				"nextBouquet": self.nextBouquet,
				"prevBouquet": self.prevBouquet,
				"nextService": self.goToPrimeTimeNextDay,
				"prevService": self.goToPrimeTimePreviousDay,
				"showMovies": self.enterDateTime,
				"showTv": self.zapTo,
				"showRadio": self.zapAndRefresh,
				"0": self.goToCurrentTime,
				"1": self.setPrimeTime1,
				"2": self.setPrimeTime2,
				"3": self.setPrimeTime3
			},-1)

	def closeScreen(self):
		self.close(True)

	def goToCurrentTime(self):
		self["list"].fillMultiEPG(self.services, -1)
		self.initPrimeTime = False

	def setNewPrimeTime(self):
		today = localtime()
		primetime = (today[0],today[1],today[2],self.primeTimeHour,self.primeTimeMinute,0,today[6],today[7],0)
		self.ask_time = int(mktime(primetime))
		self.initPrimeTime = True
		if self.ask_time > int(mktime(today)):
			self["list"].fillMultiEPG(self.services, self.ask_time)

	def okPressed(self):
		if  config.plugins.EasyInfo.easyPGOK.value == "exitzap":
			self.zapTo()
			self.close(True)
		elif config.plugins.EasyInfo.easyPGOK.value == "zap":
			self.zapTo()
		else:
			self.infoKeyPressed()

	def redButtonPressed(self):
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EPGSearch/plugin.pyo"):
			from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
			epg_event = self["list"].getCurrent()[0]
			if epg_event:
				epg_name = epg_event and epg_event.getEventName() or ''
				self.session.open(EPGSearch, epg_name, False)
		else:
			self.session.open(MessageBox, text = _('EPGsearch is not installed!'), type = MessageBox.TYPE_INFO)

	def goToPrimeTimeNextDay(self):
		if not self["list"].getCurrent()[0]:
			return
		today = localtime()
		if not self.initPrimeTime:
			primetime = (today[0],today[1],today[2],self.primeTimeHour,self.primeTimeMinute,0,today[6],today[7],0)
			self.ask_time = int(mktime(primetime))
			self.initPrimeTime = True
			if self.ask_time < int(mktime(today)):
				self.ask_time = self.ask_time + 86400
		else:
			self.ask_time = self.ask_time + 86400
		self["list"].fillMultiEPG(self.services, self.ask_time)

	def goToPrimeTimePreviousDay(self):
		today = localtime()
		if not self.initPrimeTime:
			primetime = (today[0],today[1],today[2],self.primeTimeHour,self.primeTimeMinute,0,today[6],today[7],0)
			self.ask_time = int(mktime(primetime))
			self.initPrimeTime = True
		else:
			self.ask_time = self.ask_time - 86400
		if self.ask_time > int(mktime(today)):
			self["list"].fillMultiEPG(self.services, self.ask_time)
		else:
			self["list"].fillMultiEPG(self.services, -1)
			self.initPrimeTime = False

	def setPrimeTime1(self):
		self.primeTimeHour = config.plugins.EasyInfo.primeTime1.value[0]
		self.primeTimeMinute = config.plugins.EasyInfo.primeTime1.value[1]
		self.setNewPrimeTime()

	def setPrimeTime2(self):
		self.primeTimeHour = config.plugins.EasyInfo.primeTime2.value[0]
		self.primeTimeMinute = config.plugins.EasyInfo.primeTime2.value[1]
		self.setNewPrimeTime()

	def setPrimeTime3(self):
		self.primeTimeHour = config.plugins.EasyInfo.primeTime3.value[0]
		self.primeTimeMinute = config.plugins.EasyInfo.primeTime3.value[1]
		self.setNewPrimeTime()

	def openContextMenu(self):
		self.session.open(EasyInfoConfig)

	def zapAndRefresh(self):
		self.zapTo()
		self.refreshTimer.start(4000, True)

	def refreshEPG(self):
		self.refreshTimer.stop()
		self.GoFirst()

class EasySelection(EPGSelection, Screen):
	skin = """
		<screen name="NewEasySelection" backgroundColor="background" flags="wfNoBorder" position="center,0" size="1240,720" title="Easy Selection">
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="20,35" size="660,650" zPosition="-1" scale="stretch" />
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyInfo/lines.png" position="680,35" size="540,650" zPosition="-1" scale="stretch" />
			<widget name="list" position="20,35" scrollbarMode="showNever" size="660,650" transparent="1"/>
			<widget name="listNext" position="680,35" scrollbarMode="showNever" size="540,650" transparent="1"/>
		</screen>"""

	def __init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
		Screen.__init__(self, session)
		EPGSelection.__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
		EPGSelection.skinName = "NewEasySelection"
		self.skinName = "NewEasySelection"
		
		global EINposition
		EINposition = 0
		bouquets = InfoBar_instance.servicelist.getBouquetList()
		for pos in range(0, len(bouquets)):
			if InfoBar_instance.servicelist.getRoot() == bouquets[pos][1]:
				EINposition = pos
				break
		
		self.session = session

		self["list"] = EasyInfoEventList(type = EPG_TYPE_MULTI, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer)
		self["listNext"] = EasyInfoEventList(type = EPG_TYPE_MULTI, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer, hasChannelInfo=False)

		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions", "DirectionActions"],
			{
				"cancel": self.closeScreen,
				"ok": self.okPressed,
				"info": self.infoKeyPressed,
				"nextBouquet": self.nextBouquet,
				"prevBouquet": self.prevBouquet,
				"right": self.rightPressed,
				"rightRepeated": self.rightPressed,
				"left": self.leftPressed,
				"leftRepeated": self.leftPressed,
				"up": self.upPressed,
				"upRepeated": self.upPressed,
				"down": self.downPressed,
				"downRepeated": self.downPressed,
				"nextService": self.setModePrimeTime,
				"prevService": self.setModeNowNext,
			},-1)
		
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self["listNext"].fillMultiEPG(self.services, -1)
		self["listNext"].moveToService(self.session.nav.getCurrentlyPlayingServiceReference())
		self["listNext"].updateMultiEPG(1)

	def closeScreen(self):
		self.close(True)

	def okPressed(self):
		self.zapTo()
		self.close(True)

	def leftPressed(self):
		self["list"].instance.moveSelection(self["list"].instance.pageUp)
		self["listNext"].instance.moveSelection(self["list"].instance.pageUp)

	def rightPressed(self):
		self["list"].instance.moveSelection(self["list"].instance.pageDown)
		self["listNext"].instance.moveSelection(self["list"].instance.pageDown)

	def upPressed(self):
		self["list"].moveUp()
		self["listNext"].moveUp()

	def downPressed(self):
		self["list"].moveDown()
		self["listNext"].moveDown()

	def nextBouquet(self):
		if self.bouquetChangeCB:
			self.bouquetChangeCB(1, self)
			self.layoutFinished()

	def prevBouquet(self):
		if self.bouquetChangeCB:
			self.bouquetChangeCB(-1, self)
			self.layoutFinished()

	def setModePrimeTime(self):
		today = localtime()
		pt = (today[0],today[1],today[2],config.plugins.EasyInfo.primeTime2.value[0],config.plugins.EasyInfo.primeTime2.value[1],0,today[6],today[7],0)
		ask_time = int(mktime(pt))
		if ask_time > int(mktime(today)):
			self["list"].fillMultiEPG(self.services, ask_time)
			pt = (today[0],today[1],today[2],config.plugins.EasyInfo.primeTime3.value[0],config.plugins.EasyInfo.primeTime3.value[1],0,today[6],today[7],0)
			ask_time = int(mktime(pt))
			self["listNext"].fillMultiEPG(self.services, ask_time)

	def setModeNowNext(self):
		self["list"].fillMultiEPG(self.services, -1)
		self["listNext"].fillMultiEPG(self.services, -1)
		self["listNext"].updateMultiEPG(1)

	def infoKeyPressed(self):
		cur = self["list"].getCurrent()
		service = cur[1].ref.toString()
		ref = eServiceReference(service)
		if ref:
			InfoBar_instance.servicelist.savedService = ref
			self.session.openWithCallback(InfoBar_instance.servicelist.SingleServiceEPGClosed, EPGSelection, ref, serviceChangeCB = InfoBar_instance.servicelist.changeServiceCB)
