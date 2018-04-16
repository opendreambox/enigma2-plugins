from Plugins.Extensions.WebInterface.WebScreens import WebScreen

class StreamServerSeekWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		
		from WebComponents.Sources.StreamServerSeek import StreamServerSeek
		self["SeekTo"] = StreamServerSeek(session, StreamServerSeek.SEEK_TO)
		self["SeekRelative"] = StreamServerSeek(session, StreamServerSeek.SEEK_RELATIVE)
		self["SeekChapter"] = StreamServerSeek(session, StreamServerSeek.SEEK_CHAPTER)
		self["GetLength"] = StreamServerSeek(session, StreamServerSeek.GET_LENGTH)
		self["GetPlayPosition"] = StreamServerSeek(session, StreamServerSeek.GET_PLAY_POSITION)
		self["Pause"] = StreamServerSeek(session, StreamServerSeek.PAUSE)
		self["Unpause"] = StreamServerSeek(session, StreamServerSeek.UNPAUSE)
		self["FastForward"] = StreamServerSeek(session, StreamServerSeek.FAST_FORWARD)
		self["FastBackward"] = StreamServerSeek(session, StreamServerSeek.FAST_BACKWARD)
		self["SlowMotion"] = StreamServerSeek(session, StreamServerSeek.SLOW_MOTION)
		self["Play"] = StreamServerSeek(session, StreamServerSeek.PLAY)
