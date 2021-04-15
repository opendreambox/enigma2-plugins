#enigma2
from Components.config import config
#twisted
from twisted.internet import reactor, threads
#youtube
from youtube_dl import YoutubeDL
#local
from YoutubeQueryBase import YoutubeQueryBase

from Tools.Log import Log

import datetime
import re
from Tools.HardwareInfo import HardwareInfo


class Videos(YoutubeQueryBase):
	MOST_POPULAR = "mostPopular"

	def list(self, callback, maxResults=25, chart=None, videoCategoryId=None, ids=[]):
		if not chart:
			chart = self.MOST_POPULAR

		self._args = {
			"part": "id,snippet,statistics,contentDetails",
			"maxResults": maxResults,
			"hl": config.osd.language.value.split("_")[0]
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
		data = {k: int(v) for k, v in data.groupdict().items() if v}
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

	def _onUrlReady(self, url, fmt, suburi=None, *args):
		Log.d(url)
		if url:
			self._url = url
			self._format = fmt
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


from sys import _getframe
from Tools.LogConfig import LOG_TYPE_INFO, LOG_TYPE_WARNING, LOG_TYPE_ERROR


class YTDLLogger(object):
	def debug(self, msg):
		self._log(LOG_TYPE_INFO, msg)

	def warning(self, msg):
		self._log(LOG_TYPE_WARNING, msg)

	def error(self, msg):
		self._log(LOG_TYPE_ERROR, msg)

	def _log(self, logType, msg):
		callframe = None
		try:
			callframe = _getframe(3)
		except:
			pass
		Log._log(logType, msg, callframe)


class VideoUrlRequest(object):
	VIDEO_FMT_PRIORITY_MAP_UHD = [
		'315+172', #DASH-webm 2160p60
		'315+171', #DASH-webm 2160p60
		'313+172', #DASH-webm 2160p
		'313+171', #DASH-webm 2160p
	]
	VIDEO_FMT_PRIORITY_MAP_WQHD = [
		'308+172', #DASH-webm 1440p60
		'308+171', #DASH-webm 1440p60
		'271+172', #DASH-webm 1440p
		'271+171', #DASH-webm 1440p
	]
	VIDEO_FMT_PRIORITY_MAP_FHD_WEBM = [
		'170+172',#DASH-webm 1080p
		'170+171', #DASH-webm 1080p
		'248+172', #DASH-webm 1080p
		'248+171', #DASH-webm 1080p
	]
	VIDEO_FMT_PRIORITY_MAP_FHD = [
		'96', #HLS 1080p
		'37', #MP4 1080p
		'46', #MP4 1080p
		'137+171', #DASH-mp4 1080p
		'137+172', #DASH-mp4 1080p
	]
	VIDEO_FMT_PRIORITY_MAP_HD = [
		'95', #HLS 720p
		'22', #MP4 720p
		]
	VIDEO_FMT_PRIORITY_MAP = [
		'94', #HLS 480p
		'59', #MP4 480p
		'78', #MP4 480p
		'35', #FLV 480p
		'93', #HLS 360p
		'18', #MP4 360p
		'34', #FLV 360p
		'92', #HLS 240p
		'91', #HLS 144p
	]
	KEY_FORMAT_ID = u"format_id"
	KEY_URL = u"url"
	KEY_ENTRIES = u"entries"
	KEY_FORMATS = u"formats"
	KEY_REQUESTED_FORMATS = u"requested_formats"
	KEY_VCODEC = u"vcodec"
	KEY_ACODEC = u"acodec"

	@staticmethod
	def isHls(fmt):
		return False

	def __init__(self, baseurl, callbacks=[], async=True):
		self._canceled = False
		self._callbacks = callbacks
		self._baseurl = baseurl
		self._async = async
		self._params = {
			"youtube_include_dash_manifest": False,
			"nocheckcertificate": True,
			"noplaylist": False,
			"playlist_items": 1,
			"logger": YTDLLogger(),
		}
		self._setupFormatMap()
		if self._async:
			threads.deferToThread(self._request)
		else:
			self._request()

	def _setupFormatMap(self):
		fmt = self.VIDEO_FMT_PRIORITY_MAP
		modernCodecs = HardwareInfo().device_name in ["dm900", "dm920"]
		try:
			maxres = int(config.usage.max_stream_resolution.value)
		except:
			maxres = 1080
		# Low to high, so high is first
		if maxres >= 720:
			fmt = self.VIDEO_FMT_PRIORITY_MAP_HD + fmt
		if maxres >= 1080:
			if modernCodecs:
				fmt = self.VIDEO_FMT_PRIORITY_MAP_FHD_WEBM + fmt
			fmt = self.VIDEO_FMT_PRIORITY_MAP_FHD + fmt
		if modernCodecs:
			if maxres >= 1440:
				fmt = self.VIDEO_FMT_PRIORITY_MAP_WQHD + fmt
			if maxres >= 2160:
				fmt = self.VIDEO_FMT_PRIORITY_MAP_UHD + fmt
		self._params["format"] = "/".join(fmt)

	def _request(self):
		ie_key = "YoutubeLive" if "live" in self._baseurl.lower() else "Youtube"
		try:
			self._setupFormatMap()
			with YoutubeDL(self._params) as ytdl:
				result = ytdl.extract_info(self._baseurl, ie_key=ie_key, download=False, process=True)
				if self.KEY_ENTRIES in result: # Can be a playlist or a list of videos
					entry = result[self.KEY_ENTRIES][0] #TODO handle properly
				else:# Just a video
					entry = result
				fmt = entry.get(self.KEY_FORMAT_ID)
				url = ""
				suburi = ""
				for f in entry.get(self.KEY_REQUESTED_FORMATS, []):
					if not url and f.get(self.KEY_VCODEC, u"none") != u"none":
						url = str(f.get(self.KEY_URL, ""))
					elif not suburi and f.get(self.KEY_ACODEC, u"none") != u"none":
						suburi = str(f.get(self.KEY_URL, ""))
				if not url:
					url = str(entry.get(self.KEY_URL, ""))
				self._onResult(True, url, fmt, suburi)
				return
		except Exception as e:
			Log.w(e)
		self._onResult(False, None, -1)

	def _onResult(self, success, url, fmt, suburi=""):
		if self._canceled:
			return
		for callback in self._callbacks:
			if self._async:
				reactor.callFromThread(callback, url, fmt, suburi)
			else:
				callback(url, fmt, suburi)

	def cancel(self):
		self._canceled = True
