# for localized messages
from enigma import eEPGCache, eServiceCenter, eServiceReference, RT_HALIGN_LEFT, \
		RT_HALIGN_RIGHT, RT_VALIGN_CENTER, eListboxPythonMultiContent

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from ServiceReference import ServiceReference

from EPGSearchSetup import EPGSearchSetup
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import ChannelSelectionBase
from Screens.EventView import EventViewEPGSelect, EventViewBase
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar
from Screens.Screen import Screen
from Plugins.SystemPlugins.Toolkit.NTIVirtualKeyBoard import NTIVirtualKeyBoard

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Button import Button
from Components.config import config
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.TimerList import TimerList
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event
from Components.ServiceList import ServiceList, PiconLoader

from . import SearchType
from time import localtime, time
from operator import itemgetter
from Tools.BoundFunction import boundFunction
from skin import componentSizes

# Partnerbox installed and icons in epglist enabled?
try:
	from Plugins.Extensions.Partnerbox.PartnerboxEPGList import \
			isInRemoteTimer, getRemoteClockPixmap
	from Plugins.Extensions.Partnerbox.plugin import \
			showPartnerboxIconsinEPGList
	PartnerBoxIconsEnabled = showPartnerboxIconsinEPGList()
except ImportError:
	PartnerBoxIconsEnabled = False

# AutoTimer installed?
try:
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import \
			addAutotimerFromEvent, addAutotimerFromSearchString
	autoTimerAvailable = True
except ImportError:
	autoTimerAvailable = False

# Overwrite EPGSelection.__init__ with our modified one
baseEPGSelection__init__ = None
def EPGSelectionInit():
	global baseEPGSelection__init__
	if baseEPGSelection__init__ is None:
		baseEPGSelection__init__ = EPGSelection.__init__
	EPGSelection.__init__ = EPGSelection__init__

# Modified EPGSelection __init__
def EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)

	def bluePressed():
		cur = self["list"].getCurrent()
		if cur[0] is not None:
			name = cur[0].getEventName()
		else:
			name = ''
		self.session.open(EPGSearch, name)

	self["epgsearch_epgselection"] = ActionMap(["InfobarAudioSelectionActions"],
			{
				"audioSelection": bluePressed,
			})

	if self.type != EPG_TYPE_MULTI and config.plugins.epgsearch.add_search_to_epg.value:
		self["epgsearch_actions"] = ActionMap(["EPGSelectActions"],
				{
					"blue": bluePressed,
				})
		self["key_blue"].text = _("Search")


# Overwrite ChannelSelectionBase.__init__ with our modified one
baseChannelSelectionBase__init__ = None
def ChannelSelectionBaseInit():
	global baseChannelSelectionBase__init__
	if baseChannelSelectionBase__init__ is None:
		baseChannelSelectionBase__init__ = ChannelSelectionBase.__init__
	ChannelSelectionBase.__init__ = ChannelSelectionBase__init__

def ChannelSelectionBase__init__(self, session):
	baseChannelSelectionBase__init__(self, session)

	def getEventName(cur):
		serviceref = cur
		refstr = serviceref.toString()
		event = None
		try:
			epg = eEPGCache.getInstance()
			event = epg.lookupEventTime(serviceref, -1, 0)
			if event is None:
				info = eServiceCenter.getInstance().info(serviceref)
				event = info.getEvent(0)
		except:
			pass
		if event is not None:
			return event.getEventName()
		else:
			return ""

	def searchEPG():
		eventName = getEventName(cur = self.servicelist.getCurrent())
		from Plugins.Extensions.EPGSearch.EPGSearch import EPGSearch
		self.session.open(EPGSearch, eventName)

	self["epgsearch_channelbase"] = HelpableActionMap(self, "InfobarAudioSelectionActions",
			{
				"audioSelection":  (searchEPG, _("Search EPG with event name")),
		})

# Overwrite EventViewBase.__init__ with our modified one
baseEventViewBase__init__ = None
def EventViewBaseInit():
	global baseEventViewBase__init__
	if baseEventViewBase__init__ is None:
		baseEventViewBase__init__ = EventViewBase.__init__
	EventViewBase.__init__ = EventViewBase__init__

