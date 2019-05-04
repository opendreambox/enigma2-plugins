# for localized messages
from enigma import eEPGCache, eServiceReference, iServiceInformation, eServiceCenter
from ServiceReference import ServiceReference
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry

from time import localtime, time
from Tools.BoundFunction import boundFunction

# AutoTimer installed?
try:
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import \
		AutoTimerEditor, AutoTimerFilterEditor, AutoTimerServiceEditor, hasVps
	from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
	from Plugins.Extensions.AutoTimer.AutoTimerConfiguration import buildConfig
	from Plugins.Extensions.AutoTimer.AutoTimerOverview import AutoTimerOverview
	from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
except ImportError:
	AutoTimerEditor = AutoTimerFilterEditor = AutoTimerServiceEditor = Screen
	AutoTimer = AutoTimerOverview = AutoTimerImporter = Screen
	hasVps = False

class EPGSearchATEditor(AutoTimerEditor):
	def __init__(self, session, timer, editingDefaults = False, **kwargs):
		AutoTimerEditor.__init__(self, session, timer, editingDefaults = False, **kwargs)
		
		self.skinName = ["EPGSearchATEditor", "AutoTimerEditor"]
		self.setup_title = _("SearchFilter Editor")
		self.partnerbox = False
		self.removeConfigListEntries()
		
	def removeConfigListEntries(self):
		#remove config entries not use in EPGSearch filter
		try:
			self.list.remove(getConfigListEntry(_("Enabled"), self.enabled))
			self.list.remove(getConfigListEntry(_("Timer type"), self.justplay))
			self.list.remove(getConfigListEntry(_("Custom offset"), self.offset))
			#self.list.remove(getConfigListEntry(_("Offset before recording (in m)"), self.offsetbegin))
			#self.list.remove(getConfigListEntry(_("Offset after recording (in m)"), self.offsetend))
			self.list.remove(getConfigListEntry(_("After event"), self.afterevent))
			#self.list.remove(getConfigListEntry(_("Execute \"after event\" during timespan"), self.afterevent_timespan))
			#self.list.remove(getConfigListEntry(_("Begin of \"after event\" timespan"), self.afterevent_timespanbegin))
			#self.list.remove(getConfigListEntry(_("End of \"after event\" timespan"), self.afterevent_timespanend))
			self.list.remove(getConfigListEntry(_("Tags"), self.tags))
			self.list.remove(getConfigListEntry(_("Record a maximum of x times"), self.counter))
			self.list.remove(getConfigListEntry(_("Use a custom location"), self.useDestination))
			if hasVps:
				self.list.remove(getConfigListEntry(_("Activate VPS"), self.vps_enabled))
		except:
			#import traceback
			#traceback.print_exc()
			pass
	
	def reloadList(self, value):
		self.refresh()
		self.removeConfigListEntries()
		self["config"].setList(self.list)

	def setCustomTitle(self):
		self.setTitle(_("Edit EPGSearch search filter"))
	
	def editFilter(self):
		self.session.openWithCallback(
			self.editFilterCallback,
			EPSearchFilterEditor,
			self.filterSet,
			self.excludes,
			self.includes
		)
	
	def editServices(self):
		self.session.openWithCallback(
			self.editServicesCallback,
			EPSearchServiceEditor,
			self.serviceRestriction,
			self.services,
			self.bouquets
		)

class EPSearchFilterEditor(AutoTimerFilterEditor, ConfigListScreen):
	def __init__(self, session, filterset, excludes, includes):
		AutoTimerFilterEditor.__init__(self, session, filterset, excludes, includes)
		
		self.skinName = ["EPGSearchATFilterEditor", "AutoTimerFilterEditor"]
		self.setup_title = _("EPGSearch Filters")
	
	def setCustomTitle(self):
		self.setTitle(_("Edit EPGSearch filter"))

class EPSearchServiceEditor(AutoTimerServiceEditor, ConfigListScreen):
	def __init__(self, session, servicerestriction, servicelist, bouquetlist):
		AutoTimerServiceEditor.__init__(self, session, servicerestriction, servicelist, bouquetlist)
		
		self.skinName = ["EPGSearchATServiceEditor", "AutoTimerServiceEditor"]
		self.setup_title = _("EPGSearch Services")
	
	def setCustomTitle(self):
		self.setTitle(_("Edit EPGSearch Services"))

