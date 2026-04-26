#!/usr/bin/python
# -*- coding: utf-8 -*-

from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eTimer, iPlayableService, eEPGCache, getDesktop, ePoint, eSize
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import config, getConfigListEntry
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from ServiceReference import ServiceReference
from time import time
from math import floor as math_floor
from . import _

sz_w = getDesktop(0).size().width()
plugin_version = "0.1-r1"

class WerbeZapperChoiceBox(ChoiceBox):
	def __init__(self, session, title="", list=[], keys=None, selection=0, zap_time=0, zap_service=None, monitored_event=None, monitored_service=None, skin_name=[]):
		ChoiceBox.__init__(self, session, title, list, keys, selection, skin_name)
		
		self.update_timer = eTimer()
		self.update_timer_conn = self.update_timer.timeout.connect(self.update)
		
		self.zap_time = zap_time
		self.zap_service = zap_service
		self.monitored_event = monitored_event
		self.monitored_service = monitored_service
		
		# Start timer to update the ChoiceBox every second
		self.update_timer.start(1000)
		self.setTitle( "WerbeZapper" + " v%s" % plugin_version)
		self.update()

	def update(self):
		#TODO getServiceName() begin end
		text = ""
		if self.monitored_event:
			name = self.monitored_event and self.monitored_event.getEventName()
			if len(name) > 25: name = name[:25] + "..."
			remaining = ( self.monitored_event.getDuration() - ( time() - self.monitored_event.getBeginTime() ) )
			if remaining > 0:
				text += _("Monitoring: %s (%d:%02d Min)") % (name, remaining/60, remaining%60)
		if self.zap_time:
			remaining = int( math_floor( self.zap_time - time() ) )
			if remaining > 0:
				ServiceName = ServiceReference(self.zap_service).getServiceName()
				if not self.monitored_event:
					text += _("Zapping back in %d:%02d Min") % (remaining/60, remaining%60)
					text += "\n" + "(%s)" % ServiceName
				else:
					text += "\n" + _("Zapping back in %d:%02d Min") % (remaining/60, remaining%60)
					text += " (%s)" % ServiceName
		if text:
			self.setText(text)

	def setText(self, text):
		self["text"].setText(text)

	def close(self, param=None):
		self.update_timer.stop()
		ChoiceBox.close(self, param)


