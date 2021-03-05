
class VendorHandlerBase(object):
	def __init__(self, vendor):
		self._vendor = vendor

	@property
	def vendor(self):
		return self._vendor

	def onMessage(self, cec, device, sender, message):
		raise NotImplementedError