def EventViewBase__init__(self, Event, Ref, callback=None, similarEPGCB=None):
	baseEventViewBase__init__(self, Event, Ref, callback, similarEPGCB)

	def searchEPG():
		eventName = self.event.getEventName()
		self.session.open(EPGSearch, eventName)

	self["epgsearch_eventview"] = HelpableActionMap(self, "InfobarAudioSelectionActions",
			{
				"audioSelection":  (searchEPG, _("Search EPG with event name")),
		})

# Overwrite pzyP4T.__init__ with our modified one
basePzyP4T__init__ = None
def pzyP4TInit():
	global basePzyP4T__init__
	try:
		from Plugins.Extensions.pzyP4T.plugin import PzyP4T
		if basePzyP4T__init__ is None:
			basePzyP4T__init__ = PzyP4T.__init__
		PzyP4T.__init__ = PzyP4T__init__
	except:
		basepzyP4T__init__ = None

# Modified PzyP4T__init__ for audio-key
def PzyP4T__init__(self, session):
	basePzyP4T__init__(self, session)

	def openEPGSearch():
		event = event = self["Event"].getCurrentEvent()
		if event:
			eventName = event.getEventName()
			self.session.open(EPGSearch, eventName)

	self["InfobarAudioSelectionActions"] = ActionMap(["InfobarAudioSelectionActions"],
			{
				"audioSelection": openEPGSearch,
			})

# Modified EPGSearchList with support for PartnerBox
class EPGSearchList(EPGList):
	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None):
		EPGList.__init__(self, type, selChangedCB, timer)
		self.l.setBuildFunc(self.buildEPGSearchEntry)

		self.piconLoader = PiconLoader()

		sizes = componentSizes[EPGList.SKIN_COMPONENT_KEY]
		self._iconWidth = sizes.get(EPGList.SKIN_COMPONENT_ICON_WIDTH, 21)
		self._iconHeight = sizes.get(EPGList.SKIN_COMPONENT_ICON_HEIGHT, 21)
		self._iconHPos = sizes.get(EPGList.SKIN_COMPONENT_ICON_HPOS, 4)
		self._itemMargin = sizes.get(EPGList.SKIN_COMPONENT_ITEM_MARGIN, 10)

		servicelist_sizes = componentSizes["ServiceList"]
		self._picon_width = servicelist_sizes.get(ServiceList.KEY_PICON_WIDTH, 58)

		if PartnerBoxIconsEnabled:
			# Partnerbox Clock Icons
			self.remote_clock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock.png')
			self.remote_clock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_add.png')
			self.remote_clock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_pre.png')
			self.remote_clock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_post.png')
			self.remote_clock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_prepost.png')

	def buildEPGSearchEntry(self, service, eventId, beginTime, duration, EventName):
		rec1 = beginTime and self.timer.isInTimer(eventId, beginTime, duration, service)
		# Partnerbox
		if PartnerBoxIconsEnabled:
			rec2 = beginTime and isInRemoteTimer(self,beginTime, duration, service)
		else:
			rec2 = False
		r1 = self.weekday_rect
		r2 = self.datetime_rect
		r3 = self.descr_rect
		t = localtime(beginTime)
		serviceref = ServiceReference(service) # for Servicename
		serviceName = serviceref.getServiceName() + ": "

		#delete serviceName if set it in setup and it is most matched service
		if config.plugins.epgsearch.show_sname_in_title.value and service == self.mostSearchService:
			serviceName = ""

		res = [
			None, # no private data needed
			(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, self.days[t[6]]),
			(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
		]

		#add picon if set this option in setup
		picon = None
		if config.plugins.epgsearch.show_picon.value:
			picon = self.piconLoader.getPicon(service)
		left_pos = r3.left()
		if picon is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, left_pos, 2, self._picon_width, r3.height()-3, picon))
			left_pos = r3.left() + self._picon_width + self._itemMargin
			serviceName = "" #if load picon delete servicename

		if rec1 or rec2:
			if rec1:
				clock_pic = self.getClockPixmap(service, beginTime, duration, eventId)
				# maybe Partnerbox too
				if rec2:
					clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
			else:
				clock_pic = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
			if rec1 and rec2:
				# Partnerbox and local
				res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, left_pos, self._iconHPos, self._iconWidth, self._iconHeight, clock_pic),
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, left_pos + self._iconWidth + self._itemMargin, self._iconHPos, self._iconWidth, self._iconHeight, clock_pic_partnerbox),
					(eListboxPythonMultiContent.TYPE_TEXT, left_pos + self._iconWidth*2 + self._itemMargin*2, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName + EventName)))
			else:
				res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, left_pos, self._iconHPos, self._iconWidth, self._iconHeight, clock_pic),
					(eListboxPythonMultiContent.TYPE_TEXT, left_pos + self._iconWidth + self._itemMargin, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName + EventName)))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, left_pos, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceName + EventName))
		return res

