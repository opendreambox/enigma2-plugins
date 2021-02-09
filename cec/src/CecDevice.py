from enigma import eCec

class CecDevice(object):
	def __init__(self, logicalAddress=eCec.ADDR_FREE_USE):
		self.physicalAddress = (0xff, 0xff)
		self.logicalAddress = logicalAddress
		self.vendor = eCec.VENDOR_UNKNOWN
		self.name = None
		self.powerState = eCec.POWER_STATE_UNKNOWN


	@property
	def vendorName(self):
		return eCec.vendor(self.vendor)