# -*- coding: UTF-8 -*-
# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.EpgSelection import EPGSelection
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import getConfigListEntry, ConfigOnOff, \
	ConfigYesNo, ConfigText, ConfigClock, ConfigNumber, ConfigSelection, \
	ConfigDateTime, config, NoSave

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime, mktime

# Show ServiceName instead of ServiceReference
from ServiceReference import ServiceReference

# addAutotimerFromService, AutoTimerChannelSelection
from enigma import eServiceCenter, eServiceReference, iServiceInformation, getDesktop

# Default Record Directory
from Tools import Directories

# Tags
from Screens.MovieSelection import getPreferredTagEditor

weekdays = [
	("0", _("Monday")),
	("1", _("Tuesday")),
	("2", _("Wednesday")),
	("3", _("Thursday")),
	("4", _("Friday")),
	("5", _("Saturday")),
	("6", _("Sunday")),
	("weekend", _("Weekend")),
	("weekday", _("Weekday"))
]

try:
	from Plugins.SystemPlugins.vps import Vps
except ImportError as ie:
	hasVps = False
else:
	hasVps = True

try:
	from Plugins.Extensions.SeriesPlugin.plugin import Plugins
except ImportError as ie:
	hasSeriesPlugin = False
else:
	hasSeriesPlugin = True

sz_w = getDesktop(0).size().width()

def importerCallback(ret):
	if ret:
		ret, session = ret

		session.openWithCallback(
			editorCallback,
			AutoTimerEditor,
			ret
		)

def editorCallback(ret):
	if ret:
		from plugin import autotimer
		autotimer.add(ret)

		# Save modified xml
		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()

class ExtendedConfigText(ConfigText):
	def __init__(self, default="", fixed_size=True, visible_width=False):
		ConfigText.__init__(self, default=default, fixed_size=fixed_size, visible_width=visible_width)

		# Workaround some characters currently not "typeable" using NumericalTextInput
		mapping = self.mapping
		if mapping:
			if "&" not in mapping[0]:
				mapping[0] += "&"
			if ";" not in mapping[0]:
				mapping[0] += ";"
			if "%" not in mapping[0]:
				mapping[0] += "%"
			if "|" not in mapping[0]:
				mapping[0] += "|"
			if "\\" not in mapping[0]:
				mapping[0] += "\\"

class SimpleBouquetSelection(SimpleChannelSelection):
	def __init__(self, session, title):
		SimpleChannelSelection.__init__(self, session, title)
		self.skinName = "SimpleChannelSelection"

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.close(ref)
		else:
			# We return the currently active path here
			# Asking the user if this is what he wants might be better though
			self.close(self.servicePath[-1])

class AutoTimerChannelSelection(SimpleChannelSelection):
	def __init__(self, session, autotimer):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = "SimpleChannelSelection"
		self.autotimer = autotimer

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.channelSelected
			}
		)

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.open(
				AutoTimerEPGSelection,
				ref
			)

class AutoTimerEPGSelection(EPGSelection):
	def __init__(self, *args):
		EPGSelection.__init__(self, *args)
		self.skinName = "EPGSelection"

	def infoKeyPressed(self):
		self.timerAdd()

	def timerAdd(self):
		cur = self["list"].getCurrent()
		evt = cur[0]
		sref = cur[1]
		if not evt:
			return

		addAutotimerFromEvent(self.session, evt=evt, service=sref)


