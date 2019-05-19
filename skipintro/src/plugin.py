# -*- coding: utf-8 -*-
from __future__ import division
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import HelpableActionMap
from Components.config import config
from Screens.MessageBox import MessageBox
from Screens.InfoBarGenerics import InfoBarSeek
from SkipIntroDatabase import SIDatabase
from SkipIntroSetup import SISetupScreen
import re

baseInfoBarSeek__init__ = None
baseInfoBarSeek__serviceStarted = None
baseInfoBarSeek__seekableStatusChanged = None

def getServiceName(self):
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		serviceName = info and info.getName()

		season=""
		if config.plugins.skipintro.title_pattern.value != "Off":
			serviceNameRegex = re.compile(config.plugins.skipintro.title_pattern.value)
			serviceNameRegexResult = serviceNameRegex.search(serviceName)

			if serviceNameRegexResult and serviceNameRegexResult.group(2):
				if int(serviceNameRegexResult.group(2).replace("S","")) > 0:
					season = " " + serviceNameRegexResult.group(2)
			#if config.plugins.skipintro.save_season.value:
			return (serviceNameRegexResult.group(1), season) if serviceNameRegexResult else (serviceName, season)
		else:
			return (serviceName, season)

def InfoBarSeek__serviceStarted(self):
	print "=== InfoBarSeek__serviceStarted SkipIntro"
	baseInfoBarSeek__serviceStarted(self)

	seek = self.getSeek()
	if seek is None:
		return
	#make here your own code at starting a video
	if config.plugins.skipintro.show_videostartmsg.value:
		from Tools import Notifications

		# get the video title
		title = getServiceName(self)
		# read seek time from database
		self.skipSeekTime, self.seriesName = self.database.getSkipTime(title[0], title[1])

		if self.skipSeekTime == 0:
			msgtxt = _("No skip time saved for\n%s") % title[0]
		else:
			msgtxt = _("Saved skip time found for\n%s:\n%s seconds") %(self.seriesName, str(self.skipSeekTime // 90000))
		Notifications.AddNotification(MessageBox, msgtxt, MessageBox.TYPE_INFO, timeout=3)

def InfoBarSeek__seekableStatusChanged(self):
		print "=== InfoBarSeek__seekableStatusChanged SkipIntro"
		baseInfoBarSeek__seekableStatusChanged(self)
		if self["SkipIntroSeekActions"] is not None:
			#do not use this actionmap in tv-mode or on active timeshift
			if not self.isSeekable() or (hasattr(self, "timeshift_enabled") and self.timeshift_enabled):
				self["SkipIntroSeekActions"].setEnabled(False)
			else:
				self["SkipIntroSeekActions"].setEnabled(True)

def InfoBarSeek__init__(self, actionmap = "InfobarSeekActions"):
	print "== InfoBarSeek__init__ SkipIntro"
	self["SkipIntroSeekActions"] = None
	baseInfoBarSeek__init__(self, actionmap)

	self.setSkipTimeStart = False
	self.setSeasonIntroTime = False
	self.skipTimeStartPos = 0
	self.skipTimeStopPos = 0
	self.skipSeekTime = 0
	self.seriesName = ""
	self.database = SIDatabase()
	self.database.initialize()

	def skipIntro():
		print "== skip intro"
		title = getServiceName(self)

		if self.setSkipTimeStart:
			setIntroTime()
			return

		# read seek time from database
		self.skipSeekTime, self.seriesName = self.database.getSkipTime(title[0],title[1])

		if self.skipSeekTime == 0:
			#self.setSkipTimeStart = False
			setIntroTime()
		else:
			if config.plugins.skipintro.show_skipmsg.value:
				self.session.open(MessageBox, _("SkipIntro found seek time for\n%s:\n%s seconds") %(self.seriesName,str(self.skipSeekTime // 90000)), MessageBox.TYPE_INFO, timeout=3)
			self.doSeekRelative(self.skipSeekTime)

	def skipIntro_long():
		if self.setSkipTimeStart:
			self.setSeasonIntroTime=True
			setIntroTime()
		else:
			setIntroTime()

	def setIntroTime_long():
		if self.setSkipTimeStart:
			self.setSeasonIntroTime=True
		setIntroTime()

	def setIntroTime():
		if self.setSkipTimeStart:
			seekable = self.getSeek()
			if seekable:
				self.skipTimeStopPos = seekable.getPlayPosition()
				if self.skipTimeStopPos[0]:
					self.skipTimeStopPos = self.skipTimeStopPos[0]
				else:
					self.skipTimeStopPos = self.skipTimeStopPos[1]
			self.skipSeekTime = int(self.skipTimeStopPos) - int(self.skipTimeStartPos) 

			title = getServiceName(self)

			db_title = title[0]
			if self.setSeasonIntroTime:
				db_title = title[0] + title[1]

			msgtxt = _("Stopping time measurment for intro duration for\n%s.\nIntro duration: %s seconds") %(db_title, str(self.skipSeekTime // 90000))
			msgtxt += _(" (-%s seconds).") %(config.plugins.skipintro.skiptime_decrease.value)
			if self.setSeasonIntroTime:
				msgtxt += _("\nIntro duration will be saved with season.")
			self.session.open(MessageBox, msgtxt, MessageBox.TYPE_INFO, timeout=3)

			#reduce the calculated skiptime
			self.skipSeekTime = int(self.skipSeekTime) - (int(config.plugins.skipintro.skiptime_decrease.value) * 90000)

			if self.skipSeekTime<0:
				self.skipSeekTime=0

			# save seek time into database
			self.database.setSkipTime(db_title, self.skipSeekTime)
			self.setSkipTimeStart = False
			self.setSeasonIntroTime = False

		else:
			self.setSeasonIntroTime=False
			seekable = self.getSeek()
			if seekable:
				self.skipTimeStartPos = seekable.getPlayPosition()
				if self.skipTimeStartPos[0]:
					self.skipTimeStartPos = self.skipTimeStartPos[0]
				else:
					self.skipTimeStartPos = self.skipTimeStartPos[1]
			title = getServiceName(self)
			self.session.open(MessageBox, _("Starting time measurement for intro duration for:\n%s") %(title[0]), MessageBox.TYPE_INFO, timeout=3)
			self.setSkipTimeStart = True

	self["SkipIntroSeekActions"] = HelpableActionMap(self, "SkipIntroSeekActions",
			{
				"2": (skipIntro, _("skip intro")),
				"8": (skipIntro_long, _("set intro time")),
				"2_long": (skipIntro_long, _("skip intro")),
			}, prio=-5)
			# give them a more priority to win over SeekActions in VTI-Image
	self["SkipIntroSeekActions"].setEnabled(False)

##############################################

def autostart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		session = kwargs["session"]

		global baseInfoBarSeek__init__, baseInfoBarServiceErrorPopupSupport__serviceStarted
		if baseInfoBarSeek__init__ is None:
			baseInfoBarSeek__init__ = InfoBarSeek.__init__
		InfoBarSeek.__init__ = InfoBarSeek__init__

		global baseInfoBarSeek__serviceStarted
		if baseInfoBarSeek__serviceStarted is None:
			baseInfoBarSeek__serviceStarted = InfoBarSeek._InfoBarSeek__serviceStarted
		InfoBarSeek._InfoBarSeek__serviceStarted = InfoBarSeek__serviceStarted

		global baseInfoBarSeek__seekableStatusChanged
		if baseInfoBarSeek__seekableStatusChanged is None:
			baseInfoBarSeek__seekableStatusChanged = InfoBarSeek._InfoBarSeek__seekableStatusChanged
		InfoBarSeek._InfoBarSeek__seekableStatusChanged = InfoBarSeek__seekableStatusChanged

def setup(session, **kwargs):
	session.open(SISetupScreen)

##############################################

def Plugins(**kwargs):
	from SkipIntroSetup import version
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart),
		PluginDescriptor(where=[PluginDescriptor.WHERE_PLUGINMENU], fnc=setup, name="SkipIntro", description=_("Skip intro by predefined skip time"), icon="plugin.png"),
	]
