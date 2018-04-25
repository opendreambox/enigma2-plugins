#######################################################################
#
#  MerlinSkinThemes for Dreambox/Enigma-2
#  Modul PluginStart
#  Coded by marthom (c)2012 - 2016
#
#  Support: www.dreambox-tools.info
#  E-Mail: marthom@dreambox-tools.info
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Multimedia GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Multimedia GmbH.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep MY license and inform me about the modifications by mail.
#
#######################################################################

from Plugins.Plugin import PluginDescriptor
from Components.config import config

import MerlinSkinThemes

def merlinskinthemes_start(session, **kwargs):

	# old versions clear
	config.plugins.MerlinSkinThemes.Skin.cancel()
	config.plugins.MerlinSkinThemes.ColorTheme.cancel()
	config.plugins.MerlinSkinThemes.FontTheme.cancel()
	config.plugins.MerlinSkinThemes.BorderSetTheme.cancel()
	config.plugins.MerlinSkinThemes.InfoBar.cancel()
	config.plugins.MerlinSkinThemes.ChannelSelection.cancel()
	config.plugins.MerlinSkinThemes.MovieSelection.cancel()
	config.plugins.MerlinSkinThemes.SecondInfoBar.cancel()
	config.plugins.MerlinSkinThemes.MessageBox.cancel()
	config.plugins.MerlinSkinThemes.InputBox.cancel()

	reload(MerlinSkinThemes)
	session.open(MerlinSkinThemes.MerlinSkinThemes)

def Plugins(**kwargs):
	return [
		PluginDescriptor(name="MerlinSkinThemes", description="MerlinSkinThemes",where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", fnc=merlinskinthemes_start),
		PluginDescriptor(name="MerlinSkinThemes", description="MerlinSkinThemes", where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=merlinskinthemes_start)
	]