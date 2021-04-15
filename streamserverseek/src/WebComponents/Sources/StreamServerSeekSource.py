from Components.Sources.Source import Source

import os.path

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek

if os.path.isfile("/usr/lib/enigma2/python/Plugins/SystemPlugins/GstRtspServer/StreamServerControl.py"):
	from Plugins.SystemPlugins.GstRtspServer.StreamServerControl import streamServerControl
else:
	from Components.StreamServerControl import streamServerControl


class StreamServerSeekSource(Source):
	SEEK_TO = 0
	SEEK_RELATIVE = 1
	SEEK_CHAPTER = 2
	GET_LENGTH = 3
	GET_PLAY_POSITION = 4
	PAUSE = 5
	UNPAUSE = 6
	FAST_FORWARD = 7
	FAST_BACKWARD = 8
	SLOW_MOTION = 9
	PLAY = 10
	INFO = 11

	REQUIRE_PAUSABLE = {PAUSE, UNPAUSE, FAST_FORWARD, FAST_BACKWARD, SLOW_MOTION, PLAY}
	REQUIRE_SEEKABLE = {SEEK_TO, SEEK_RELATIVE, SEEK_CHAPTER, GET_LENGTH, GET_PLAY_POSITION}

	_func = None
	_unitMultiplier = 1

	_pause = None
	_seek = None

	res = None

	def __init__(self, session, func):
		Source.__init__(self)
		self.session = session
		self.func = func

	def pause(self):
		return self._pause.pause()

	def unpause(self):
		return self._pause.unpause()

	def fastForward(self, speed):
		if speed == 0:
			return self.unpause()
		return self._pause.setFastForward(speed)

	def fastBackward(self, speed):
		return self.fastForward(speed * -1)

	def slowMotion(self, speed):
		if speed == 0:
			return self.unpause()
		return self._pause.setSlowMotion(speed)

	def seekTo(self, pos):
		return self._seek.seekTo(pos * self._unitMultiplier)

	def seekRelative(self, pos):
		if pos > 0:
			return self._seek.seekRelative(1, pos * self._unitMultiplier)
		elif pos < 0:
			return self._seek.seekRelative(-1, pos * self._unitMultiplier * -1)
		return -1

	def seekChapter(self, number):
		return self._seek.seekChapter(number)

	def getLength(self):
		result = self._seek.getLength()
		if not result[0]:
			if result[1] == 0:
				return 0
			return result[1] / self._unitMultiplier
		return -1

	def getPlayPosition(self):
		result = self._seek.getPlayPosition()
		if not result[0]:
			if result[1] == 0:
				return 0
			return result[1] / self._unitMultiplier
		return -1

	def initVars(self):
		encoderService = streamServerControl._encoderService
		if StreamServerSeek()._isTemporaryLiveMode:
			encoderService = self.session.nav.getCurrentService()
		elif not encoderService:
			self.res = (False, _("encoder service not running"))
			return False

		if self.func in self.REQUIRE_PAUSABLE:
			pause = encoderService.pause()
			if not pause:
				self.res = (False, _("encoder service not pausable"))
				return False
			self._pause = pause

		if self.func in self.REQUIRE_SEEKABLE:
			seek = encoderService.seek()
			if not seek:
				self.res = (False, _("encoder service not seekable"))
				return False
			self._seek = seek

		return True

	def handleCommand(self, params):
		if not self.initVars():
			return

		pos = None
		number = None
		speed = None

		if self.func is self.SEEK_TO or self.func is self.SEEK_RELATIVE:
			pos = params.get("pos", None)
			if not pos:
				self.res = (False, _("required parameter '%s' missing") % "pos")
				return
			try:
				pos = int(pos)
			except Exception:
				self.res = (False, _("invalid parameter '%s'") % "pos")
				return

		if self.func is self.SEEK_CHAPTER:
			number = params
			if not number:
				self.res = (False, _("required parameter '%s' missing") % "number")
				return
			try:
				number = int(number)
			except Exception:
				self.res = (False, _("invalid parameter '%s'") % "number")
				return

		if self.func is self.FAST_FORWARD or self.func is self.FAST_BACKWARD or self.func is self.SLOW_MOTION:
			speed = params
			if not speed:
				self.res = (False, _("required parameter '%s' missing") % "speed")
				return
			try:
				speed = int(speed)
			except Exception:
				self.res = (False, _("invalid parameter '%s'") % "speed")
				return

		if self.func is self.SEEK_TO or self.func is self.SEEK_RELATIVE or self.func is self.GET_LENGTH or self.func is self.GET_PLAY_POSITION:
			self._unitMultiplier = 1
			if self.func is self.GET_LENGTH or self.func is self.GET_PLAY_POSITION:
				unit = params
			else:
				unit = params.get("unit", None)
			if unit and unit == "sec":
				self._unitMultiplier = 90000
			elif unit and unit == "min":
				self._unitMultiplier = 90000 * 60
			elif unit:
				self.res = (False, _("invalid parameter '%s'") % "unit")
				return

		if self.func is self.SEEK_TO:
			result = self.seekTo(pos)
		elif self.func is self.SEEK_RELATIVE:
			result = self.seekRelative(pos)
		elif self.func is self.SEEK_CHAPTER:
			result = self.seekChapter(number)
		elif self.func is self.GET_LENGTH:
			result = self.getLength()
		elif self.func is self.GET_PLAY_POSITION:
			result = self.getPlayPosition()
		elif self.func is self.FAST_FORWARD:
			result = self.fastForward(speed)
		elif self.func is self.FAST_BACKWARD:
			result = self.fastBackward(speed)
		elif self.func is self.SLOW_MOTION:
			result = self.slowMotion(speed)
		elif self.func is self.INFO:
			result = self.info()

		self.res = (True, result)

	def getResult(self):
		if not self.res:
			if not self.initVars():
				return self.res
			elif self.func is self.GET_LENGTH:
				return (True, self.getLength())
			elif self.func is self.GET_PLAY_POSITION:
				return (True, self.getPlayPosition())
			elif self.func is self.PAUSE:
				return (True, self.pause())
			elif self.func is self.UNPAUSE or self.func is self.PLAY:
				return (True, self.unpause())
			elif self.func is self.INFO:
				return self.info()
			else:
				return (False, _("required parameter(s) missing"))

		return self.res

	result = property(getResult)
