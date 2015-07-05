
#  YTTrailer
#
#  Coded by Dr.Best (c) 2011
#  Support: www.dreambox-tools.info
#
#  All Files of this Software are licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License if not stated otherwise in a Files Head. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.

#  Additionally, this plugin may only be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.

from __init__ import decrypt_block, validate_cert, read_random, rootkey, l2key
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Components.Sources.StaticText import StaticText
from Components.GUIComponent import GUIComponent
from enigma import eServiceReference,  RT_WRAP, RT_VALIGN_CENTER, RT_HALIGN_LEFT, gFont, eListbox, eListboxPythonMultiContent, eTPM

from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry, configfile, ConfigText, ConfigInteger, ConfigYesNo
from Components.ConfigList import ConfigListScreen

from Screens.InfoBarGenerics import InfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarMoviePlayerSummarySupport
from Components.ServiceEventTracker import InfoBarBase

# for localized messages
from . import _

config.plugins.yttrailer = ConfigSubsection()
config.plugins.yttrailer.show_in_extensionsmenu = ConfigYesNo(default = False)
config.plugins.yttrailer.best_resolution = ConfigSelection(default="2", choices = [("0", _("1080p")),("1", _("720p")), ("2", _("No HD streaming"))])
config.plugins.yttrailer.ext_descr = ConfigText(default="german", fixed_size = False)
config.plugins.yttrailer.max_results =  ConfigInteger(5,limits = (1, 10))
config.plugins.yttrailer.close_player_with_exit =  ConfigYesNo(default = False)

from Screens.EventView import EventViewBase
baseEventViewBase__init__ = None

from Screens.EpgSelection import EPGSelection
baseEPGSelection__init__ = None
etpm = eTPM()

from Plugins.SystemPlugins.TubeLib.youtube.Base import buildYoutube
from Plugins.SystemPlugins.TubeLib.youtube.Search import Search
from Plugins.SystemPlugins.TubeLib.youtube.Videos import Videos

def autostart(reason, **kwargs):
	global l2key
	l2cert = etpm.getData(eTPM.DT_LEVEL2_CERT)
	if l2cert:
		l2key = validate_cert(l2cert, rootkey)
		if l2key:
			global baseEventViewBase__init__, baseEPGSelection__init__
			if baseEventViewBase__init__ is None:
				baseEventViewBase__init__ = EventViewBase.__init__
			EventViewBase.__init__ = EventViewBase__init__
			EventViewBase.showTrailer = showTrailer
			EventViewBase.showTrailerList = showTrailerList
			EventViewBase.showConfig = showConfig

			if baseEPGSelection__init__ is None:
				baseEPGSelection__init__ = EPGSelection.__init__
			EPGSelection.__init__ = EPGSelection__init__
			EPGSelection.showTrailer = showTrailer
			EPGSelection.showConfig = showConfig
			EPGSelection.showTrailerList = showTrailerList


def setup(session,**kwargs):
	session.open(YTTrailerSetup)

