from enigma import eServiceReference
from Plugins.Plugin import PluginDescriptor
from Tools.Log import Log

from ChannelListTubeServiceHelper import ChannelListTubeServiceHelper

try:
	from enigma import eUriResolver
	#YouTube
	from youtube.YoutubeUriResolver import YoutubeUriResolver
	YoutubeUriResolver.instance = YoutubeUriResolver()
	eUriResolver.addResolver(YoutubeUriResolver.instance)
	#twitch.tv
	from twitch.TwitchUriResolver import TwitchUriResolver
	TwitchUriResolver.instance = TwitchUriResolver()
	eUriResolver.addResolver(TwitchUriResolver.instance)
except ImportError as e:
	Log.w(e)

def isBouquetAndOrRoot(csel):
	if csel.movemode:
		return (False, False)
	inBouquet = csel.getMutableList() is not None
	current_root = csel.getRoot()
	current_root_path = current_root and current_root.getPath()
	inBouquetRootList = current_root_path and current_root_path.find('FROM BOUQUET "bouquets.') != -1 #FIXME HACK
	Log.w("inBouquet: %s, current_root_path %s, inBouquetRootList %s" %(inBouquet, current_root_path, inBouquetRootList))
	return (inBouquet, inBouquetRootList)

def check_channel(csel):
	inBouquet, inBouquetRootList = isBouquetAndOrRoot(csel)
	return inBouquet and not inBouquetRootList

def main_channellist(session, ref, csel, **kwargs):
	Log.i(kwargs)
	if ref:
		ChannelListTubeServiceHelper(session, csel, onChannelSelected)

def onChannelSelected(csel, data, bouquetName=None):
	if not csel or not data:
		return
	if bouquetName:
		csel.addBouquet(bouquetName, data)
		return
	if csel.inBouquet() and data:
		if isinstance(data, eServiceReference):
			csel.addServiceToBouquet(csel.getRoot(), service=data)

def Plugins(path, **kwargs):
	return [
		PluginDescriptor(
			name=_("Add Live-Streaming Channel"),
			description=_("Add Live-Streaming Channel"),
			where = PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU,
			fnc=main_channellist,
			helperfnc=check_channel,
			icon="plugin.png"),
		]