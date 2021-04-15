from enigma import eCec, eTimer
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.Log import Log

from .Cec import cec

class CecDeviceList(Screen):
	DEVICE_TYPE = {
		eCec.ADDR_TV: _("TV"),
		eCec.ADDR_RECORDING_DEVICE_1: _("Recording Device"),
		eCec.ADDR_RECORDING_DEVICE_2: _("Recording Device 2"),
		eCec.ADDR_TUNER_1: _("Tuner"),
		eCec.ADDR_PLAYBACK_DEVICE_1: _("Playback Device"),
		eCec.ADDR_AUDIO_SYSTEM: _("Audio System"),
		eCec.ADDR_TUNER_2: _("Tuner 2"),
		eCec.ADDR_TUNER_3: _("Tuner 3"),
		eCec.ADDR_PLAYBACK_DEVICE_2: _("Playback Device 2"),
		eCec.ADDR_RECORDING_DEVICE_3: _("Recording Device 3"),
		eCec.ADDR_TUNER_4: _("Tuner 4"),
		eCec.ADDR_PLAYBACK_DEVICE_3: _("Playback Device 3"),
	}

	DEVICE_POWERSTATE = {
		eCec.POWER_STATE_ON: _("On"),
		eCec.POWER_STATE_STANDBY: _("Standby"),
		eCec.POWER_STATE_TRANSITION_STANDBY_TO_ON: _("Standby to On"),
		eCec.POWER_STATE_TRANSITION_ON_TO_STANDBY: _("On to Standby"),
		eCec.POWER_STATE_UNKNOWN: _("Unknown"),
	}

	skin = """
	<screen name="CeCDeviceListv2" position="center,center" size="560,400" title="HDMI CeC: Devices">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,0" size="150,40" scale="stretch" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="160,0" size="150,40" scale="stretch"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="310,0" size="150,40" scale="stretch"/>
		<widget source="key_red" render="Label" position="10,0" zPosition="1" size="150,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="160,0" zPosition="1" size="150,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_yellow" render="Label" position="310,0" zPosition="1" size="150,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
		<ePixmap pixmap="skin_default/buttons/key_info.png" position="470,5" size="72,30" />
		<eLabel position="10,50" size="540,1" backgroundColor="grey" />
		<widget name="list" position="10,60" size="540,330" scrollbarMode="showOnDemand" zPosition="1"/>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "CeCDeviceListv2"
		self["list"] = MenuList([], enableWrapAround=True)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Refresh"))
		self["key_yellow"] = StaticText(_("Scan"))
		self["deviceActions"] = ActionMap(["OkCancelActions", "ColorActions", "EPGSelectActions"],
		actions={
			"cancel": self.close,
			"green": self.updateDeviceInfo,
			"yellow": self.scanDevices,
			"info": self.deviceInfo,
		})

		self._reloadtimer = eTimer()
		self._reloadtimer_conn = self._reloadtimer.timeout.connect(self.reload)

		self.setTitle(_("HDMI CeC: Devices"))
		self.reload()

	def scanDevices(self):
		for i in list(range(eCec.ADDR_TV, eCec.ADDR_UNREGISTERED_BROADCAST)):
			device = cec.getDevice(i)
			if not device: #search for unlisted devices
				cec.send(i, eCec.MSG_GIVE_DEVICE_POWER_STATUS)
		self.updateDeviceInfo()

	def updateDeviceInfo(self):
		cec.checkDevices()
		for device in cec.devices:
			Log.i("requesting latest powerState from %s" % (device.logicalAddress))
			commands = [eCec.MSG_GIVE_DEVICE_POWER_STATUS]
			if device.physicalAddress == (255, 255):
				Log.i("requesting physicalAddress from %s" % (device.logicalAddress))
				commands.append(eCec.MSG_GIVE_PHYS_ADDR)
			[cec.send(device.logicalAddress, cmd) for cmd in commands]
		self._reloadtimer.start(1500, True)

	def deviceInfo(self):
		cur = self['list'].getCurrent()
		if cur:
			device = cec.getDevice(cur[1])
			if device:
				txt = _("Name: %s\n") % (device.name or _("Unknown"),)
				txt += _("Type: %s\n") % self.DEVICE_TYPE.get(device.logicalAddress, _("Other"))
				txt += _("Vendor: %s\n") % _(device.vendorName)
				txt += _("Logical address: %s\n") % cur[1]
				txt += _("Physical address: %s\n") % cec.physicalToString(device.physicalAddress)
				txt += _("Power state: %s\n") % self.DEVICE_POWERSTATE.get(device.powerState, _("Other"))
				self.session.open(MessageBox, txt, MessageBox.TYPE_INFO, title="HDMI CEC: Device Info")

	def reload(self):
		devices = []
		for device in cec.devices:
			deviceType = self.DEVICE_TYPE.get(device.logicalAddress, _("Other"))
			text = "{0} - {1} ({2})".format(deviceType, device.name or _("Unknown"), _(device.vendorName))
			Log.i(text)
			devices.append((text, device.logicalAddress))
		self["list"].setList(devices)
