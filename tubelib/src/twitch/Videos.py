from twisted.internet import threads
from youtube_dl.YoutubeDL import YoutubeDL
from Tools.Log import Log

class TwitchVideoUrlResolver(object):
	_ytdl = YoutubeDL(params={
			"nocheckcertificate" : True,
			"noplaylist" : False
		})

	KEY_FORMAT_ID = u"format_id"
	KEY_URL = u"url"

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
		ie_key = "TwitchStream"
		try:
			result = self._ytdl.extract_info(self._baseurl, ie_key=ie_key, download=False, process=True)
			url = str(result[self.KEY_URL])
			fmt = str(result[self.KEY_FORMAT_ID])
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
