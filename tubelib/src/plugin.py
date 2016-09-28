try:
	from enigma import eUriResolver
	from youtube.YoutubeUriResolver import YoutubeUriResolver
	YoutubeUriResolver.instance = YoutubeUriResolver()
	eUriResolver.addResolver(YoutubeUriResolver.instance)
except ImportError:
	pass
