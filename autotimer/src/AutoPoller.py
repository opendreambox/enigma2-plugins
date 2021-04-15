from __future__ import print_function

# Core functionality
from enigma import eTimer, ePythonMessagePump

# Config
from Components.config import config

# Notifications
from Tools.FuzzyDate import FuzzyTime
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

from ServiceReference import ServiceReference

NOTIFICATIONID = 'AutoTimerConflictEncounteredNotification'
SIMILARNOTIFICATIONID = 'AutoTimerSimilarUsedNotification'

from threading import Thread, Semaphore
from collections import deque

from twisted.internet import reactor

from Logger import doLog

class AutoPollerThread(Thread):
	"""Background thread where the EPG is parsed (unless initiated by the user)."""
	def __init__(self):
		Thread.__init__(self)
		self.__semaphore = Semaphore(0)
		self.__queue = deque(maxlen=1)
		self.__pump = ePythonMessagePump()
		self.__pump_recv_msg_conn = self.__pump.recv_msg.connect(self.gotThreadMsg)
		self.__timer = eTimer()
		self.__timer_conn = self.__timer.timeout.connect(self.timeout)
		self.running = False

	def timeout(self):
		self.__semaphore.release()

	def gotThreadMsg(self, msg):
		"""Create Notifications if there is anything to display."""
		ret = self.__queue.pop()
		conflicts = ret[4]
		if conflicts and config.plugins.autotimer.notifconflict.value:
			AddPopup(
				_("%(conflicts)d conflict(s) encountered when trying to add new timers:\n%(timers)s") %
				{"conflicts":len(conflicts), "timers":'\n'.join([_("%(sname)s - %(tname)s: %(name)s at %(begin)s") % {"sname":ServiceReference(x[3]).getServiceName(), "tname":x[4], "name":x[0], "begin":FuzzyTime(x[2])} for x in conflicts])},
				MessageBox.TYPE_INFO,
				config.plugins.autotimer.popup_timeout.value,
				NOTIFICATIONID
			)
		similars = ret[5]
		if similars and config.plugins.autotimer.notifsimilar.value:
			AddPopup(
				_("%(similars)d conflict(s) solved with similar timer(s):\n%(timers)s") %
				{"similars":len(similars), "timers":'\n'.join([_("%(tname)s: %(name)s at %(begin)s") % {"tname":x[4], "name":x[0], "begin":FuzzyTime(x[2])} for x in similars])},
				MessageBox.TYPE_INFO,
				config.plugins.autotimer.popup_timeout.value,
				SIMILARNOTIFICATIONID
			)

	def start(self, initial=True):
		# NOTE: we wait for several minutes on initial launch to not delay enigma2 startup time
		if initial:
			delay = config.plugins.autotimer.delay.value * 60
		else:
			delay = config.plugins.autotimer.interval.value * 3600

		self.__timer.startLongTimer(delay)
		if not self.isAlive():
			Thread.start(self)

	def pause(self):
		self.__timer.stop()

	def stop(self):
		self.__timer.stop()
		self.running = False
		self.__semaphore.release()
		self.__pump_recv_msg_conn = None
		self.__timer_conn = None

	def run(self):
		sem = self.__semaphore
		queue = self.__queue
		pump = self.__pump
		timer = self.__timer

		self.running = True
		while 1:
			sem.acquire()
			# NOTE: we have to check this here and not using the while to prevent the parser to be started on shutdown
			if not self.running:
				break
			
			if config.plugins.autotimer.skip_during_records.value:
				try:
					import NavigationInstance
					if NavigationInstance.instance.RecordTimer.isRecording():
						doLog("[AutoTimer]: Skip check during running records")
						reactor.callFromThread(timer.startLongTimer, config.plugins.autotimer.interval.value * 3600)
						continue
				except:
					pass

			if config.plugins.autotimer.skip_during_epgrefresh.value:
				try:
					from Plugins.Extensions.EPGRefresh.EPGRefresh import epgrefresh
					if epgrefresh.isrunning:
						doLog("[AutoTimer]: Skip check during EPGRefresh")
						reactor.callFromThread(timer.startLongTimer, config.plugins.autotimer.interval.value * 3600)
						continue
				except:
					pass

			from plugin import autotimer
			# Ignore any program errors
			try:
				queue.append(autotimer.parseEPG())
				pump.send(0)
			except Exception:
				# Dump error to stdout
				import traceback
				import sys
				traceback.print_exc(file=sys.stdout)
			#Keep that eTimer in the mainThread
			reactor.callFromThread(timer.startLongTimer, config.plugins.autotimer.interval.value * 3600)

class AutoPoller:
	"""Manages actual thread which does the polling. Used for convenience."""

	def __init__(self):
		self.thread = AutoPollerThread()

	def start(self, initial=True):
		self.thread.start(initial=initial)

	def pause(self):
		self.thread.pause()

	def stop(self):
		self.thread.stop()
		# NOTE: while we don't need to join the thread, we should do so in case it's currently parsing
		self.thread.join()
		self.thread = None