class WerbeZapper(Screen):
	"""Simple Plugin to automatically zap back to a Service after a given amount
	   of time."""
	def __init__(self, session, servicelist, cleanupfnc = None):
		Screen.__init__(self, session)
		
		# Save Session&Servicelist
		self.session = session
		self.servicelist = servicelist
		
		# Create zap timer
		self.zap_time = None
		self.zap_timer = eTimer()
		self.zap_timer_conn = self.zap_timer.timeout.connect(self.zap)

		# Create event monitoring timer
		self.monitor_timer = eTimer()
		self.monitor_timer_conn = self.monitor_timer.timeout.connect(self.stopMonitoring)

		# Create delay timer
		self.delay_timer = eTimer()
		self.delay_timer_conn = self.delay_timer.timeout.connect(self.zappedAway)

		# Initialize services
		self.zap_service = None
		self.move_service = None
		self.root = None
		
		#	Initialize monitoring
		self.monitored_service = None
		self.monitored_event = None
		self.__event_tracker = None
		
		# Keep Cleanup
		self.cleanupfnc = cleanupfnc
		
		self.zapbackMessage = None

	def showSelection(self):
		title = _("When to Zap back?")
		select = int(config.werbezapper.duration.value)
		keys = []

		# Number keys
		choices = [
					( _("Custom"), 'custom'),
					('1 ' + _('minute'),  1),
					('2 ' + _('minutes'), 2),
					('3 ' + _('minutes'), 3),
					('4 ' + _('minutes'), 4),
					('5 ' + _('minutes'), 5),
					('6 ' + _('minutes'), 6),
					('7 ' + _('minutes'), 7),
					('8 ' + _('minutes'), 8),
					('9 ' + _('minutes'), 9),
					]
		keys.extend( [ "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ] )

		# Dummy entry to seperate the color keys
		choices.append( ( "--", ) )
		keys.append( "" )  # No key

		# Blue key - Covers the monitoring functions without closing Werbezapper
		if self.monitor_timer.isActive():
			choices.append( ( _("Stop monitoring"), 'stopmonitoring' ) )
		else:
			choices.append( ( _("Start monitoring"), 'startmonitoring' ) )
		keys.append( "blue" )

		# Red key - Covers all stop and close functions
		if self.zap_timer.isActive():
			choices.append( ( _("Stop timer"), 'stoptimer' ) )
			keys.append( "red" )

		# Green key - Manual rezap
		if self.zap_timer.isActive() and self.zap_service != self.session.nav.getCurrentlyPlayingServiceReference():
			ServiceName = ServiceReference(self.zap_service).getServiceName()
			choices.append( ( _("Rezap") + " (%s)" % ServiceName, 'rezap' ) )
			keys.append( "green" )
		
		# Yellow key - setup
		choices.append( ( _("Setup"), 'setup' ) )
		keys.append( "yellow" )

		# Select Timer Length
		self.session.openWithCallback(
			self.choicesCallback,
			WerbeZapperChoiceBox,
			title,
			choices,
			keys,
			select,
			self.zap_time,
			self.zap_service,
			self.monitored_event,
			self.monitored_service
		)

	def choicesCallback(self, result):
		result = result and result[1]
		
		if result == "custom":
			from Screens.InputBox import InputBox
			from Components.Input import Input

			#TODO allow custom input in seconds or parts of a minute 1.5
			self.session.openWithCallback(self.inputCallback, InputBox, title=_("How many minutes to wait until zapping back?"), text="10", maxSize=False, type=Input.NUMBER)
			return
		
		elif result == "startmonitoring":
			self.startMonitoring()
		
		elif result == "stopmonitoring":
			self.stopMonitoring()
		
		elif result == "rezap":
			self.stopTimer()
			self.zap(False)
		
		elif result == "stoptimer":
			self.stopTimer()
		
		elif result == "setup":
			self.session.open(WerbeZapperSetup)
		
		elif isinstance(result, int):
			self.startTimer(result)
		
		self.cleanup()

	def inputCallback(self, result):
		if result is not None:
			self.startTimer(int(result))
		else:
			# Clean up if possible
			self.cleanup()

	def changeExtMenuEntryText(self, type="timer"):
		if type == "timer":
			from plugin import startstopTimer as startstop_call
			if self.zap_timer.isActive():
				pluginname = _("WerbeZapper stop timer")
			else:
				pluginname = _("WerbeZapper start timer")
				pluginname += _(" (%smin)") % config.werbezapper.duration.value
		else:
			from plugin import startstopMonitoring as startstop_call
			if self.monitored_service:
				pluginname = _("WerbeZapper stop monitoring")
			else:
				pluginname = _("WerbeZapper start monitoring")
		
		pdList = [(p) for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_EXTENSIONSMENU]) if p.__call__ == startstop_call]
		for pd in pdList:
			pd.name = pluginname

	def startMonitoring(self, notify=True):
		# Stop active zap timer
		self.stopTimer()
		
		# Get current service and event
		service = self.session.nav.getCurrentService()
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.monitored_service = ref

		# Notify us on new services
		# ServiceEventTracker will remove itself on close
		if not self.__event_tracker:
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evStart: self.serviceStarted,
			})

		# Get event information
		info = service and service.info()
		event = info and info.getEvent(0)
		if not event:
			# Alternative to get the current event
			epg = eEPGCache.getInstance()
			event = ref and ref.valid() and epg.lookupEventTime(ref, -1)
		if event:
			# Set monitoring end time
			self.monitored_event = event
			duration = event.getDuration() - ( time() - event.getBeginTime() )
			self.monitor_timer.startLongTimer( int( duration ) )
			if notify:
				name = event and event.getEventName()
				infotext = _("WerbeZapper\nMonitoring started\n%s") % (name)
				self.session.toastManager.showToast(infotext, 4)
		else:
			#TEST SF2 or something without an valid epg
			#IDEA detect event is finished
			#IDEA inputbox monitoring in minutes
			if notify:
				infotext = _("WerbeZapper\nMonitoring started unlimited\nHas to be deactivated manually")
				self.session.toastManager.showToast(infotext, 4)
		
		self.changeExtMenuEntryText("monitoring")

	def stopMonitoring(self, notify=True):
		
		# Stop active zap timer
		self.stopTimer()
		
		self.monitor_timer.stop()
		
		if notify:
			# Notify the User that the monitoring is ending
			name = self.monitored_event and self.monitored_event.getEventName()
			infotext = _("WerbeZapper\nMonitoring ends\n%s") % (name)
			self.session.toastManager.showToast(infotext, 4)
		
		self.monitored_service = None
		self.monitored_event = None
		
		self.changeExtMenuEntryText("monitoring")

	def serviceStarted(self):
		# Verify monitoring is active
		if self.monitor_timer.isActive():
			# Verify there is no active zap timer
			if not self.zap_timer.isActive():
				# Is the zap away check already running
				if not self.delay_timer.isActive():
					# Delay the zap away check only once
					self.delay_timer.startLongTimer( 3 )

	def zappedAway(self):
		# Verify that the currently played service has changed
		# Avoid that we trigger on a background recording or streaming service
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		if ref and self.monitored_service != ref:
			# Start zap timer
			self.startTimer(zapto=self.monitored_service)

	def startTimer(self, duration=0, notify=True, zapto=None):
		if duration > 0:
			# Save the last selected zap time for reusing it later
			config.werbezapper.duration.value = duration
			config.werbezapper.duration.save()
		else:
			# Reuse last duration
			duration = int(config.werbezapper.duration.value)
		
		# Keep any service related information (zap_service might not equal move_service -> subservices)
		self.zap_service = zapto or self.session.nav.getCurrentlyPlayingServiceReference()
		self.move_service = zapto if zapto else self.servicelist.getCurrentSelection()
		self.root = self.servicelist.getRoot()

		# Start Timer
		self.zap_time = time() + ( duration * 60 )
		self.zap_timer.startLongTimer( int( duration * 60 ) )
		
		if notify:
			ServiceName = ServiceReference(self.zap_service).getServiceName()
			if self.zapbackMessage:
				self.session.deleteDialog(self.zapbackMessage)
				self.zapbackMessage = None
			if config.werbezapper.show_zappingmessage_permanently.value:
				self.zapbackMessage = self.session.instantiateDialog(ZapBackMessage, self.zap_time, ServiceName)
				self.zapbackMessage.show()
			else:
				text = "WerbeZapper" + " - " 
				text += _("Zapping back in %d Minute(s)") % (duration)
				text += " (%s)" % ServiceName
				self.session.toastManager.showToast(text, 5)
		
		self.changeExtMenuEntryText("timer")

	def stopTimer(self):
		# Stop Timer
		self.zap_timer.stop()
		self.zap_time = None
		if self.zapbackMessage:
			self.session.deleteDialog(self.zapbackMessage)
			self.zapbackMessage = None
		
		self.changeExtMenuEntryText("timer")

	def zap(self, notify=True):
		if self.zap_service is not None:
			if self.root:
				import ServiceReference
				if not self.servicelist.preEnterPath(str(ServiceReference.ServiceReference(self.root))):
					if self.servicelist.isBasePathEqual(self.root):
						self.servicelist.pathUp()
						self.servicelist.enterPath(self.root)
					else:
						currentRoot = self.servicelist.getRoot()
						if currentRoot is None or currentRoot != self.root:
							#self.servicelist.clearPath() #not works if current service in an other bouquet
							self.servicelist.pathUp() #works if current service in an other bouquet
							self.servicelist.enterPath(self.root)

			if self.move_service:
				self.servicelist.setCurrentSelection(self.move_service)
				self.servicelist.zap()

			# Play zap_service (won't rezap if service equals to move_service)
			self.session.nav.playService(self.zap_service)
		
		#close zapping dialog and change menu entry text
		self.stopTimer()

		if notify:
			# Remind the User what happens here
			duration = int(config.werbezapper.duration.value)
			if duration == 1:
				mintext = _(" after %s minute")
			else:
				mintext = _(" after %s minutes")
			infotext = "WerbeZapper" + " - " + _("Zapped back") + mintext % duration
			self.session.toastManager.showToast(infotext, 5)

		# Cleanup if end timer is not running
		if not self.monitor_timer.isActive():
			
			# Reset services
			self.zap_service = None
			self.move_service = None
			self.root = None

	def cleanup(self):
		# Clean up if no timer is running
		if self.monitor_timer and not self.monitor_timer.isActive() and self.zap_timer and not self.zap_timer.isActive():
			if self.cleanupfnc:
				self.cleanupfnc()

	def shutdown(self):
		self.zap_timer_conn = None
		self.zap_timer = None
		self.monitor_timer_conn = None
		self.monitor_timer = None


