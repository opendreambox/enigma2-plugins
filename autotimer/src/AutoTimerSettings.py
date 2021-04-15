# for localized messages

# GUI (System)
from enigma import getDesktop

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, getConfigListEntry

sz_w = getDesktop(0).size().width()


class AutoTimerSettings(Screen, ConfigListScreen):

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerSettings" position="center,170" size="1200,820" title="AutoTimer Settings">
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" scale="stretch" size="350,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="360,5" scale="stretch" size="350,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,70" source="key_red" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="360,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,70" source="key_green" transparent="1" valign="center" zPosition="1" />
		<widget font="Regular;34" halign="right" position="1050,25" render="Label" size="120,40" source="global.CurrentTime">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget font="Regular;34" halign="right" position="800,25" render="Label" size="240,40" source="global.CurrentTime">
			<convert type="ClockToText">Date</convert>
		</widget>
		<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
		<widget enableWrapAround="1" name="config" position="10,90" scrollbarMode="showOnDemand" size="1180,540" />
		<eLabel backgroundColor="grey" position="10,650" size="1180,1" />
		<widget font="Regular;32" halign="center" position="10,655" render="Label" size="1180,145" source="help" valign="center" />
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerSettings" title="AutoTimer Settings" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,360" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		<eLabel	position="10,430" size="800,1" backgroundColor="grey"/>
		<widget source="help" render="Label" position="10,440" size="800,70" font="Regular;20" halign="center" valign="center" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("AutoTimer Settings")
		self.onChangedEntry = []

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Poll automatically"), config.plugins.autotimer.autopoll, _("Unless this is enabled AutoTimer will NOT automatically look for events matching your AutoTimers but only when you leave the GUI with the green button.")),
				getConfigListEntry(_("Startup delay (in min)"), config.plugins.autotimer.delay, _("This is the delay in minutes that the AutoTimer will wait on initial launch to not delay enigma2 startup time.")),
				getConfigListEntry(_("Delay after editing (in sec)"), config.plugins.autotimer.editdelay, _("This is the delay in seconds that the AutoTimer will wait after editing the AutoTimers.")),
				getConfigListEntry(_("Poll Interval (in h)"), config.plugins.autotimer.interval, _("This is the delay in hours that the AutoTimer will wait after a search to search the EPG again.")),
				getConfigListEntry(_("Timeout (in min)"), config.plugins.autotimer.timeout, _("This is the duration in minutes that the AutoTimer is allowed to run.")),
				getConfigListEntry(_("Only add timer for next x days"), config.plugins.autotimer.maxdaysinfuture, _("You can control for how many days in the future timers are added. Set this to 0 to disable this feature.")),
				getConfigListEntry(_("Show in extension menu"), config.plugins.autotimer.show_in_extensionsmenu, _("Enable this to be able to access the AutoTimer Overview from within the extension menu.")),
				getConfigListEntry(_("Modify existing timers"), config.plugins.autotimer.refresh, _("This setting controls the behavior when a timer matches a found event.")),
				# TRANSLATORS: the double-percent is intentional and required, please don't make me hunt you down individually
				getConfigListEntry(_("Guess existing timer based on begin/end"), config.plugins.autotimer.try_guessing, _("If this is enabled an existing timer will also be considered recording an event if it records at least 80%% of it.")),
				getConfigListEntry(_("Add similar timer on conflict"), config.plugins.autotimer.addsimilar_on_conflict, _("If a timer conflict occurs, AutoTimer will search outside the timespan for a similar event and add it.")),
				getConfigListEntry(_("Add timer as disabled on conflict"), config.plugins.autotimer.disabled_on_conflict, _("This toggles the behavior on timer conflicts. If an AutoTimer matches an event that conflicts with an existing timer it will not ignore this event but add it disabled.")),
				getConfigListEntry(_("Include \"AutoTimer\" in tags"), config.plugins.autotimer.add_autotimer_to_tags, _("If this is selected, the tag \"AutoTimer\" will be given to timers created by this plugin.")),
				getConfigListEntry(_("Include AutoTimer name in tags"), config.plugins.autotimer.add_name_to_tags, _("If this is selected, the name of the respective AutoTimer will be added as a tag to timers created by this plugin.")),
				getConfigListEntry(_("Show notification on conflicts"), config.plugins.autotimer.notifconflict, _("By enabling this you will be notified about timer conflicts found during automated polling. There is no intelligence involved, so it might bother you about the same conflict over and over.")),
				getConfigListEntry(_("Show notification on similars"), config.plugins.autotimer.notifsimilar, _("By enabling this you will be notified about similar timers added during automated polling. There is no intelligence involved, so it might bother you about the same conflict over and over.")),
				getConfigListEntry(_("Editor for new AutoTimers"), config.plugins.autotimer.editor, _("The editor to be used for new AutoTimers. This can either be the Wizard or the classic editor.")),
				getConfigListEntry(_("Support \"Fast Scan\"?"), config.plugins.autotimer.fastscan, _("When supporting \"Fast Scan\" the service type is ignored. You don't need to enable this unless your Image supports \"Fast Scan\" and you are using it.")),
				getConfigListEntry(_("Skip poll during records"), config.plugins.autotimer.skip_during_records, _("If enabled, the polling will be skipped if the Dreambox is recording.")),
				getConfigListEntry(_("Skip poll during epg refresh"), config.plugins.autotimer.skip_during_epgrefresh, _("If enabled, the polling will be skipped if EPGRefres is currently running.")),
				getConfigListEntry(_("Popup timeout in seconds"), config.plugins.autotimer.popup_timeout, _("If 0, the popup will remain open.")),
				getConfigListEntry(_("Remove not existing events"), config.plugins.autotimer.check_eit_and_remove, _("Check the event id (eit) and remove the timer if there is no corresponding EPG event. Due to compatible issues with SerienRecorder and IPRec, only timer created by AutoTimer are affected.")),
				getConfigListEntry(_("Always write config"), config.plugins.autotimer.always_write_config, _("Write the config file after every change which the user quits by saving.")),
				getConfigListEntry(_("Send debug messages to shell"), config.plugins.autotimer.log_shell, _("Send debug messages to shell")),
				getConfigListEntry(_("Write debug messages into file"), config.plugins.autotimer.log_write, _("Write debug messages into file")),
				getConfigListEntry(_("Location and name of log file"), config.plugins.autotimer.log_file, _("Location and name of log file")),
				getConfigListEntry(_("Save/check labelled series in filter list (SeriesPlugin)"), config.plugins.autotimer.series_save_filter, _("Save timer name generated by SeriesPlugin in filter list to use filter for future timer searches (only with SeriesPlugin)")),
				getConfigListEntry(_("Show 'add to filter list' in movielist context menu"), config.plugins.autotimer.show_addto_in_filmmenu, _("Enable to add recordings to filter list from movielist context menu.")),
				getConfigListEntry(_("Match ratio for title duplicate check"), config.plugins.autotimer.title_match_ratio, _("Match ratio defines a minimum value to be met to consider a timer a duplicate when comparing the title (min.=80, max.=100; title must be identical to skip duplicates when set to 100, default=97)")),
				getConfigListEntry(_("Match ratio for extended description duplicate check"), config.plugins.autotimer.extdesc_match_ratio, _("Match ratio defines a minimum value to be met to consider a timer a duplicate when comparing the extended description (min.=80, max.=100; extended description must be identical to skip duplicates when set to 100, default=90)")),
				getConfigListEntry(_("Match ratio for short description duplicate check"), config.plugins.autotimer.shortdesc_match_ratio, _("Match ratio defines a minimum value to be met to consider a timer a duplicate when comparing the short description (min.=80, max.=100; short description must be identical to skip duplicates when set to 100, default=90)")),
				getConfigListEntry(_("Location of autotimer_search.log"), config.plugins.autotimer.searchlog_path, _("Select the path where the autotimer_search.log should be saved")),
				getConfigListEntry(_("Max number of retained search logs"), config.plugins.autotimer.searchlog_max, _("Define the number of search logs to be retained") + " (min.=5, max.=20)"),
			],
			session=session,
			on_change=self.changed
		)

		def selectionChanged():
			if self["config"].current:
				self["config"].current[1].onDeselect(self.session)
			self["config"].current = self["config"].getCurrent()
			if self["config"].current:
				self["config"].current[1].onSelect(self.session)
			for x in self["config"].onSelectionChanged:
				x()
		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["help"] = StaticText()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ChannelSelectBaseActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"nextBouquet": self.pageUp,
				"prevBouquet": self.pageDown,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		from plugin import AUTOTIMER_VERSION
		self.setTitle(_("Configure AutoTimer behavior") + " - Version: " + AUTOTIMER_VERSION)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)
