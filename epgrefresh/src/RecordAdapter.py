from __future__ import print_function

from Components.SystemInfo import SystemInfo

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Config
from Components.config import config

from . import STARTNOTIFICATIONID, NOTIFICATIONDOMAIN


class RecordAdapter:
	backgroundCapable = True

	def __init__(self, session):
		self.backgroundRefreshAvailable = True
		self.__service = None
		self.navcore = session.nav

	def prepare(self):
		if not self.backgroundRefreshAvailable:
			return False
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("EPG refresh started in background."), MessageBox.TYPE_INFO, 4, STARTNOTIFICATIONID, domain=NOTIFICATIONDOMAIN)

		return True

	def play(self, service):
		print("[EPGRefresh.RecordAdapter.play]")
		if not self.backgroundRefreshAvailable:
			return False
		self.stopStreaming()
		self.__service = self.navcore.recordService(service)
		if self.__service is not None:
			self.__service.prepareStreaming()
			self.__service.start()
			return True
		return False

	def stopStreaming(self):
		if self.__service is not None:
			self.navcore.stopRecordService(self.__service)
			self.__service = None

	def stop(self):
		print("[EPGRefresh.RecordAdapter.stop]")
		self.stopStreaming()
