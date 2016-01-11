#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Coded by betonme (c) 2011 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=162629
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

# Config
from Components.config import *

from Plugins.Plugin import PluginDescriptor

# Globals
InfoBarShow = None
InfoBarHide = None
InfoBarToggle = None


#######################################################
# Extension menu
def addExtension():
	# Add to extension menu
	from Components.PluginComponent import plugins
	from Plugins.Extensions.InfoBarTunerState.plugin import IBTSSHOW, IBTSSETUP, show, setup
	if plugins:
		if config.infobartunerstate.extensions_menu_show.value:
			for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
				if p.name == IBTSSHOW:
					# Plugin is already in menu
					break
			else:
				# Plugin not in menu - add it
				plugin = PluginDescriptor(name = IBTSSHOW, description = IBTSSHOW, where = PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart = False, fnc = show)
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].append(plugin)
		if config.infobartunerstate.extensions_menu_setup.value:
			for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
				if p.name == IBTSSETUP:
					# Plugin is already in menu
					break
			else:
				# Plugin not in menu - add it
				plugin = PluginDescriptor(name = IBTSSETUP, description = IBTSSETUP, where = PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart = False, fnc = setup)
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].append(plugin)

def removeExtension():
	# Remove from extension menu
	from Components.PluginComponent import plugins
	from Plugins.Extensions.InfoBarTunerState.plugin import IBTSSHOW, IBTSSETUP
	if config.infobartunerstate.extensions_menu_show.value:
		for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
			if p.name == IBTSSHOW:
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].remove(p)
				break
	if config.infobartunerstate.extensions_menu_setup.value:
		for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
			if p.name == IBTSSETUP:
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].remove(p)
				break