class ZapBackMessage(Screen):
	if sz_w == 2560:
		skin = """
		<screen backgroundColor="#ff000000" flags="wfNoBorder" name="ZapBackMessage" position="center,10" size="2000,0">
			<widget backgroundColor="#28343b" cornerDia="50" font="Regular;36" foregroundColor="white" halign="center" name="text" size="2000,0" valign="center"/>
		</screen>"""
	elif sz_w == 1920:
		skin = """
		<screen backgroundColor="#ff000000" flags="wfNoBorder" name="ZapBackMessage" position="center,7" size="1200,0">
			<widget backgroundColor="background" cornerRadius="40" font="Regular;32" halign="center" name="text" size="1200,0" valign="center"/>
		</screen>"""
	else:
		skin = """
		<screen backgroundColor="#ff000000" flags="wfNoBorder" name="ZapBackMessage" position="center,5" size="700,0">
			<widget backgroundColor="background" cornerRadius="30" font="Regular;21" halign="center" name="text" size="700,0" valign="center"/>
		</screen>"""

	def __init__(self, session, zap_time=0, service_name=""):
		Screen.__init__(self, session)

		self.service_name = service_name
		self.zap_time = zap_time
		
		self.refreshText_timer = eTimer()
		self.refreshText_timer_conn = self.refreshText_timer.timeout.connect(self.refreshZappingText)
		self.timerRunning = False
		
		self["text"] = Label(self.getZappingText())
		self.onLayoutFinish.append(self._onLayoutFinish)

	def refreshZappingText(self):
		self["text"].setText(self.getZappingText())

	def getZappingText(self):
		remaining = int( math_floor( self.zap_time - time() ) )
		text = "WerbeZapper" + " - " 
		text += _("Zapping back in %d:%02d Min") % (remaining/60, remaining%60) 
		text += " (%s)" % self.service_name
		return text

	def _onLayoutFinish(self):
		orgwidth = self.instance.size().width()
		orgpos = self.instance.position()
		textsize = self["text"].getSize()

		# y size still must be fixed in font stuff...
		if sz_w == 1280:
			textsize = (textsize[0] + 20, textsize[1] + 15)
		elif sz_w == 1920:
			textsize = (textsize[0] + 35, textsize[1] + 20)
		else:
			textsize = (textsize[0] + 50, textsize[1] + 25)
		self.instance.resize(eSize(*textsize))
		self["text"].instance.resize(eSize(*textsize))

		# center window
		newwidth = textsize[0]
		self.instance.move(ePoint(orgpos.x() + (orgwidth - newwidth) // 2, orgpos.y()))
		
		# Start timer to update the ZappinText every second
		self.refreshText_timer.start(1000)

class WerbeZapperSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self.setTitle(_("%(pname)s Setup (v%(pversion)s)") % {"pname": "WerbeZapper", "pversion": plugin_version})
		
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": 	self.keyCancel,
				"green": 	self.keySave,
			},-2)
		
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)
		self.createSetup()

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("show zapping back info permanently"), config.werbezapper.show_zappingmessage_permanently))
		self.list.append(getConfigListEntry(_("show start/stop timer entry in extensionsmenu"), config.werbezapper.show_startstop_timer_extentry))
		self.list.append(getConfigListEntry(_("show start/stop monitoring entry in extensionsmenu"), config.werbezapper.show_startstop_monitoring_extentry))
		self["config"].setList(self.list)

