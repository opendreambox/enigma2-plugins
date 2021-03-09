from enigma import eCec

from .VendorHandlerSamsung import VendorHandlerSamsung
class CecDevice(object):
	def __init__(self, logicalAddress=eCec.ADDR_FREE_USE):
		self._physicalAddress = (0xff, 0xff)
		self._logicalAddress = logicalAddress
		self._vendor = eCec.VENDOR_UNKNOWN
		self._name = None
		self._powerState = eCec.POWER_STATE_UNKNOWN
		self._vendorHandler = None

	def _checkVendorHandler(self):
		if self._vendorHandler and self._vendorHandler.vendor == self.vendorName:
			return
		if self.vendorName == "Samsung":
			self._vendorHandler = VendorHandlerSamsung()

	@property
	def physicalAddress(self):
		return self._physicalAddress

	@physicalAddress.setter
	def physicalAddress(self, value):
		self._physicalAddress = value

	@property
	def logicalAddress(self):
		return self._logicalAddress

	@logicalAddress.setter
	def logicalAddress(self, value):
		self._logicalAddress = value

	@property
	def vendor(self):
		return self._vendor

	@vendor.setter
	def vendor(self, value):
		self._vendor = value
		self._checkVendorHandler()

	@property
	def vendorName(self):
		return eCec.vendor(self.vendor)

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, value):
		self._name = value

	@property
	def powerState(self):
		return self._powerState

	@powerState.setter
	def powerState(self, value):
		self._powerState = value

	def onMessage(self, cec, sender, message):
		if self._vendorHandler:
			return self._vendorHandler.onMessage(cec, self, sender, message)
		return False