class AutoTimerEditorBase:
	""" Base Class for all Editors """
	def __init__(self, timer, editingDefaults=False):
		# Keep Timer
		self.timer = timer
		self.editingDefaults = editingDefaults

		# See if we are filtering some strings
		excludes = (
			timer.getExcludedTitle(),
			timer.getExcludedShort(),
			timer.getExcludedDescription(),
			timer.getExcludedDays()
		)
		includes = (
			timer.getIncludedTitle(),
			timer.getIncludedShort(),
			timer.getIncludedDescription(),
			timer.getIncludedDays()
		)
		if excludes[0] or excludes[1] \
				or excludes[2] or excludes[3] \
				or includes[0] or includes[1] \
				or includes[2] or includes[3]:
			self.filterSet = True
		else:
			self.filterSet = False
		self.excludes = excludes
		self.includes = includes

		# See if services are restricted
		self.services = timer.services
		self.bouquets = timer.bouquets
		if self.services or self.bouquets:
			self.serviceRestriction = True
		else:
			self.serviceRestriction = False

		self.createSetup(timer)

	def createSetup(self, timer):
		# Name
		self.name = NoSave(ExtendedConfigText(default=timer.name, fixed_size=False))

		# Match
		self.match = NoSave(ExtendedConfigText(default=timer.match, fixed_size=False))

		# ...
		self.searchType = NoSave(ConfigSelection(choices=[("partial", _("partial match")), ("exact", _("exact match")), ("description", _("description match"))], default=timer.searchType))
		self.searchCase = NoSave(ConfigSelection(choices=[("sensitive", _("case-sensitive search")), ("insensitive", _("case-insensitive search"))], default=timer.searchCase))

		# Alternatives override
		self.overrideAlternatives = NoSave(ConfigYesNo(default=timer.overrideAlternatives))

		# Justplay
		self.justplay = NoSave(ConfigSelection(choices=[("zap", _("zap")), ("record", _("record"))], default={0: "record", 1: "zap"}[int(timer.justplay)]))
		self.setEndtime = NoSave(ConfigYesNo(default=timer.setEndtime))

		# Timespan
		now = [x for x in localtime()]
		if timer.hasTimespan():
			default = True
			now[3] = timer.timespan[0][0]
			now[4] = timer.timespan[0][1]
			begin = mktime(now)
			now[3] = timer.timespan[1][0]
			now[4] = timer.timespan[1][1]
			end = mktime(now)
		else:
			default = False
			now[3] = 20
			now[4] = 15
			begin = mktime(now)
			now[3] = 23
			now[4] = 15
			end = mktime(now)
		self.timespan = NoSave(ConfigOnOff(default=default))
		self.timespanbegin = NoSave(ConfigClock(default=begin))
		self.timespanend = NoSave(ConfigClock(default=end))

		# Timeframe
		if timer.hasTimeframe():
			default = True
			begin = timer.getTimeframeBegin()
			end = timer.getTimeframeEnd()
		else:
			default = False
			now = [x for x in localtime()]
			now[3] = 0
			now[4] = 0
			begin = mktime(now)
			end = begin + 604800 # today + 7d
		self.timeframe = NoSave(ConfigOnOff(default=default))
		self.timeframebegin = NoSave(ConfigDateTime(begin, _("%d.%B %Y"), increment=86400))
		self.timeframeend = NoSave(ConfigDateTime(end, _("%d.%B %Y"), increment=86400))

		# Services have their own Screen

		# Offset
		if timer.hasOffset():
			default = True
			begin = timer.getOffsetBegin()
			end = timer.getOffsetEnd()
		else:
			default = False
			begin = 5
			end = 5
		self.offset = NoSave(ConfigOnOff(default=default))
		self.offsetbegin = NoSave(ConfigNumber(default=begin))
		self.offsetend = NoSave(ConfigNumber(default=end))

		# AfterEvent
		if timer.hasAfterEvent():
			default = {
				None: "default",
				AFTEREVENT.NONE: "nothing",
				AFTEREVENT.DEEPSTANDBY: "deepstandby",
				AFTEREVENT.STANDBY: "standby",
				AFTEREVENT.AUTO: "auto"
			}[timer.afterevent[0][0]]
		else:
			default = "default"
		self.afterevent = NoSave(ConfigSelection(choices=[
			("default", _("standard")), ("nothing", _("do nothing")),
			("standby", _("go to standby")),
			("deepstandby", _("go to deep standby")),
			("auto", _("auto"))], default=default))

		# AfterEvent (Timespan)
		if timer.hasAfterEvent() and timer.afterevent[0][1][0] is not None:
			default = True
			now[3] = timer.afterevent[0][1][0][0]
			now[4] = timer.afterevent[0][1][0][1]
			begin = mktime(now)
			now[3] = timer.afterevent[0][1][1][0]
			now[4] = timer.afterevent[0][1][1][1]
			end = mktime(now)
		else:
			default = False
			now[3] = 23
			now[4] = 15
			begin = mktime(now)
			now[3] = 7
			now[4] = 0
			end = mktime(now)
		self.afterevent_timespan = NoSave(ConfigOnOff(default=default))
		self.afterevent_timespanbegin = NoSave(ConfigClock(default=begin))
		self.afterevent_timespanend = NoSave(ConfigClock(default=end))

		# Enabled
		self.enabled = NoSave(ConfigYesNo(default=timer.enabled))

		# Maxduration
		if timer.hasDuration():
			default = True
			duration = timer.getDuration()
		else:
			default = False
			duration =70
		self.duration = NoSave(ConfigOnOff(default=default))
		self.durationlength = NoSave(ConfigNumber(default=duration))

		# Counter
		if timer.hasCounter():
			default = timer.matchCount
		else:
			default = 0
		self.counter = NoSave(ConfigNumber(default=default))
		self.counterLeft = NoSave(ConfigNumber(default=timer.matchLeft))
		default = timer.getCounterFormatString()
		selection = [("", _("Never")), ("%m", _("Monthly")), ("%U", _("Weekly (Sunday)")), ("%W", _("Weekly (Monday)"))]
		if default not in ('', '%m', '%U', '%W'):
			selection.append((default, _("Custom (%s)") % (default)))
		self.counterFormatString = NoSave(ConfigSelection(selection, default=default))

		# Avoid Duplicate Description
		self.avoidDuplicateDescription = NoSave(ConfigSelection([
				("0", _("No")),
				("1", _("On same service")),
				("2", _("On any service")),
				("3", _("Any service/recording")),
			],
			default=str(timer.getAvoidDuplicateDescription())
		))

		# Search for Duplicate Desciption in...
		self.searchForDuplicateDescription = NoSave(ConfigSelection([
				("0", _("Title")),
				("1", _("Title and short description")),
				("2", _("Title and all descriptions")),
			],
		    default=str(timer.searchForDuplicateDescription)
		))

		# Custom Location
		if timer.hasDestination():
			default = True
		else:
			default = False

		self.useDestination = NoSave(ConfigYesNo(default=default))

		default = timer.destination or Directories.resolveFilename(Directories.SCOPE_HDD)
		choices = config.movielist.videodirs.value

		if default not in choices:
			choices.append(default)
		self.destination = NoSave(ConfigSelection(default=default, choices=choices))

		# Tags
		self.timerentry_tags = timer.tags
		self.tags = NoSave(ConfigSelection(choices=[len(self.timerentry_tags) == 0 and _("None") or ' '.join(self.timerentry_tags)]))

		# Vps
		self.vps_enabled = NoSave(ConfigYesNo(default=timer.vps_enabled))
		self.vps_overwrite = NoSave(ConfigYesNo(default=timer.vps_overwrite))

		# SeriesPlugin
		self.series_labeling = NoSave(ConfigYesNo(default=timer.series_labeling))
		self.series_save_filter = NoSave(ConfigYesNo(default=timer.series_save_filter))

	def pathSelected(self, res):
		if res is not None:
			# I'm pretty sure this will always fail
			if config.movielist.videodirs.value != self.destination.choices:
					self.destination.setChoices(config.movielist.videodirs.value, default=res)
			self.destination.value = res

	def chooseDestination(self):
		from Screens.LocationBox import MovieLocationBox

		self.session.openWithCallback(
			self.pathSelected,
			MovieLocationBox,
			_("Choose target folder"),
			self.destination.value,
			minFree=100 # Same requirement as in Screens.TimerEntry
		)

	def tagEditFinished(self, ret):
		if ret is not None:
			self.timerentry_tags = ret
			self.tags.setChoices([len(ret) == 0 and _("None") or ' '.join(ret)])

	def chooseTags(self):
		preferredTagEditor = getPreferredTagEditor()
		if preferredTagEditor:
			self.session.openWithCallback(
				self.tagEditFinished,
				preferredTagEditor,
				self.timerentry_tags
			)

