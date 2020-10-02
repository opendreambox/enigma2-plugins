from __future__ import absolute_import

from enigma import getExitCode
from Components.config import config
from Plugins.Plugin import PluginDescriptor

from .Cec import Cec, cec
from .CecConfig import CecConfig

def start(reason, session):
	cec.start(session)

def autostart(reason):
	code = getExitCode()
	if reason is 1 and code is 1:
		cec.powerOff()

def conf(session, **kwargs):
	session.open(CecConfig)

def menu(menuid, **kwargs):
	if menuid == "devices":
		return [(_("HDMI CEC 2.0"), conf, "hdmi_cec_v2", 40)]
	else:
		return []

def Plugins(**kwargs):
	return [
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART] , fnc = start, weight=100),
		PluginDescriptor(where = [PluginDescriptor.WHERE_AUTOSTART] , fnc = autostart, weight=100),
		PluginDescriptor(name = "HDMI CEC 2.0", description = "Configure HDMI CEC 2.0", where = PluginDescriptor.WHERE_MENU, needsRestart = True, fnc = menu)
		]