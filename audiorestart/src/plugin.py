from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import NumberActionMap
from Components.Button import Button
from Components.Label import Label
from Components.SystemInfo import SystemInfo
from enigma import eTimer
from Plugins.Plugin import PluginDescriptor
from Screens import Standby
hasAudioFormats = True
try:
	from Screens.AudioSelection import AUDIO_FORMATS
except:
	hasAudioFormats = False
from Screens.Screen import Screen

import NavigationInstance

config.plugins.AudioRestart = ConfigSubsection()
config.plugins.AudioRestart.restartSelection = ConfigSelection( default = "disabled", choices = [("disabled", _("disabled")), ("restart", _("after restart")), ("standby", _("after standby")), ("both", _("after restart/standby"))])
config.plugins.AudioRestart.restartDelay = ConfigInteger(default = 5, limits = (0,30))

PLUGIN_BASE = "AudioRestart"
PLUGIN_VERSION = "0.2"

def doRestartAudio():
	service = NavigationInstance.instance.getCurrentService()
	audioTracks = service and service.audioTracks()
	isAC3 = False
	if audioTracks is not None:
		n = audioTracks.getNumberOfTracks()
		idx = audioTracks.getCurrentTrack()
		if 0 <= idx < n:
			trackInfo = audioTracks.getTrackInfo(idx)
			desc = trackInfo.getDescription()
			codec = hasAudioFormats and AUDIO_FORMATS.get(trackInfo.getType(), (None, ""))[1]
			if "AC3" in desc or "AC-3" in desc or "DTS" in desc or (hasAudioFormats and codec in ("AC3","AC3+")):
				isAC3 = True
	if isAC3 and SystemInfo["CanDownmixAC3"] and (config.av.downmix_ac3.value == False):
		config.av.downmix_ac3.value = True
		config.av.downmix_ac3.save()
		config.av.downmix_ac3.value = False
		config.av.downmix_ac3.save()
		print "[AudioSync] audio restarted"

class AudioRestart():
	def __init__(self):
		self.activateTimer = eTimer()
		self.activateTimer_conn = self.activateTimer.timeout.connect(self.restartAudio)
		if config.plugins.AudioRestart.restartSelection.value in ["standby", "both"]:
			config.misc.standbyCounter.addNotifier(self.enterStandby, initial_call = False)
		if config.plugins.AudioRestart.restartSelection.value in ["restart", "both"]:
			self.startTimer()

	def enterStandby(self, configElement):
		Standby.inStandby.onClose.append(self.endStandby)

	def endStandby(self):
		self.startTimer()

	def startTimer(self):
		self.intDelay = config.plugins.AudioRestart.restartDelay.value * 1000
		print "[AudioSync] audio restart in ", self.intDelay
		self.activateTimer.start(self.intDelay, True)

	def restartAudio(self):
		self.activateTimer.stop()
		doRestartAudio()

class AudioRestartSetup(ConfigListScreen, Screen):
	skin = """
	<screen position="center,center" size="840,600" title="Audio Restart Setup">
	  <ePixmap pixmap="~/img/button-red.png" position="0,0" zPosition="0" size="210,60" transparent="1" alphatest="on" />
	  <ePixmap pixmap="~/img/button-green.png" position="210,0" zPosition="0" size="210,60" transparent="1" alphatest="on" />
	  <ePixmap pixmap="~/img/button-yellow.png" position="420,0" zPosition="0" size="210,60" transparent="1" alphatest="on" />
	  <ePixmap pixmap="~/img/button-blue.png" position="630,0" zPosition="0" size="210,60" transparent="1" alphatest="on" />
	  <widget name="key_red" position="0,0" zPosition="1" size="210,60"
		font="Regular;30" valign="center" halign="center" backgroundColor="#9f1313" transparent="1"
		shadowColor="#000000" shadowOffset="-1,-1" />
	  <widget name="key_green" position="210,0" zPosition="1" size="210,60"
		font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1"
		shadowColor="#000000" shadowOffset="-1,-1" />
	  <widget name="key_yellow" position="420,0" zPosition="1" size="210,60"
		font="Regular;30" valign="center" halign="center" backgroundColor="#a08500" transparent="1"
		shadowColor="#000000" shadowOffset="-1,-1" />
	  <widget name="key_blue" position="630,0" zPosition="1" size="210,60"
		font="Regular;30" valign="center" halign="center" backgroundColor="#18188b" transparent="1"
		shadowColor="#000000" shadowOffset="-1,-1" />
	  <widget name="config" position="15,60" size="810,480" scrollbarMode="showOnDemand" />
	  <widget name="PluginInfo" position="15,555" size="810,30" zPosition="4" font="Regular;27" foregroundColor="#cccccc" />
	</screen>"""

	def __init__(self, session, plugin_path):
		Screen.__init__(self, session)

		# Lets get a list of elements for the config list
		self.list = [
			getConfigListEntry(_("Restart audio"), config.plugins.AudioRestart.restartSelection),
			getConfigListEntry(_("Restart audio delay (in sec)"), config.plugins.AudioRestart.restartDelay)
		]
		
		ConfigListScreen.__init__(self, self.list)

		self["config"].list = self.list

		self.skin_path = plugin_path

		# Plugin Information
		self["PluginInfo"] = Label(_("Plugin: %(plugin)s - Version: %(version)s") %dict(plugin=PLUGIN_BASE,version=PLUGIN_VERSION))

		# BUTTONS
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Restart audio now"))
		self["key_blue"] = Button()

		self["setupActions"] = NumberActionMap(["SetupActions", "ColorActions"],
		{
			"save": self.keySave,
			"cancel": self.keyCancel,
			"green": self.keySave,
			"red": self.keyCancel,
			"ok": self.keySave,
			"yellow": self.restartAudioNow,
		}, -2)

	def restartAudioNow(self):
		doRestartAudio()

def sessionstart(reason, **kwargs):
	if reason == 0:
		AudioRestart()

def setup(session, **kwargs):
	session.open(AudioRestartSetup, plugin_path)
		
def Plugins(path,**kwargs):
	global plugin_path
	plugin_path = path
	pluginList = [ PluginDescriptor(name=_("Audio restart Setup"), description=_("Setup for the AudioRestart Plugin"), icon = "AudioRestart.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=setup)]
	if config.plugins.AudioRestart.restartSelection.value != "disabled":
		pluginAutoStart = PluginDescriptor(name="Audio restart", description = _("Restart audio"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc = sessionstart)
		pluginList.append(pluginAutoStart)
	return pluginList
