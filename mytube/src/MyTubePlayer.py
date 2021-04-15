from enigma import iPlayableService, eTimer
from Components.config import config
from Components.ActionMap import ActionMap
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarSeek
from Screens.Screen import Screen

class MyTubePlayer(Screen, InfoBarNotifications, InfoBarSeek):
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	skin = """<screen name="MyTubePlayer" position="0,540" size="1280,150" backgroundColor="transparent" flags="wfNoBorder">
		<ePixmap pixmap="menu/mediacenter.svg" position="40,60" zPosition="1" size="70,70" alphatest="on"/>
		<ePixmap position="0,0" pixmap="skin_default/infobar.png" size="1280,150" zPosition="-1" />
		<ePixmap pixmap="skin_default/icons/icon_event.png" position="120,17" size="20,13" alphatest="on" />
		<widget source="session.CurrentService" render="Label" position="150,9" size="760,27" font="Regular;24" valign="top" noWrap="1" backgroundColor="#263c59" transparent="1">
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="40,11" size="70,24" font="Regular;22" foregroundColor="grey" backgroundColor="background" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="550,61" size="200,24" font="Regular;22" halign="center" backgroundColor="#263c59" transparent="1">
			<convert type="ServicePosition">Length</convert>
		</widget>
		<ePixmap pixmap="skin_default/icons/ico_dolby_off.png" position="1100,30" size="42,20" alphatest="on" />
		<widget source="session.CurrentService" render="Pixmap" pixmap="skin_default/icons/ico_dolby_on.png" position="1100,30" size="42,20" zPosition="1" alphatest="on">
			<convert type="ServiceInfo">IsMultichannel</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<ePixmap pixmap="skin_default/icons/ico_format_off.png" position="1150,30" size="42,20" alphatest="on" />
		<widget source="session.CurrentService" render="Pixmap" pixmap="skin_default/icons/ico_format_on.png" position="1150,30" size="42,20" zPosition="1" alphatest="on">
			<convert type="ServiceInfo">IsWidescreen</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="session.CurrentService" render="Pixmap" pixmap="skin_default/icons/ico_hd_off.png" position="1200,30" size="42,20" alphatest="on">
			<convert type="ServiceInfo">VideoWidth</convert>
			<convert type="ValueRange">0,720</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="session.CurrentService" render="Pixmap" pixmap="skin_default/icons/ico_hd_on.png" position="1200,30" size="42,20" zPosition="1" alphatest="on">
			<convert type="ServiceInfo">VideoWidth</convert>
			<convert type="ValueRange">721,1980</convert>
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="session.CurrentService" render="Label" position="960,30" size="60,22" backgroundColor="#263c59" font="Regular;19" halign="right" transparent="1">
			<convert type="ServiceInfo">VideoWidth</convert>
		</widget>
		<eLabel position="1022,30" size="20,20" backgroundColor="#263c59" transparent="1" text="x" font="Regular;19" halign="center"/>
		<widget source="session.CurrentService" render="Label" position="1044,30" size="60,22" backgroundColor="#263c59" font="Regular;19" halign="left" transparent="1">
			<convert type="ServiceInfo">VideoHeight</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="150,88" size="80,24" font="Regular;22" halign="right" backgroundColor="#263c59" transparent="1">
			<convert type="ServicePosition">Position,ShowHours</convert>
		</widget>
		<eLabel position="250,99" size="800,2" backgroundColor="grey" />
		<widget source="session.CurrentService" render="Progress" position="250,96" size="800,8" zPosition="1" pixmap="skin_default/progress.png" transparent="1">
			<convert type="ServicePosition">Position</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="1070,87" size="160,24" font="Regular;22" halign="left" backgroundColor="#263c59" transparent="1">
			<convert type="ServicePosition">Remaining,Negate,ShowHours</convert>
		</widget>
	</screen>"""

	def __init__(self, session, service, lastservice, infoCallback=None, nextCallback=None, prevCallback=None):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		InfoBarSeek.__init__(self)
		self.session = session
		self.service = service
		self.infoCallback = infoCallback
		self.nextCallback = nextCallback
		self.prevCallback = prevCallback
		self.screen_timeout = 5000
		self.nextservice = None

		print "evEOF=%d" % iPlayableService.evEOF
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evEOF: self.__evEOF,
			})

		self["actions"] = ActionMap(["OkCancelActions", "InfobarSeekActions", "MediaPlayerActions", "MovieSelectionActions"],
		{
				"ok": self.ok,
				"cancel": self.leavePlayer,
				"stop": self.leavePlayer,
				"playpauseService": self.playpauseService,
				"seekFwd": self.playNextFile,
				"seekBack": self.playPrevFile,
				"showEventInfo": self.showVideoInfo,
			}, -2)


		self.lastservice = lastservice

		self.hidetimer = eTimer()
		self.hidetimer_conn = self.hidetimer.timeout.connect(self.ok)
		self.returning = False

		self.state = self.STATE_PLAYING
		self.lastseekstate = self.STATE_PLAYING

		self.onPlayStateChanged = []
		self.__seekableStatusChanged()

		self.play()
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.session.nav.stopService()

	def __evEOF(self):
		print "evEOF=%d" % iPlayableService.evEOF
		print "Event EOF"
		self.handleLeave(config.plugins.mytube.general.on_movie_stop.value)

	def __setHideTimer(self):
		self.hidetimer.start(self.screen_timeout)

	def showInfobar(self):
		self.show()
		if self.state == self.STATE_PLAYING:
			self.__setHideTimer()
		else:
			pass

	def hideInfobar(self):
		self.hide()
		self.hidetimer.stop()

	def ok(self):
		if self.shown:
			self.hideInfobar()
		else:
			self.showInfobar()

	def showVideoInfo(self):
		if self.shown:
			self.hideInfobar()
		if self.infoCallback is not None:
			self.infoCallback()

	def playNextFile(self):
		print "playNextFile"
		nextservice,error = self.nextCallback()
		print "nextservice--->",nextservice
		if nextservice is None:
			self.handleLeave(config.plugins.mytube.general.on_movie_stop.value, error)
		else:
			self.playService(nextservice)
			self.showInfobar()

	def playPrevFile(self):
		print "playPrevFile"
		prevservice,error = self.prevCallback()
		if prevservice is None:
			self.handleLeave(config.plugins.mytube.general.on_movie_stop.value, error)
		else:
			self.playService(prevservice)
			self.showInfobar()

	def playagain(self):
		print "playagain"
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.play()

	def playService(self, newservice):
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.service = newservice
		self.play()

	def play(self):
		if self.state == self.STATE_PAUSED:
			if self.shown:
				self.__setHideTimer()
		self.state = self.STATE_PLAYING
		self.session.nav.playService(self.service)
		if self.shown:
			self.__setHideTimer()

	def stopCurrent(self):
		print "stopCurrent"
		self.session.nav.stopService()
		self.state = self.STATE_IDLE

	def playpauseService(self):
		print "playpauseService"
		if self.state == self.STATE_PLAYING:
			self.pauseService()
		elif self.state == self.STATE_PAUSED:
			self.unPauseService()

	def pauseService(self):
		print "pauseService"
		if self.state == self.STATE_PLAYING:
			self.setSeekState(self.STATE_PAUSED)

	def unPauseService(self):
		print "unPauseService"
		if self.state == self.STATE_PAUSED:
			self.setSeekState(self.STATE_PLAYING)


	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None

		seek = service.seek()

		if seek is None or not seek.isCurrentlySeekable():
			return None

		return seek

	def isSeekable(self):
		if self.getSeek() is None:
			return False
		return True

	def __seekableStatusChanged(self):
		print "seekable status changed!"
		if not self.isSeekable():
			self["SeekActions"].setEnabled(False)
			self.setSeekState(self.STATE_PLAYING)
		else:
			self["SeekActions"].setEnabled(True)
			print "seekable"

	def __serviceStarted(self):
		self.state = self.STATE_PLAYING
		self.__seekableStatusChanged()

	def setSeekState(self, wantstate, onlyGUI=False):
		print "setSeekState"
		if wantstate == self.STATE_PAUSED:
			print "trying to switch to Pause- state:",self.STATE_PAUSED
		elif wantstate == self.STATE_PLAYING:
			print "trying to switch to playing- state:",self.STATE_PLAYING
		service = self.session.nav.getCurrentService()
		if service is None:
			print "No Service found"
			return False
		pauseable = service.pause()
		if pauseable is None:
			print "not pauseable."
			self.state = self.STATE_PLAYING

		if pauseable is not None:
			print "service is pausable"
			if wantstate == self.STATE_PAUSED:
				print "WANT TO PAUSE"
				pauseable.pause()
				self.state = self.STATE_PAUSED
				if not self.shown:
					self.hidetimer.stop()
					self.show()
			elif wantstate == self.STATE_PLAYING:
				print "WANT TO PLAY"
				pauseable.unpause()
				self.state = self.STATE_PLAYING
				if self.shown:
					self.__setHideTimer()

		for c in self.onPlayStateChanged:
			c(self.state)

		return True

	def handleLeave(self, how, error=False):
		self.is_closing = True
		if how == "ask":
			list = (
				(_("Yes"), "quit"),
				(_("No, but play video again"), "playagain"),
				(_("Yes, but play next video"), "playnext"),
				(_("Yes, but play previous video"), "playprev"),
			)
			if error is False:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list=list)
			else:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("No playable video found! Stop playing this movie?"), list=list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		self.handleLeave(config.plugins.mytube.general.on_movie_stop.value)

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer == "quit":
			print 'quited'
			self.close()
		elif answer == "playnext":
			self.playNextFile()
		elif answer == "playprev":
			self.playPrevFile()
		elif answer == "playagain":
			self.playagain()

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.handleLeave(config.usage.on_movie_eof.value)