def Plugins(**kwargs):

	list = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)]
	list.append(PluginDescriptor(name="YTTrailer Setup", description=_("YouTube-Trailer Setup"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=setup, icon="YTtrailer.png"))
	if config.plugins.yttrailer.show_in_extensionsmenu.value:
		list.append(PluginDescriptor(name="YTTrailer Setup", description=_("YouTube-Trailer Setup"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=setup, icon="YTtrailer.png"))
	return list

def EventViewBase__init__(self, Event, Ref, callback=None, similarEPGCB=None):
	baseEventViewBase__init__(self, Event, Ref, callback, similarEPGCB)
	self["trailerActions"] = ActionMap(["InfobarActions", "InfobarTeletextActions"],
	{
		"showTv": self.showTrailer,
		"showRadio": self.showTrailerList,
		"startTeletext": self.showConfig
	})


def EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
	self["trailerActions"] = ActionMap(["InfobarActions", "InfobarTeletextActions"],
	{
		"showTv": self.showTrailer,
		"showRadio": self.showTrailerList,
		"startTeletext": self.showConfig
	})

def showConfig(self):
	self.session.open(YTTrailerSetup)

def showTrailer(self):
	eventname = ""
	if isinstance(self, EventViewBase):
		if self.event:
			eventname = self.event.getEventName()
	else:
		cur = self["list"].getCurrent()
		if cur and cur[0]:
			event = cur[0]
			eventname = event.getEventName()

	ytTrailer = YTTrailer(self.session)
	ytTrailer.showTrailer(eventname)

def showTrailerList(self):
	eventname = ""
	if isinstance(self, EventViewBase):
		if self.event:
			eventname = self.event.getEventName()
	else:
		cur = self["list"].getCurrent()
		if cur and cur[0]:
			event = cur[0]
			eventname = event.getEventName()

	self.session.open(YTTrailerList, eventname)

class YTTrailer:
	def __init__(self, session):
		self.session = session
		self._youtube = None
		self._query = None
		self.l3cert = etpm.getData(eTPM.DT_LEVEL3_CERT)

	def showTrailer(self, eventname):
		if eventname:
			self.getYTFeeds(eventname, 1)

	def _gotYTFeeds(self, success, videos, data):
		if videos:
			ref = self.setServiceReference(videos[0])
			if ref:
				from twisted.internet import reactor
				reactor.callLater(0, self.session.open, TrailerPlayer, ref)

	def getYTFeeds(self, eventname, max_results):
		if not self._youtube:
			self._youtube = buildYoutube()
		if int(config.plugins.yttrailer.best_resolution.value) <= 1:
			shd = "HD"
		else:
			shd = ""
		q = "%s %s Trailer %s" % (eventname, shd, config.plugins.yttrailer.ext_descr.value)
		search = Search(self._youtube)
		self._query = search.list(self._gotYTFeeds, searchTerm=q, maxResults=max_results)

	def setServiceReference(self, entry):
		url = entry.url
		if url:
			ref = eServiceReference(4097,0,url)
			ref.setName(entry.title)
		else:
			ref = None
		return ref

class YTTrailerList(Screen, YTTrailer):

	skin = """
		<screen name="YTTrailerList" position="center,center" size="580,436" title="YT Trailer-List" backgroundColor="#ff000000">
			<widget name="list" position="0,0" size="580,436" />
		</screen>"""

	def __init__(self, session, eventname):
		Screen.__init__(self, session)
		YTTrailer.__init__(self, session)

		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.okPressed,
			"back": self.close
		}, -1)

		self.eventName = eventname
		self["list"] = TrailerList()
		self.onFirstExecBegin.append(self.startRun)

	def _gotYTFeeds(self, success, videos, data):
		if videos:
			entryList = []
			for entry in videos:
				entryList.append(((entry),))
			self["list"].setList(entryList)

	def startRun(self):
		self.getYTFeeds(self.eventName, config.plugins.yttrailer.max_results.value)

	def okPressed(self):
		entry = self["list"].getCurrent()
		if entry:
			ref = self.setServiceReference(entry)
			if ref:
				self.session.open(TrailerPlayer, ref)

class TrailerList(GUIComponent, object):

	GUI_WIDGET = eListbox

	def __init__(self):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildList)
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setItemHeight(75)

	def buildList(self, entry):
		width = self.l.getItemSize().width()
		res = [ entry ]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width , 24, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, entry.title))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 28, width , 40, 1, RT_WRAP, entry.description))
		return res

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		self.instance.setWrapAround(True)

	def preWidgetRemove(self, instance):
		instance.setContent(None)

	def setList(self, list):
		self.l.setList(list)

class TrailerPlayer(InfoBarBase, InfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarMoviePlayerSummarySupport, Screen):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, ref):
		Screen.__init__(self, session)
		self.session = session
		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"leavePlayer": (self.leavePlayer, _("leave movie player..."))
			})

		if config.plugins.yttrailer.close_player_with_exit.value:
			self["closeactions"] = HelpableActionMap(self, "WizardActions",
				{
					"back": (self.close, _("leave movie player..."))
				})


		self.allowPiP = False
		for x in InfoBarShowHide, InfoBarBase, InfoBarSeek, \
				InfoBarAudioSelection, InfoBarNotifications, \
				InfoBarServiceNotifications, InfoBarPVRState,  \
				InfoBarMoviePlayerSummarySupport:
			x.__init__(self)

		self.returning = False
		self.skinName = "MoviePlayer"
		self.lastservice = session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.playService(ref)
		self.onClose.append(self.__onClose)

	def leavePlayer(self):
		self.close()

	def doEofInternal(self, playing):
		self.close()

	def __onClose(self):
		self.session.nav.playService(self.lastservice)

class YTTrailerSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,400" title="YT-Trailer Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="0,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="20,50" size="520,330" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		cfglist = [ ]
		cfglist.append(getConfigListEntry(_("Show Setup in Extensions menu"), config.plugins.yttrailer.show_in_extensionsmenu))
		cfglist.append(getConfigListEntry(_("Extended search filter"), config.plugins.yttrailer.ext_descr))
		cfglist.append(getConfigListEntry(_("Best resolution"), config.plugins.yttrailer.best_resolution))
		cfglist.append(getConfigListEntry(_("Max. results in list-mode"), config.plugins.yttrailer.max_results))
		cfglist.append(getConfigListEntry(_("Close Player with exit-key"), config.plugins.yttrailer.close_player_with_exit))


		ConfigListScreen.__init__(self, cfglist, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose
		}, -2)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close()

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