# main class of plugin
class EPGSearch(EPGSelection):
	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self.skinName = ["EPGSearch", "EPGSelection"]

		self.searchargs = args
		self.currSearch = ""

		# XXX: we lose sort begin/end here
		self["key_yellow"] = Button(_("New Search"))
		self["key_blue"] = Button(_("History"))

# begin stripped copy of EPGSelection.__init__
		self.bouquetChangeCB = None
		self.serviceChangeCB = None
		self.ask_time = -1 #now
		self["key_red"] = Button("")
		self.closeRecursive = False
		self.saved_title = None
		self["Service"] = ServiceEvent()
		self["Event"] = Event()
		self.type = EPG_TYPE_SINGLE
		self.currentService=None
		self.zapFunc = None
		self.sort_type = 0
		self["key_green"] = Button(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		self.key_red_choice = self.EMPTY
		self["list"] = EPGSearchList(type = self.type, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer)
		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions", "MenuActions", "InputActions", "InfobarAudioSelectionActions"],
			{
				"menu": self.menu,
				"cancel": self.closeScreen,
				"ok": self.eventSelected,
				"timerAdd": self.timerAdd,
				"yellow": self.yellowButtonPressed,
				"blue": self.blueButtonPressed,
				"info": self.infoKeyPressed,
				"red": self.zapTo, # needed --> Partnerbox
				"nextBouquet": self.nextBouquet, # just used in multi epg yet
				"prevBouquet": self.prevBouquet, # just used in multi epg yet
				"nextService": self.nextService, # just used in single epg yet
				"prevService": self.prevService, # just used in single epg yet
				"1": self.importFromTimer,
				"2": self.importFromEPG,
				"3": self.importFromAutoTimer,
				"4": self.addAutoTimer,
				"5": self.exportAutoTimer,
				"6": self.openSPInfoScreen,
				"7": self.openImdb,
				"8": self.openTMDb,
				"9": self.openTMDbSerie,
				"0": self.setup,
				"audioSelection": self.searchNoNumber,
			})

		self["actions"].csel = self
		self["list"].mostSearchService = ""
		self.onLayoutFinish.append(self.onCreate)
