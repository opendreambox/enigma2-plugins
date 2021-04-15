# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor


def main(session, **kwargs):
	from eparted import Ceparted
	session.open(Ceparted)


def Plugins(**kwargs):
	return [PluginDescriptor(name="eParted", description=_("creating and manipulating partition tables"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="eparted.png"), PluginDescriptor(name="eParted", description=_("creating and manipulating partition tables"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]
