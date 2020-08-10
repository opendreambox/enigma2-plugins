from enigma import eCec, eActionMap
from e2reactor import monotonic_time

from Components.config import config

from Tools.Log import Log
from keyids import KEYIDS

class CecRemote(object):
	KEY_MAP_RECEIVE = {
		eCec.RC_SELECT : KEYIDS["KEY_OK"],
		eCec.RC_UP : KEYIDS["KEY_UP"],
		eCec.RC_DOWN : KEYIDS["KEY_DOWN"],
		eCec.RC_LEFT : KEYIDS["KEY_LEFT"],
		eCec.RC_RIGHT : KEYIDS["KEY_RIGHT"],
		eCec.RC_RIGHT_UP : (KEYIDS["KEY_RIGHT"], KEYIDS["KEY_UP"]),
		eCec.RC_RIGHT_DOWN : (KEYIDS["KEY_RIGHT"], KEYIDS["KEY_DOWN"]),
		eCec.RC_LEFT_UP : (KEYIDS["KEY_LEFT"], KEYIDS["KEY_UP"]),
		eCec.RC_LEFT_DOWN : (KEYIDS["KEY_LEFT"], KEYIDS["KEY_DOWN"]),
		eCec.RC_ROOT_MENU : KEYIDS["KEY_MENU"],
		eCec.RC_SETUP_MENU : KEYIDS["KEY_MENU"],
		eCec.RC_CONTENTS_MENU : KEYIDS["KEY_MENU"],
		eCec.RC_FAVORITE_MENU : KEYIDS["KEY_MENU"],
		eCec.RC_EXIT : KEYIDS["KEY_EXIT"],
		eCec.RC_0 : KEYIDS["KEY_0"],
		eCec.RC_1 : KEYIDS["KEY_1"],
		eCec.RC_2 : KEYIDS["KEY_2"],
		eCec.RC_3 : KEYIDS["KEY_3"],
		eCec.RC_4 : KEYIDS["KEY_4"],
		eCec.RC_5 : KEYIDS["KEY_5"],
		eCec.RC_6 : KEYIDS["KEY_6"],
		eCec.RC_7 : KEYIDS["KEY_7"],
		eCec.RC_8 : KEYIDS["KEY_8"],
		eCec.RC_9 : KEYIDS["KEY_9"],
		eCec.RC_CHANNEL_UP : KEYIDS["KEY_CHANNELUP"],
		eCec.RC_CHANNEL_DOWN : KEYIDS["KEY_CHANNELDOWN"],
		eCec.RC_INFO : KEYIDS["KEY_INFO"],
		eCec.RC_HELP : KEYIDS["KEY_HELP"],
		eCec.RC_PAGE_UP : KEYIDS["KEY_CHANNELUP"],
		eCec.RC_PAGE_DOWN : KEYIDS["KEY_CHANNELDOWN"],
		eCec.RC_POWER : KEYIDS["KEY_POWER"],
		eCec.RC_VOLUME_UP : KEYIDS["KEY_VOLUMEUP"],
		eCec.RC_VOLUME_DOWN : KEYIDS["KEY_VOLUMEDOWN"],
		eCec.RC_MUTE : KEYIDS["KEY_MUTE"],
		eCec.RC_PLAY : KEYIDS["KEY_PLAY"],
		eCec.RC_STOP : KEYIDS["KEY_STOP"],
		eCec.RC_PAUSE : KEYIDS["KEY_PAUSE"],
		eCec.RC_RECORD : KEYIDS["KEY_RECORD"],
		eCec.RC_RWD : KEYIDS["KEY_REWIND"],
		eCec.RC_FWD : KEYIDS["KEY_FASTFORWARD"],
		eCec.RC_EPG : KEYIDS["KEY_INFO"],
		eCec.RC_TIMER : KEYIDS["KEY_RECORD"],
		eCec.RC_PLAY_F : KEYIDS["KEY_PLAY"],
		eCec.RC_PAUSEPLAY_F : KEYIDS["KEY_PAUSE"],
		eCec.RC_REC_F : KEYIDS["KEY_RECORD"],
		eCec.RC_STOP_F : KEYIDS["KEY_STOP"],
		eCec.RC_MUTE_F : KEYIDS["KEY_MUTE"],
		eCec.RC_POWER_F : KEYIDS["KEY_POWER"],
		eCec.RC_BLUE : KEYIDS["KEY_BLUE"],
		eCec.RC_RED : KEYIDS["KEY_RED"],
		eCec.RC_GREEN : KEYIDS["KEY_GREEN"],
		eCec.RC_YELLOW : KEYIDS["KEY_YELLOW"],
	}

	KEY_MAP_SEND = {
		KEYIDS["KEY_VOLUMEUP"] : eCec.RC_VOLUME_UP,
		KEYIDS["KEY_VOLUMEDOWN"] : eCec.RC_VOLUME_DOWN,
		KEYIDS["KEY_MUTE"] : eCec.RC_MUTE,
	}

	SYSTEM_AUDIO_KEYS = (KEYIDS["KEY_VOLUMEUP"], KEYIDS["KEY_VOLUMEDOWN"], KEYIDS["KEY_MUTE"])

	FLAG_MAKE = 0
	FLAG_BREAK = 1

	REMOTE_TYPE_ADVANCED = "dreambox advanced remote control (native)"

	def __init__(self, cec):
		self._cec = cec
		self.actionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self._onKeyPress) #highest prio
		self._press_conn = self._cec.onKeyPressed.append(self._receivedKeyPress)
		self._release_conn = self._cec.onKeyReleased.append(self._receivedKeyRelease)
		self._lastKey = -1
		self._lastKeyPress = 0

	def _onKeyPress(self, keyid, flag):
		if config.cec.volume_forward.value:
			if flag == 0 or flag == 2:
				self.sendSystemAudioKey(keyid)
		return 0

	def _receivedKeyPress(self, sender, code):
		if not config.cec.receive_remotekeys.value:
			return
		mcode = self.KEY_MAP_RECEIVE.get(code, None)
		Log.i("code mapped: %s => %s" % (code, mcode))
		if mcode is not None:
			am = eActionMap.getInstance()
			if isinstance(mcode, tuple):
				for c in mcode:
					am.keyPressed(self.REMOTE_TYPE_ADVANCED, c, self.FLAG_MAKE)
					am.keyPressed(self.REMOTE_TYPE_ADVANCED, c, self.FLAG_BREAK)
			else:
				am.keyPressed(self.REMOTE_TYPE_ADVANCED, mcode, self.FLAG_MAKE)
				am.keyPressed(self.REMOTE_TYPE_ADVANCED, mcode, self.FLAG_BREAK)

	def _isRepeatAllowed(self):
		minDelay = int(config.cec.remote_repeat_delay.value)
		return ( monotonic_time() - self._lastKeyPress ) * 1000 >= minDelay

	def _keyPressed(self, keyid):
		self._lastKey = keyid
		self._lastKeyPress = monotonic_time()

	def _receivedKeyRelease(self, sender):
		pass

	def sendSystemAudioKey(self, keyid):
		if keyid not in self.SYSTEM_AUDIO_KEYS:
			return
		keyid = self.KEY_MAP_SEND[keyid]
		if keyid == self._lastKey and not self._isRepeatAllowed():
			Log.d("skipping keypress for %s to honor minimum delay" %keyid)
			return
		self._keyPressed(keyid)
		self._cec.sendSystemAudioKey(keyid)

	def sendKey(self, dest, keyid, translate=False):
		if translate:
			if keyid not in self.KEY_MAP_SEND:
				return
			keyid = self.KEY_MAP_SEND[keyid]
		if keyid == self._lastKey and not self._isRepeatAllowed():
			Log.d("skipping keypress for %s to honor minimum delay" %keyid)
			return
		self._keyPressed(keyid)
		self._cec.sendKey(dest, keyid)
