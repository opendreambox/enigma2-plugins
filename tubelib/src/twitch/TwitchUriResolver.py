try:
	from enigma import eServiceReference, eUriResolver, StringList
	from Videos import TwitchVideoUrlResolver

	from Tools.Log import Log

	class TwitchUriResolver(eUriResolver):
		_schemas = ("twitch", "tw")
		instance = None
		def __init__(self):
			eUriResolver.__init__(self, StringList(self._schemas))
			Log.i(self._schemas)

		def resolve(self, service, uri):
			Log.i(uri)
			watch_url = None
			try:
				uri = uri.split("://")[1]
				watch_url = "http://twitch.tv/%s" %(uri,)
			except:
				pass
			def onUrlReady(uri, fmt):
				Log.w("%s (%s)" %(uri, fmt))
				try:
					if not service.ptrValid():
						Log.w("Service became invalid!")
						return
					if uri:
						service.setResolvedUri(uri, eServiceReference.idDVB)
					else:
						service.failedToResolveUri()
				except:
					service.failedToResolveUri()
			Log.i(watch_url)
			if watch_url:
				TwitchVideoUrlResolver(watch_url, [onUrlReady], async=True)
			else:
				service.failedToResolveUri()
			return True
except ImportError:
	pass
