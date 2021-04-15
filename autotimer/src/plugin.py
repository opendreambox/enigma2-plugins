from __future__ import print_function

from twisted.internet import reactor

# GUI (Screens)
from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

from Components.config import config
from os import path as os_path

from Logger import doLog

from AutoTimer import AutoTimer
autotimer = AutoTimer()
autopoller = None

AUTOTIMER_VERSION = "4.3.2"
NOTIFICATIONDOMAIN = "AutoTimer"

#pragma mark - Help
try:
	from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS
	reader = XMLHelpReader(resolveFilename(SCOPE_PLUGINS, "Extensions/AutoTimer/mphelp.xml"), translate=_)
	autotimerHelp = registerHelp(*reader)
except Exception as e:
	doLog("[AutoTimer] Unable to initialize MPHelp:", e,"- Help not available!")
	autotimerHelp = None
#pragma mark -

# Notification-Domain
from Tools.Notifications import notificationQueue
try:
	notificationQueue.registerDomain(NOTIFICATIONDOMAIN, _("AutoTimer"), deferred_callable=True)
except Exception as e:
	print("[AutoTimer] Error registering Notification-Domain:", e)
# Autostart

def autostart(reason, **kwargs):
	global autopoller

	# Startup
	if reason == 0 and config.plugins.autotimer.autopoll.value:
		# Start Poller
		from AutoPoller import AutoPoller
		autopoller = AutoPoller()
		autopoller.start()

		# Install NPB, main is too late because the Browser is already running
		from Plugins.SystemPlugins.Toolkit import NotifiablePluginBrowser
		NotifiablePluginBrowser.install()
	# Shutdown
	elif reason == 1:
		# Stop Poller
		if autopoller is not None:
			autopoller.stop()
			autopoller = None

		# We re-read the config so we won't save wrong information
		try:
			autotimer.readXml()
		except Exception:
			# XXX: we should at least dump the error
			pass
		else:
			autotimer.writeXml()

# Webgui
def sessionstart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		try:
			from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
			from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage
			from twisted.web import static
			from twisted.python import util
			from WebChilds.UploadResource import UploadResource

			from AutoTimerResource import AutoTimerDoParseResource, \
				AutoTimerListAutoTimerResource, AutoTimerAddOrEditAutoTimerResource, \
				AutoTimerRemoveAutoTimerResource, AutoTimerChangeSettingsResource, \
				AutoTimerSettingsResource, AutoTimerSimulateResource, AutoTimerTestResource, \
				AutoTimerUploadXMLConfigurationAutoTimerResource, AutoTimerAddXMLAutoTimerResource, API_VERSION
		except ImportError as ie:
			pass
		else:
			if hasattr(static.File, 'render_GET'):
				class File(static.File):
					def render_POST(self, request):
						return self.render_GET(request)
			else:
				File = static.File

			# webapi
			root = AutoTimerListAutoTimerResource()
			root.putChild('parse', AutoTimerDoParseResource())
			root.putChild('remove', AutoTimerRemoveAutoTimerResource())
			root.putChild('upload_xmlconfiguration', AutoTimerUploadXMLConfigurationAutoTimerResource())
			root.putChild('add_xmltimer', AutoTimerAddXMLAutoTimerResource())
			root.putChild('edit', AutoTimerAddOrEditAutoTimerResource())
			root.putChild('get', AutoTimerSettingsResource())
			root.putChild('set', AutoTimerChangeSettingsResource())
			root.putChild('simulate', AutoTimerSimulateResource())
			root.putChild('test', AutoTimerTestResource())
			addExternalChild(("autotimer", root, "AutoTimer-Plugin", API_VERSION, False))

			# webgui
			session = kwargs["session"]
			root = File(util.sibpath(__file__, "web-data"))
			root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True))
			root.putChild('tmp', File('/tmp'))
			root.putChild("uploadfile", UploadResource(session))
			addExternalChild(("autotimereditor", root, "AutoTimer", "1", True))

