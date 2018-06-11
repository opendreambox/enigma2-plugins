# for localized messages
# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigSelection, NoSave

# GUI (Summary)
from Screens.Setup import SetupSummary
from Screens.InfoBar import InfoBar

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, getConfigListEntry

class EPGSearchSetup(Screen, ConfigListScreen):
	skin = """<screen name="EPGSearchSetup" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40"/>
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,350" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		<eLabel position="10,420" size="800,1" backgroundColor="grey"/>
		<widget source="help" render="Label" position="10,430" size="800,80" font="Regular;21" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("EPGSearch Setup")
		self.onChangedEntry = []

		#set config-values for search_scope-config
		self.scopeChoices = self.getScopeChoices()
		self.scopeChoices_default = self.getScopeChoicesDefault()
		self.config_search_scope = NoSave( ConfigSelection(choices=self.scopeChoices, default=self.scopeChoices_default) )

		self.list = []
		self.buildConfig()
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

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
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def buildConfig(self):
		self.list.append( getConfigListEntry(_("Length of History"), config.plugins.epgsearch.history_length, _("How many entries to keep in the search history at most. 0 disables history entirely!")) )
		self.list.append( getConfigListEntry(_("Add \"Search\" Button to EPG"), config.plugins.epgsearch.add_search_to_epg , _("If this setting is enabled, the plugin adds a \"Search\" Button to the regular EPG.")) )
		self.list.append( getConfigListEntry(_("Search type"), config.plugins.epgsearch.search_type, _("Select \"exact\" match to enforce \"Match title\" to match exactly, \"partial\" if you only want to search for a part of the event title or description or \"Ask user\"")) )
		self.list.append( getConfigListEntry(_("Search scope"), self.config_search_scope, _("Search will return only matches from services in the selected bouquet")) )
		if self.config_search_scope.value != "all":
			self.list.append( getConfigListEntry(_("show events"), config.plugins.epgsearch.show_events, _("Show 'all', 'current', 'future' or 'current & future' events. So you can filter the matches by the event-time.")) )
		self.list.append( getConfigListEntry(_("Show Picons"), config.plugins.epgsearch.show_picon, _("Show the the picon of the channel instead of channelname. Use the picon-path from the channelselection-settings.")) )
		if not config.plugins.epgsearch.show_picon.value:
			self.list.append( getConfigListEntry(_("show most matched channelname in screen-title"), config.plugins.epgsearch.show_sname_in_title, _("Show the most matched channelname in the screen-title. So you have more place to show eventname and short description.")) )
		self.list.append( getConfigListEntry(_("show short description"), config.plugins.epgsearch.show_shortdesc, _("Add the short description of the event to the search-result")) )

	def getScopeChoicesDefault(self):
		scopeChoices_default = "all"

		for choice in self.scopeChoices:
			if config.plugins.epgsearch.search_scope.value == choice[0]:
				scopeChoices_default = config.plugins.epgsearch.search_scope.value
				break

		return scopeChoices_default

	def getScopeChoices(self):
		#set config-values for bouquet-config
		config_scope_choices = [("all",_("all services")), ("current",_("current bouquet"))]

		#get bouquetlist
		infoBarInstance = InfoBar.instance
		if infoBarInstance is not None:
			bouquets = infoBarInstance.servicelist.getBouquetList()
			for bouquet in bouquets:
				config_scope_choices.append((bouquet[1].toString(),bouquet[0]))

		return config_scope_choices

	def keySave(self):
		self.saveAll()
		#config.plugins.epgsearch.search_current_bouquet.value = self.config_search_current_bouquet.value
		config.plugins.epgsearch.search_scope.value = self.config_search_scope.value
		config.plugins.epgsearch.save()
		self.close()

	def changeConfig(self):
		self.list = []
		self.buildConfig()
		self["config"].setList(self.list)

	def changed(self):
		for x in self.onChangedEntry:
			x()
		current = self["config"].getCurrent()[1]
		if (current == config.plugins.epgsearch.show_picon) or (current == self.config_search_scope):
			self.changeConfig()
			return

	def setCustomTitle(self):
		self.setTitle(_("EPGSearch Setup"))

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary