#enigma2
from Components.config import config
#twisted
from twisted.internet import reactor, threads
#youtube
from apiclient.discovery import build
from youtube_dl import YoutubeDL
#local
from ThreadedRequest import ThreadedRequest
from YoutubeQueryBase import YoutubeQueryBase

from Tools.Log import Log

import datetime, re

class Videos(YoutubeQueryBase):
	MOST_POPULAR = "mostPopular"

	def list(self, callback, maxResults=25, chart=None, videoCategoryId=None, ids=[]):
		if not chart:
			chart = self.MOST_POPULAR

		self._args = {
			"part" : "id,snippet,statistics,contentDetails",
			"maxResults" : maxResults,
			"hl" : config.plugins.mytube.search.lr.value
		}
		if videoCategoryId:
			self._args["videoCategoryId"] = videoCategoryId
		if chart:
			self._args["chart"] = chart
		if ids:
			self._args["id"] = ",".join(ids)
		Log.i(self._args)
		return self._doQuery(callback)

	def _doQuery(self, callback):
		request = self._youtube.videos().list(**self._args)
		return self._query(callback, request)

	def _onResult(self, success, data):
		videos = []
		if success:
			for item in data['items']:
				v = Video(item)
				if v.isValid():
					videos.append(v)
				else:
					Log.w("Skipped video '%s (%s)'" % (v.title, v.id))
		if self._callback:
			self._callback(success, videos, data)

	from twisted.internet import threads, reactor

class Video(object):
	def __init__(self, entry):
		self._entry = entry
		self._url = None
		self._format = 0
		self._urlRequest = None
		#self.getUrl()

	def isValid(self):
		#two checks for videos that have e.g. gone private
		return self._entry.has_key("contentDetails") and self._entry["snippet"].has_key("thumbnails")

	def isPlaylistEntry(self):
		return False

	def getId(self):
		return str(self._entry["id"])
	id = property(getId)

	def getTitle(self):
		return str(self._entry["snippet"]["title"])
	title = property(getTitle)

	def getDescription(self):
		return str(self._entry["snippet"]["description"])
	description = property(getDescription)

	def getThumbnailUrl(self, best=False):
		prios = ["maxres", "standard", "high", "medium", "default"]
		if not best:
			prios.reverse()
		for prio in prios:
			if self._entry["snippet"]["thumbnails"].has_key(prio):
				return str(self._entry["snippet"]["thumbnails"][prio]["url"])
			else:
				Log.w(self.id)
		return None
	thumbnailUrl = property(getThumbnailUrl)

	def getPublishedDate(self):
		return str(self._entry["snippet"]["publishedAt"])
	publishedDate = property(getPublishedDate)

	def getViews(self):
		return str(self._entry["statistics"]["viewCount"])
	views = property(getViews)

	def _parse_duration(self, duration):
		# isodate replacement
		if 'P' in duration:
			dt, duration = duration.split('P')

		duration_regex = re.compile(
			r'^((?P<years>\d+)Y)?'
			r'((?P<months>\d+)M)?'
			r'((?P<weeks>\d+)W)?'
			r'((?P<days>\d+)D)?'
			r'(T'
			r'((?P<hours>\d+)H)?'
			r'((?P<minutes>\d+)M)?'
			r'((?P<seconds>\d+)S)?'
			r')?$'
		)

		data = duration_regex.match(duration)
		if not data or duration[-1] == 'T':
			raise ValueError("'P%s' does not match ISO8601 format" % duration)
		data = {k:int(v) for k, v in data.groupdict().items() if v}
		if 'years' in data or 'months' in data:
			raise ValueError('Year and month values are not supported in python timedelta')

		return datetime.timedelta(**data)

	def getDuration(self):
		try:
			return self._parse_duration(str(self._entry["contentDetails"]["duration"])).total_seconds()
		except KeyError, e:
			Log.w(e)
			return 0
		except ValueError, e:
			Log.w(e)
			return 0
	duration = property(getDuration)

	def getLikes(self):
		if "likeCount" in self._entry["statistics"]:
			return str(self._entry["statistics"]["likeCount"])
		return "-"
	likes = property(getLikes)

	def getDislikes(self):
		if "dislikeCount" in self._entry["statistics"]:
			return str(self._entry["statistics"]["dislikeCount"])
		return "-"
	dislikes = property(getDislikes)

	def getChannelTitle(self):
		return str(self._entry["snippet"]["channelTitle"])
	channelTitle = property(getChannelTitle)

	def getChannelId(self):
		return str(self._entry["snippet"]["channelId"])
	channelId = property(getChannelId)

	def getChannelTitle(self):
		return str(self._entry["snippet"]["channelTitle"])
	channelTitle = property(getChannelTitle)

	def _onUrlReady(self, url, format, *args):
		Log.d(url)
		if url:
			self._url = url
			self._format = format
		else:
			self._url = "broken..."

	def getUrl(self, callback=None):
		if not self._url:
			watch_url = 'http://www.youtube.com/watch?v=%s' % self.id
			callbacks = [self._onUrlReady]
			if callback:
				callbacks.append(callback)
			isAsync = callback != None
			self._urlRequest = VideoUrlRequest(watch_url, callbacks, async=isAsync)
			return self._url
		else:
			if callback:
				callback(self._url)
			return self._url
	url = property(getUrl)

class VideoUrlRequest(object):
	VIDEO_FMT_PRIORITY_MAP = {
		1 : '96', #HLS 1080P
		2 : '95', #HLS 720p
		3 : '94', #HLS 480p
		4 : '93', #HLS 360p
		5 : '92', #HLS 240p
		6 : '91', #HLS 144p
		7 : '38', #MP4 Original (HD)
		8 : '37', #MP4 1080p (HD)
		9 : '22', #MP4 720p (HD)
		10 : '18', #MP4 360p
		11 : '35', #FLV 480p
		12 : '34', #FLV 360p
	}
	KEY_FORMAT_ID = u"format_id"
	KEY_URL = u"url"
	KEY_ENTRIES = u"entries"
	KEY_FORMATS = u"formats"

	@staticmethod
	def isHls(format):
		return format >= 91 and format <= 96

	def __init__(self, baseurl, callbacks=[], async=True):
		self._canceled = False
		self._callbacks = callbacks
		self._baseurl = baseurl
		self._async = async
		if self._async:
			threads.deferToThread(self._request)
		else:
			self._request()

	def _request(self):
		try:
			format_prio = "/".join(self.VIDEO_FMT_PRIORITY_MAP.itervalues())
			ytdl = YoutubeDL(params={"youtube_include_dash_manifest": False, "format" : format_prio, "nocheckcertificate" : True})
			result = ytdl.extract_info(self._baseurl, download=False)
			if self.KEY_ENTRIES in result: # Can be a playlist or a list of videos
				entry = result[self.KEY_ENTRIES][0] #TODO handle properly
			else:# Just a video
				entry = result
				url = str(entry.get(self.KEY_URL))
				format = int(entry.get(self.KEY_FORMAT_ID))
			self._onResult(True, url, format)
		except Exception as e:
			Log.w(e)
			self._onResult(False, None)

	def _onResult(self, success, url, format):
		if self._canceled:
			return
		for callback in self._callbacks:
			reactor.callFromThread(callback, url, format)

	def cancel(self):
		self._canceled = True