# Mainfunction
def main(session, **kwargs):
	global autopoller

	try:
		autotimer.readXml()
	except SyntaxError as se:
		session.open(
			MessageBox,
			_("Your config file is not well-formed:\n%s") % (str(se)),
			type=MessageBox.TYPE_ERROR,
			timeout=10
		)
		return

	# Do not run in background while editing, this might screw things up
	if autopoller is not None:
		autopoller.pause()

	from AutoTimerOverview import AutoTimerOverview
	session.openWithCallback(
		editCallback,
		AutoTimerOverview,
		autotimer
	)

def handleAutoPoller():
	global autopoller

	# Start autopoller again if wanted
	if config.plugins.autotimer.autopoll.value:
		if autopoller is None:
			from AutoPoller import AutoPoller
			autopoller = AutoPoller()
		autopoller.start(initial=False)
	# Remove instance if not running in background
	else:
		autopoller = None

def editCallback(session):
	# Don't parse EPG if editing was canceled
	if session is not None:
		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()
		delay = config.plugins.autotimer.editdelay.value
		parseFunc = lambda: autotimer.parseEPGAsync().addCallback(parseEPGCallback)#.addErrback(parseEPGErrback)
		reactor.callLater(delay, parseFunc)
	else:
		handleAutoPoller()

#def parseEPGErrback(failure):
#	AddPopup(
#		_("AutoTimer failed with error %s" (str(failure),)),
#	)
#
#	# Save xml
#	if config.plugins.autotimer.always_write_config.value:
#		autotimer.writeXml()
#	handleAutoPoller()

def showFinishPopup(ret):
	
	#prepare searchlogentries to show in finishPopup
	searchlog_txt = ""
	logpath = config.plugins.autotimer.searchlog_path.value
	if logpath == "?likeATlog?":
		logpath = os_path.dirname(config.plugins.autotimer.log_file.value)
	path_search_log = os_path.join(logpath, "autotimer_search.log")
	if os_path.exists(path_search_log):
		searchlog_txt = open(path_search_log).read()
		#find last log in logfile 
		if "\n########## " in searchlog_txt:
			searchlog_txt = searchlog_txt.split("\n########## ")
			searchlog_txt = str(searchlog_txt[-1]).split("\n")[2:]
			
			#check count and length of searchlog_entries
			maxlistcount = 10
			maxtextlength = 55
			listcount = len(searchlog_txt)
			searchlog_txt = searchlog_txt[:maxlistcount]
			for i, entry in enumerate(searchlog_txt):
				if len(entry) > maxtextlength:
					searchlog_txt[i] = entry[:maxtextlength-3] + "..."
			searchlog_txt = "\n".join(searchlog_txt)
			if listcount > maxlistcount+1:
				searchlog_txt += "\n" + "and %d searchlog-entries more ..." % (listcount-maxlistcount)

	AddPopup(_("Found a total of %(matches)d matching Events.\n%(timer)d Timer were added and\n%(modified)d modified,\n%(conflicts)d conflicts encountered,\n%(similars)d similars added.") %
		{"matches":ret[0], "timer":ret[1], "modified":ret[2], "conflicts":len(ret[4]), "similars":len(ret[5])} + "\n\n" + str(searchlog_txt),
		MessageBox.TYPE_INFO, config.plugins.autotimer.popup_timeout.value, domain=NOTIFICATIONDOMAIN, id='AT_PopUp_ID_ParseEPGCallback')

def parseEPGCallback(ret):
	
	showFinishPopup(ret)
	
	# Save xml
	if config.plugins.autotimer.always_write_config.value:
		autotimer.writeXml()
	handleAutoPoller()

# Movielist
def movielist(session, service, **kwargs):
	from AutoTimerEditor import addAutotimerFromService
	addAutotimerFromService(session, service)

# Event Info
def eventinfo(session, servicelist, **kwargs):
	from AutoTimerEditor import AutoTimerEPGSelection
	ref = session.nav.getCurrentlyPlayingServiceReference()
	session.open(AutoTimerEPGSelection, ref)

# EventView or EPGSelection
def eventview(session, event, ref):
	from AutoTimerEditor import addAutotimerFromEvent, addAutotimerFromService, importerCallback
	if ref.getPath() and ref.getPath()[0] == "/":
		from enigma import eServiceReference
		addAutotimerFromService(session, eServiceReference(str(ref)))
	else:
		addAutotimerFromEvent(session, evt=event, service=ref, importer_Callback=importerCallback)

