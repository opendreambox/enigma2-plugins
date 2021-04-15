
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
#  is licensed by Dream Property GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Components.Sources.StaticText import StaticText
from Components.GUIComponent import GUIComponent
from enigma import eServiceReference, RT_WRAP, RT_VALIGN_CENTER, RT_HALIGN_LEFT, gFont, eListbox, eListboxPythonMultiContent

from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry, configfile, ConfigText, ConfigInteger, ConfigYesNo
from Components.ConfigList import ConfigListScreen

from Screens.InfoBarGenerics import InfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarMoviePlayerSummarySupport
from Components.ServiceEventTracker import InfoBarBase
from skin import TemplatedListFonts, componentSizes

config.plugins.yttrailer = ConfigSubsection()
config.plugins.yttrailer.show_in_extensionsmenu = ConfigYesNo(default=False)
config.plugins.yttrailer.ext_descr = ConfigText(default="german", fixed_size=False)
config.plugins.yttrailer.max_results = ConfigInteger(5, limits=(1, 10))
config.plugins.yttrailer.close_player_with_exit = ConfigYesNo(default=False)

from Plugins.SystemPlugins.TubeLib.youtube.Base import buildYoutube
from Plugins.SystemPlugins.TubeLib.youtube.Search import Search
from Plugins.SystemPlugins.TubeLib.youtube.Videos import Videos

def setup(session, **kwargs):
	session.open(YTTrailerSetup)

def Plugins(**kwargs):
	list = [PluginDescriptor(name="YTTrailer Setup", description=_("YouTube-Trailer Setup"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=setup, icon="YTtrailer.png"),
			PluginDescriptor(name=_("Watch Trailer"), where=[PluginDescriptor.WHERE_EVENTVIEW, PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE], fnc=showTrailer),
			PluginDescriptor(name=_("Show Trailers"), where=[PluginDescriptor.WHERE_EVENTVIEW, PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE], fnc=showTrailerList),
	]
	if config.plugins.yttrailer.show_in_extensionsmenu.value:
		list.append(PluginDescriptor(name="YTTrailer Setup", description=_("YouTube-Trailer Setup"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=setup, icon="YTtrailer.png"))
	return list

def showConfig(self):
	self.session.open(YTTrailerSetup)

def showTrailer(session, event, ref):
	if not event:
		return
	eventname = event.getEventName()
	ytTrailer = YTTrailer(session)
	ytTrailer.showTrailer(eventname)

def showTrailerList(session, event, ref):
	session.open(YTTrailerList, event.getEventName())

class YTTrailer:
	def __init__(self, session):
		self.session = session
		self._youtube = None
		self._query = None

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
		q = "%s Trailer %s" % (eventname, config.plugins.yttrailer.ext_descr.value)
		search = Search(self._youtube)
		self._query = search.list(self._gotYTFeeds, searchTerm=q, maxResults=max_results)

	def setServiceReference(self, entry):
		if not entry.id:
			return
		url = "yt://%s" % (entry.id)
		if url:
			ref = eServiceReference(eServiceReference.idURI, 0, url)
			ref.setName(entry.title)
		else:
			ref = None
		return ref

class YTTrailerList(Screen, YTTrailer):

	skin = """
		<screen name="YTTrailerList" position="center,center" size="820,410" title="YT Trailer-List">
			<widget name="list" position="10,10" size="800,385" enableWrapAround="1" scrollbarMode="showOnDemand" />
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
	SKIN_COMPONENT_KEY = "YTTrailerList"
	SKIN_COMPONENT_TITLE_HEIGHT = "titleHeight"
	SKIN_COMPONENT_DESCRIPTION_HEIGHT = "descriptionHeight"
	SKIN_COMPONENT_LINE_SPACING = "lineSpacing"


	GUI_WIDGET = eListbox

	def __init__(self):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildList)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		self.l.setFont(1, gFont(tlf.face(tlf.SMALL), tlf.size(tlf.SMALL)))
		self.l.setItemHeight(componentSizes.itemHeight(self.SKIN_COMPONENT_KEY, 77))

	def buildList(self, entry):
		sizes = componentSizes[TrailerList.SKIN_COMPONENT_KEY]
		configEntryWidth = sizes.get(componentSizes.ITEM_WIDTH, 800)
		titleHeight = sizes.get(TrailerList.SKIN_COMPONENT_TITLE_HEIGHT, 25)
		descriptionHeight = sizes.get(TrailerList.SKIN_COMPONENT_DESCRIPTION_HEIGHT, 40)
		lineSpacing = sizes.get(TrailerList.SKIN_COMPONENT_LINE_SPACING, 3)		
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 2, configEntryWidth, titleHeight, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry.title))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, titleHeight + lineSpacing, configEntryWidth, descriptionHeight, 1, RT_WRAP, entry.description))
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
		<screen position="center,center" size="820,410" title="YT-Trailer Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="config" position="10,60" size="800,330" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		cfglist = []
		cfglist.append(getConfigListEntry(_("Show Setup in Extensions menu"), config.plugins.yttrailer.show_in_extensionsmenu))
		cfglist.append(getConfigListEntry(_("Extended search filter"), config.plugins.yttrailer.ext_descr))
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

