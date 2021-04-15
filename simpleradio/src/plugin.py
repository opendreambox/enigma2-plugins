from __future__ import absolute_import

from Plugins.Plugin import PluginDescriptor
from .RadioScreen import RadioScreen


def main(session, **kwargs):
	session.open(RadioScreen)


def menu(menuid):
	if menuid != "mainmenu":
		return []
	return [(_("Simple Radio"), main, "radio_listen", None)]


def Plugins(**kwargs):
	return [PluginDescriptor(
			name=_("Simple Radio"),
			description=_("Simply listen to internet radio"),
			where=PluginDescriptor.WHERE_MENU,
			fnc=menu,
			needsRestart=False,
		),
	]