class AutoTimerEditor(Screen, ConfigListScreen, AutoTimerEditorBase):
	"""Edit AutoTimer"""

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerEditor" position="center,170" size="1200,820" title="Edit AutoTimer">
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="305,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/yellow.svg" position="600,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/blue.svg" position="895,5" size="295,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
		<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
		<widget enableWrapAround="1" name="config" position="10,90" scrollbarMode="showOnDemand" size="1180,540" />
		<eLabel backgroundColor="grey" position="10,650" size="1180,1" />
		<widget font="Regular;32" halign="center" position="10,655" render="Label" size="1180,145" source="help" valign="center" />
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerEditor" title="Edit AutoTimer" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,360" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		<eLabel	position="10,430" size="800,1" backgroundColor="grey"/>
		<widget source="help" render="Label" position="10,440" size="800,70" font="Regular;20" halign="center" valign="center" />
	</screen>"""


	def __init__(self, session, timer, editingDefaults=False, **kwargs):
		Screen.__init__(self, session)

		AutoTimerEditorBase.__init__(self, timer, editingDefaults)

		self.partnerbox = False
		if "partnerbox" in kwargs:
			self.partnerbox = kwargs["partnerbox"]			

		# Summary
		self.setup_title = _("AutoTimer Editor")
		self.onChangedEntry = []

		# We might need to change shown items, so add some notifiers
		self.justplay.addNotifier(self.reloadList, initial_call=False)
		self.timespan.addNotifier(self.reloadList, initial_call=False)
		self.timeframe.addNotifier(self.reloadList, initial_call=False)
		self.offset.addNotifier(self.reloadList, initial_call=False)
		self.duration.addNotifier(self.reloadList, initial_call=False)
		self.afterevent.addNotifier(self.reloadList, initial_call=False)
		self.afterevent_timespan.addNotifier(self.reloadList, initial_call=False)
		self.counter.addNotifier(self.reloadList, initial_call=False)
		self.avoidDuplicateDescription.addNotifier(self.reloadList, initial_call=False)
		self.useDestination.addNotifier(self.reloadList, initial_call=False)
		self.vps_enabled.addNotifier(self.reloadList, initial_call=False)
		self.series_labeling.addNotifier(self.reloadList, initial_call=False)
		self.series_save_filter.addNotifier(self.reloadList, initial_call=False)

		self.refresh()
		self.initHelpTexts()

		# XXX: no help for numericaltextinput since it is shown on top of our help
		ConfigListScreen.__init__(self, self.list, on_change=self.changed)
		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText()
 		self["key_blue"] = StaticText()

		self["help"] = StaticText()

		# Set Button texts
		self.renameServiceButton()
		self.renameFilterButton()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "ChannelSelectBaseActions"],
			{
				"cancel": self.cancel,
				"save": self.maybeSave,
				"ok": self.ok,
				"yellow": self.editFilter,
				"blue": self.editServices,
				"nextBouquet": self.pageUp,
				"prevBouquet": self.pageDown
			}, -2
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Edit AutoTimer"))

	def renameFilterButton(self):
		if self.filterSet:
			self["key_yellow"].text = _("edit filters")
		else:
			self["key_yellow"].text = _("add filters")

	def renameServiceButton(self):
		if self.serviceRestriction:
			self["key_blue"].text = _("edit services")
		else:
			self["key_blue"].text = _("add services")

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = self.helpDict.get(cur[1], "")

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def initHelpTexts(self):
		self.helpDict = {
			self.enabled: _("Set this NO to disable this AutoTimer."),
			self.name: _("This is a name you can give the AutoTimer. It will be shown in the Overview and the Preview."),
			self.match: _("This is what will be looked for in event titles. Note that looking for e.g. german umlauts can be tricky as you have to know the encoding the channel uses."),
			self.searchType: _("Select \"exact match\" to enforce \"Match title\" to match exactly, \"partial match\" if you only want to search for a part of the event title or \"description match\" if you only want to search for a part of the event description"),
			self.searchCase: _("Select whether or not you want to enforce case correctness."),
			self.justplay: _("Add zap timer instead of record timer?"),
			self.setEndtime: _("Set an end time for the timer. If you do, the timespan of the event might be blocked for recordings."),
			self.overrideAlternatives: _("With this option enabled the channel to record on can be changed to a alternative service it is restricted to."),
			self.timespan: _("Should this AutoTimer be restricted to a timespan?"),
			self.timespanbegin: _("Lower bound of timespan. Nothing before this time will be matched. Offsets are not taken into account!"),
			self.timespanend: _("Upper bound of timespan. Nothing after this time will be matched. Offsets are not taken into account!"),
			self.timeframe: _("By enabling this events will not be matched if they don't occur on certain dates."),
			self.timeframebegin: _("First day to match events. No event that begins before this date will be matched."),
			self.timeframeend: _("Last day to match events. Events have to begin before this date to be matched."),
			self.offset: _("Change default recording offset?"),
			self.offsetbegin: _("Time in minutes to prepend to recording."),
			self.offsetend: _("Time in minutes to append to recording."),
			self.duration: _("Should this AutoTimer only match up to a certain event duration?"),
			self.durationlength: _("Maximum event duration to match. If an event is longer than this amount of time (without offset) it won't be matched."),
			self.afterevent: _("Power state to change to after recordings. Select \"standard\" to not change the default behavior of enigma2 or values changed by yourself."),
			self.afterevent_timespan: _("Restrict \"after event\" to a certain timespan?"),
			self.afterevent_timespanbegin: _("Lower bound of timespan."),
			self.afterevent_timespanend: _("Upper bound of timespan."),
			self.counter: _("With this option you can restrict the AutoTimer to a certain amount of scheduled recordings. Set this to 0 to disable this functionality."),
			self.counterLeft: _("Number of scheduled recordings left."),
			self.counterFormatString: _("The counter can automatically be reset to the limit at certain intervals."),
			self.avoidDuplicateDescription: _("When this option is enabled the AutoTimer won't match events where another timer with the same description already exists in the timer list."),
			self.searchForDuplicateDescription: _("Defines where to search for duplicates (only title, short description or even extended description)"),
			self.useDestination: _("Should timers created by this AutoTimer be recorded to a custom location?"),
			self.destination: _("Select the location to save the recording to."),
			self.tags: _("Tags the timer/recording will get."),
			self.series_labeling: _("Label timers with season, episode and title according to the SeriesPlugin settings."),
			self.series_save_filter: _("Save the timer name generated by SeriesPlugin in a filter list to filter during future timer searches (only with SeriesPlugin)"),
		}

	def refresh(self):
		# First three entries are only showed when not editing defaults
		list = []
		if not self.editingDefaults:
			list.extend((
				getConfigListEntry(_("Enabled"), self.enabled),
				getConfigListEntry(_("Description"), self.name),
				getConfigListEntry(_("Match title"), self.match),
			))

		list.extend((
			getConfigListEntry(_("Search type"), self.searchType),
			getConfigListEntry(_("Search strictness"), self.searchCase),
			getConfigListEntry(_("Timer type"), self.justplay),
		))
		if self.justplay.value == "zap":
			list.append(getConfigListEntry(_("Set End Time"), self.setEndtime))
		list.extend((
			getConfigListEntry(_("Override found with alternative service"), self.overrideAlternatives),
			getConfigListEntry(_("Only match during timespan"), self.timespan)
		))

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			list.extend((
				getConfigListEntry(_("Begin of timespan"), self.timespanbegin),
				getConfigListEntry(_("End of timespan"), self.timespanend)
			))

		list.append(getConfigListEntry(_("Restrict to events on certain dates"), self.timeframe))

		# Only allow editing timeframe when it's enabled
		if self.timeframe.value:
			list.extend((
				getConfigListEntry(_("Not before"), self.timeframebegin),
				getConfigListEntry(_("Not after"), self.timeframeend)
			))

		list.append(getConfigListEntry(_("Custom offset"), self.offset))

		# Only allow editing offsets when it's enabled
		if self.offset.value:
			list.extend((
				getConfigListEntry(_("Offset before recording (in m)"), self.offsetbegin),
				getConfigListEntry(_("Offset after recording (in m)"), self.offsetend)
			))

		list.append(getConfigListEntry(_("Set maximum duration"), self.duration))

		# Only allow editing maxduration when it's enabled
		if self.duration.value:
			list.append(getConfigListEntry(_("Maximum duration (in m)"), self.durationlength))

		list.append(getConfigListEntry(_("After event"), self.afterevent))

		# Only allow setting afterevent timespan when afterevent is active
		if self.afterevent.value != "default":
			list.append(getConfigListEntry(_("Execute \"after event\" during timespan"), self.afterevent_timespan))

			# Only allow editing timespan when it's enabled
			if self.afterevent_timespan.value:
				list.extend((
					getConfigListEntry(_("Begin of \"after event\" timespan"), self.afterevent_timespanbegin),
					getConfigListEntry(_("End of \"after event\" timespan"), self.afterevent_timespanend)
				))

		list.append(getConfigListEntry(_("Record a maximum of x times"), self.counter))

		# Only allow setting matchLeft when counting hits
		if self.counter.value:
			if not self.editingDefaults:
				list.append(getConfigListEntry(_("Amount of recordings left"), self.counterLeft))
			list.append(getConfigListEntry(_("Reset count"), self.counterFormatString))

		list.append(getConfigListEntry(_("Require description to be unique"), self.avoidDuplicateDescription))

		if int(self.avoidDuplicateDescription.value) > 0:
			list.append(getConfigListEntry(_("Check for uniqueness in"), self.searchForDuplicateDescription))

		# We always add this option though its expert only in enigma2
		list.append(getConfigListEntry(_("Use a custom location"), self.useDestination))
		if self.useDestination.value:
			list.append(getConfigListEntry(_("Custom location"), self.destination))

		list.append(getConfigListEntry(_("Tags"), self.tags))

		if hasVps:
			list.append(getConfigListEntry(_("Activate VPS"), self.vps_enabled))
			if self.vps_enabled.value:
				list.append(getConfigListEntry(_("Control recording completely by service"), self.vps_overwrite))

		if hasSeriesPlugin:
			list.append(getConfigListEntry(_("Label series"), self.series_labeling))
			if self.series_labeling.value:
				list.append(getConfigListEntry(_("Save/check labelled series in filter list (SeriesPlugin)"), self.series_save_filter))
				if not self.series_save_filter.value and config.plugins.autotimer.series_save_filter.value:
					list.append(getConfigListEntry(_(" == Warning: global option 'save/check filter list is still active!! ==")))

		self.list = list

	def reloadList(self, value):
		self.refresh()
		self["config"].setList(self.list)

	def editFilter(self):
		self.session.openWithCallback(
			self.editFilterCallback,
			AutoTimerFilterEditor,
			self.filterSet,
			self.excludes,
			self.includes
		)

	def editFilterCallback(self, ret):
		if ret:
			self.filterSet = ret[0]
			self.excludes = ret[1]
			self.includes = ret[2]
			self.renameFilterButton()

	def editServices(self):
		self.session.openWithCallback(
			self.editServicesCallback,
			AutoTimerServiceEditor,
			self.serviceRestriction,
			self.services,
			self.bouquets
		)

	def editServicesCallback(self, ret):
		if ret:
			self.serviceRestriction = ret[0]
			self.services = ret[1][0]
			self.bouquets = ret[1][1]
			if self.partnerbox:
				idx = 0
				for service in self.services:
					serviceref = eServiceReference(service)
					if serviceref.getPath():
						serviceref.setPath("")
						ref_split = serviceref.toString().split(":")
						ref_split[1] = "0"
						self.services[idx] = ":".join(ref_split)
					idx += 1
			self.renameServiceButton()

	def keyLeft(self):
		cur = self["config"].getCurrent()
		cur = cur and cur[1]
		if cur == self.tags:
			self.chooseTags()
		else:
			ConfigListScreen.keyLeft(self)

	def keyRight(self):
		cur = self["config"].getCurrent()
		cur = cur and cur[1]
		if cur == self.tags:
			self.chooseTags()
		else:
			ConfigListScreen.keyRight(self)

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def ok(self):
		cur = self["config"].getCurrent()
		cur = cur and cur[1]
		if cur == self.destination:
			self.chooseDestination()
		elif cur == self.tags:
			self.chooseTags()
		else:
			ConfigListScreen.keyOK(self)

	def cancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def maybeSave(self):
		if self.editingDefaults:
			self.save()
			return
		# Check if any match is set
		if not self.match.value.strip():
			self.session.open(
					MessageBox,
					_("The match attribute is mandatory."),
					type=MessageBox.TYPE_ERROR,
					timeout=5
			)
		# Check if we have a trailing whitespace
		elif self.match.value[-1:] == " ":
			self.session.openWithCallback(
				self.saveCallback,
				MessageBox,
				_('You entered "%s" as Text to match.\nDo you want to remove trailing whitespaces?') % (self.match.value)
			)
		# Just save else
		else:
			self.save()

	def saveCallback(self, ret):
		if ret is not None:
			if ret:
				self.match.value = self.match.value.rstrip()
			self.save()
		# Don't to anything if MessageBox was canceled!

	def save(self):
		# Match
		self.timer.match = self.match.value

		# Name
		self.timer.name = self.name.value.strip() or self.timer.match

		# ...
		self.timer.searchType = self.searchType.value
		self.timer.searchCase = self.searchCase.value

		# Alternatives
		self.timer.overrideAlternatives = self.overrideAlternatives.value

		# Enabled
		self.timer.enabled = self.enabled.value

		# Justplay
		self.timer.justplay = self.justplay.value == "zap"
		self.timer.setEndtime = self.setEndtime.value

		# Timespan
		if self.timespan.value:
			start = self.timespanbegin.value
			end = self.timespanend.value
			self.timer.timespan = (start, end)
		else:
			self.timer.timespan = None

		# Timeframe
		if self.timeframe.value:
			start = self.timeframebegin.value
			end = self.timeframeend.value
			self.timer.timeframe = (start, end)
		else:
			self.timer.timeframe = None

		# Services
		if self.serviceRestriction:
			self.timer.services = self.services
			self.timer.bouquets = self.bouquets
		else:
			self.timer.services = None
			self.timer.bouquets = None

		# Offset
		if self.offset.value:
			self.timer.offset = (self.offsetbegin.value*60, self.offsetend.value*60)
		else:
			self.timer.offset = None

		# AfterEvent
		if self.afterevent.value == "default":
			self.timer.afterevent = []
		else:
			afterevent = {
				"nothing": AFTEREVENT.NONE,
				"deepstandby": AFTEREVENT.DEEPSTANDBY,
				"standby": AFTEREVENT.STANDBY,
				"auto": AFTEREVENT.AUTO
			}[self.afterevent.value]
			# AfterEvent Timespan
			if self.afterevent_timespan.value:
				start = self.afterevent_timespanbegin.value
				end = self.afterevent_timespanend.value
				self.timer.afterevent = [(afterevent, (start, end))]
			else:
				self.timer.afterevent = [(afterevent, None)]

		# Maxduration
		if self.duration.value:
			self.timer.maxduration = self.durationlength.value*60
		else:
			self.timer.maxduration = None

		# Ex-&Includes
		if self.filterSet:
			self.timer.exclude = self.excludes
			self.timer.include = self.includes
		else:
			self.timer.exclude = None
			self.timer.include = None

		# Counter
		if self.counter.value:
			self.timer.matchCount = self.counter.value
			if self.counterLeft.value <= self.counter.value:
				self.timer.matchLeft = self.counterLeft.value
			else:
				self.timer.matchLeft = self.counter.value
			if self.counterFormatString.value:
				self.timer.matchFormatString = self.counterFormatString.value
			else:
				self.timer.matchFormatString = ''
		else:
			self.timer.matchCount = 0
			self.timer.matchLeft = 0
			self.timer.matchFormatString = ''

		self.timer.avoidDuplicateDescription = int(self.avoidDuplicateDescription.value)
		self.timer.searchForDuplicateDescription = int(self.searchForDuplicateDescription.value)

		if self.useDestination.value:
			self.timer.destination = self.destination.value
		else:
			self.timer.destination = None

		self.timer.tags = self.timerentry_tags

		self.timer.vps_enabled = self.vps_enabled.value
		self.timer.vps_overwrite = self.vps_overwrite.value

		self.timer.series_labeling = self.series_labeling.value
		self.timer.series_save_filter = self.series_save_filter.value
		
		# Close
		self.close(self.timer)

class AutoTimerFilterEditor(Screen, ConfigListScreen):
	"""Edit AutoTimer Filter"""

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerFilterEditor" position="center,170" size="1200,820" title="Edit AutoTimer Filters">
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="305,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/yellow.svg" position="600,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/blue.svg" position="895,5" size="295,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
		<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
		<widget enableWrapAround="1" name="config" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerFilterEditor" title="Edit AutoTimer Filters" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand"/>
	</screen>"""


	def __init__(self, session, filterset, excludes, includes):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("AutoTimer Filters")
		self.onChangedEntry = []

		self.typeSelection = NoSave(ConfigSelection(choices=[
			("title", _("in title")),
			("short", _("in short description")),
			("desc", _("in description")),
			("day", _("on weekday"))]
		))
		#self.typeSelection.addNotifier(self.refresh, initial_call = False)

		self.enabled = NoSave(ConfigOnOff(default=filterset))

		self.excludes = excludes
		self.includes = includes

		self.reloadList()

		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changed)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("delete"))
		self["key_blue"] = StaticText(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.remove,
				"blue": self.new
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Edit AutoTimer filters"))


	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def saveCurrent(self):
		
		# Warning, accessing a ConfigListEntry directly might be considered evil!
		
		#reset all filter in self and refill new from configList
		idx = -1
		for type in self.typeSelection.getChoices():
			idx += 1
			del self.includes[idx][:]
			del self.excludes[idx][:]

		idx = -1
		for item in self["config"].getList()[:]:
			idx += 1
			#print "=== item: ", idx, item
			if idx > 1 and len(item) < 2: # set filtertype
				idx_type = 0
				for type in self.typeSelection.getChoices():
					#print "=== type:", type, type[0], type[1]
					if _(type[1]) == item[0]:
						self.idx = idx_type
						break
					idx_type +=1
				#print "=== self.idx: ", self.idx
			elif idx > 1: # set include/exclude
				#print "=== item: ", idx, item[0]
				pass

			# Skip empty entries (and those which are no filters)
			if idx < 2 or len(item) < 2 or item[1].value == "":
				continue
			elif item[0] == _("Exclude"):
				self.excludes[self.idx].append(item[1].value.encode("UTF-8"))
				#pass
			elif item[0] == _("Include"):
				self.includes[self.idx].append(item[1].value.encode("UTF-8"))
				#pass

	def refresh(self, *args, **kwargs):
		self.saveCurrent()

		self.reloadList()
		self["config"].setList(self.list)

	def reloadList(self):
		self.list = [
			getConfigListEntry(_("Enable Filtering"), self.enabled),
			getConfigListEntry(_("Filter"), self.typeSelection)
		]
		
		for type in self.typeSelection.getChoices():
			
			print "=== type ", type
			if type[0] == "day": 
				self.idx = 3
				cfgList = []
				
				# Weekdays are presented as ConfigSelection
				cfgList.extend([
					getConfigListEntry(_("Exclude"), NoSave(ConfigSelection(choices=weekdays, default=x)))
						for x in self.excludes[3]
				])
				self.lenExcludes = len(cfgList)
				cfgList.extend([
					getConfigListEntry(_("Include"), NoSave(ConfigSelection(choices=weekdays, default=x)))
						for x in self.includes[3]
				])
				if len(cfgList):
					print "=== cfgList day:", cfgList
					for item in cfgList:
						print "=== cfgList day item:", item, item[0], item[1], item[1].value
					self.list.append(getConfigListEntry(type[1]))
					cfgList = sorted(cfgList, key=lambda x: [x[0],x[1].value], reverse=False)
					self.list.extend(cfgList)
		
			else:
				if type[0] == "title":
					self.idx = 0
				elif type[0] == "short":
					self.idx = 1
				else: # self.typeSelection.value == "desc":
					self.idx = 2
				
				cfgList = []
				
				cfgList.extend([
					getConfigListEntry(_("Exclude"), NoSave(ExtendedConfigText(default=x, fixed_size=False)))
						for x in self.excludes[self.idx]
				])
				self.lenExcludes = len(cfgList)
				cfgList.extend([
					getConfigListEntry(_("Include"), NoSave(ExtendedConfigText(default=x, fixed_size=False)))
						for x in self.includes[self.idx]
				])
				if len(cfgList):
					self.list.append(getConfigListEntry(type[1]))
					cfgList = sorted(cfgList, key=lambda x: [x[0],x[1].value], reverse=False)
					self.list.extend(cfgList)

	def remove(self):
		idx = self["config"].getCurrentIndex()
		if idx and idx > 1:
			if idx < self.lenExcludes:
				self.lenExcludes -= 1

			list = self["config"].getList()
			list.remove(self["config"].getCurrent())
			self["config"].setList(list)
			#remove empty config-section
			print "==== getcurrent:", self["config"].getCurrent()
			print "==== len getcurrent:", len(self["config"].getCurrent())

			#self.refresh()
			
			if len(self["config"].getCurrent())<2:
				self.remove()
			#	list.remove(self["config"].getCurrent())
			#	self["config"].setList(list)

	def new(self):
		self.session.openWithCallback(
			self.typeSelected,
			ChoiceBox,
			_("Select type of Filter"),
			[
				(_("Exclude"), 0),
				(_("Include"), 1),
			]
		)

	def typeSelected(self, ret):
		if ret is not None:
			list = self["config"].getList()
			# get the filtertype-text
			type_text = list[1][1].getText()
			#print "=== type_text", type_text, list

			if self.typeSelection.value == "day":
				entry = getConfigListEntry(ret[0], NoSave(ConfigSelection(choices=weekdays)))
			else:
				entry = getConfigListEntry(ret[0], NoSave(ExtendedConfigText(fixed_size=False)))
			
			#get the position of the new filterentry
			pos=0
			filter_exist = False
			for item in list:
				pos +=1
				if item[0] == _(type_text):
					filter_exist = True
					break
			if filter_exist == False:
				list.insert(pos, getConfigListEntry(_(type_text)))
				pos +=1
			list.insert(pos, entry)
			self["config"].setList(list)
			self["config"].setCurrentIndex(pos) #select the new entry in the list

	def cancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def save(self):
		self.refresh()

		self.close((
			self.enabled.value,
			self.excludes,
			self.includes
		))

class AutoTimerServiceEditor(Screen, ConfigListScreen):
	"""Edit allowed Services of a AutoTimer"""

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerServiceEditor" position="center,170" size="1200,820" title="Edit AutoTimer Services">
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="305,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/yellow.svg" position="600,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/blue.svg" position="895,5" size="295,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
		<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
		<widget enableWrapAround="1" name="config" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerServiceEditor" title="Edit AutoTimer Services" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand"/>
	</screen>"""


	def __init__(self, session, servicerestriction, servicelist, bouquetlist):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("AutoTimer Services")
		self.onChangedEntry = []

		self.services = (
			servicelist[:],
			bouquetlist[:]
		)

		self.enabled = NoSave(ConfigOnOff(default=servicerestriction))
		self.typeSelection = NoSave(ConfigSelection(choices=[
			("channels", _("Channels")),
			("bouquets", _("Bouquets"))]
		))
		#self.typeSelection.addNotifier(self.refresh, initial_call = False)

		self.reloadList()

		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changed)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("delete"))
		self["key_blue"] = StaticText(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.remove,
				"blue": self.new
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Edit AutoTimer services"))

	def saveCurrent(self):
		
		# Warning, accessing a ConfigListEntry directly might be considered evil!
		
		#reset all Servicefilter in self and refill new from configList
		idx = -1
		for type in self.typeSelection.getChoices():
			idx += 1
			del self.services[idx][:]

		idx = -1
		for item in self["config"].getList()[:]:
			idx += 1
			#print "=== item: ", idx, item
			if idx > 1 and len(item) < 2: # set filtertype
				idx_type = 0
				for type in self.typeSelection.getChoices():
					#print "=== type:", type, type[0], type[1]
					if _(type[1]) == item[0]:
						self.idx = idx_type
						break
					idx_type +=1
			# Skip empty entries (and those which are no filters)
			if idx < 2 or len(item) < 2 or item[1].value == "":
				continue
			self.services[self.idx].append(item[1].value)

	def refresh(self, *args, **kwargs):
		self.saveCurrent()

		self.reloadList()
		self["config"].setList(self.list)

	def reloadList(self):
		
		self.list = [
			getConfigListEntry(_("Enable Service Restriction"), self.enabled),
			getConfigListEntry(_("Editing"), self.typeSelection)
		]

		for type in self.typeSelection.getChoices():
			if type[0] == "channels":
				self.idx = 0
			else: # self.typeSelection.value == "bouquets":
				self.idx = 1

			cfgList = []
			cfgList.extend([
					getConfigListEntry(_("Record on"), NoSave(ConfigSelection(choices=[(str(x), ServiceReference(str(x)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])))
						for x in self.services[self.idx]
			])
			
			if len(cfgList):
				self.list.append(getConfigListEntry(type[1]))
				cfgList = sorted(cfgList, key=lambda x: [x[1].getText()], reverse=False)
				self.list.extend(cfgList)

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def remove(self):
		
		idx = self["config"].getCurrentIndex()
		if idx and idx > 1:
			list = self["config"].getList()
			list.remove(self["config"].getCurrent())
			self["config"].setList(list)
			#remove empty config-section
			if len(self["config"].getCurrent())<2:
				self.remove()

	def new(self):
		if self.typeSelection.value == "channels":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleChannelSelection,
				_("Select channel to record on")
			)
		else: # self.typeSelection.value == "bouquets":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleBouquetSelection,
				_("Select bouquet to record on")
			)

	def finishedServiceSelection(self, *args):
		if args:
			list = self["config"].getList()
			sname = args[0].toString()

			if self.typeSelection.value == "channels" and not (args[0].flags & eServiceReference.isGroup):
				# strip all after last : when adding a (non alternative) channel
				pos = sname.rfind(':')
				if pos != -1:
					if sname[pos-1] == ':':
						pos -= 1
					sname = sname[:pos+1]
			
			# get the filtertype-text
			type_text = list[1][1].getText()

			entry = getConfigListEntry(_("Record on"), NoSave(ConfigSelection(choices=[(sname, ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])))
			
			#get the position of the new filterentry
			pos=0
			filter_exist = False
			for item in list:
				pos +=1
				if item[0] == _(type_text):
					filter_exist = True
					break
			if filter_exist == False:
				list.insert(pos, getConfigListEntry(_(type_text)))
				pos +=1
			list.insert(pos, entry)
			self["config"].setList(list)
			self["config"].setCurrentIndex(pos) #select the new entry in the list

	def cancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		if ret:
			self.close(None)

	def save(self):
		self.refresh()

		self.close((
			self.enabled.value,
			self.services
		))

def addAutotimerFromSearchString(session, match, importer_Callback=importerCallback):
	from AutoTimerComponent import preferredAutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer

	autotimer.readXml()

	newTimer = autotimer.defaultTimer.clone()
	newTimer.id = autotimer.getUniqueId()
	newTimer.name = match
	newTimer.match = ''
	newTimer.enabled = True

	session.openWithCallback(
		importer_Callback,
		AutoTimerImporter,
		newTimer,
		match,		# Proposed Match
		None,		# Proposed Begin
		None,		# Proposed End
		None,		# Proposed Disabled
		None,		# Proposed ServiceReference
		None,		# Proposed afterEvent
		None,		# Proposed justplay
		None,		# Proposed dirname, can we get anything useful here?
		[]			# Proposed tags
	)

def addAutotimerFromEvent(session, evt=None, service=None, importer_Callback=importerCallback):
	from AutoTimerComponent import preferredAutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer

	autotimer.readXml()

	match = evt and evt.getEventName() or ""
	name = match or "New AutoTimer"
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

	newTimer = autotimer.defaultTimer.clone()
	newTimer.id = autotimer.getUniqueId()
	newTimer.name = name
	newTimer.match = ''
	newTimer.enabled = True

	session.openWithCallback(
		importer_Callback,
		AutoTimerImporter,
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

def addAutotimerFromService(session, service=None, importer_Callback=importerCallback):
	from AutoTimerComponent import preferredAutoTimerComponent
	from AutoTimerImporter import AutoTimerImporter
	from plugin import autotimer

	autotimer.readXml()

	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)

	match = info and info.getName(service) or ""
	name = match or "New AutoTimer"
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

	newTimer = autotimer.defaultTimer.clone()
	newTimer.id = autotimer.getUniqueId()
	newTimer.name = name
	newTimer.match = ''
	newTimer.enabled = True

	# XXX: we might want to make sure that we actually collected any data because the importer does not do so :-)

	session.openWithCallback(
		importer_Callback,
		AutoTimerImporter,
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
