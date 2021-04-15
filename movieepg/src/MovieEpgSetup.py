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


class MovieEpgSetup(Screen, ConfigListScreen):
	skin = """<screen name="MovieEpgSetup" position="center,center" size="820,300" >
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel position="10,50" size="800,1" backgroundColor="grey" />
		<widget name="config" position="10,60" size="800,120" enableWrapAround="1" scrollbarMode="showOnDemand" />
		<eLabel position="10,200" size="800,1" backgroundColor="grey" />
		<widget source="help" render="Label" position="10,210" size="800,80" font="Regular;21" halign="center" valign="center" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("Movie-EPG Configuration")
		self.onChangedEntry = []

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Show \"EPG\" entry"), config.plugins.movieepg.show_epg_entry, _("Configures where to show the \"EPG\"-Entry in the Extensions-List. You can either show this just in the movie player, the movie player and TV-mode or never.")),
				getConfigListEntry(_("Show all Plugins in MoviePlayer?"), config.plugins.movieepg.show_servicelist_plugins_in_movieplayer, _("Enables you to show all plugins in the (regular) movie player, including ones which may have previously been hidden there like the Graphical Multi-EPG.")),
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
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Movie-EPG Configuration"))

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
