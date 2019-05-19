# -*- coding: UTF-8 -*-
from __future__ import print_function

# To check if in Standby
import Screens.Standby

# eServiceReference
from enigma import quitMainloop, eServiceReference, eServiceCenter, eEPGCache, cachestate

# ...
from ServiceReference import ServiceReference

from RecordTimer import RecordTimerEntry
from Components.ParentalControl import parentalControl

# Timer
from EPGRefreshTimer import epgrefreshtimer, EPGRefreshTimerEntry, checkTimespan

# To calculate next timer execution
from time import time

# Error-print
from traceback import print_exc
from sys import stdout

# Plugin Config
from xml.etree.cElementTree import parse as cet_parse
from Tools.XMLTools import stringToXML
from os import path as path
from os import remove as remove

# We want a list of unique services
from EPGRefreshService import EPGRefreshService

from OrderedSet import OrderedSet

# Configuration
from Components.config import config

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications
from Tools.BoundFunction import boundFunction

# epg.db 
from enigma import cachestate                                                
from sqlite3 import dbapi2 as sqlite      

# ... II
from . import ENDNOTIFICATIONID, NOTIFICATIONDOMAIN
from MainPictureAdapter import MainPictureAdapter
from PipAdapter import PipAdapter
from RecordAdapter import RecordAdapter

# timeout timer for eEPGCache-signal based refresh
from enigma import eTimer
from enigma import eDVBSatelliteEquipmentControl

# Path to configuration
CONFIG = "/etc/enigma2/epgrefresh.xml"
XML_VERSION = "1"

class EPGRefresh:
	"""Simple Class to refresh EPGData"""

	def __init__(self):
		# Initialize
		self.services = (OrderedSet(), OrderedSet())
		self.currentServiceRef = None
		self.forcedScan = False
		self.isrunning = False
		self.doStopRunningRefresh = False
		self.session = None
		self.beginOfTimespan = 0
		self.refreshAdapter = None
		# to call additional tasks (from other plugins)
		self.finishNotifiers = { }

		# Mtime of configuration files
		self.configMtime = -1
		
		# Todos after finish
		self._initFinishTodos()

		# Read in Configuration
		self.readConfiguration()

		# Initialise myEpgCacheInstance
		self.myEpgCacheInstance = None

		# timeout timer for eEPGCache-signal based refresh
		self.epgTimeoutTimer = eTimer()
		self.epgTimeoutTimer_conn = self.epgTimeoutTimer.timeout.connect(self.epgTimeout)
		
		# set state for pending services message box
		self.showPendingServicesMessageShown = False		

	def epgTimeout(self):
		if eDVBSatelliteEquipmentControl.getInstance().isRotorMoving():
			# rotor is moving, timeout raised too early...check again in 5 seconds
			self.epgTimeoutTimer.start(5000, True)
		else:
			# epgcache-signal is not responding...maybe service/transponder is already running or cache was already updated...? step to next entry
			print("[EPGRefresh] - finished channel without epg update. Reason: epgTimeout")
			epgrefreshtimer.add(EPGRefreshTimerEntry(
					time(),
					self.refresh,
					nocheck = True)
			)
			
	# _onCacheStateChanged is called whenever an eEPGCache-signal is sent by enigma2
	#  0 = started, 1 = stopped, 2 = aborted, 3 = deferred, 4 = load_finished, 5 = save_finished
	def _onCacheStateChanged(self, cState):
		sref = self.currentServiceRef
		if sref is None:
			print("[EPGRefresh] - got EPG message but no epgrefresh running... ignore")
			return

		if cState.state in (cachestate.load_finished, cachestate.save_finished, cachestate.aborted):
			print("[EPGRefresh] - assuming the state is not relevant for EPGRefresh. State:" + str(cState.state))
			return

		sdata = sref.getUnsignedData
		tsid = sdata(2)
		onid = sdata(3)
		ns = sdata(4)

		if cState.tsid != tsid or cState.onid != onid or cState.dvbnamespace != ns:
			print("[EPGRefresh] - ignored EPG message for wrong transponder %04x:%04x:%08x <> %04x:%04x:%08x" %(cState.tsid, cState.onid, cState.dvbnamespace, tsid, onid, ns))
			return

		print("[EPGRefresh] - state is:" + str(cState.state))

		self.epgTimeoutTimer.stop()
		if cState.state == cachestate.started:
			print("[EPGRefresh] - EPG update started for transponder %04x:%04x:%08x" %(tsid, onid, ns))
		elif cState.state == cachestate.stopped or cState.state == cachestate.deferred:
			print("[EPGRefresh] - EPG update finished for transponder %04x:%04x:%08x" %(tsid, onid, ns))

			if self.refreshAdapter:
				self.refreshAdapter.stop()

			epgrefreshtimer.add(EPGRefreshTimerEntry(
					time(),
					self.refresh,
					nocheck = True)
			)

	def _initFinishTodos(self):
		self.finishTodos = [self._ToDoCallAutotimer, self._ToDoAutotimerCalled, self._callFinishNotifiers, self.finish]
	
	def addFinishNotifier(self, notifier):
		if not callable(notifier):
			print("[EPGRefresh] notifier" + str(notifier) + " isn't callable")
			return
		self.finishNotifiers[str(notifier)] = notifier

	def removeFinishNotifier(self, notifier):
		notifierKey = str(notifier)
		if notifierKey in self.finishNotifiers:
			self.finishNotifiers.pop(notifierKey)

	def readConfiguration(self):
		# Check if file exists
		if not path.exists(CONFIG):
			return

		# Check if file did not change
		mtime = path.getmtime(CONFIG)
		if mtime == self.configMtime:
			return

		# Keep mtime
		self.configMtime = mtime

		# Empty out list
		self.services[0].clear()
		self.services[1].clear()

		# Open file
		configuration = cet_parse(CONFIG).getroot()
		version = configuration.get("version", None)
		if version is None:
			factor = 60
		else: #if version == "1"
			factor = 1

		# Add References
		for service in configuration.findall("service"):
			value = service.text
			if value:
				# strip all after last : (custom name)
				pos = value.rfind(':')
				# don't split alternative service
				if pos != -1 and not value.startswith('1:134:'):
					value = value[:pos+1]

				duration = service.get('duration', None)
				duration = duration and int(duration)*factor

				self.services[0].add(EPGRefreshService(value, duration))
		for bouquet in configuration.findall("bouquet"):
			value = bouquet.text
			if value:
				duration = bouquet.get('duration', None)
				duration = duration and int(duration)
				self.services[1].add(EPGRefreshService(value, duration))

	def buildConfiguration(self, webif = False):
		list = ['<?xml version="1.0" ?>\n<epgrefresh version="', XML_VERSION, '">\n\n']

		if webif:
			for serviceref in self.services[0].union(self.services[1]):
				ref = ServiceReference(str(serviceref))
				list.extend((
					' <e2service>\n',
					'  <e2servicereference>', str(serviceref), '</e2servicereference>\n',
					'  <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
					' </e2service>\n',
				))
		else:
			for service in self.services[0]:
				ref = ServiceReference(service.sref)
				list.extend((' <!--', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '-->\n', ' <service'))
				if service.duration is not None:
					list.extend((' duration="', str(service.duration), '"'))
				list.extend(('>', stringToXML(service.sref), '</service>\n'))
			for bouquet in self.services[1]:
				ref = ServiceReference(bouquet.sref)
				list.extend((' <!--', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '-->\n', ' <bouquet'))
				if bouquet.duration is not None:
					list.extend((' duration="', str(bouquet.duration), '"'))
				list.extend(('>', stringToXML(bouquet.sref), '</bouquet>\n'))

		list.append('\n</epgrefresh>')

		return list

	def saveConfiguration(self):
		file = open(CONFIG, 'w')
		file.writelines(self.buildConfiguration())

		file.close()

	def maybeStopAdapter(self):
		if self.refreshAdapter:
			self.refreshAdapter.stop()
			self.refreshAdapter = None

	def forceRefresh(self, session = None):
		print("[EPGRefresh] Forcing start of EPGRefresh")
		if self.session is None:
			if session is not None:
				self.session = session
			else:
				return False

		self.forcedScan = True
		self.prepareRefresh()
		return True
	
	def stopRunningRefresh(self, session = None):
		print("[EPGRefresh] Forcing stop of EPGRefresh")
		if self.session is None:
			if session is not None:
				self.session = session
			else:
				return False
		self.doStopRunningRefresh = True
		# stopping the refresh only has an effect when nextService() is still called which is not necessarily happening when signal-based method is used. So, just call it
		if config.plugins.epgrefresh.usetimebased.value == False:
			self.nextService()

	def start(self, session = None):
		if session is not None:
			self.session = session

		epgrefreshtimer.setRefreshTimer(self.createWaitTimer)

	def stop(self):
		print("[EPGRefresh] Stopping Timer")
		self.maybeStopAdapter()
		epgrefreshtimer.clear()

	def addServices(self, fromList, toList, channelIds):
		for scanservice in fromList:
			service = eServiceReference(scanservice.sref)
			if not service.valid() \
				or service.type != eServiceReference.idDVB \
				or (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)):
				continue

			channelID = '%08x%04x%04x' % (
				service.getUnsignedData(4), # NAMESPACE
				service.getUnsignedData(2), # TSID
				service.getUnsignedData(3), # ONID
			)

			if channelID not in channelIds:
				toList.append(scanservice)
				channelIds.append(channelID)

	def generateServicelist(self, services, bouquets):
		# This will hold services which are not explicitely in our list
		additionalServices = []
		additionalBouquets = []

		# See if we are supposed to read in autotimer services
		if config.plugins.epgrefresh.inherit_autotimer.value:
			try:
				# Import Instance
				from Plugins.Extensions.AutoTimer.plugin import autotimer

				if autotimer is None:
					# Create an instance
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
					autotimer = AutoTimer()

				# Read in configuration
				autotimer.readXml()
			except Exception as e:
				print("[EPGRefresh] Could not inherit AutoTimer Services:", e)
			else:
				# Fetch services
				for timer in autotimer.getEnabledTimerList():
					additionalServices.extend([EPGRefreshService(x, None) for x in timer.services])
					additionalBouquets.extend([EPGRefreshService(x, None) for x in timer.bouquets])

		scanServices = []
		channelIdList = []
		self.addServices(services, scanServices, channelIdList)

		serviceHandler = eServiceCenter.getInstance()
		for bouquet in bouquets.union(additionalBouquets):
			myref = eServiceReference(bouquet.sref)
			list = serviceHandler.list(myref)
			if list is not None:
				while True:
					s = list.getNext()
					# TODO: I wonder if its sane to assume we get services here (and not just new lists)
					if s.valid() and s.type == eServiceReference.idDVB:
						additionalServices.append(EPGRefreshService(s.toString(), None))
					else:
						break
		del additionalBouquets[:]

		self.addServices(additionalServices, scanServices, channelIdList)
		del additionalServices[:]

		return scanServices

	def isRunning(self):
		return self.isrunning
	
	def isRefreshAllowed(self):
		if self.isRunning():
			message = _("There is still a refresh running. The Operation isn't allowed at this moment.")
			try:
				if self.session != None:
					self.session.open(MessageBox, message, \
						 MessageBox.TYPE_INFO, timeout=10)
			except:
				print("[EPGRefresh] Error while opening Messagebox!")
				print_exc(file=stdout)
				Notifications.AddPopup(message, MessageBox.TYPE_INFO, 10, domain = NOTIFICATIONDOMAIN)
			return False
		return True

	def prepareRefresh(self):
		if not self.isRefreshAllowed():
			return
		self.isrunning = True
		print("[EPGRefresh] About to start refreshing EPG")

		self._initFinishTodos()
		# Maybe read in configuration
		try:
			self.readConfiguration()
		except Exception as e:
			print("[EPGRefresh] Error occured while reading in configuration:", e)

		self.scanServices = self.generateServicelist(self.services[0], self.services[1])

		# Debug
		print("[EPGRefresh] Services we're going to scan:", ', '.join([repr(x) for x in self.scanServices]))

		self.maybeStopAdapter()
		# NOTE: start notification is handled in adapter initializer
		if config.plugins.epgrefresh.adapter.value.startswith("pip"):
			hidden = config.plugins.epgrefresh.adapter.value == "pip_hidden"
			refreshAdapter = PipAdapter(self.session, hide=hidden)
		elif config.plugins.epgrefresh.adapter.value.startswith("record"):
			refreshAdapter = RecordAdapter(self.session)
		else:
			refreshAdapter = MainPictureAdapter(self.session)

		if (not refreshAdapter.backgroundCapable and Screens.Standby.inStandby) or not refreshAdapter.prepare():
			print("[EPGRefresh] Adapter is not able to run in background or not available, falling back to MainPictureAdapter")
			refreshAdapter = MainPictureAdapter(self.session)
			refreshAdapter.prepare()
		self.refreshAdapter = refreshAdapter

		try:
			from plugin import AdjustExtensionsmenu, extStopDescriptor, extPendingServDescriptor, extRunDescriptor
			AdjustExtensionsmenu(True, extPendingServDescriptor)
			AdjustExtensionsmenu(True, extStopDescriptor)
			AdjustExtensionsmenu(False, extRunDescriptor)
		except:
			print("[EPGRefresh] Error while adding 'Stop Running EPG-Refresh' to Extensionmenu")
			print_exc(file=stdout)
			
		self.refresh()

	def cleanUp(self):
		print("[EPGRefresh] Debug: Cleanup")
		config.plugins.epgrefresh.lastscan.value = int(time())
		config.plugins.epgrefresh.lastscan.save()
		# stop the epgTimeoutTimer - just in case one is running
		self.epgTimeoutTimer.stop()
		
		try:
			from plugin import AdjustExtensionsmenu, housekeepingExtensionsmenu, extStopDescriptor, extPendingServDescriptor
			AdjustExtensionsmenu(False, extPendingServDescriptor)
			AdjustExtensionsmenu(False, extStopDescriptor)
			housekeepingExtensionsmenu(config.plugins.epgrefresh.show_run_in_extensionsmenu, force=True)
		except:
			print("[EPGRefresh] Error while removing 'Stop Running EPG-Refresh' to Extensionmenu:")
			print_exc(file=stdout)

		self.currentServiceRef = None
		# Start Todo-Chain
		self._nextTodo()

	def _nextTodo(self, *args, **kwargs):
		print("[EPGRefresh] Debug: Calling nextTodo")
		if len(self.finishTodos) > 0:
			finishTodo = self.finishTodos.pop(0)
			print("[EPGRefresh] Debug: Call " + str(finishTodo))
			finishTodo(*args, **kwargs)

	def _ToDoCallAutotimer(self):
		if config.plugins.epgrefresh.parse_autotimer.value != "never":
			if config.plugins.epgrefresh.parse_autotimer.value in ("ask_yes", "ask_no"):
				defaultanswer = True if config.plugins.epgrefresh.parse_autotimer.value == "ask_yes" else False
				if self.forcedScan:
					# only if we are interactive
					Notifications.AddNotificationWithCallback(self._ToDoCallAutotimerCB, MessageBox, \
						text = _("EPG refresh finished.\nShould AutoTimer be search for new matches?"), \
						type = MessageBox.TYPE_YESNO, default = defaultanswer, timeout = 10, domain = NOTIFICATIONDOMAIN)
				else:
					self._ToDoCallAutotimerCB(parseAT=defaultanswer)
			else:
				if self.forcedScan\
					and config.plugins.epgrefresh.parse_autotimer.value == "bg_only":
					self._nextTodo()
				else:
					# config.parse_autotimer = always / bg_only
					self._ToDoCallAutotimerCB(parseAT=True)
		else:
			self._nextTodo()

	def _ToDoCallAutotimerCB(self, parseAT):
		print("[EPGRefresh] Debug: Call AutoTimer: " + str(parseAT))
		if parseAT:
			try:
				# Import Instance
				from Plugins.Extensions.AutoTimer.plugin import autotimer
	
				if autotimer is None:
					# Create an instance
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
					autotimer = AutoTimer()
	
				# Parse EPG
				autotimer.parseEPGAsync(simulateOnly=False).addCallback(self._nextTodo).addErrback(self._autotimerErrback)
			except:
				from traceback import format_exc
				print("[EPGRefresh] Could not start AutoTimer:" + str(format_exc()))
				self._nextTodo()
		else:
			self._nextTodo()
	
	def _autotimerErrback(self, failure):
		print("[EPGRefresh] Debug: AutoTimer failed:" + str(failure))
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("AutoTimer failed with error %s") % (str(failure)), \
				MessageBox.TYPE_ERROR, 10, domain = NOTIFICATIONDOMAIN)
		self._nextTodo()

	def _ToDoAutotimerCalled(self, *args, **kwargs):
		if config.plugins.epgrefresh.enablemessage.value:
			if len(args):
				# Autotimer has been started
				ret=args[0]
				try:
					#try import new advanced AT-message with searchlog-info 
					from Plugins.Extensions.AutoTimer.plugin import showFinishPopup
					showFinishPopup(ret)
				except:
					from traceback import format_exc
					print("[EPGRefresh] Could not start Autotimer showPopup:" + str(format_exc()))
					Notifications.AddPopup(_("Found a total of %d matching Events.\n%d Timer were added and\n%d modified,\n%d conflicts encountered,\n%d similars added.") \
					% (ret[0], ret[1], ret[2], len(ret[4]), len(ret[5])),
					MessageBox.TYPE_INFO, 10, domain = NOTIFICATIONDOMAIN)
		
		self._nextTodo()
	
	def _callFinishNotifiers(self, *args, **kwargs):
		for notifier in self.finishNotifiers.keys():
			print("[EPGRefresh] Debug: call " + str(notifier))
			self.finishNotifiers[notifier]()
		self._nextTodo()
	
	def finish(self, *args, **kwargs):
		if self.showPendingServicesMessageShown:
			self.msg.close()
		print("[EPGRefresh] Debug: Refresh finished!")
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("EPG refresh finished."), MessageBox.TYPE_INFO, 4, ENDNOTIFICATIONID, domain = NOTIFICATIONDOMAIN)
		epgrefreshtimer.cleanup()
		self.maybeStopAdapter()
                if config.plugins.epgrefresh.epgsave.value:
                        Notifications.AddPopup(_("EPG refresh save."), MessageBox.TYPE_INFO, 4, ENDNOTIFICATIONID, domain = NOTIFICATIONDOMAIN)
                        from enigma import eEPGCache
                        myEpg = None
                        myEpg = eEPGCache.getInstance()
                        myEpg.save()
		
		# shutdown if we're supposed to go to standby and not recording
		# forced scan --> manually started scan / non-forced scan --> automated scan
		# dontshutdownonabort overrides the shutdown
		if not self.forcedScan and config.plugins.epgrefresh.afterevent.value \
			and not Screens.Standby.inTryQuitMainloop:
			if (not config.plugins.epgrefresh.dontshutdownonabort.value and self.doStopRunningRefresh) or not self.doStopRunningRefresh:
				self.forcedScan = False
				if Screens.Standby.inStandby:
					RecordTimerEntry.TryQuitMainloop()
				else:
					Notifications.AddNotificationWithID("Shutdown", Screens.Standby.TryQuitMainloop, 1, domain = NOTIFICATIONDOMAIN)
		# reset doStopRunningRefresh here instead of cleanUp as it is needed to avoid shutdown
		self.doStopRunningRefresh = False
		self.forcedScan = False
		self.isrunning = False
		self._nextTodo()
		
	def refresh(self):
		if self.doStopRunningRefresh:
			self.cleanUp()
			return
		
		if self.forcedScan:
			self.nextService()
		else:
			# Abort if a scan finished later than our begin of timespan
			if self.beginOfTimespan < config.plugins.epgrefresh.lastscan.value:
				return
			if config.plugins.epgrefresh.force.value \
				or (Screens.Standby.inStandby and \
					not self.session.nav.RecordTimer.isRecording()):

				self.nextService()
			# We don't follow our rules here - If the Box is still in Standby and not recording we won't reach this line
			else:
				if not checkTimespan(
					config.plugins.epgrefresh.begin.value,
					config.plugins.epgrefresh.end.value):

					print("[EPGRefresh] Gone out of timespan while refreshing, sorry!")
					self.cleanUp()
				else:
					print("[EPGRefresh] Box no longer in Standby or Recording started, rescheduling")

					# Recheck later
					epgrefreshtimer.add(EPGRefreshTimerEntry(
							time() + config.plugins.epgrefresh.delay_standby.value*60,
							self.refresh,
							nocheck = True)
					)

	def createWaitTimer(self):
		self.beginOfTimespan = time()

		# Add wait timer to epgrefreshtimer
		epgrefreshtimer.add(EPGRefreshTimerEntry(time() + 30, self.prepareRefresh))

	def isServiceProtected(self, service):
		if not config.ParentalControl.configured.value \
			or not config.ParentalControl.servicepinactive.value:
			print("[EPGRefresh] DEBUG: ParentalControl not configured")
			return False
		print("[EPGRefresh] DEBUG: ParentalControl ProtectionLevel:" + str(parentalControl.getProtectionLevel(str(service))))
		return parentalControl.getProtectionLevel(str(service)) != -1

	def nextService(self):
		# Debug
		print("[EPGRefresh] Maybe zap to next service")

		# update pending services message box (if shown)
		if self.showPendingServicesMessageShown:
			print("[EPGRefresh] - MessageBox is shown. Update pending services")
			self.showPendingServices(self.session)			

		try:
			# Get next reference
			service = self.scanServices.pop(0)
		except IndexError:
			# Debug
			print("[EPGRefresh] Done refreshing EPG")

			# Clean up
			self.cleanUp()
		else:
			if self.myEpgCacheInstance is None and config.plugins.epgrefresh.usetimebased.value == False:
				# get eEPGCache instance if None and eEPGCache-signal based is used
				print("[EPGRefresh] - myEpgCacheInstance is None. Get it")
				self.myEpgCacheInstance = eEPGCache.getInstance()
				self.EpgCacheStateChanged_conn = self.myEpgCacheInstance.cacheState.connect(self._onCacheStateChanged)

			if self.isServiceProtected(service):
				if (not self.forcedScan) or config.plugins.epgrefresh.skipProtectedServices.value == "always":
					print("[EPGRefresh] Service is protected, skipping!")
					self.refresh()
					return
			
			# If the current adapter is unable to run in background and we are in fact in background now,
			# fall back to main picture
			if (not self.refreshAdapter.backgroundCapable and Screens.Standby.inStandby):
				print("[EPGRefresh] Adapter is not able to run in background or not available, falling back to MainPictureAdapter")
				self.maybeStopAdapter()
				self.refreshAdapter = MainPictureAdapter(self.session)
				self.refreshAdapter.prepare()

			if config.plugins.epgrefresh.usetimebased.value == False:
				# set timeout timer for eEPGCache-signal based refresh
				self.epgTimeoutTimer.start(5000, True)
			# Play next service
			# XXX: we might want to check the return value
			self.currentServiceRef = eServiceReference(service.sref)
			self.refreshAdapter.play(self.currentServiceRef)
			ref = ServiceReference(service.sref)
			channelname = ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
			print("[EPGRefresh] - Service is: %s" %(str(channelname)))
					
			if config.plugins.epgrefresh.usetimebased.value:
				# Start Timer
				delay = service.duration or config.plugins.epgrefresh.interval_seconds.value
				epgrefreshtimer.add(EPGRefreshTimerEntry(
					time() + delay,
					self.refresh,
					nocheck = True)
				)

	def resetEPG(self, session):
		self.reset_session=session
		# remove database
		if path.exists(config.misc.epgcache_filename.value):
			remove(config.misc.epgcache_filename.value)
		# create empty database
		connection = sqlite.connect(config.misc.epgcache_filename.value, timeout=10)
		connection.text_factory = str
		cursor = connection.cursor()
		cursor.execute("CREATE TABLE T_Service (id INTEGER PRIMARY KEY, sid INTEGER NOT NULL, tsid INTEGER, onid INTEGER, dvbnamespace INTEGER, changed DATETIME NOT NULL DEFAULT current_timestamp)")
		cursor.execute("CREATE TABLE T_Source (id INTEGER PRIMARY KEY, source_name TEXT NOT NULL, priority INTEGER NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp)")
		cursor.execute("CREATE TABLE T_Title (id INTEGER PRIMARY KEY, hash INTEGER NOT NULL UNIQUE, title TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp)")
		cursor.execute("CREATE TABLE T_Short_Description (id INTEGER PRIMARY KEY, hash INTEGER NOT NULL UNIQUE, short_description TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp)")
		cursor.execute("CREATE TABLE T_Extended_Description (id INTEGER PRIMARY KEY, hash INTEGER NOT NULL UNIQUE, extended_description TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp)")
		cursor.execute("CREATE TABLE T_Event (id INTEGER PRIMARY KEY, service_id INTEGER NOT NULL, begin_time INTEGER NOT NULL, duration INTEGER NOT NULL, source_id INTEGER NOT NULL, dvb_event_id INTEGER, changed DATETIME NOT NULL DEFAULT current_timestamp)")
		cursor.execute("CREATE TABLE T_Data (event_id INTEGER NOT NULL, title_id INTEGER, short_description_id INTEGER, extended_description_id INTEGER, iso_639_language_code TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp)")
		cursor.execute("CREATE INDEX data_title ON T_Data (title_id)")
		cursor.execute("CREATE INDEX data_shortdescr ON T_Data (short_description_id)")
		cursor.execute("CREATE INDEX data_extdescr ON T_Data (extended_description_id)")
		cursor.execute("CREATE INDEX service_sid ON T_Service (sid)")
		cursor.execute("CREATE INDEX event_service_id_begin_time ON T_Event (service_id, begin_time)")
		cursor.execute("CREATE INDEX event_dvb_id ON T_Event (dvb_event_id)")
		cursor.execute("CREATE INDEX data_event_id ON T_Data (event_id)")
		cursor.execute("CREATE TRIGGER tr_on_delete_cascade_t_event AFTER DELETE ON T_Event FOR EACH ROW BEGIN DELETE FROM T_Data WHERE event_id = OLD.id; END")
		cursor.execute("CREATE TRIGGER tr_on_delete_cascade_t_service_t_event AFTER DELETE ON T_Service FOR EACH ROW BEGIN DELETE FROM T_Event WHERE service_id = OLD.id; END")
		cursor.execute("CREATE TRIGGER tr_on_delete_cascade_t_data_t_title AFTER DELETE ON T_Data FOR EACH ROW WHEN ((SELECT event_id FROM T_Data WHERE title_id = OLD.title_id LIMIT 1) ISNULL) BEGIN DELETE FROM T_Title WHERE id = OLD.title_id; END")
		cursor.execute("CREATE TRIGGER tr_on_delete_cascade_t_data_t_short_description AFTER DELETE ON T_Data FOR EACH ROW WHEN ((SELECT event_id FROM T_Data WHERE short_description_id = OLD.short_description_id LIMIT 1) ISNULL) BEGIN DELETE FROM T_Short_Description WHERE id = OLD.short_description_id; END")
		cursor.execute("CREATE TRIGGER tr_on_delete_cascade_t_data_t_extended_description AFTER DELETE ON T_Data FOR EACH ROW WHEN ((SELECT event_id FROM T_Data WHERE extended_description_id = OLD.extended_description_id LIMIT 1) ISNULL) BEGIN DELETE FROM T_Extended_Description WHERE id = OLD.extended_description_id; END")
		cursor.execute("CREATE TRIGGER tr_on_update_cascade_t_data AFTER UPDATE ON T_Data FOR EACH ROW WHEN (OLD.title_id <> NEW.title_id AND ((SELECT event_id FROM T_Data WHERE title_id = OLD.title_id LIMIT 1) ISNULL)) BEGIN DELETE FROM T_Title WHERE id = OLD.title_id; END")
		cursor.execute("INSERT INTO T_Source (id,source_name,priority) VALUES('0','Sky Private EPG','0')")
		cursor.execute("INSERT INTO T_Source (id,source_name,priority) VALUES('1','DVB Now/Next Table','0')")
		cursor.execute("INSERT INTO T_Source (id,source_name,priority) VALUES('2','DVB Schedule (same Transponder)','0')")
		cursor.execute("INSERT INTO T_Source (id,source_name,priority) VALUES('3','DVB Schedule Other (other Transponder)','0')")
		cursor.execute("INSERT INTO T_Source (id,source_name,priority) VALUES('4','Viasat','0')")
                connection.commit()
		cursor.close()
		connection.close()
		self.myEpgCacheInstance = eEPGCache.getInstance()
		self.EpgCacheStateChanged_conn = self.myEpgCacheInstance.cacheState.connect(self.resetStateChanged)
		self.myEpgCacheInstance.load()                   

	def resetStateChanged(self, state):
		if state.state == cachestate.load_finished:
			self.reset_session.openWithCallback(self.doRestart, MessageBox, \
				text = _("Reset")+" "+_("EPG.db")+" "+_("successful")+"\n\n"+_("Restart GUI now?"), \
				type = MessageBox.TYPE_YESNO, default = True, timeout = 10)

	def doRestart(self, answer):
		if answer is not None:
			if answer:
				quitMainloop(3)
			
	def showPendingServices(self, session):
		LISTMAX = 15
		servcounter = 0
		try:
			servtxt = ""
			for service in self.scanServices:
				if self.isServiceProtected(service):
					if not self.forcedScan or config.plugins.epgrefresh.skipProtectedServices.value == "always":
						continue
				if servcounter < LISTMAX:
					ref = ServiceReference(service.sref)
					txt = ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
					servtxt = servtxt + str(txt) + "\n"
				servcounter = servcounter + 1
			
			if servcounter > LISTMAX:
				servtxt = servtxt + _("%d more services") % (servcounter-LISTMAX)
			
			# open message box only if not already shown
			if self.showPendingServicesMessageShown == False:
				self.msg = session.open(MessageBox, _("Following Services have to be scanned:") \
					+ "\n" + servtxt, MessageBox.TYPE_INFO)
				# update state for pending services message box on close
				self.msg.onClose.append(self.setMessageBoxState)
				self.showPendingServicesMessageShown = True
			else:
				self.msg["text"].setText(_("Following Services have to be scanned:") + "\n" + servtxt)
			self.msg["Text"].setText(_("Remaining services: %d") %(servcounter))	
		except:
			print("[EPGRefresh] showPendingServices Error!")
			print_exc(file=stdout)
			
	def setMessageBoxState(self):
		self.showPendingServicesMessageShown = False				

epgrefresh = EPGRefresh()
