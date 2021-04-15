#
#  AutomaticTimerlistCleanup E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Property GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from enigma import eTimer
from time import time, strftime, localtime
from timer import TimerEntry

config.plugins.automatictimerlistcleanup = ConfigSubsection()
config.plugins.automatictimerlistcleanup.type = ConfigSelection(default="-1", choices=[("-1", _("disabled")), ("0", _("immediately after recording")), ("1", _("older than 1 day")), ("3", _("older than 3 days")), ("7", _("older than 1 week")), ("14", _("older than 2 weeks")), ("28", _("older than 4 weeks")), ("42", _("older than 6 weeks"))])


class AutomaticTimerlistCleanUpSetup(Screen, ConfigListScreen): # config

	skin = """
		<screen position="center,center" size="620,200" title="%s" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="600,1" backgroundColor="grey" />
			<widget name="config" position="10,60" size="600,120" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>""" % _("Automatic Timerlist Cleanup Setup")

	def __init__(self, session):
		Screen.__init__(self, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.list = []
		self.list.append(getConfigListEntry(_("Cleanup timerlist-entries"), config.plugins.automatictimerlistcleanup.type))
		ConfigListScreen.__init__(self, self.list, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
		}, -2)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		self.close(True)

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)


class AutomaticTimerlistCleanUp:
	TIMER_INTERVAL = 86400 # check timerlist every 24 hour

	def __init__(self, session):
		self.session = session
		print "[AutomaticTimerlistCleanUp] Starting AutomaticTimerlistCleanUp..."
		self.timer = eTimer() # check timer
		self.timer_conn = self.timer.timeout.connect(self.cleanupTimerlist)
		self.cleanupTimerlist() # always check immediately after starting plugin
		config.plugins.automatictimerlistcleanup.type.addNotifier(self.configChange, initial_call=False)
		self.session.nav.RecordTimer.on_state_change.append(self.timerentryOnStateChange)

	def cleanupTimerlist(self):
		if int(config.plugins.automatictimerlistcleanup.type.value) > -1: # check only if feature is enabled
			value = time() - int(config.plugins.automatictimerlistcleanup.type.value) * 86400 # calculate end time for comparison with processed timers
			print "[AutomaticTimerlistCleanUp] Cleaning up timerlist-entries older than ", strftime("%c", localtime(value))
			self.session.nav.RecordTimer.processed_timers = [timerentry for timerentry in self.session.nav.RecordTimer.processed_timers if timerentry.disabled or (timerentry.end and timerentry.end > value)] # cleanup timerlist
			print "[AutomaticTimerlistCleanUp] Next automatic timerlist cleanup at ", strftime("%c", localtime(time() + self.TIMER_INTERVAL))
			self.timer.startLongTimer(self.TIMER_INTERVAL) # check again in x secs
		else:
			print "[AutomaticTimerlistCleanUp] disabled"
		
	def configChange(self, configElement=None):
		# config was changed in setup
		if self.timer.isActive(): # stop timer if running
			self.timer.stop()
		print "[AutomaticTimerlistCleanUp] Setup values have changed"
		if int(config.plugins.automatictimerlistcleanup.type.value) > -1:
			print "[AutomaticTimerlistCleanUp] Next automatic timerlist cleanup at ", strftime("%c", localtime(time() + 120))
			self.timer.startLongTimer(120) # check timerlist in 2 minutes after changing 
		else:
			print "[AutomaticTimerlistCleanUp] disabled"
		
	def timerentryOnStateChange(self, timer):
		if int(config.plugins.automatictimerlistcleanup.type.value) > -1 and timer.state == TimerEntry.StateEnded and timer.cancelled is not True: #if enabled, timerentry ended and it was not cancelled by user
			print "[AutomaticTimerlistCleanUp] Timerentry has been changed to StateEnd"
			if self.timer.isActive(): # stop timer if running
				self.timer.stop()
			self.cleanupTimerlist() # and check if entries have to be cleaned up in the timerlist


def autostart(session, **kwargs):
	AutomaticTimerlistCleanUp(session) # start plugin at sessionstart
	

def setup(session, **kwargs):
	session.open(AutomaticTimerlistCleanUpSetup) # start setup


def startSetup(menuid):
	if menuid != "services_recordings": # show setup only in system level menu
		return []
	return [(_("Automatic Timerlist Cleanup Setup"), setup, "automatictimerlistcleanup", 46)]
	

def Plugins(**kwargs):
	return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart), PluginDescriptor(name="Automatic Timerlist Cleanup Setup", description=_("Automatic Timerlist Cleanup Setup"), where=PluginDescriptor.WHERE_MENU, fnc=startSetup)]
