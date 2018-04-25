from Components.Sources.Source import Source

import os.path

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek

if os.path.isfile("/usr/lib/enigma2/python/Plugins/SystemPlugins/GstRtspServer/StreamServerControl.py"):
	from Plugins.SystemPlugins.GstRtspServer.StreamServerControl import streamServerControl
else:
	from Components.StreamServerControl import streamServerControl

class CurrentService(Source):
	session = None
	_state = None
	
	STATE_INACTIVE = 0
	STATE_BACKGROUND = 1
	STATE_LIVE = 2

	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def getCurrentService(self):
		encoderService = streamServerControl._encoderService

		if encoderService:
			self._state = self.STATE_BACKGROUND

		if StreamServerSeek()._isTemporaryLiveMode:
			encoderService = self.session.nav.getCurrentService()
			self._state = self.STATE_LIVE

		if not encoderService:
			self._state = self.STATE_INACTIVE
			return None

		return encoderService

	service = property(getCurrentService)

	def getState(self):
		if self._state is None:
			self.getCurrentService()
		return self._state

	state = property(getState)
	
	def getStateText(self):
		if self.state == self.STATE_BACKGROUND:
			return "BACKGROUND"
		elif self._state == self.STATE_LIVE:
			return "LIVE"
		else:
			return "INACTIVE"

	statetext = property(getStateText)
	
	def destroy(self):
		Source.destroy(self)