class EPGSearchAT(AutoTimer):
	FILENAME = "/etc/enigma2/epgsearchAT.xml"
	def readXml(self, **kwargs):
		if "xml_string" in kwargs:
			AutoTimer.readXml(self, **kwargs)

	def load(self):
		result = False
		from os import path as os_path
		if os_path.exists(EPGSearchAT.FILENAME):
			with open(EPGSearchAT.FILENAME, 'r') as file:
				data = file.read()
				kwargs = {"xml_string": data}
				self.readXml(**kwargs)
				result = True
		return result

	def save(self, timer=None):
		if timer:
			self.timers.append(timer)
		from Tools.IO import saveFile
		saveFile(EPGSearchAT.FILENAME, buildConfig(self.defaultTimer, self.timers))

def ATeditorCallback(session, save, timer):
	if timer:
		epgsearchAT = EPGSearchAT()
		epgsearchAT.add(timer)
		total, new, modified, timers, conflicts, similars = epgsearchAT.parseEPG(simulateOnly = True)
		results = []
		if timers:
			epgcache = eEPGCache.getInstance()
			for t in timers:
				if timer.hasOffset():
					rbegin = t[1] + timer.offset[0]
					rend = t[2] - timer.offset[1]
				else:
					rbegin = t[1] + config.recording.margin_before.value * 60
					rend = t[2] - config.recording.margin_after.value * 60
				evt = epgcache.lookupEventTime(eServiceReference(t[3]), rbegin)
				if evt:
					results.append((t[3], evt.getEventId(), rbegin, rend - rbegin, t[0]))
		
		from EPGSearch import EPGSearch
		if results:
			kwargs = {"AT": results}
			session.open(EPGSearch, **kwargs)
		else:
			session.open(EPGSearch)
		if save:
			if epgsearchAT.load():
				epgsearchAT.save(timer)
			else:
				epgsearchAT.save()
		epgsearchAT = None

def ATimporterCallback(ret):
	if ret:
		ret, session = ret
		session.openWithCallback(boundFunction(ATeditorCallback, session, True), EPGSearchATEditor, ret)

def ATeditCallback(epgsearchAT):
	if epgsearchAT is not None:
		epgsearchAT.save()

class EPGSearchATOverview(AutoTimerOverview):
	def __init__(self, session, autotimer):
		AutoTimerOverview.__init__(self, session, autotimer)
		self["EPGSelectActions"].setEnabled(False)
		self["InfobarActions"].setEnabled(False)
		self.skinName = ["EPGSearchATOverview", "AutoTimerOverview"]
		
		self["InfobarActions"] = HelpableActionMap(self, "InfobarActions",
			{
				"showMovies": (self.search, _("search for current search filter")),
			}
		)
		
		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
			{
				"menu": (self.menu, _("Open Context Menu"))
			}
		)

	def ok(self):
		# Edit selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(
				self.editCallback,
				EPGSearchATEditor,
				current
			)

	def cancel(self):
		if self.changed:
			self.session.openWithCallback(self.cancelConfirm, ChoiceBox, title=_('Really close without saving settings?\nWhat do you want to do?') , list=[(_('close without saving'), 'close'), (_('close and save'), 'close_save'),(_('cancel'), 'exit'), ])
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		ret = ret and ret[1]
		if ret == 'close':
			self.close(None)
		elif ret == 'close_save':
			self.close(self.autotimer)

	def save(self):
		self.close(self.autotimer)

	def search(self):
		current = self["entries"].getCurrent()
		if current:
			self.autotimer.save()
			self.changed = False
			ATeditorCallback(self.session, False, current)

	def setCustomTitle(self):
		self.setTitle(_("EPGSearch search filter overview"))

	def menu(self):
		list = [
			(_("search for current search filter"), "search filter")
		]

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = list,
		)

	def menuCallback(self, ret):
		ret = ret and ret[1]
		if ret:
			if ret == "search filter":
				self.search()

	def add(self):
		newTimer = self.autotimer.defaultTimer.clone()
		newTimer.id = self.autotimer.getUniqueId()
		
		self.session.openWithCallback(
				self.addCallback,
				EPGSearchATEditor,
				newTimer
			)

class EPGSearchATImporter(AutoTimerImporter):
	def __init__(self, session, autotimer, name, begin, end, disabled, sref, afterEvent, justplay, dirname, tags):
		AutoTimerImporter.__init__(self, session, autotimer, name, begin, end, disabled, sref, afterEvent, justplay, dirname, tags)
		self.skinName = ["EPGSearchATImporter", "AutoTimerImporter"]

	def setCustomTitle(self):
		self.setTitle(_("Add EPGSearch search filter"))

