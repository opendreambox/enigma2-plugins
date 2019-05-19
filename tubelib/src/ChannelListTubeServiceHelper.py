from Screens.ChoiceBox import ChoiceBox
from Tools.Log import Log
import six

class ChannelListServiceProviderBase(object):
	def __init__(self, session, csel, callback):
		self._session = session
		self._csel = csel
		self._callback = callback
		self._tubeUri = None
		self._createServiceForChannelList()

	def _createServiceForChannelList(self):
		raise NotImplementedError

	def _finish(self, ref):
		self._callback(self._csel, ref)

class ChannelListTubeServiceHelper(object):
	PROVIDER = {}

	@staticmethod
	def addProvider(key, cls):
		Log.w("%s, %s" % (key, cls))
		assert(isinstance(cls, ChannelListServiceProviderBase))
		mykey = key
		i = 1
		while mykey in ChannelListTubeServiceHelper.PROVIDER:
			mykey = "%s_%s" % (key, i)
			i += 1
		ChannelListTubeServiceHelper.PROVIDER[mykey] = cls

	def __init__(self, session, csel, callback):
		self._session = session
		self._csel = csel
		self._callback = callback
		self.addTubeServiceToChannelList()

	def _run(self, provider):
		return provider(self._session, self._csel, self._callback)

	def addTubeServiceToChannelList(self):
		if not self.PROVIDER:
			return False
		if len(self.PROVIDER) == 1 and False:
			provider = self.PROVIDER[list(self.PROVIDER.keys())[0]]
			return self._run(provider)
		self._pickTube()

	def _pickTube(self):
		choices = []
		for key, cls in six.iteritems(self.PROVIDER):
			choices.append((cls.DESCRIPTION, key))
		self._session.openWithCallback(self._onTubePicked, ChoiceBox, list=choices, windowTitle=_("Pick a Source"), title="Available Sources")

	def _onTubePicked(self, data):
		if data:
			provider = self.PROVIDER[data[1]]
			self._run(provider)