# end stripped copy of EPGSelection.__init__

		# Partnerbox
		if PartnerBoxIconsEnabled:
			EPGSelection.PartnerboxInit(self, False)

		# Hook up actions for yttrailer if installed
		try:
			from Plugins.Extensions.YTTrailer.plugin import baseEPGSelection__init__
		except ImportError as ie:
			pass
		else:
			if baseEPGSelection__init__ is not None:
				self["trailerActions"] = ActionMap(["InfobarActions", "InfobarTeletextActions"],
				{
					"showTv": self.showTrailer,
					"showRadio": self.showTrailerList,
					"startTeletext": self.showConfig
				})

	def onCreate(self):
		self.setTitle(_("EPG Search"))

		if self.searchargs:
			self.doSearchEPG(*self.searchargs)
		else:
			l = self["list"]
			l.recalcEntrySize()
			l.list = []
			l.l.setList(l.list)
		del self.searchargs

		# Partnerbox
		if PartnerBoxIconsEnabled:
			EPGSelection.GetPartnerboxTimerlist(self)

	def closeScreen(self):
		# Save our history
		config.plugins.epgsearch.save()
		EPGSelection.closeScreen(self)

	def yellowButtonPressed(self):
		self.session.openWithCallback(
			self.searchEPG,
			NTIVirtualKeyBoard,
			title = _("Enter text to search for"),
			text = self.currSearch
		)

	def infoKeyPressed(self):
		cur = self["list"].getCurrent()
		event = cur[0]
		service = cur[1]
		if event is not None:
			self.session.open(EventViewEPGSelect, event, service, self.eventViewCallback, self.openSingleServiceEPG, InfoBar.instance.openMultiServiceEPG, self.openSimilarList)

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def openSingleServiceEPG(self):
		cur = self["list"].getCurrent()
		event = cur[0]
		service = cur[1]
		if event is not None:
			self.session.open(EPGSelection, cur[1].ref)

	def menu(self):
		options = [
			(_("Import from Timer"), self.importFromTimer),
			(_("Import from EPG"), self.importFromEPG),
		]
		keys = ["1","2"]

		if autoTimerAvailable:
			options.extend((
				(_("Import from AutoTimer"), self.importFromAutoTimer),
				(_("Save search as AutoTimer"), self.addAutoTimer),
				(_("Export selected as AutoTimer"), self.exportAutoTimer),
			))
			keys.extend(("3","4","5"))
		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/SeriesPlugin/plugin.py")):
			options.append((_("Show series info (SP)"), self.openSPInfoScreen))
			keys.append("6")

		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/IMDb/plugin.py")):
			options.append((_("Open selected in IMDb"), self.openImdb))
			keys.append("7")

		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/AdvancedMovieSelection/plugin.py")):
			options.append((_("Open selected in TMDB Info (AMS)"), self.openTMDb))
			options.append((_("Open selected in TMDB Serie Info (AMS)"), self.openTMDbSerie))
			keys.extend(("8","9"))

		options.append((_("Setup"), self.setup))
		keys.append("0")

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = options,
			keys = keys,
			title = _("EPGSearch menu")
		)

	def menuCallback(self, ret):
		ret and ret[1]()

	def importFromTimer(self):
		self.session.openWithCallback(
			self.searchEPG,
			EPGSearchTimerImport
		)

	def importFromEPG(self):
		self.session.openWithCallback(
			self.searchEPG,
			EPGSearchChannelSelection
		)

	def importFromAutoTimer(self):
		removeInstance = False
		try:
			# Import Instance
			from Plugins.Extensions.AutoTimer.plugin import autotimer

			if autotimer is None:
				removeInstance = True
				# Create an instance
				from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
				autotimer = AutoTimer()

			# Read in configuration
			autotimer.readXml()
		except Exception as e:
			self.session.open(
				MessageBox,
				_("Could not read AutoTimer timer list: %s") % e,
				type = MessageBox.TYPE_ERROR
			)
		else:
			# Fetch match strings
			# XXX: we could use the timer title as description
			options = [(x.match, x.match) for x in autotimer.getTimerList()]

			self.session.openWithCallback(
				self.searchEPGWrapper,
				ChoiceBox,
				title = _("Select text to search for"),
				list = options
			)
		finally:
			# Remove instance if there wasn't one before
			if removeInstance:
				autotimer = None

	def addAutoTimer(self):
		if autoTimerAvailable:
			addAutotimerFromSearchString(self.session, self.currSearch)

	def exportAutoTimer(self):
		cur = self['list'].getCurrent()
		if cur is None:
			return
		if autoTimerAvailable:
			addAutotimerFromEvent(self.session, cur[0], cur[1])

	def openSPInfoScreen(self):
		cur = self['list'].getCurrent()
		if cur is None:
			return
		try:
			from Plugins.Extensions.SeriesPlugin.SeriesPluginInfoScreen import SeriesPluginInfoScreen
			service=cur[1]
			event = cur[0]
			self.session.open(SeriesPluginInfoScreen, service, event)
		except ImportError as ie:
			pass

	def openImdb(self):
		cur = self['list'].getCurrent()
		if cur is None:
			return
		try:
			from Plugins.Extensions.IMDb.plugin import IMDB
			self.session.open(IMDB, cur[0].getEventName())
		except ImportError as ie:
			pass

	def openTMDb(self):
		cur = self['list'].getCurrent()
		if cur is None:
			return
		try:
			from Plugins.Extensions.AdvancedMovieSelection.plugin import tmdbInfo
			tmdbInfo(self.session, cur[0].getEventName())
		except ImportError as ie:
			pass

	def openTMDbSerie(self):
		cur = self['list'].getCurrent()
		if cur is None:
			return
		try:
			from Plugins.Extensions.AdvancedMovieSelection.plugin import tmdbSeriesInfo
			tmdbSeriesInfo(self.session, cur[0].getEventName())
		except ImportError as ie:
			pass

	def setup(self):
		self.session.openWithCallback(self.closeSetupCallback, EPGSearchSetup)

	def closeSetupCallback(self):
		self.doSearchEPG(self.currSearch, self.currSearchSave, self.currSearchDescription)

	def searchNoNumber(self):
		search_txt = self.currSearch
		search_txt = search_txt.translate(None, "1234567890(/)").strip()

		self.doSearchEPG(search_txt, self.currSearchSave, self.currSearchDescription)

	def blueButtonPressed(self):
		options = [(x, x) for x in config.plugins.epgsearch.history.value]

		if options:
			self.session.openWithCallback(
				self.searchEPGWrapper,
				ChoiceBox,
				title = _("Select text to search for"),
				list = options
			)
		else:
			self.session.open(
				MessageBox,
				_("No history"),
				type = MessageBox.TYPE_INFO
			)

	def searchEPGWrapper(self, ret):
		if ret:
			self.searchEPG(ret[1])

	def searchEPG(self, searchString = None, searchSave = True):
		if not searchString:
			return
		searchType = config.plugins.epgsearch.search_type.value
		if  searchType == SearchType.ASK:
			boundCallback = boundFunction(self.onSearchEPGCallback, searchString=searchString, searchSave=searchSave)
			choices = [ (_("Title only"), False),
						(_("Title and Description"), True) ]
			self.session.openWithCallback(boundCallback, ChoiceBox, list=choices, title=_("Where to search for '%s'?") %(searchString), windowTitle=_("EPG Search"))
		else:
			searchDescription = searchType == SearchType.TITLE_DESCRIPTION
			self.doSearchEPG(searchString, searchSave, searchDescription)

	def onSearchEPGCallback(self, answer, searchString=None, searchSave=True):
		searchDescription = answer and answer[1]
		self.doSearchEPG(searchString, searchSave, searchDescription)

	def doSearchEPG(self, searchString = None, searchSave = True, searchDescription=False):
		self.currSearchSave = searchSave
		self.currSearchDescription = searchDescription
		if searchString:
			self.currSearch = searchString
			if searchSave:
				# Maintain history
				history = config.plugins.epgsearch.history.value
				if searchString not in history:
					history.insert(0, searchString)
					maxLen = config.plugins.epgsearch.history_length.value
					if len(history) > maxLen:
						del history[maxLen:]
				else:
					history.remove(searchString)
					history.insert(0, searchString)

			# Search EPG, default to empty list
			searchType = eEPGCache.PARTIAL_TITLE_SEARCH
			if config.plugins.epgsearch.search_type.value == "exact_title":
				searchType = eEPGCache.EXACT_TITLE_SEARCH
			epgcache = eEPGCache.getInstance() # XXX: the EPGList also keeps an instance of the cache but we better make sure that we get what we want :-)
			ret = epgcache.search(('RIBDT', 1000, searchType, searchString, eEPGCache.NO_CASE_CHECK)) or []
			if searchDescription:
				ret += epgcache.search(('RIBDT', 1000, eEPGCache.PARTIAL_DESCRIPTION_SEARCH, searchString, eEPGCache.NO_CASE_CHECK)) or []
				#condense by eventids
				condensed = {}
				for item in ret:
					condensed[item[1]] = item
				ret = condensed.values()
			ret.sort(key=itemgetter(2)) # sort by time

			#filter epg-matches for selected bouquet from settings
			if config.plugins.epgsearch.search_scope.value != "all" and len(ret):
				ret = self.filterEPGmatches(ret)

			#add short description to search result
			if config.plugins.epgsearch.show_shortdesc.value and len(ret):
				ret = self.addShortDescription(epgcache, ret)

			#get most searched service
			mostSearchService = ""
			if not config.plugins.epgsearch.show_picon.value and config.plugins.epgsearch.show_sname_in_title.value and len(ret):
				mostSearchService = self.getMostSearchService(ret)

			# Update List
			l = self["list"]

			#set mostsearchservice to screen-title
			title = _("EPG Search")
			l.mostSearchService = mostSearchService #save the value also to EPGList-Class
			if not config.plugins.epgsearch.show_picon.value and mostSearchService != "":
				serviceref = ServiceReference(mostSearchService) # for Servicename
				serviceName = serviceref.getServiceName()
				title += " - " + serviceName
			self.setTitle(title)
			l.recalcEntrySize()
			l.list = ret
			l.l.setList(ret)

	def getMostSearchService(self, matches):
		services = [x[0]for x in matches]
		mostSearchService = max(services, key = services.count)
		return mostSearchService

	def filterEPGmatches(self, matches):
		services = self.getBouquetServiceList(config.plugins.epgsearch.search_scope.value)
		if len(services): #only if return services to check
			ret1 = []
			for event in matches:
				timecheck=True
				if config.plugins.epgsearch.show_events.value == "current_future" and int(event[2])+int(event[3]) < time():
					timecheck = False #if is an old event
				elif config.plugins.epgsearch.show_events.value == "future" and int(event[2]) < time():
					timecheck = False #if is a current or old event
				if config.plugins.epgsearch.show_events.value == "current" and (int(event[2]) > time() or int(event[2])+int(event[3]) < time()):
					timecheck = False #if is a future or an old event
				if str(event[0]) in services and timecheck:
					ret1.append(event)
			matches = ret1
		return matches

	def addShortDescription(self, epgcache, events):
		new_events=[]
		for event in events:
			epgEvent = epgcache.lookupEventId(eServiceReference(event[0]), int(event[1]))
			if epgEvent:
				shortdesc = str(epgEvent.getShortDescription())
				if len(shortdesc) > 0:
					event_lst = list(event)
					event_lst[4] = event_lst[4] + "  |  " + shortdesc
					event = tuple(event_lst)
			new_events.append(event)

		return new_events

	def getBouquetServiceList(self, bouquet="current"):
		infoBarInstance = InfoBar.instance
		if infoBarInstance is not None:
			servicelist = infoBarInstance.servicelist
			if bouquet == "current":
				bouquet = servicelist.getRoot().toString()
			services = infoBarInstance.getBouquetServices(eServiceReference(bouquet))

			service_list = []
			for service in services:
				service_ref = service.ref.toString()

				serviceref_split = service_ref.split(":")
				if len(serviceref_split)>10: #perhaps on ip-tv or renamed service
					serviceref_split[0]="1"
					serviceref_split[1]="0"
					#cut the service_ref
					service_ref = ":".join(serviceref_split[:10]) + ":"

				service_list.append(service_ref)

			return service_list

