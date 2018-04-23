from Plugins.Extensions.WebInterface.WebScreens import WebScreen

class StreamServerSeekWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		
		from WebComponents.Sources.StreamServerSeekSource import StreamServerSeekSource
		self["SeekTo"] = StreamServerSeekSource(session, StreamServerSeekSource.SEEK_TO)
		self["SeekRelative"] = StreamServerSeekSource(session, StreamServerSeekSource.SEEK_RELATIVE)
		self["SeekChapter"] = StreamServerSeekSource(session, StreamServerSeekSource.SEEK_CHAPTER)
		self["GetLength"] = StreamServerSeekSource(session, StreamServerSeekSource.GET_LENGTH)
		self["GetPlayPosition"] = StreamServerSeekSource(session, StreamServerSeekSource.GET_PLAY_POSITION)
		self["Pause"] = StreamServerSeekSource(session, StreamServerSeekSource.PAUSE)
		self["Unpause"] = StreamServerSeekSource(session, StreamServerSeekSource.UNPAUSE)
		self["FastForward"] = StreamServerSeekSource(session, StreamServerSeekSource.FAST_FORWARD)
		self["FastBackward"] = StreamServerSeekSource(session, StreamServerSeekSource.FAST_BACKWARD)
		self["SlowMotion"] = StreamServerSeekSource(session, StreamServerSeekSource.SLOW_MOTION)
		self["Play"] = StreamServerSeekSource(session, StreamServerSeekSource.PLAY)