# XXX: we need this helper function to identify the descriptor
# Extensions menu - open Autotimer
def extensionsmenu(session, **kwargs):
	main(session, **kwargs)

# Extensions menu - only scan Autotimer
def extensionsmenu_scan(session, **kwargs):
	
	try:
		autotimer.readXml()
	except SyntaxError as se:
		session.open(MessageBox, _("Your config file is not well-formed:\n%s") % (str(se)), type=MessageBox.TYPE_ERROR, timeout=10)
		return
	
	editCallback(session)
	

# Movielist menu add to filterList
def add_to_filterList(session, service, services=None, *args, **kwargs):
	
	try:
		if services:
			if not isinstance(services, list):
				services = [services]	
		else:
			services = [service]
		autotimer.addToFilterList(session, services)
	except Exception as e:
		print("[AutoTimer] Unable to add Recordtitle to FilterList:", e)
		doLog("[AutoTimer] Unable to add Recordtitle to FilterList:", e)


def housekeepingExtensionsmenu(el):
	if el.value:
		plugins.addPlugin(extDescriptor)
		plugins.addPlugin(extDescriptor_scan)
	else:
		try:
			plugins.removePlugin(extDescriptor)
			plugins.removePlugin(extDescriptor_scan)
		except ValueError as ve:
			doLog("[AutoTimer] housekeepingExtensionsmenu got confused, tried to remove non-existant plugin entry... ignoring.")

def housekeepingFilmmenu(el):
	if el.value:
		plugins.addPlugin(filmDescriptor_addto)
	else:
		try:
			plugins.removePlugin(filmDescriptor_addto)
		except ValueError as ve:
			doLog("[AutoTimer] housekeepingFilmmenu got confused, tried to remove non-existant plugin entry... ignoring.")

config.plugins.autotimer.show_in_extensionsmenu.addNotifier(housekeepingExtensionsmenu, initial_call=False, immediate_feedback=True)
extDescriptor = PluginDescriptor(name="AutoTimer", description=_("Edit Timers and scan for new Events"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=extensionsmenu, needsRestart=False)
extDescriptor_scan = PluginDescriptor(name="AutoTimer scan", description=_("scan for new Events"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=extensionsmenu_scan, needsRestart=False)

config.plugins.autotimer.show_addto_in_filmmenu.addNotifier(housekeepingFilmmenu, initial_call=False, immediate_feedback=True)
filmDescriptor_addto = PluginDescriptor(name=_("add to AutoTimer filter list"), description=_("add to AutoTimer filter list"), where=PluginDescriptor.WHERE_MOVIELIST, fnc=add_to_filterList, needsRestart=False)

def Plugins(**kwargs):
	l = [
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart, needsRestart=False),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False),
		# TRANSLATORS: description of AutoTimer in PluginBrowser
		PluginDescriptor(name="AutoTimer", description=_("Edit Timers and scan for new Events"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main, needsRestart=False),
		# TRANSLATORS: AutoTimer title in MovieList (automatically opens importer, I consider this no further interaction)
		PluginDescriptor(name="AutoTimer", description=_("add AutoTimer"), where=PluginDescriptor.WHERE_MOVIELIST, fnc=movielist, needsRestart=False),
		# TRANSLATORS: AutoTimer title in EventInfo dialog (requires the user to select an event to base the AutoTimer on)
		PluginDescriptor(name=_("add AutoTimer..."), where=PluginDescriptor.WHERE_EVENTINFO, fnc=eventinfo, needsRestart=False),
		PluginDescriptor(name=_("add AutoTimer..."), where=[PluginDescriptor.WHERE_EVENTVIEW, PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE], fnc=eventview, needsRestart=False, weight=100),
	]
	if config.plugins.autotimer.show_in_extensionsmenu.value:
		l.append(extDescriptor)
		l.append(extDescriptor_scan)
	
	if config.plugins.autotimer.show_addto_in_filmmenu.value:
		l.append(filmDescriptor_addto)
		
	return l

