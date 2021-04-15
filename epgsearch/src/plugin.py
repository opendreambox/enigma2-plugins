from enigma import eServiceCenter
from Components.config import config

# Plugin
from EPGSearch import EPGSearch, EPGSearchEPGSelection, searchEvent, pzyP4TInit, autoTimerAvailable
from EPGSearchFilter import searchEventWithFilter, addSearchFilterFromMovieList

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


def openHistory(session, event, service):
	kwargs = {"startWithHistory": True}
	session.open(EPGSearch, **kwargs)


def Plugins(**kwargs):

	l = [PluginDescriptor(
		where=PluginDescriptor.WHERE_AUTOSTART,
		fnc=autostart, needsRestart=False)]

	l.append(PluginDescriptor(
		name="EPGSearch",
		# TRANSLATORS: description of EPGSearch in PluginBrowser
		description=_("Search EPG"),
		where=PluginDescriptor.WHERE_PLUGINMENU,
		fnc=main, icon="EPGSearch.png", needsRestart=False))

	l.append(PluginDescriptor(
		# TRANSLATORS: EPGSearch title in EventInfo dialog (requires the user to select an event to search for)
		name=_("search EPG..."),
		where=PluginDescriptor.WHERE_EVENTINFO,
		fnc=eventinfo, needsRestart=False))

	l.append(PluginDescriptor(
		# TRANSLATORS: EPGSearch title in MovieList (does not require further user interaction)
		description=_("Search EPG"),
		where=PluginDescriptor.WHERE_MOVIELIST,
		fnc=movielist, needsRestart=False))

	searchEventDescriptors = []
	if config.plugins.epgsearch.searchEPG_menu.value in ("all", "blue"):
		searchEventDescriptors = [PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE, PluginDescriptor.WHERE_EVENTVIEW]
	if config.plugins.epgsearch.searchEPG_menu.value in ("all", "red"):
		searchEventDescriptors.append(PluginDescriptor.WHERE_CHANNEL_SELECTION_RED)
	if searchEventDescriptors:
		l.append(PluginDescriptor(
			name=_("Search EPG"),
			where=searchEventDescriptors,
			fnc=searchEvent))

	openHistoryDescriptors = []
	if config.plugins.epgsearch.openSearchFilter_menu.value in ("all", "blue"):
		openHistoryDescriptors = [PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE, PluginDescriptor.WHERE_EVENTVIEW]
	if config.plugins.epgsearch.openSearchFilter_menu.value in ("all", "red"):
		openHistoryDescriptors.append(PluginDescriptor.WHERE_CHANNEL_SELECTION_RED)
	if openHistoryDescriptors:
		l.append(PluginDescriptor(
			name=_("open EPGSearch search list"),
			where=openHistoryDescriptors,
			fnc=openHistory))

	#add only if AutoTimer-Plugin is found
	if autoTimerAvailable:
		l.append(PluginDescriptor(
			name=_("add search filter to EPGSearch"),
			description=_("add search filter to EPGSearch"),
			where=[PluginDescriptor.WHERE_MOVIELIST],
			fnc=addSearchFilterFromMovieList))

		searchEventWithFilterDescriptors = []
		if config.plugins.epgsearch.addSearchFilter_menu.value in ("all", "blue"):
			searchEventWithFilterDescriptors = [PluginDescriptor.WHERE_EPG_SELECTION_SINGLE_BLUE, PluginDescriptor.WHERE_EVENTVIEW]
		if config.plugins.epgsearch.addSearchFilter_menu.value in ("all", "red"):
				searchEventWithFilterDescriptors.append(PluginDescriptor.WHERE_CHANNEL_SELECTION_RED)
		if searchEventWithFilterDescriptors:
			l.append(PluginDescriptor(
				name=_("add search filter to EPGSearch"),
				where=searchEventWithFilterDescriptors,
				fnc=searchEventWithFilter))

	return l
