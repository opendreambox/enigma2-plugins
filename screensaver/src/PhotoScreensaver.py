from enigma import ePicLoad, eTimer, eWindowAnimationSet, eFloatAnimation, eLinearInterpolator, eWindowAnimationManager, ePixmap, eActionMap, getDesktop
from Components.config import config
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Tools.Directories import fileExists
from Tools.Log import Log

from twisted.web.client import downloadPage

class MyPixmap(Pixmap):
	def postWidgetCreate(self, instance):
		Pixmap.postWidgetCreate(self, instance)
		self.setupAnimation()

	def setupAnimation(self):
		if self.instance:
			self.instance.setShowHideAnimation(PhotoScreensaver.ANIMATION_KEY_FADE)
			self.instance.setScale(ePixmap.SCALE_TYPE_WIDTH)


class PhotoScreensaver(Screen):
	skin = """<screen name="Screensaver" title="Screensaver" position="center,center" size="fill_parent,fill_parent" backgroundColor="#000000">
		<widget name="wallpaper" position="0,0" size="fill_parent,fill_parent" zPosition="1"/>
	</screen>"""

	TEMPFILE = "/tmp/wallpaper"
	ANIMATION_KEY_FADE = "wallpaper_slow_fade"

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions"], {
				"ok": self._onOk,
				"cancel": self.close},
			- 2)

		self.highPrioActionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self._onKeypress) #highest prio

		self._pixmap = MyPixmap()
		self["wallpaper"] = self._pixmap
		self._setupAnimation()
		#picload setup
		size = getDesktop(0).size()
		width, height = size.width(), size.height()
		self._picload = ePicLoad()
		self.__picload_conn = self._picload.PictureData.connect(self._onPixmapReady)
		self._picload.setPara((width, height, width, height, False, 1, '#ff000000'))
		self._nextPixmap = None
		self._timer = eTimer()
		self.__timer_conn = self._timer.timeout.connect(self._onTimeout)
		self._inactivityTimer = eTimer()
		self.__inactivityTimer_conn = self._inactivityTimer.timeout.connect(self._onInactivityTimeout)

		self._immediateShow = True
		self._isEnabled = False
		self._isInitial = True

		self.onShow.append(self._onShow)
		self.onClose.append(self._onClose)
		config.plugins.screensaver.photo.speed.addNotifier(self._setupAnimation, initial_call=False)

	def _onShow(self):#
		self._immediateShow = self._isInitial
		if not self._immediateShow:
			self._restartTimer()
		self._check()

	def _onClose(self):
		config.plugins.screensaver.photo.speed.removeNotifier(self._setupAnimation)

	def _setupAnimation(self, *args):
		animset = eWindowAnimationSet.create()
		animset.setKey(PhotoScreensaver.ANIMATION_KEY_FADE)
		animset.setName("Slow wallpaper fade")
		animset.setInternal(True)
		interpolator = eLinearInterpolator.create()
		duration = int(config.plugins.screensaver.photo.speed.value) * 1000
		animset.setAlpha(eFloatAnimation.create(duration, 0.0, 1.0, False, interpolator))
		eWindowAnimationManager.setAnimationSet(animset)
		self._pixmap.setupAnimation()

	def _check(self):
		if fileExists(self.TEMPFILE):
			self._onFileReady()
		else:
			self._loadNext()

	def isEnabled(self):
		return self._isEnabled

	def setEnabled(self, enabled):
		Log.i("%s" % (enabled,))
		if enabled == self._isEnabled:
			return
		self._isEnabled = enabled
		if self._isEnabled:
			self._onKeypress()
			self._check()
		else:
			self._reset()

	enabled = property(isEnabled, setEnabled)

	def _reset(self):
		self._nextPixmap = None
		self._timer.stop()
		self._inactivityTimer.stop()

	def _onKeypress(self, *args):
		self.hide()
		self._reset()
		if self._isEnabled:
			self._inactivityTimer.startLongTimer(int(config.plugins.screensaver.delay.value))
		return 0

	def _onInactivityTimeout(self):
		self.show()

	def _onOk(self):
		pass

	def _loadNext(self):
		Log.i("Getting next photo")
		url = "https://source.unsplash.com/random/1920x1080"
		self._d = downloadPage(url, self.TEMPFILE).addCallbacks(self._onFileReady, self._failed)

	def _onFileReady(self, *args):
		self._picload.startDecode(self.TEMPFILE)

	def _failed(self, *args):
		Log.w(args)

	def _onPixmapReady(self, picInfo=None):
		Log.d(picInfo)
		if not self._isEnabled:
			self._reset()
			return
		self._picInfo = picInfo
		self._nextPixmap = self._picload.getData()
		if self._immediateShow:
			self._immediateShow = False
			self._onTimeout()

	def _restartTimer(self):
		self._timer.startLongTimer(int(config.plugins.screensaver.photo.retention.value))

	def _showNext(self):
		if not self._isEnabled:
			self._reset()
			return
		if self._nextPixmap:
			self._isInitial = False
			self._pixmap.setPixmap(self._nextPixmap)
			self._nextPixmap = None
			self._restartTimer()
			return True
		return False

	def _onTimeout(self):
		if self._showNext():
			self._loadNext()
			self._restartTimer()
		else:
			self._immediateShow = True
