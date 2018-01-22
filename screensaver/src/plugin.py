from enigma import iPlayableService, iServiceInformation
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Tools.Log import Log

from PhotoScreensaver import PhotoScreensaver
from ScreensaverSetup import ScreensaverSetup

class ScreenSaverHandler(object):
	def __init__(self):
		self.session = None

	def start(self, session):
		self.session = session
		self._screenSaver = None
		self.session.screensaver = self
		self.session.nav.event.append(self._onEvent)
		self._enabled = True

	def enable(self):
		self._enabled = True
		self._onEvent(iPlayableService.evPlay)

	def disable(self):
		self._enabled = False
		self._onEvent(-1) #event doesn't matter when disabled

	def _instantiateSaver(self):
		if not self._screenSaver:
			self._screenSaver = self.session.instantiateDialog(PhotoScreensaver, zPosition=4000)

	def _onEvent(self, evt):
		self._instantiateSaver()

		if evt == iPlayableService.evPlay:
			if not (self._enabled and config.plugins.screensaver.enabled.value):
				self._screenSaver.enabled = False
				return
			Log.i("play event, checking for video")
			service = self.session.nav.getCurrentService()
			info = service and service.info()
			if not info:
				return
			width = info.getInfo(iServiceInformation.sVideoWidth)
			Log.d(width)
			self._screenSaver.enabled = width <= 0
		elif evt == iPlayableService.evStopped:
			self._screenSaver.enabled = True

screenSaverHandler = ScreenSaverHandler()

def runSetup(session, *args):
	session.open(ScreensaverSetup)

def menu(menuid, *args):
	if menuid == "osd_video_audio":
		return [(_("Screensaver"), runSetup, "screensaver", 100)]
	return []

def infobar(session):
	screenSaverHandler.start(session)

def main(session, **kwargs):
	session.open(PhotoScreensaver)

def Plugins(**kwargs):
	return [
		PluginDescriptor(name=_("Screensaver"), description=_("Screensaver using random photos"), where = PluginDescriptor.WHERE_MENU, fnc=menu),
		PluginDescriptor(name=_("Screensaver"), description=_("Screensaver using random photos"), where = PluginDescriptor.WHERE_INFOBAR, fnc=infobar),
		PluginDescriptor(name=_("Screensaver"), description=_("Screensaver using random photos"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
	]