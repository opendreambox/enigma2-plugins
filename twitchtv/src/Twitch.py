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
		self.id = channel["_id"]
		self.name = channel["name"].encode('utf-8')
		self.display_name = channel.get("display_name", channel["name"]).encode('utf-8')
		self.game = channel["game"].encode('utf-8') if channel.get("game", None) else ""
		self.banner = channel["profile_banner"].encode('utf-8') if channel.get("profile_banner", None) else ""
		self.status = channel["status"].encode('utf-8') if channel.get("status", None) else ""
		self.followers = channel["followers"] if channel.get("followers", None) else ""

	def __str__(self):
		return "~TwitchChannel-%s-%s-%s-%s-%s" % (self.name, self.display_name, self.status, self.followers, self.banner)

class TwitchVideoBase(TwitchDataObject):
	def __init__(self, data, type_key):
		TwitchDataObject.__init__(self, data)
		self.type = data[type_key].encode('utf-8')
		self.created = data["created_at"].encode('utf-8')
		self.channel = TwitchChannel(data["channel"])
		self.preview_small = data["preview"]["small"].encode('utf-8')
		self.preview_medium = data["preview"]["medium"].encode('utf-8')
		self.preview_large = data["preview"]["large"].encode('utf-8')
		self.preview = self.preview_medium

class TwitchStream(TwitchVideoBase):
	TYPE_LIVE = "live"

	def __init__(self, stream):
		TwitchVideoBase.__init__(self, stream, "stream_type")
		self.viewers = stream["viewers"]

	def __str__(self):
		return "~TwitchStream-%s-%s-%s-(%s | %s | %s)" % (self.type, self.viewers, self.channel, self.preview_small, self.preview_medium, self.preview_large)

class TwitchVOD(TwitchVideoBase):
	def __init__(self, vod):
		TwitchVideoBase.__init__(self, vod, "broadcast_type")
		self.id = vod["_id"][1:].encode("utf-8")
		self.title = vod["title"].encode("utf-8")
		self.views = vod["views"]
		self.game = vod["game"].encode("utf-8") if vod.get("game", None) else ""
		self.title = vod["title"].encode('utf-8')

class Twitch(object):
	USERAGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
	TEMPFILE = "/tmp/twitch_channellogo"

	def __init__(self, client_id="1kke40cmxc5s65xuw82vgphjhos0ds"):
		self._client_id = client_id

	def _get(self, url, args=[], method="GET",):
		headers = {
			"Client-ID": self._client_id,
			"Accept": "application/vnd.twitchtv.v5+json",
		}
		if args:
			url = "%s%s" % (url, urllib.urlencode(args))
		Log.w(url)
		return getPage(url, method=method, agent=Twitch.USERAGENT, headers=headers)

	def livestreams(self, callback, game=None):
		url = "https://api.twitch.tv/kraken/streams/featured?"
		args = [("limit", 100)]
		if game:
			url = "https://api.twitch.tv/kraken/streams?"
			args.append(("game", game))
		self._get(url, args).addCallbacks(self._onLivestreams, self._onErrorLivestreams, callbackArgs=[callback], errbackArgs=[callback])

	def _onLivestreams(self, html, callback):
		Log.i("Got all livestreams!")
		livestreams = json.loads(html)
		items = []
		streams = livestreams.get("streams", livestreams.get("featured", []))
		for stream in streams:
			if stream.has_key("stream"):
				stream = stream["stream"]
			stream = TwitchStream(stream)
			items.append(stream)
		callback(items)

	def _onErrorLivestreams(self, error, callback):
		Log.w("Couldnt get all livestreams! Error: %s" % (error,))
		callback([])

	def followedChannels(self, username, callback):
		Log.w(username)
		self._get("https://api.twitch.tv/kraken/users?", args=[("login", str(username))]).addCallbacks(self._onFollowedChannelsUserID, self._onErrorFollowedChannels, callbackArgs=[callback], errbackArgs=[callback])

	def _onFollowedChannelsUserID(self, html, callback):
		try:
			data = json.loads(html)
			userid = urllib.quote(str(data["users"] and data["users"][0]["_id"]))
			if userid:
				self._get("https://api.twitch.tv/kraken/users/%s/follows/channels" % (userid)).addCallbacks(self._onFollowedChannels, self._onErrorFollowedChannels, callbackArgs=[callback], errbackArgs=[callback])
				return
		except:
			pass
		self._onErrorFollowedChannels("ERROR GETTING USERID!", callback)

	def _onFollowedChannels(self, html, callback):
		data = json.loads(html)
		channels = []
		for item in data.get("follows", []):
			channels.append(TwitchChannel(item["channel"]))
		callback(channels)

	def _onErrorFollowedChannels(self, error, callback):
		Log.w(error)
		callback(None)

	def searchChannel(self, needle, callback):
		self._get("https://api.twitch.tv/kraken/search/channels?", args=[("query", needle)]).addCallbacks(self._onSearchChannel, self._onErrorSearchChannel, callbackArgs=[callback], errbackArgs=[callback])

	def _onSearchChannel(self, html, callback):
		data = json.loads(html)
		channels = []
		for channel in data.get("channels", []):
			channels.append(TwitchChannel(channel))
		callback(channels)

	def _onErrorSearchChannel(self, error, callback):
		Log.w(error)
		callback(None)

	def channelDetails(self, channel_id, callback):
		self._get("https://api.twitch.tv/kraken/channels/%s" % (channel_id,)).addCallbacks(self._onChannelDetails, self._onErrorChannelDetails, callbackArgs=[callback], errbackArgs=[callback])

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
		Log.w("Error while getting channel details: %s" % (error,))
		callback(None)

	def liveStreamDetails(self, channel_id, callback):
		self._get("https://api.twitch.tv/kraken/streams/%s" % (str(channel_id),)).addCallbacks(self._onLiveStreamDetails, self._onErrorLiveStreamDetails, callbackArgs=[callback], errbackArgs=[callback])
		#self._get("https://api.twitch.tv/kraken/streams/?", args=[("channel", channel_id)]).addCallbacks(self._onLiveStreamDetails, self._onErrorLiveStreamDetails, callbackArgs=[callback], errbackArgs=[callback])

	def _onLiveStreamDetails(self, html, callback):
		details_json = json.loads(html)
		Log.w(details_json)
		stream = None
		if details_json["stream"]:
			stream = TwitchStream(details_json["stream"])
		callback(stream)

	def _onErrorLiveStreamDetails(self, error, callback):
		Log.w("Error while getting live stream details: %s" % (error))
		callback(None)

	def videosForChannel(self, channel_id, broadcast_type, callback):
		url = "https://api.twitch.tv/kraken/channels/%s/videos?" % (channel_id,)
		self._get(url, args=[("limit", 100), ("broadcast_type", broadcast_type)]).addCallbacks(self._onVideosForChannel, self._onErrorVideosForChannel, callbackArgs=[callback], errbackArgs=[callback])

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
		Log.w("Error while getting videos from channel: %s" % (error,))
		callback(-1, [])

	def topGames(self, callback, limit=100, offset=0):
		url = "https://api.twitch.tv/kraken/games/top?"
		self._get(url, args=[("limit", limit), ("offset", offset)]).addCallbacks(self._onTopGames, self._onErrorTopGames, callbackArgs=[callback], errbackArgs=[callback])

	def _onTopGames(self, html, callback):
		data = json.loads(html)
		games = []
		for game in data["top"]:
			games.append(TwitchGameData(game))
		callback(games)

	def _onErrorTopGames(self, error, callback):
		Log.w(error)
		callback(None)
