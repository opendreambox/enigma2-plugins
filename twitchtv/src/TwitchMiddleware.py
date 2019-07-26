from enigma import eServiceReference
from Screens.MoviePlayer import MoviePlayer

from Twitch import Twitch, TwitchChannel

import os.path
import json
from Tools.Log import Log
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_CONFIG


class TwitchMiddleware(object):
	instance = None

	def __init__(self):
		assert(not TwitchMiddleware.instance)
		TwitchMiddleware.instance = self

		self.twitch = Twitch()
		self.favorites = []
		self.favorites_path = resolveFilename(SCOPE_CONFIG, "twitch_favorites.json")
		Log.w(self.favorites_path)
		self.loadFavorites()

	def loadFavorites(self):
		try:
			if os.path.isfile(self.favorites_path) is False:
				self.favorites = []
				return
			with open(self.favorites_path, "rb") as f:
				channels = json.load(f)
				for c in channels:
					self.favorites.append(TwitchChannel(c))
		except Exception as e:
			Log.w(e)

	def saveFavorites(self):
		try:
			channels = []
			for f in self.favorites:
				channels.append(f.data)
			with open(self.favorites_path, "wb") as f:
				json.dump(channels, f)
			return True
		except Exception as e:
			Log.w(e)
		return False

	def addToFavorites(self, channel):
		self.favorites.append(channel)
		return self.saveFavorites()

	def removeFromFavorites(self, channel):
		for f in self.favorites:
			if f.name == channel.name:
				self.favorites.remove(f)
				break
		return self.saveFavorites()

	def watchLivestream(self, session, channel, infoCallback=None):
		Log.i(channel)
		boundCallback = boundFunction(self._onLiveStreamDetails, session, channel, infoCallback)
		self.twitch.liveStreamDetails(channel.id, boundCallback)

	def _onLiveStreamDetails(self, session, channel, infoCallback, stream):
		if not stream:
			session.toastManager.showToast(_("%s is offline") %(channel.display_name), 3)
		else:
			ref = eServiceReference(eServiceReference.idURI, 0, "twitch://" + stream.channel.display_name)
			ref.setName("%s - %s" % (stream.channel.display_name, stream.channel.status))
			session.toastManager.showToast(_("%s is live, please wait...") %(stream.channel.display_name,), 3)
			session.open(MoviePlayer, ref, infoCallback=infoCallback, streamMode=True)

	def watchVOD(self, session, vod, infoCallback=None):
		ref = eServiceReference(eServiceReference.idURI, 0, "twitch://video/%s" % (vod.id,))
		ref.setName("%s - %s" % (vod.channel.display_name, vod.title))
		session.open(MoviePlayer, ref, infoCallback=infoCallback, streamMode=True)

TwitchMiddleware()
