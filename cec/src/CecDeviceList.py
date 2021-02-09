from enigma import eCec
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Screens.Screen import Screen
from Tools.Log import Log

from .Cec import cec

class CecDeviceList(Screen):
	DEVICE_TYPE = {
		eCec.ADDR_TV : _("TV"),
		eCec.ADDR_RECORDING_DEVICE_1 : _("Recording Device"),
		eCec.ADDR_RECORDING_DEVICE_2 : _("Recording Device 2"),
		eCec.ADDR_TUNER_1 : _("Tuner"),
		eCec.ADDR_PLAYBACK_DEVICE_1 : _("Playback Device"),
		eCec.ADDR_AUDIO_SYSTEM : _("Audio System"),
		eCec.ADDR_TUNER_2 : _("Tuner 2"),
		eCec.ADDR_TUNER_3 : _("Tuner 3"),
		eCec.ADDR_PLAYBACK_DEVICE_2 : _("Playback Device 2"),
		eCec.ADDR_RECORDING_DEVICE_3 : _("Recording Device 3"),
		eCec.ADDR_TUNER_4 : _("Tuner 4"),
		eCec.ADDR_PLAYBACK_DEVICE_3 : _("Playback Device 3"),
	}

	skin = """
	<screen name="CeCDeviceList" position="center,center" size="560,400" title="HDMI CeC: Devices">
			<widget name="list" position="5,5" size="550,490" scrollbarMode="showOnDemand" zPosition="1"/>
	</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self["list"] = MenuList([], enableWrapAround=True)
		self["deviceActions"] = ActionMap(["OkCancelActions"],
		actions={
			"cancel" : self.close,
		})
		self.setTitle(_("HDMI CeC: Devices"))
		self.reload()

	def reload(self):
		devices = []
		for device in cec.devices:
			deviceType = self.DEVICE_TYPE.get(device.logicalAddress, _("Other"))
			text = "{0} - {1} {2}".format(deviceType, device.vendorName, device.name)
			Log.i(text)
			devices.append(text)
		self["list"].setList(devices)
