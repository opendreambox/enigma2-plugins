from Plugins.Plugin import PluginDescriptor

from SatIPTunerSetup import SatIPTunerSetup

def satip_setup(session, **kwargs):
	session.open(SatIPTunerSetup)

def menu(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Sat>IP Tuner"), satip_setup, "satiptuner", 50)]
	return []

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Sat>IP Tuner"), description=_("Sat>IP Tuner Setup"), where=PluginDescriptor.WHERE_MENU, fnc=menu)
