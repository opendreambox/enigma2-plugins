from __future__ import absolute_import
from Plugins.Extensions.WebInterface.WebScreens import WebScreen

class StreamServerSeekWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		
		from .WebComponents.Sources.StreamServerSeekSource import StreamServerSeekSource
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

class StreamServerSeekInfoWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Components.Sources.StaticText import StaticText
		from .WebComponents.Sources.CurrentService import CurrentService
		from .WebComponents.Sources.StreamServerSeekSource import StreamServerSeekSource
		from .WebComponents.Sources.NaSource import NaSource
		from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek
		import os.path
		if os.path.isfile("/usr/lib/enigma2/python/Plugins/SystemPlugins/GstRtspServer/StreamServerControl.py"):
			from Plugins.SystemPlugins.GstRtspServer.StreamServerControl import streamServerControl
		else:
			from Components.StreamServerControl import streamServerControl
		from enigma import iServiceInformation, eServiceReference

		currentServiceSource = CurrentService(session)
		currentService = currentServiceSource.service
		
		self["State"] = StaticText(str(currentServiceSource.state))
		self["StateText"] = StaticText(currentServiceSource.statetext)

		naText = ""
		na = StaticText(naText)

		if currentService:
			self["CurrentService"] = currentServiceSource
			self["MoviePath"] = StaticText(eServiceReference(currentService.info().getInfoString(iServiceInformation.sServiceref)).getPath())
			if currentService.pause():
				self["Pausable"] = StaticText("1")
			else:
				self["Pausable"] = StaticText("0")
			if currentService.seek():
				self["Seekable"] = StaticText("1")
				self["Length"] = StreamServerSeekSource(session, StreamServerSeekSource.GET_LENGTH)
				self["PlayPosition"] = StreamServerSeekSource(session, StreamServerSeekSource.GET_PLAY_POSITION)
			else:
				self["Seekable"] = StaticText("0")
				self["Length"] = NaSource(naText)
				self["PlayPosition"] = NaSource(naText)
		else:
			self["CurrentService"] = currentServiceSource
			self["MoviePath"] = na
			self["Pausable"] = na
			self["Seekable"] = na
			self["Length"] = NaSource(naText)
			self["PlayPosition"] = NaSource(naText)
