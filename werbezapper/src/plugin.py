#!/usr/bin/python
# -*- coding: utf-8 -*-

from Components.config import config, ConfigSubsection, ConfigNumber, ConfigYesNo
from Plugins.Plugin import PluginDescriptor
from Components.PluginComponent import plugins
from Screens.Screen import Screen
from WerbeZapper import WerbeZapperSetup, plugin_version
from Tools.BoundFunction import boundFunction
#from . import _

zapperInstance = None

def getExtMenuEntryText(configElement = None):
	if configElement == config.werbezapper.show_startstop_timer_extentry:
		if zapperInstance and zapperInstance.zap_timer.isActive():
			pluginname = _("WerbeZapper stop timer")
		else:
			pluginname = _("WerbeZapper start timer")
			pluginname += " (%smin)" % config.werbezapper.duration.value
	else:
		if zapperInstance and zapperInstance.monitored_service:
			pluginname = _("WerbeZapper stop monitoring")
		else:
			pluginname = _("WerbeZapper start monitoring")
	return pluginname

#add/remove extensionmenu-entry without e2-restart
def AddRemovePluginDescriptorExtEntry(configElement = None):
	if configElement == config.werbezapper.show_startstop_timer_extentry:
		pd = startStopTimerPluginDescriptor
	else:
		pd = startStopMonitoringPluginDescriptor
	show_entry = configElement.value
	pdList = [(p) for p in plugins.getPlugins(where=pd.where[:]) if p is pd]
	if show_entry:
		if pd not in pdList:
			pd.name = getExtMenuEntryText(configElement)
			plugins.addPlugin(pd)
	else:
		for pd in pdList:
			plugins.removePlugin(pd)

# Config options
config.werbezapper          = ConfigSubsection()
config.werbezapper.duration = ConfigNumber(default = 5)
config.werbezapper.show_zappingmessage_permanently    = ConfigYesNo(default = True)
config.werbezapper.show_startstop_timer_extentry = ConfigYesNo(default = True)
config.werbezapper.show_startstop_monitoring_extentry = ConfigYesNo(default = True)
config.werbezapper.show_startstop_timer_extentry.addNotifier(AddRemovePluginDescriptorExtEntry, False, False)
config.werbezapper.show_startstop_monitoring_extentry.addNotifier(AddRemovePluginDescriptorExtEntry, False, False)

def setZapperInstance(session, servicelist):
	global zapperInstance
	if zapperInstance is None:
		import WerbeZapper
		reload(WerbeZapper)
		zapperInstance = session.instantiateDialog( WerbeZapper.WerbeZapper, servicelist, boundFunction(cleanup, session) )

# Mainfunction
def main(session, servicelist, **kwargs):
	# Create Instance if none present
	setZapperInstance(session, servicelist)
	# Show dialog
	zapperInstance.showSelection()

# Instant start/stop zapping timer
def startstopTimer(session, servicelist, **kwargs):
	# Create Instance if none present
	setZapperInstance(session, servicelist)
	# Start or stop timer
	if not zapperInstance.zap_timer.isActive():
		duration = int(config.werbezapper.duration.value)
		zapperInstance.startTimer(duration)
	else:
		zapperInstance.stopTimer()

# Instant start/stop monitoring
def startstopMonitoring(session, servicelist, **kwargs):
	# Create Instance if none present
	setZapperInstance(session, servicelist)
	# Start or stop monitoring
	if not zapperInstance.monitor_timer.isActive():
		zapperInstance.startMonitoring()
	else:
		zapperInstance.stopMonitoring()

#WerbeZapper setup
def setup(session, **kwargs):
	session.open(WerbeZapperSetup)

def cleanup(session):
	global zapperInstance
	if zapperInstance is not None:
		zapperInstance.shutdown()
		session.deleteDialog(zapperInstance)
		zapperInstance = None

plugin_name = _("WerbeZapper start timer")
plugin_name += " (%smin)" % config.werbezapper.duration.value
startStopTimerPluginDescriptor = PluginDescriptor(name = plugin_name, description = _("Start / Stop zapping timer"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = startstopTimer, needsRestart = False, )

startStopMonitoringPluginDescriptor = PluginDescriptor(name = _("WerbeZapper start monitoring"), description = _("Start / Stop monitoring instantly"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = startstopMonitoring, needsRestart = False, )

def Plugins(**kwargs):
	descriptors = []
	
	descriptors.append(PluginDescriptor(name = "WerbeZapper", description = _("Automatically zaps back to current service after given Time"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = main, needsRestart = False, ))
	
	if config.werbezapper.show_startstop_timer_extentry.value:
		descriptors.append(startStopTimerPluginDescriptor)
	
	if config.werbezapper.show_startstop_monitoring_extentry.value:
		descriptors.append(startStopMonitoringPluginDescriptor)
	
	desc = _("%(pname)s Setup (v%(pversion)s)") % {"pname": "WerbeZapper", "pversion": plugin_version}
	descriptors.append( PluginDescriptor(name = _("WerbeZapper setup"), description=_(desc), where= PluginDescriptor.WHERE_PLUGINMENU, fnc = setup, needsRestart = False, icon="werbezapper.svg" ))
	
	return descriptors

