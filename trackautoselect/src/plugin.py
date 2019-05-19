from __future__ import print_function
from Plugins.Plugin import PluginDescriptor

track_autoselect_config = None # global TrackautoselectConfig object

def config_fnc(session, **kwargs):
	from TrackAutoselectSetup import TrackAutoselectSetup
	if track_autoselect_config:
		session.open(TrackAutoselectSetup, track_autoselect_config)

def start_fnc(session, **kwargs):
	from TrackAutoselector import TrackAutoselector
	if track_autoselect_config and TrackAutoselector.instance is None:
		TrackAutoselector(session, track_autoselect_config)

def Plugins(path, **kwargs):
	try:
		from Screens.AudioSelection import AUDIO_FORMATS
		from Components.Language import language
		language.addCallback(localeAndConfigInit)
		return [PluginDescriptor(name=_("Track Autoselect"), description=_("Configure Track Autoselect"), where = PluginDescriptor.WHERE_AUDIOMENU, fnc=config_fnc),
			PluginDescriptor(name=_("Track Autoselect"), where = PluginDescriptor.WHERE_INFOBAR, fnc=start_fnc)]
	except ImportError:
		print("[TrackAutoselect] can't load plugin, needs new Enigma2 audio/subtitle API from April 2016!")
		return PluginDescriptor()

def localeAndConfigInit():
	from TrackAutoselectConfig import TrackAutoselectConfig
	global track_autoselect_config
	track_autoselect_config = TrackAutoselectConfig()

