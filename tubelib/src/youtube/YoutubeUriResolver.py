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
			watch_url = None
			try:
				uri = uri.split("://")[1]
				uri = uri.split("/")
				if uri[0] == "live":
					watch_url = "https://www.youtube.com/user/%s/live" % (uri[1],)
				else:
					video_id = uri[0]
					watch_url = "https://www.youtube.com/watch?v=%s" % (video_id,)
			except:
				pass
			def onUrlReady(uri, format, suburi=""):
				Log.d("%s # %s (%s)" % (uri, suburi, format))
				try:
					if not service.ptrValid():
						Log.w("Service became invalid!")
						return
					if uri:
						try:
							service.setResolvedUri(uri, eServiceReference.idGST, suburi or "")
						except:
							service.setResolvedUri(uri, eServiceReference.idGST)
					else:
						service.failedToResolveUri()
				except:
					service.failedToResolveUri()
			Log.i(watch_url)
			if watch_url:
				VideoUrlRequest(watch_url, [onUrlReady], async=True)
			else:
				service.failedToResolveUri()
			return True
except ImportError:
	pass
