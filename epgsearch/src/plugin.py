from enigma import eServiceCenter
from Components.config import config

# Plugin
from EPGSearch import EPGSearch, EPGSearchEPGSelection, searchEvent, pzyP4TInit, autoTimerAvailable
from EPGSearchFilter import searchEventWithFilter, openSearchFilterList, addSearchFilterFromEventinfo

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Autostart
def autostart(reason, **kwargs):
	if reason == 0:
		try:
			# for blue and audio key activating in EPG-Screens
			pzyP4TInit()
		except Exception:
			import traceback
			traceback.print_exc()

# Mainfunction
def main(session, *args, **kwargs):
	s = session.nav.getCurrentService()
	if s:
		info = s.info()
		event = info.getEvent(0) # 0 = now, 1 = next
		name = event and event.getEventName() or ''
		session.open(EPGSearch, name, config.plugins.epgsearch.add_history_onOpen.value)
	else:
		session.open(EPGSearch)

# Event Info
def eventinfo(session, *args, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceReference()
	session.open(EPGSearchEPGSelection, ref, True)

# Movielist
def movielist(session, service, **kwargs):
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)
	name = info and info.getName(service) or ''

	session.open(EPGSearch, name, config.plugins.epgsearch.add_history_onOpen.value)

def Plugins(**kwargs):
	l = [
		PluginDescriptor(
			name=_("Search EPG"),
			where = [PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE, PluginDescriptor.WHERE_CHANNEL_SELECTION_RED, PluginDescriptor.WHERE_EVENTVIEW],
			fnc = searchEvent
		),
		PluginDescriptor(
			where = PluginDescriptor.WHERE_AUTOSTART,
			fnc = autostart,
			needsRestart = False,
		),
		PluginDescriptor(
			name = "EPGSearch",
			# TRANSLATORS: description of EPGSearch in PluginBrowser
			description = _("Search EPG"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main,
			icon = "EPGSearch.png",
			needsRestart = False,
		),
		PluginDescriptor(
			# TRANSLATORS: EPGSearch title in EventInfo dialog (requires the user to select an event to search for)
			name = _("search EPG..."),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = eventinfo,
			needsRestart = False,
		),
		PluginDescriptor(
			# TRANSLATORS: EPGSearch title in MovieList (does not require further user interaction)
			description = _("search EPG"),
			where = PluginDescriptor.WHERE_MOVIELIST,
			fnc = movielist,
			needsRestart = False,
		),
	]
	
	#add only if AutoTimer-Plugin is found
	if autoTimerAvailable:
		l.append(PluginDescriptor(
			name=_("add search filter to EPGSearch"),
			where = [PluginDescriptor.WHERE_EVENTINFO],
			fnc = addSearchFilterFromEventinfo
			))
		l.append(PluginDescriptor(
			name=_("add search filter to EPGSearch"),
			where = [PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE, PluginDescriptor.WHERE_CHANNEL_SELECTION_RED, PluginDescriptor.WHERE_EVENTVIEW],
			fnc = searchEventWithFilter
			))
		l.append(PluginDescriptor(
			name=_("open EPGSearch filterlist"),
			where = [PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE, PluginDescriptor.WHERE_CHANNEL_SELECTION_RED, PluginDescriptor.WHERE_EVENTVIEW],
			fnc = openSearchFilterList
			))
	
	return l