def addEPGSearchATFromEvent(session, evt, service, importer_Callback):
	epgsearchAT = EPGSearchAT()
	epgsearchAT.load()
	match = evt and evt.getEventName() or ""
	name = match or "New Searchfilter"
	sref = None
	if service is not None:
		service = str(service)
		myref = eServiceReference(service)
		if not (myref.flags & eServiceReference.isGroup):
			# strip all after last :
			pos = service.rfind(':')
			if pos != -1:
				if service[pos-1] == ':':
					pos -= 1
				service = service[:pos+1]

		sref = ServiceReference(myref)
	if evt:
		# timespan defaults to +- 1h
		begin = evt.getBeginTime()-3600
		end = begin + evt.getDuration()+7200
	else:
		begin = end = 0

	# XXX: we might want to make sure that we actually collected any data because the importer does not do so :-)

	newTimer = epgsearchAT.defaultTimer.clone()
	newTimer.id = epgsearchAT.getUniqueId()
	newTimer.name = name
	newTimer.match = ''
	newTimer.enabled = True

	session.openWithCallback(
		importer_Callback,
		EPGSearchATImporter,
		newTimer,
		match,		# Proposed Match
		begin,		# Proposed Begin
		end,		# Proposed End
		None,		# Proposed Disabled
		sref,		# Proposed ServiceReference
		None,		# Proposed afterEvent
		None,		# Proposed justplay
		None,		# Proposed dirname, can we get anything useful here?
		[]			# Proposed tags
	)

def addEPGSearchATFromService(session, service, importer_Callback):
	epgsearchAT = EPGSearchAT()
	epgsearchAT.load()
	serviceHandler = eServiceCenter.getInstance()
	service = eServiceReference(str(service))

	info = serviceHandler.info(service)

	match = info and info.getName(service) or ""
	name = match or "New Searchfilter"
	sref = info and info.getInfoString(service, iServiceInformation.sServiceref)
	if sref:
		# strip all after last :
		pos = sref.rfind(':')
		if pos != -1:
			if sref[pos-1] == ':':
				pos -= 1
			sref = sref[:pos+1]

		sref = ServiceReference(sref)
	if info:
		begin = info.getInfo(service, iServiceInformation.sTimeCreate)
		end = begin + info.getLength(service)
	else:
		begin = end = 0

	from os.path import dirname
	path = dirname(service.getPath())
	if not path == '/':
		path += '/'

	tags = info.getInfoString(service, iServiceInformation.sTags)
	tags = tags and tags.split(' ') or []

	newTimer = epgsearchAT.defaultTimer.clone()
	newTimer.id = epgsearchAT.getUniqueId()
	newTimer.name = name
	newTimer.match = ''
	newTimer.enabled = True

	# XXX: we might want to make sure that we actually collected any data because the importer does not do so :-)

	session.openWithCallback(
		importer_Callback,
		EPGSearchATImporter,
		newTimer,
		match,		# Proposed Match
		begin,		# Proposed Begin
		end,		# Proposed End
		None,		# Proposed Disabled
		sref,		# Proposed ServiceReference
		None,		# Proposed afterEvent
		None,		# Proposed justplay
		path,		# Proposed dirname
		tags		# Proposed tags
	)

# from pluginlist (WHERE_EPG_SELECTION_SINGLE_BLUE, WHERE_CHANNEL_SELECTION_RED)
def searchEventWithFilter(session, event, service):
	if service.getPath() and service.getPath()[0] == "/":
		addEPGSearchATFromService(session, service, ATimporterCallback)
	else:
		if event:
			addEPGSearchATFromEvent(session, event, service, ATimporterCallback)

# from pluginlist (WHERE_EPG_SELECTION_SINGLE_BLUE, WHERE_CHANNEL_SELECTION_RED)
def openSearchFilterList(session, event, service):
	epgsearchAT = EPGSearchAT()
	epgsearchAT.load()
	session.openWithCallback(ATeditCallback, EPGSearchATOverview, epgsearchAT)

# from pluginlist (WHERE_EVENTINFO)
def addSearchFilterFromEventinfo(session, service=None, event=None, *args, **kwargs):
	if not event:
		sref = session.nav.getCurrentlyPlayingServiceReference()
		service = ServiceReference(sref)
		epg = eEPGCache.getInstance()
		event = epg.lookupEventTime(service.ref, int(time())+1)
	if not event:
		return
	addEPGSearchATFromEvent(session, event, service, ATimporterCallback)
