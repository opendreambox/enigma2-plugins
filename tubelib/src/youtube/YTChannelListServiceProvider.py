from enigma import eServiceReference
from Screens.InputBox import InputBox
from Tools.Log import Log

from Plugins.SystemPlugins.TubeLib.ChannelListTubeServiceHelper import ChannelListServiceProviderBase, ChannelListTubeServiceHelper

class YTChannelListServiceProvider(ChannelListServiceProviderBase):
	TYPE = "youtube"
	DESCRIPTION = _("Youtube Live Channel")

	def _createServiceForChannelList(self):
		self._addYoutubeService()

	def _addYoutubeService(self):
		self._session.openWithCallback(self._onYoutubeChannel, InputBox, title=_("Please provide a YouTube Channel-/Username"), windowTitle=_("Youtube Channel/User"))

	def _onYoutubeChannel(self, data):
		if data:
			self._tubeUri = "yt://live/%s" % (data,)
			self._session.openWithCallback(self._onLocalChannelName, InputBox, title=_("Please provide a channel name for your local channel list"), windowTitle=_("Local channel name"))
		else:
			self._finish(None)

	def _onLocalChannelName(self, name):
		Log.w("uri=%s, name=%s" % (self._tubeUri, name))
		if name and self._tubeUri:
			ref = eServiceReference(eServiceReference.idURI, eServiceReference.isLive, self._tubeUri)
			ref.setName(name)
			self._finish(ref)
		else:
			self._finish(None)

ChannelListTubeServiceHelper.addProvider(YTChannelListServiceProvider.TYPE, YTChannelListServiceProvider)
