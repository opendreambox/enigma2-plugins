from Screens.Screen import Screen
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

class ScreensaverSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		title = _("Screensaver - Setup")
		self.setup_title = _(title)
		Screen.__init__(self, session, windowTitle=title)
		ConfigListScreen.__init__(self, [], session, self.recreateSetup)
		self.skinName = "Setup"

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["actions"] = ActionMap(["SetupActions"], {
			"cancel": self.keyCancel,
			"save": self.keySave,
		})
		self.recreateSetup()

	def keyOK(self):
		self.keySave()

	def recreateSetup(self):
		cfg = config.plugins.screensaver
		lst = [
			getConfigListEntry(_("Automatic Screensaver"), cfg.enabled),
		]
		if cfg.enabled.value:
			lst.append(getConfigListEntry(_("Seconds before activation"), cfg.delay))
		lst.extend([
			getConfigListEntry(_("Seconds between images"), cfg.photo.retention),
			getConfigListEntry(_("Cross fade duration (seconds)"), cfg.photo.speed)
		])
		self["config"].list = lst
