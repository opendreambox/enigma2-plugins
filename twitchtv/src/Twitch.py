from Tools.Log import Log

from twisted.web.client import getPage

import json
import urllib

# Infos zu Channel: https://api.twitch.tv/kraken/channels/bierbankb?client_id=jk9zwvlr4npb3ujr0dshx1k33zxksa

# Letzte Streams von Channel: https://api.twitch.tv/kraken/channels/bierbankb/videos?client_id=jk9zwvlr4npb3ujr0dshx1k33zxksa&broadcast_type=archive
# Highlights von Channel: https://api.twitch.tv/kraken/channels/bierbankb/videos?client_id=jk9zwvlr4npb3ujr0dshx1k33zxksa&broadcast_type=highlight
# Uploads von Channel: https://api.twitch.tv/kraken/channels/bierbankb/videos?client_id=jk9zwvlr4npb3ujr0dshx1k33zxksa&broadcast_type=upload
# Begrenzen mit "limit" (Max: 100), Starten bei "offset"

# Infos zu Video : https://api.twitch.tv/api/videos/<id>?client_id=jk9zwvlr4npb3ujr0dshx1k33zxksa

class TwitchDataObject(object):
	def __init__(self, data):
		self.data = data
		self.preview = None

class TwitchGameData(TwitchDataObject):
	def __init__(self, data):
		TwitchDataObject.__init__(self, data)
		self.name = data["game"]["name"].encode('utf-8')
		self.channels = data["channels"]
		self.viewers = data["viewers"]
		self.popularity = data["game"].get("popularity", 0)
		self.boxArtLarge = data["game"]["box"].get("large", "").encode("utf-8")
		self.boxArtMedium = data["game"]["box"].get("medium", "").encode("utf-8")
		self.boxArtSmall = data["game"]["box"].get("small", "").encode("utf-8")
		self.preview = self.boxArtLarge

class TwitchChannel(TwitchDataObject):
	def __init__(self, channel):
		TwitchDataObject.__init__(self, channel)
		self.name = channel["name"].encode('utf-8')
		self.display_name = channel.get("display_name", channel["name"]).encode('utf-8')
		self.game = channel["game"].encode('utf-8') if channel.get("game", None) else ""
		self.banner = channel["profile_banner"].encode('utf-8') if channel.get("profile_banner", None) else ""
		self.status = channel["status"].encode('utf-8') if channel.get("status", None) else ""
		self.followers = channel["followers"] if channel.get("followers", None) else ""

	def __str__(self):
		return "~TwitchChannel-%s-%s-%s-%s-%s" %(self.name, self.display_name, self.status, self.followers, self.banner)

class TwitchVideoBase(TwitchDataObject):
	def __init__(self, data, type_key):
		TwitchDataObject.__init__(self, data)
		self.type = data[type_key].encode('utf-8')
		self.created = data["created_at"].encode('utf-8')
		self.channel = TwitchChannel(data["channel"])

class TwitchStream(TwitchVideoBase):
	TYPE_LIVE = "live"

	def __init__(self, stream):
		TwitchVideoBase.__init__(self, stream, "stream_type")
		self.viewers = stream["viewers"]
		self.preview_small = stream["preview"]["small"].encode('utf-8')
		self.preview_medium = stream["preview"]["medium"].encode('utf-8')
		self.preview_large = stream["preview"]["large"].encode('utf-8')
		self.preview = self.preview_medium

	def __str__(self):
		return "~TwitchStream-%s-%s-%s-(%s | %s | %s)" %(self.type, self.viewers, self.channel, self.preview_small, self.preview_medium, self.preview_large)

class TwitchVOD(TwitchVideoBase):
	def __init__(self, vod):
		TwitchVideoBase.__init__(self, vod, "broadcast_type")
		self.id = vod["_id"][1:].encode("utf-8")
		self.title = vod["title"].encode("utf-8")
		self.views = vod["views"]
		self.game = vod["game"].encode("utf-8") if vod.get("game", None) else ""
		self.preview = vod["preview"].encode("utf-8")
		self.title = vod["title"].encode('utf-8')

