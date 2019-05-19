from __future__ import print_function
from ctypes import *

from enigma import eStreamServer, eServiceReference, iPlayableService, eTimer
from Components.config import config
from Components.PerServiceDisplay import PerServiceBase

from twisted.python import util

import os.path

if os.path.isfile("/usr/lib/enigma2/python/Plugins/SystemPlugins/GstRtspServer/StreamServerControl.py"):
	from Plugins.SystemPlugins.GstRtspServer.StreamServerControl import streamServerControl
else:
	from Components.StreamServerControl import streamServerControl

from subprocess import call

class StreamServerSeekNoSessionException(BaseException):
	pass

class StreamServerSeekAlreadyInitializedException(BaseException):
	pass

class StreamServerSeek(PerServiceBase):
	__instance = None
	_session = None
	_seekToMin = 0
	_isTemporaryLiveMode = False
	_isTemporaryLiveModeActive = False
	_temporaryLiveModeService = False
	_tvLastService = False
	_origCec = False
	_isVodActive = False
	_libsssSegment = None
	_m3u8Timer = None

	def __new__(cls, *p, **k):
		if StreamServerSeek.__instance is None:
			if not 'session' in k:
				raise StreamServerSeekNoSessionException
			StreamServerSeek._session = k["session"]
			StreamServerSeek.__instance = PerServiceBase.__new__(cls)
		elif 'session' in k:
			raise StreamServerSeekAlreadyInitializedException

		return StreamServerSeek.__instance
	
	def __init__(self, *p, **k):
		if not 'session' in k:
			return

		print("[StreamServerSeek] init")
		
		config.misc.standbyCounter.addNotifier(self._onStandby, initial_call = False)

		PerServiceBase.__init__(self, self._session.nav,
			{ 
				iPlayableService.evServiceChanged: self._onServiceChanged,
				iPlayableService.evEOF: self._onEOF,
				iPlayableService.evPlay: self._onPlaying
			}, with_event=False)
		
		
		self._timer = eTimer()
		self._timer_conn = self._timer.timeout.connect(self.endTemporaryLiveMode)

		streamServerControl.onSourceStateChanged.append(self._onSourceStateChanged)
		
	def _onStandby(self, element):
		if self._isTemporaryLiveMode:
			print("[StreamServerSeek] onStandBy: Ending temporary Live-Mode")
			self.endTemporaryLiveMode(False)

		if self._origCec:
			print("[StreamServerSeek] Re-enable CEC")
			config.cec.enabled.value = True
			config.cec.enabled.save()

	def _onServiceChanged(self):
		if self._isTemporaryLiveModeActive and self._temporaryLiveModeService and eServiceReference(self._temporaryLiveModeService).toCompareString() != self.navcore.getCurrentServiceReference().toCompareString():
			print("[StreamServerSeek] onServiceChanged: Ending temporary Live-Mode")
			self.endTemporaryLiveMode(False)

	def _onEOF(self):
		if self._isTemporaryLiveModeActive:
			print("[StreamServerSeek] onEOF: Ending temporary Live-Mode")
			self.endTemporaryLiveMode()

	def _onPlaying(self):
		if self._isTemporaryLiveModeActive:
			self.doSeek()
	
	def _onSourceStateChanged(self, state):
		if self._isTemporaryLiveMode and (state == False or state == 2):
			print("[StreamServerSeek] Temporary Live-Mode active, but all clients disconnected. End it in 15 seconds")
			self._timer.start(15000, True)
		elif self._isTemporaryLiveMode and self._timer.isActive():
			print("[StreamServerSeek] Reset end-timer")
			self._timer.stop()
		
		if state == True or state == 4:
			self.doSeek()
		elif state == False or state == 2:
			self._isVodActive = False

	def getSeek(self):
		seek = False
		if self._isTemporaryLiveModeActive:
			seek = self._session.nav.getCurrentService().seek()
		elif streamServerControl._encoderService:
			seek = streamServerControl._encoderService.seek()
		return seek

	def doSeek(self):
		if not self._seekToMin:
			return

		print("[StreamServerSeek] doSeek()")

		seek = self.getSeek()

		if seek:
			print("[StreamServerSeek] Seeking to %d minutes" % self._seekToMin)
			seek.seekTo(self._seekToMin * 60 * 90000)

		self._seekToMin = 0

	def changeIdleMode(self, idle):
		from Screens.Standby import inStandby
		if (inStandby is None and not idle) or (not inStandby is None and idle):
			return

		if not idle:
			self._origCec = config.cec.enabled.value
			if self._origCec:
				print("[StreamServerSeek] Disable CEC")
				config.cec.enabled.value = False
				config.cec.enabled.save()
			inStandby.Power()
		else:
			from Screens.Standby import Standby
			self._session.open(Standby)

	def forceInputMode(self, inputMode):
		if os.path.isfile("/usr/lib/enigma2/python/Plugins/SystemPlugins/GstRtspServer/StreamServerControl.py"):
			from Plugins.SystemPlugins.GstRtspServer.StreamServerConfig import applyConfig
			config.streamserver.source.value = str(inputMode)
			applyConfig(streamServerControl, False, True)
			return

		# This *should* work like done below the "return". However this leads to EncoderTimeout and hanging daemon sometimes
		# Therefor just kill it...
		call(["systemctl", "disable", "dreamliveserver.socket"])
		call(["killall", "-9", "dreamliveserver"])
		streamServerControl.config.streamserver.source.value = str(inputMode)
		streamServerControl.setInputMode(inputMode)
		call(["systemctl", "enable", "dreamliveserver.socket"])
		streamServerControl.config.streamserver.source.save()
		return

		# doesn't work reliably if a client is still connected:
		isMediatorEnabled = streamServerControl.config.streamserver.mediator.enabled.value

		rtsp_enabled = streamServerControl.config.streamserver.rtsp.enabled.value
		rtsp_path = streamServerControl.config.streamserver.rtsp.path.value
		rtsp_user = streamServerControl.config.streamserver.rtsp.user.value
		rtsp_password = streamServerControl.config.streamserver.rtsp.password.value
		#rtsp_port = streamServerControl.config.streamserver.rtsp.port.value
		hls_enabled = streamServerControl.config.streamserver.hls.enabled.value
		hls_path = streamServerControl.config.streamserver.hls.path.value
		#hls_port = streamServerControl.config.streamserver.hls.port.value
		hls_user = streamServerControl.config.streamserver.hls.user.value
		hls_password = streamServerControl.config.streamserver.hls.password.value

		streamServerControl.enableRTSP(False, rtsp_path, 554, rtsp_user, rtsp_password)
		streamServerControl.enableHLS(False, hls_path, 8080, hls_user, hls_password)
		streamServerControl.config.streamserver.mediator.enabled.value = False

		streamServerControl.config.streamserver.source.value = str(inputMode)
		streamServerControl.setInputMode(inputMode)

		streamServerControl.enableRTSP(rtsp_enabled, rtsp_path, 554, rtsp_user, rtsp_password)
		streamServerControl.enableHLS(hls_enabled, hls_path, 8080, hls_user, hls_password)
		streamServerControl.config.streamserver.mediator.enabled.value = isMediatorEnabled

	def endTemporaryLiveMode(self, idle = True):
		if not self._isTemporaryLiveMode:
			return

		self._isTemporaryLiveMode = False
		self._isTemporaryLiveModeActive = False
		self._temporaryLiveModeService = False
		self._isVodActive = False
		
		if self._tvLastService:
			service = eServiceReference(self._tvLastService)
			if service and service.valid():
				self._session.nav.playService(service)
	
		print("[StreamServerSeek] Set input mode to BACKGROUND")
		self.forceInputMode(eStreamServer.INPUT_MODE_BACKGROUND)

		if idle:
			self.changeIdleMode(True)

	def getSegmentOffsetFunc(self):
		if self._libsssSegment is None:
			libPath = "/usr/lib/libsss-segment.so.0"
			if os.path.exists(libPath):
				cdll.LoadLibrary(libPath)
				self._libsssSegment = CDLL(libPath)
			else:
				return None

		return self._libsssSegment.segmentOffset

	def destroy(self):
		PerServiceBase.destroy(self)
