#######################################################################
#
#  MerlinSkinThemes for Dreambox/Enigma2
#  Modul PluginStart
#  Coded by marthom/dre (c)2012 - 2021
#
#  Support: www.dreamboxtools.de
#  E-Mail: marthom@dreamboxtools.de / dre@dreamboxtools.de
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep MY license and inform me about the modifications by mail.
#
#######################################################################
from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigNumber, ConfigText, ConfigInteger, ConfigSubDict, ConfigBoolean
from Screens.MessageBox import MessageBox
from Tools import Notifications
from Tools.Directories import resolveFilename, SCOPE_SKIN, fileExists
from Tools.HardwareInfo import HardwareInfo
from enigma import quitMainloop
import xml.etree.cElementTree as Tree

import MerlinSkinThemes

CONFDIR = "/etc/enigma2/merlinskinthemes/"

try:
        Notifications.notificationQueue.registerDomain("MerlinSkinThemes", _("MerlinSkinThemes"), deferred_callable=True)
except Exception as e:
        print("[MST] - Error registering Notification-Domain: ", e)


def merlinskinthemes_start(session, **kwargs):
	reload(MerlinSkinThemes)
	session.open(MerlinSkinThemes.MerlinSkinThemes)


def checkSkin(session, **kwargs):
	if config.plugins.MerlinSkinThemes3.rebuildSkinOnBoot.value:

		# a config exists for the currently active skin
		if fileExists(CONFDIR + config.skin.primary_skin.value[:-9] + ".cfg"):
			print("[MST] - config found for active skin")
			skinFile = resolveFilename(SCOPE_SKIN) + config.skin.primary_skin.value
			if fileExists(skinFile):
				xmlFile = Tree.ElementTree(file=skinFile)
				root = xmlFile.getroot()

				mst = root.find("merlinskinthemes")
				if mst is not None:
					print("[MST] - skin was edited with MST and tag is present - assume rebuild is not required")
				else:
					print("[MST] - skin was edited with MST but tag is not present - assume rebuild required")
					configDictFile = CONFDIR + config.skin.primary_skin.value[:-9] + ".cfg"

					if fileExists(resolveFilename(SCOPE_SKIN) + config.skin.primary_skin.value[:-9] + "/themes.xml"):
						# update skin with data from config
						retValue = MerlinSkinThemes.setThemes(resolveFilename(SCOPE_SKIN) + config.skin.primary_skin.value[:-9] + "/themes.xml", resolveFilename(SCOPE_SKIN) + config.skin.primary_skin.value, configDictFile)
						showMessage(retValue)
					else:
						print("[MST] - themes.xml not found")
						Notifications.AddNotification(MessageBox, _("Skin could not be rebuilt due to missing themes.xml"), MessageBox.TYPE_ERROR, 10, windowTitle="MerlinSkinThemes", domain="MerlinSkinThemes")


def showMessage(retValue=None):
	if retValue == False:
		Notifications.AddNotification(MessageBox, _("Skin could not be rebuilt due to unsupported version of theme"), MessageBox.TYPE_ERROR, 10, windowTitle="MerlinSkinThemes", domain="MerlinSkinThemes")
	else:
		Notifications.AddNotificationWithCallback(messageBoxCallback, MessageBox, _("Skin was rebuilt and a restart of enigma2 is required. Do you want to restart now?"), MessageBox.TYPE_YESNO, 10, windowTitle="MerlinSkinThemes", domain="MerlinSkinThemes")


def messageBoxCallback(answer=False):
	if answer == True:
		quitMainloop(3)


def Plugins(**kwargs):
	return [
		PluginDescriptor(name="MerlinSkinThemes", description="MerlinSkinThemes", where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=merlinskinthemes_start),
		PluginDescriptor(name="MerlinSkinThemes", description="MerlinSkinThemes", where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=merlinskinthemes_start),
		PluginDescriptor(where=[PluginDescriptor.WHERE_INFOBAR], fnc=checkSkin)
	]