class Twitch(object):
	USERAGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
	TEMPFILE = "/tmp/twitch_channellogo"

	def __init__(self):
		pass

	def livestreams(self, client_id, callback, game=None):
		url = "https://api.twitch.tv/kraken/streams?limit=100&client_id=%s" %(client_id,)
		if game:
			url = "%s&game=%s" %(url, urllib.quote(game))
		getPage(url, method="GET", agent=Twitch.USERAGENT).addCallbacks(self._onLivestreams, self._onErrorLivestreams, callbackArgs=[callback], errbackArgs=[callback])

	def _onLivestreams(self, html, callback):
		Log.i("Got all livestreams!")
		livestreams_json = json.loads(html)
		items = []
		for stream in livestreams_json["streams"]:
			stream = TwitchStream(stream)
			items.append(stream)
		#items.append((_("Load next 100 livestreams"), 0))
		callback(items)

	def _onErrorLivestreams(self, error, callback):
		Log.w("Couldnt get all livestreams! Error: %s" %(error,))
		callback([])

	def followedChannels(self, username, client_id, callback):
		getPage("https://api.twitch.tv/kraken/users/%s/follows/channels?client_id=%s" %(urllib.quote(username),client_id)).addCallbacks(self._onFollowedChannels, self._onErrorFollowedChannels, callbackArgs=[callback], errbackArgs=[callback] )

	def _onFollowedChannels(self, html, callback):
		data = json.loads(html)
		channels = []
		for item in data.get("follows", []):
			channels.append(TwitchChannel(item["channel"]))
		callback(channels)

	def _onErrorFollowedChannels(self, error, callback):
		Log.w(error)
		callback(None)

	def searchChannel(self, needle, client_id, callback):
		getPage("https://api.twitch.tv/kraken/search/channels?client_id=%s&query=%s" %(client_id, urllib.quote(needle))).addCallbacks(self._onSearchChannel, self._onErrorSearchChannel, callbackArgs=[callback], errbackArgs=[callback])

	def _onSearchChannel(self, html, callback):
		data = json.loads(html)
		channels = []
		for channel in data.get("channels", []):
			channels.append(TwitchChannel(channel))
		callback(channels)

	def _onErrorSearchChannel(self, error, callback):
		Log.w(error)
		callback(None)

	def channelDetails(self, channel_id, client_id, callback):
		getPage("https://api.twitch.tv/kraken/channels/" + channel_id + "?client_id=" + client_id, method="GET", agent=Twitch.USERAGENT).addCallbacks(self._onChannelDetails, self._onErrorChannelDetails, callbackArgs=[callback], errbackArgs=[callback])

	def _onChannelDetails(self, html, callback):
		Log.i("Received Channel Details!")
		data = json.loads(html)
		channel = None
		try:
			channel = TwitchChannel(data)
		except:
			pass
		callback(channel)

	def _onErrorChannelDetails(self, error, callback):
		Log.w("Error while getting channel details: %s" %(error,))
		callback(None)

	def liveStreamDetails(self, channel_id, client_id, callback):
		getPage("https://api.twitch.tv/kraken/streams/%s?client_id=%s" %(channel_id, client_id), method="GET", agent=Twitch.USERAGENT).addCallbacks(self._onLiveStreamDetails, self._onErrorLiveStreamDetails, callbackArgs=[callback], errbackArgs=[callback])

	def _onLiveStreamDetails(self, html, callback):
		details_json = json.loads(html)
		stream = None
		if details_json["stream"]:
			stream = TwitchStream(details_json["stream"])
		callback(stream)

	def _onErrorLiveStreamDetails(self, error, callback):
		Log.w("Error while getting live stream details: %s" %(error))
		callback(None)

	def videosForChannel(self, channel_id, client_id, broadcast_type, callback):
		url = "https://api.twitch.tv/kraken/channels/%s/videos?limit=100&broadcast_type=%s&client_id=%s" %(channel_id, broadcast_type, client_id)
		getPage(url, method="GET", agent=Twitch.USERAGENT).addCallbacks(self._onVideosForChannel, self._onErrorVideosForChannel, callbackArgs=[callback], errbackArgs=[callback])

	def _onVideosForChannel(self, html, callback):
		vod_json = json.loads(html)
		total_vods = vod_json["_total"]
		videos = vod_json["videos"]
		items = []
		for video in videos:
			if video:
				vod = TwitchVOD(video)
				items.append(vod)
		callback(total_vods, items)

	def _onErrorVideosForChannel(self, error, callback):
		Log.w("Error while getting videos from channel: %s" %(error,))
		callback(-1, [])

	def topGames(self, client_id, callback, limit=100, offset=0):
		url = "https://api.twitch.tv/kraken/games/top?client_id=%s&limit=%s&offset=%s" %(client_id,limit,offset)
		getPage(url, method="GET", agent=Twitch.USERAGENT).addCallbacks(self._onTopGames, self._onErrorTopGames, callbackArgs=[callback], errbackArgs=[callback])

	def _onTopGames(self, html, callback):
		data = json.loads(html)
		games = []
		for game in data["top"]:
			games.append(TwitchGameData(game))
		callback(games)

	def _onErrorTopGames(self, error, callback):
		Log.w(error)
		callback(None)
