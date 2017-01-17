# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from NetworkBrowser import NetworkBrowser
from Components.Network import iNetworkInfo
from MountManager import AutoMountManager

plugin_path = ""

def NetworkBrowserMain(session, iface = None, **kwargs):
	session.open(NetworkBrowser,iface, plugin_path)

def MountManagerMain(session, iface = None, **kwargs):
	session.open(AutoMountManager, iface, plugin_path)

def NetworkBrowserCallFunction(iface):
	interfaceState = iNetworkInfo.isConnected()
	if interfaceState is True:
		return NetworkBrowserMain
	else:
		return None

def MountManagerCallFunction(iface):
	return MountManagerMain

def menu_browser(menuid, **kwargs):
	if menuid == "network":
		return [(_("Network Browser"), NetworkBrowserMain, "nwbrowser", 10)]
	else:
		return []

def menu_manager(menuid, **kwargs):
	if menuid == "network":
		return [(_("Mount Manager"), MountManagerMain, "nwmntmng", 11)]
	else:
		return []

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return [
		PluginDescriptor(name=_("NetworkBrowser"), description=_("Browse network shares..."), where=PluginDescriptor.WHERE_MENU, fnc=menu_browser),
		PluginDescriptor(name=_("Mount Manager"), description=_("Manage network mounts..."), where=PluginDescriptor.WHERE_MENU, fnc=menu_manager),
	]