class EPGSearchTimerImport(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["EPGSearchTimerImport", "TimerEditList"]

		self.list = []
		self.fillTimerList()

		self["timerlist"] = TimerList(self.list)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.search,
			"cancel": self.cancel,
			"green": self.search,
			"red": self.cancel
		}, -1)
		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Select a timer to search"))

	def fillTimerList(self):
		l = self.list
		del l[:]

		for timer in self.session.nav.RecordTimer.timer_list:
			l.append((timer, False))

		for timer in self.session.nav.RecordTimer.processed_timers:
			l.append((timer, True))
		l.sort(key = lambda x: x[0].begin)

	def search(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			self.close(cur.name)

	def cancel(self):
		self.close(None)

class EPGSearchChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = ["EPGSearchChannelSelection", "SimpleChannelSelection"]

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
		{
				"showEPGList": self.channelSelected
		})

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.openWithCallback(
				self.epgClosed,
				EPGSearchEPGSelection,
				ref,
				False
			)

	def epgClosed(self, ret = None):
		if ret:
			self.close(ret)

class EPGSearchEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin):
		EPGSelection.__init__(self, session, ref)
		self.skinName = ["EPGSearchEPGSelection", "EPGSelection"]
		self["key_green"].text = _("Search")
		self.openPlugin = openPlugin

	def infoKeyPressed(self):
		self.timerAdd()

	def timerAdd(self):
		cur = self["list"].getCurrent()
		evt = cur[0]
		sref = cur[1]
		if not evt:
			return

		if self.openPlugin:
			self.session.open(EPGSearch,evt.getEventName())
		else:
			self.close(evt.getEventName())