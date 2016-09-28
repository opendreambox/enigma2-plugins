try:
	from enigma import eServiceReference, eUriResolver, StringList
	from Videos import VideoUrlRequest

	from Tools.Log import Log

	class YoutubeUriResolver(eUriResolver):
		_schemas = ("youtube", "yt")
		instance = None
		def __init__(self):
			eUriResolver.__init__(self, StringList(self._schemas))
			Log.i(self._schemas)

		def resolve(self, service, uri):
			Log.i(uri)
			video_id = uri.split("://")[1]
			watch_url = "http://youtube.com/watch?v=%s" % (video_id,)
			def onUrlReady(uri, format):
				Log.d("%s (%s)" %(uri, format))
				try:
					if not service.ptrValid():
						Log.w("Service became invalid!")
						return
					if uri:
						if VideoUrlRequest.isHls(format):
							service.setResolvedUri(uri, eServiceReference.idDVB)
						else:
							service.setResolvedUri(uri, eServiceReference.idGST)
					else:
						service.failedToResolveUri()
				except:
					service.failedToResolveUri()

			VideoUrlRequest(watch_url, [onUrlReady], async=True)
			return True
except ImportError:
	pass
