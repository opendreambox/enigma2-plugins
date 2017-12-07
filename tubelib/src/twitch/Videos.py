from twisted.internet import threads
from youtube_dl.YoutubeDL import YoutubeDL
from Components.config import config
from Tools.Log import Log

class TwitchVideoUrlResolver(object):
	_ytdl = YoutubeDL(params={
			"nocheckcertificate" : True,
			"noplaylist" : False
		})

	KEY_FORMAT_ID = u"format_id"
	KEY_URL = u"url"
	KEY_HEIGHT = u"height"
	KEY_FORMATS = u"formats"

	def __init__(self, baseurl, callbacks=[], async=True):
		self._canceled = False
		self._callbacks = callbacks
		self._baseurl = baseurl
		self._async = async
		if self._async:
			threads.deferToThread(self._request)
		else:
			self._request()


	def _selectFormat(self, twitchInfo):
		try:
			maxres = int(config.usage.max_stream_resolution.value)
		except:
			maxres = 1080
		url = ""
		fmt = ""
		current = maxres;
		for twitchFmt in twitchInfo.get(self.KEY_FORMATS, []):
			height = twitchFmt.get(self.KEY_HEIGHT, 0)
			if height and height <= maxres and height > current:
				url = str(twitchFmt[self.KEY_URL])
				fmt = str(twitchFmt[self.KEY_FORMAT_ID])
				current = height
		if not url:
			url = str(twitchInfo[self.KEY_URL])
			fmt = str(twitchInfo[self.KEY_FORMAT_ID])
		Log.w("Selected resolution: %s" %(fmt,))
		return url, fmt

	def _request(self):
		ie_key = "TwitchStream"
		try:
			result = self._ytdl.extract_info(self._baseurl, ie_key=ie_key, download=False, process=True)
			url, fmt = self._selectFormat(result)
			self._onResult(True, url, fmt)
		except Exception as e:
			Log.w(e)
			self._onResult(False, None, -1)

	def _onResult(self, success, url, fmt):
		from twisted.internet import reactor
		if self._canceled:
			return
		for callback in self._callbacks:
			if self._async:
				reactor.callFromThread(callback, url, fmt)
			else:
				callback(url, fmt)

	def cancel(self):
		self._canceled = True
