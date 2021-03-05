from Tools.Log import Log
from enigma import eCec

from .VendorHandlerBase import VendorHandlerBase

class VendorHandlerSamsung(VendorHandlerBase):
	MAGIC_TOKEN = 0x23

	def __init__(self):
		VendorHandlerBase.__init__(self, "Samsung")
		Log.i()

	def onMessage(self, cec, device, sender, message):
		Log.i()
		cmd = message[0]
		if cmd == eCec.MSG_SET_MENU_LANG:
			device.powerState = eCec.POWER_STATE_ON
		elif cmd == eCec.MSG_VENDOR_COMMAND_WITH_ID:
			if len(message) < 5 or message[5] != self.MAGIC_TOKEN:
				cec.featureAbort(sender, cmd, eCec.ABORT_REASON_INVALID_OPERAND)
				return True
			cec.send(sender, eCec.MSG_VENDOR_COMMAND_WITH_ID, (message[1], message[2], message[3], 0x24, 0x00, 0x80))
			return True
		return False
