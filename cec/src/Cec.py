from enigma import eCec, eTimer, IntList
from Tools.Log import Log
from Components.config import config
from Components.HdmiCec import HdmiCec #Keep this, it initializes the config elements
from Screens import Standby
from Tools.Notifications import isPendingOrVisibleNotificationID

from .CecDevice import CecDevice
from .CecRemote import CecRemote
from .CecBoot import CecBoot

from twisted.internet import reactor

class Cec(object):
	CEC_VERSION_1_1 = 0x00
	CEC_VERSION_1_2 = 0x01
	CEC_VERSION_1_2a = 0x02
	CEC_VERSION_1_3 = 0x03
	CEC_VERSION_1_3a = 0x04
	CEC_VERSION_1_4 = 0x05
	CEC_VERSION_2_0 = 0x06

	def __init__(self):
		self._cec = eCec.getInstance()
		self._cec.handleExternal(True)
		self.session = None
		self.__msg_conn = self._cec.receivedMessage.connect(self._onMessage)
		self._logicalAddress = self._cec.logicalAddress()
		self._physicalAddress = tuple(self._cec.physicalAddress())
		self._activeSource = None
		self._vendor = eCec.VENDOR_DREAM
		self._powerState = eCec.POWER_STATE_ON
		self._devices = {}
		self._checkDevicesTimer = eTimer()
		self.__check_devices_connection = self._checkDevicesTimer.timeout.connect(self.onCheckDevices)
		self._audioStatusTimer = eTimer()
		self.__audio_status_connection = self._audioStatusTimer.timeout.connect(self.giveAudioStatus)
		config.misc.standbyCounter.addNotifier(self._onStandby, initial_call=False)

		#Volume control
		self._volumeDest = eCec.ADDR_TV
		self._volume = -1
		self._muted = False
		self.onVolumeChanged = []

		#Remote control
		self.onKeyPressed = []
		self.onKeyReleased = []
		self._remote = CecRemote(self)

	def start(self, session):
		self.session = session
		#don't set this in init to avoid powerOn on boot to idle
		self.__ready_conn = self._cec.ready.connect(self._onReady)
		self._onReady(self._cec.logicalAddress(), self._cec.physicalAddress(), force=True)

	@property
	def devices(self):
		return self._devices.values()

	@property
	def physicalAddress(self):
		return self.physicalToString(self._physicalAddress)

	@property
	def logicalAddress(self):
		return self._logicalAddress

	def physicalToString(self, addr):
		if not addr:
			return "<invalid address>"
		return "%x.%x.%x.%x" % ((addr[0] >> 4) & 0xf, addr[0] & 0xf, (addr[1] >> 4) & 0xf, addr[1] & 0xf)

	def isStandby(self, state):
		return state == eCec.POWER_STATE_STANDBY or state == eCec.POWER_STATE_TRANSITION_ON_TO_STANDBY

	def _onReady(self, logicalAddress, physicalAddress, force=False):
		oldPhysical = self._physicalAddress
		self._logicalAddress = logicalAddress
		self._physicalAddress = tuple(physicalAddress)

		if self._activeSource == oldPhysical and self.isReady():
			self.handleActiveSource(physicalAddress)

		Log.i("Physical address: %s # Logical address: %s" % (self.physicalToString(self._physicalAddress), self._logicalAddress))
		if not self.getDevice(eCec.ADDR_TV):
			self.givePhysicalAddress(eCec.ADDR_TV)

		if self.isReady():
			if oldPhysical != self._physicalAddress or force:
				self.reportPhysicalAddress()
				self.givePhysicalAddress(eCec.ADDR_AUDIO_SYSTEM)
				self.giveSystemAudioModeStatus()
			if isPendingOrVisibleNotificationID("Standby"):
				Log.i("Standby pending. Doing nothing")
				return
			if Standby.inStandby == None:
				self.powerOn()
			else:
				Log.i("Standby, not waking up.")

	def isReady(self):
		return self._physicalAddress != (0xff, 0xff)

	def isForMe(self, logicalAddress):
		return logicalAddress == self._logicalAddress

	def dumpDevices(self):
		for d in self._devices.values():
			Log.i("%s (%s)\t%s\t%s" % (d.name, d.vendorName, d.logicalAddress, self.physicalToString(d.physicalAddress)))

	def checkDevices(self):
		self.onCheckDevices(allDevices=True)

	def onCheckDevices(self, allDevices=False):
		for d in self._devices.values():
			if not allDevices:
				if not d.logicalAddress in (eCec.ADDR_AUDIO_SYSTEM, eCec.ADDR_TV):
					return
			commands = []
			if allDevices and d.physicalAddress == (0xff, 0xff):
				Log.i("requesting physical address of %s" % (d.logicalAddress,))
				commands.append(eCec.MSG_GIVE_PHYS_ADDR)
			if d.vendor == eCec.VENDOR_UNKNOWN:
				Log.i("requesting vendor of %s" % (d.logicalAddress))
				commands.append(eCec.MSG_GIVE_DEVICE_VENDOR_ID)
			if allDevices and not d.name:
				Log.i("requesting name of %s" % (d.logicalAddress,))
				commands.append(eCec.MSG_GIVE_OSD_NAME)
			commands.append(eCec.MSG_GIVE_DEVICE_POWER_STATUS)
			[self.send(d.logicalAddress, cmd) for cmd in commands]

	def requireDevice(self, logicalAddress):
		device = self.getDevice(logicalAddress)
		if device:
			return device
		Log.i("add device logicalAddress: %s" % logicalAddress)
		device = CecDevice(logicalAddress)
		self._devices[logicalAddress] = device
		if not self._checkDevicesTimer.isActive():
			self._checkDevicesTimer.start(200, True)
		return device

	def getDevice(self, logicalAddress):
		return self._devices.get(logicalAddress, None)

	def updateDeviceAddress(self, logicalAddress, physicalAddress):
		self.requireDevice(logicalAddress).physicalAddress = physicalAddress
		self.dumpDevices()

	def updateDeviceVendor(self, logicalAddress, vendor):
		self.requireDevice(logicalAddress).vendor = vendor
		self.dumpDevices()

	def updateDeviceName(self, logicalAddress, name):
		self.requireDevice(logicalAddress).name = name
		self.dumpDevices()

	def updateDevicePowerState(self, logicalAddress, powerState):
		self.requireDevice(logicalAddress).powerState = powerState
		self.dumpDevices()

	def _onStandby(self, element):
		Standby.inStandby.onClose.append(self.powerOn)
		self.powerOff()

	def powerOff(self):
		Log.i(" ")
		if not (config.cec.enabled.value and config.cec.sendpower.value):
			CecBoot.uninstall()
			return
		CecBoot.install(self.logicalAddress, self.physicalAddress)
		self.systemStandby()
		self.inactiveSource()
		self.setPowerState(eCec.POWER_STATE_STANDBY)

	def powerOn(self):
		Log.i(" ")
		if not config.cec.sendpower.value:
			return
		self.setPowerState(eCec.POWER_STATE_ON)
		self.oneTouchPlay()

	def isActiveSource(self):
		Log.i("%s <=> %s" % (self.physicalToString(self._activeSource), self.physicalToString(self._physicalAddress)))
		return self._activeSource == self._physicalAddress

	def toHexString(self, message):
		msg = ""
		for b in message:
			msg += "%02x " % (b)
		return msg

	def stringMessage(self, value):
		return [ord(x) for x in value]

	def send(self, to, command, message=[]):
		message = (message)
		Log.i("self > %x :: %02x %s (%s)" % (to, command, self.toHexString(message), config.cec.enabled.value))
		if not config.cec.enabled.value:
			return
		self._cec.sendMsg(to, command, IntList(message))

	def sendKey(self, to, code):
		if self.isActiveSource():
			self.send(to, eCec.MSG_USER_CONTROL_PRESSED, [code])
			self.send(to, eCec.MSG_USER_CONTROL_RELEASED)

	def sendSystemAudioKey(self, keyid, test=False):
		if self._volumeDest is eCec.ADDR_AUDIO_SYSTEM:
			self.sendKey(self._volumeDest, keyid)
			if not self._audioStatusTimer.isActive():
				self._audioStatusTimer.start(500, True)
			return True
		return False

	def featureAbort(self, to, command, reason):
		self.send(to, eCec.MSG_FEATURE_ABORT, [command, reason])

	def _onMessage(self, sender, receiver, message):
		Log.i("%x > %x :: %s (%s)" % (sender, receiver, self.toHexString(message), config.cec.enabled.value))
		if not config.cec.enabled.value:
			return
		if sender == eCec.ADDR_FREE_USE:
			return
		device = self.requireDevice(sender)
		if sender == eCec.ADDR_AUDIO_SYSTEM and self._volumeDest != eCec.ADDR_AUDIO_SYSTEM:
			self._volumeDest = eCec.ADDR_AUDIO_SYSTEM
			if self.isActiveSource():
				self.systemAudioModeRequest()

		if device.onMessage(self, sender, message):
			return

		cmd = message[0]
		if cmd == eCec.MSG_GIVE_PHYS_ADDR:
			self.onGivePhysicalAddress(sender)
		elif cmd == eCec.MSG_GET_CEC_VERSION:
			self.onGetCecVersion(sender)
		elif cmd == eCec.MSG_REPORT_PHYS_ADDR:
			self.onReportPhysicalAddress(sender, message)
		elif cmd == eCec.MSG_ACTIVE_SOURCE:
			self.onActiveSource(sender, message)
		elif cmd == eCec.MSG_GIVE_OSD_NAME:
			self.onGiveOsdName(sender)
		elif cmd == eCec.MSG_SET_MENU_LANG:
			self.onSetMenuLang(sender, message)
		elif cmd == eCec.MSG_SET_OSD_NAME:
			self.onSetOsdName(sender, message)
		elif cmd == eCec.MSG_REPORT_POWER_STATUS:
			self.onReportPowerStatus(sender, message)
		elif cmd == eCec.MSG_GIVE_DEVICE_POWER_STATUS:
			self.onGiveDevicePowerStatus(sender)
		elif cmd == eCec.MSG_GIVE_DEVICE_VENDOR_ID:
			self.onGiveDeviceVendorId(sender)
		elif cmd == eCec.MSG_DEVICE_VENDOR_ID:
			self.onDeviceVendorId(sender, message)
		elif cmd == eCec.MSG_VENDOR_COMMAND_WITH_ID:
			self.onVendorCommandWithId(sender, message)
		elif cmd == eCec.MSG_ROUTING_INFORMATION:
			self.onRoutingInformation(sender, message)
		elif cmd == eCec.MSG_ROUTING_CHANGE:
			self.onRoutingChange(sender, message)
		elif cmd == eCec.MSG_SET_STREAMPATH:
			self.onSetStreamPath(sender, message)
		elif cmd == eCec.MSG_MENU_REQUEST:
			self.onMenuRequest(sender)
		elif cmd == eCec.MSG_STANDBY:
			self.onStandby(sender)
		elif cmd == eCec.MSG_USER_CONTROL_PRESSED:
			self.onUserControlPressed(sender, message)
		elif cmd == eCec.MSG_USER_CONTROL_RELEASED:
			self.onUserControlReleased(sender, message)
		elif cmd == eCec.MSG_SYSTEM_AUDIO_MODE_STATUS:
			self.onSystemAudioModeStatus(sender, message)
		elif cmd == eCec.MSG_SET_SYSTEM_AUDIO_MODE:
			self.onSetSystemAudioMode(sender, message)
		elif cmd == eCec.MSG_SYSTEM_AUDIO_MODE_REQUEST:
			self.onSystemAudioModeRequest(sender, message)
		elif cmd == eCec.MSG_REPORT_AUDIO_STATUS:
			self.onReportAudioStatus(sender, message)
		elif cmd == eCec.MSG_TEXT_VIEW_ON:
			self.onTextViewOn(sender, message)
		#error handling
		elif cmd == eCec.MSG_FEATURE_ABORT:
			self.onFeatureAbort(sender, message)
		elif self.isForMe(receiver): # FEATURE ABORT unhandled commands
			self.featureAbort(sender, cmd, eCec.ABORT_REASON_UNRECOGNIZED_OPCODE)

	def onGivePhysicalAddress(self, sender):
		self.reportPhysicalAddress()

	def onReportPhysicalAddress(self, sender, message):
		self.updateDeviceAddress(sender, message[1:3])
		if sender == eCec.ADDR_TV:
			self.requestActiveSource()

	def onActiveSource(self, sender, message):
		self.handleActiveSource(message[1:3])

	def onReportPowerStatus(self, sender, message):
		self.requireDevice(sender).powerState = message[1]

	def onGetCecVersion(self, sender):
		self.reportCecVersion(sender)

	def onGiveOsdName(self, sender):
		self.setOsdName(sender)

	def onSetMenuLang(self, sender, message):
		Log.i("".join([chr(x) for x in message[1:]]))

	def onSetOsdName(self, sender, message):
		self.updateDeviceName(sender, "".join([chr(x) for x in message[1:]]))

	def onGiveDevicePowerStatus(self, sender):
		self.reportPowerStatus(sender)

	def onGiveDeviceVendorId(self, sender):
		self.deviceVendorId(sender)

	def onDeviceVendorId(self, sender, message):
		self.updateDeviceVendor(sender, message[1] << 16 | message[2] << 8 | message[3])

	def onVendorCommandWithId(self, sender, message):
		self.onDeviceVendorId(sender, message)
		#answer with MSG_FEATURE_ABORT to sender
		self.featureAbort(sender, eCec.MSG_VENDOR_COMMAND_WITH_ID, eCec.ABORT_REASON_UNRECOGNIZED_OPCODE)

	def onRoutingInformation(self, sender, message):
		# cmd, pyhs_addr( (2bytes)
		activeSource = tuple(message[1:3])
		Log.i("activeSource: %s" % self.physicalToString(activeSource))
		self.handleActiveSource(activeSource)

	def onRoutingChange(self, sender, message):
		# cmd , from_phys_addr (2bytes), to_phys_addr( (2bytes)
		activeSource = tuple(message[3:5])
		Log.i("activeSource: %s" % self.physicalToString(activeSource))
		self.handleActiveSource(activeSource)

	def onSetStreamPath(self, sender, message):
		# same as routing information
		Log.i("sender: %s, message: %s" % (sender, message))
		self.onRoutingInformation(sender, message)

	def onMenuRequest(self, sender):
		self.setMenuStatus(sender)

	def onStandby(self, sender):
		Log.i("%s %s (%s)" % (sender, self.session, config.cec.receivepower.value))
		if not config.cec.receivepower.value:
			return
		if sender == eCec.ADDR_TV and self.session:
			if not Standby.inStandby and self.session.current_dialog and self.session.current_dialog.ALLOW_SUSPEND and self.session.in_exec:
				self.session.open(Standby.Standby)

	def onUserControlPressed(self, sender, message):
		Log.i("%s %s (%s)" % (sender, message, message[1]))
		#activate if we're getting keypresses from the tv
		keyid = message[1]
		if not self.isActiveSource() and sender == eCec.ADDR_TV and keyid != eCec.RC_POWER_OFF:
			self.handleActiveSource(self._physicalAddress)
		for fnc in self.onKeyPressed:
			fnc(sender, keyid)

	def onUserControlReleased(self, sender, message):
		Log.i("%s %s" % (sender, message))
		for fnc in self.onKeyReleased:
			fnc(sender)

	def onSystemAudioModeStatus(self, sender, message):
		self._volumeDest = sender if message[1] else 0

	def onSetSystemAudioMode(self, sender, message):
		self.onSystemAudioModeStatus(sender, message)

	def onSystemAudioModeRequest(self, sender, message):
		device = self.getDevice(sender)
		device.powerState = eCec.POWER_STATE_ON
		activeSource = tuple(message[1:3])
		self.handleActiveSource(activeSource)

	def onTextViewOn(self, sender, message):
		self.handleActiveSource(self.getDevice(sender).physicalAddress)

	def onFeatureAbort(self, sender, message):
		Log.w("%s :: %02x %02x" % (sender, message[1], message[2]))

	def onReportAudioStatus(self, sender, message):
		if not self._volumeDest:
			self._volumeDest = sender
		self._muted = message[1] & 0x80 == 0x80
		self._volume = message[1] & 0x7f
		Log.i("%s: muted: %s #  volume: %s" % (sender, self._muted, self._volume))
		for fnc in self.onVolumeChanged:
			fnc(self._muted, self._volume)

	def handleActiveSource(self, physicalAddress):
		Log.i("new: %s # old: %s" % (self.physicalToString(physicalAddress), self.physicalToString(self._activeSource)))
		if physicalAddress == (0xff, 0xff):
			return
		if physicalAddress != self._activeSource:
			reenforce = self.isActiveSource() and config.cec2.active_source_agression.value and physicalAddress == (0, 0)
			self._activeSource = physicalAddress
			if reenforce:
				Log.w("Reenforcing myself as Active Source!")
				reactor.callLater(1, self.oneTouchPlay)
			else:
				self.onActiveSourceChanged()

	def onActiveSourceChanged(self, force=False):
		Log.i(self.physicalToString(self._activeSource))
		if config.cec.sendpower.value and (self.isActiveSource() or force):
			if Standby.inStandby != None:
				Standby.inStandby.Power()
			self.send(eCec.ADDR_UNREGISTERED_BROADCAST, eCec.MSG_ACTIVE_SOURCE, self._physicalAddress)

		if config.cec.receivepower.value and not self.isActiveSource() and not Standby.inStandby:
			if self.session.current_dialog and self.session.current_dialog.ALLOW_SUSPEND and self.session.in_exec:
				self.session.open(Standby.Standby)

	def givePhysicalAddress(self, to):
		Log.i(" ")
		self.send(to, eCec.MSG_GIVE_PHYS_ADDR)

	def giveDevicePowerStatus(self, to):
		Log.i(" ")
		self.send(to, eCec.MSG_GIVE_DEVICE_POWER_STATUS)

	def reportPowerStatus(self, to):
		self.send(to, eCec.MSG_REPORT_POWER_STATUS, [self._powerState, ])

	def reportCecVersion(self, to):
		Log.i(" ")
		self.send(to, eCec.MSG_VERSION, [self.CEC_VERSION_1_3a, ]) # HDMI CEC Version 1.3a

	def reportPhysicalAddress(self):
		self.send(eCec.ADDR_UNREGISTERED_BROADCAST, eCec.MSG_REPORT_PHYS_ADDR, self._physicalAddress + (eCec.DEVICE_TYPE_TUNER,))

	def deviceVendorId(self, to=eCec.ADDR_UNREGISTERED_BROADCAST):
		vendor = [(self._vendor & 0xFF0000) >> 16]
		vendor.append((self._vendor & 0xFF00) >> 8)
		vendor.append((self._vendor & 0xFF))
		self.send(to, eCec.MSG_DEVICE_VENDOR_ID, vendor)

	def setOsdName(self, to):
		self.send(to, eCec.MSG_SET_OSD_NAME, self.stringMessage(config.cec.name.value))

	def setMenuStatus(self, to):
		self.send(to, eCec.MSG_MENU_STATUS, [0])

	def requestActiveSource(self):
		self.send(eCec.ADDR_UNREGISTERED_BROADCAST, eCec.MSG_REQUEST_ACTIVE_SOURCE, self._physicalAddress)

	def imageViewOn(self):
		if not config.cec.sendpower.value:
			return
		self.send(eCec.ADDR_TV, eCec.MSG_IMAGE_VIEW_ON)

	def activeSource(self):
		self.handleActiveSource(self._physicalAddress[:])

	def inactiveSource(self):
		if self._activeSource == self._physicalAddress and config.cec.sendpower.value:
			self.send(eCec.ADDR_UNREGISTERED_BROADCAST, eCec.MSG_INACTIVE_SOURCE, self._physicalAddress)
			self.handleActiveSource(None)

	def systemStandby(self):
		if config.cec.sendpower.value and self.isActiveSource():
			Log.i("send MSG_STANDBY")
			self.send(eCec.ADDR_UNREGISTERED_BROADCAST, eCec.MSG_STANDBY)

	def giveSystemAudioModeStatus(self):
		self.send(eCec.ADDR_UNREGISTERED_BROADCAST, eCec.MSG_GIVE_SYSTEM_AUDIO_MODE_STATUS)

	def systemAudioModeRequest(self):
		if not config.cec.sendpower.value or not config.cec.enable_avr.value:
			return
		self.send(eCec.ADDR_AUDIO_SYSTEM, eCec.MSG_SYSTEM_AUDIO_MODE_REQUEST, self._physicalAddress)

	def giveAudioStatus(self):
		if self._volumeDest == eCec.ADDR_AUDIO_SYSTEM:
			self.send(self._volumeDest, eCec.MSG_GIVE_AUDIO_STATUS)

	def setPowerState(self, state):
		if state == self._powerState:
			return
		self._powerState = state
		self.reportPowerStatus(eCec.ADDR_UNREGISTERED_BROADCAST)

	def oneTouchPlay(self):
		if not config.cec.sendpower.value:
			return
		self.imageViewOn()
		self.activeSource()
		self.systemAudioModeRequest()

cec = Cec()
