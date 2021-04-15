from enigma import eServiceReference
from Screens.InputBox import InputBox
from Tools.Log import Log

from Plugins.SystemPlugins.TubeLib.ChannelListTubeServiceHelper import ChannelListServiceProviderBase, ChannelListTubeServiceHelper


class TwitchChannelListServiceProvider(ChannelListServiceProviderBase):
	TYPE = "twitch"
	DESCRIPTION = _("twitch.tv Live Channel")

	def _createServiceForChannelList(self):
		self._addTwitchService()

	def _addTwitchService(self):
		self._session.openWithCallback(self._onTwitchChannel, InputBox, title=_("Please provide a Twitch Channel-/Username"), windowTitle=_("Twitch Channel/User"))

	def _onTwitchChannel(self, data):
		if data:
			self._tubeUri = "tw://%s" % (data,)
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


ChannelListTubeServiceHelper.addProvider(TwitchChannelListServiceProvider.TYPE, TwitchChannelListServiceProvider)
