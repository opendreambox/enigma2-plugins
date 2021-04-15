from __future__ import absolute_import
from Components.ActionMap import ActionMap
from Components.config import ConfigOnOff, ConfigSubsection, config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from .CecDeviceList import CecDeviceList


config.cec2 = ConfigSubsection()
config.cec2.active_source_agression = ConfigOnOff(default=False)
class CecConfig(ConfigListScreen, Screen):
	skin = """
		<screen name="CecConfig" position="center,120" size="820,520" title="HDMI CEC: Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,0" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,0" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,0" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,0" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="10,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="210,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="410,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="610,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="config" position="5,60" size="810,450" scrollbarMode="showOnDemand" enableWrapAround="1"/>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)

		ConfigListScreen.__init__(self, [], session=session)
		config.cec.enabled.addNotifier(self._recreateSetup, initial_call=False)

		self._createSetup()

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		# SKIN Compat HACK!
		self["key_yellow"] = StaticText(_("Reset"))
		self["key_blue"] = StaticText(_("Devices"))
		# EO SKIN Compat HACK!
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.restoreDefaults,
			"blue": self._showDeviceList,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.layoutFinished)

	def _showDeviceList(self):
		self.session.open(CecDeviceList)

	def __onClose(self):
		config.cec.enabled.removeNotifier(self._recreateSetup)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self._createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self._createSetup()

	def _recreateSetup(self, element):
		self._createSetup()

	def _createSetup(self):
		lst = [getConfigListEntry(_("HDMI CEC"), config.cec.enabled), ]
		if not config.cec.enabled.value:
			self["config"].list = lst
			return
		lst.extend([
			getConfigListEntry(_("OSD Name"), config.cec.name),
			getConfigListEntry(_("Power Handling")),
			getConfigListEntry(_("Send HDMI CEC Power Events"), config.cec.sendpower),
			])
		if config.cec.sendpower.value:
			lst.append(getConfigListEntry(_("Power on AV-Receiver"), config.cec.enable_avr))
		lst.extend([
				getConfigListEntry(_("Power on/off based on CEC Events"), config.cec.receivepower),
			])

		lst.extend([
			getConfigListEntry(_("Remote control")),
			getConfigListEntry(_("Allow remote control via CEC"), config.cec.receive_remotekeys),
			getConfigListEntry(_("Forward Volume keys to TV/AVR"), config.cec.volume_forward),
			getConfigListEntry(_("Remote control repeat delay (ms)"), config.cec.remote_repeat_delay),
		])

		lst.extend([
			getConfigListEntry(_("Expert options")),
			getConfigListEntry(_("Aggressive Active-Source"), config.cec2.active_source_agression)
		])

		self["config"].list = lst

	def restoreDefaults(self):
		self.session.openWithCallback(self._doRestoreDefaults, MessageBox, _("This will reset all CeC settings to their factory defaults\nContinue?"), type=MessageBox.TYPE_YESNO, title=_("Reset to defaults?"))

	def _doRestoreDefaults(self, answer):
		if answer:
			#Don't reset the name here, it jusn't doesn't change anything :)
			elements = [
				config.cec.enabled,
				config.cec.sendpower,
				config.cec.enable_avr,
				config.cec.receivepower,
				config.cec.receive_remotekeys,
				config.cec.volume_forward,
				config.cec.remote_repeat_delay,
			]
			for e in elements:
				e.value = e.default
			self._createSetup()

	def layoutFinished(self):
		self.setTitle(_("HDMI CEC: Setup"))

	def save(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		self.close(True, self.session)

	def cancel(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].cancel()
		self.close(False, self.session)
