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

from enigma import eTimer

# Config
from Components.config import *

# Plugin internal
from ExtensionHandler import addExtension, removeExtension


# Globals
InfoBarShow = None
InfoBarHide = None
InfoBarToggle = None


#######################################################
# InfoBarShowHide for MoviePlayer integration
def overwriteInfoBar():
	from Screens.InfoBarGenerics import InfoBarShowHide
	global InfoBarShow, InfoBarHide, InfoBarToggle
	if config.infobartunerstate.show_infobar.value:
		if InfoBarShow is None:
			# Backup original function
			InfoBarShow = InfoBarShowHide._InfoBarShowHide__onShow
			# Overwrite function
			InfoBarShowHide._InfoBarShowHide__onShow = InfoBarShowTunerState
	if InfoBarHide is None:
		# Backup original function
		InfoBarHide = InfoBarShowHide._InfoBarShowHide__onHide
		# Overwrite function
		InfoBarShowHide._InfoBarShowHide__onHide = InfoBarHideTunerState
	if config.infobartunerstate.show_ontoggle.value:
		if InfoBarToggle is None:
			# Backup original function
			InfoBarToggle = InfoBarShowHide.toggleShow
			# Overwrite function
			InfoBarShowHide.toggleShow = InfoBarToggleTunerState

# InfoBar Events
def recoverInfoBar():
	from Screens.InfoBarGenerics import InfoBarShowHide
	global InfoBarShow, InfoBarHide, InfoBarToggle
	if InfoBarShow:
		InfoBarShowHide._InfoBarShowHide__onShow = InfoBarShow
		InfoBarShow = None
	if InfoBarHide:
		InfoBarShowHide._InfoBarShowHide__onHide = InfoBarHide
		InfoBarHide = None
	if InfoBarToggle:
		InfoBarShowHide.toggleShow = InfoBarToggle
		InfoBarToggle = None


def InfoBarShowTunerState(self):
	from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
	global InfoBarShow
	if InfoBarShow:
		InfoBarShow(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.show()

def InfoBarHideTunerState(self):
	from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
	global InfoBarHide
	if InfoBarHide:
		InfoBarHide(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.hide()

def InfoBarToggleTunerState(self):
	from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
	global InfoBarToggle
	if InfoBarToggle:
		InfoBarToggle(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.toggle()


class InfoBarHandler(object):
	def __init__(self):
		
		self.infobar = None
		
		self.forceBindInfoBarTimer = eTimer()
		try:
			self.forceBindInfoBarTimer_conn = self.forceBindInfoBarTimer.timeout.connect(self.bindInfoBar)
		except:
			self.forceBindInfoBarTimer.callback.append(self.bindInfoBar)
		
		# Bind InfoBarEvents
		#self.bindInfoBar()
		#self.onLayoutFinish.append(self.bindInfoBar)
		# Workaround
		# The Plugin starts before the InfoBar is instantiated
		# Check every second if the InfoBar instance exists and try to bind our functions
		# Is there an alternative solution?
		if config.infobartunerstate.show_infobar.value:
			self.forceBindInfoBarTimer.start(1000, False)
		
		if config.infobartunerstate.show_overwrite.value:
			overwriteInfoBar()
		
		# Handle extension menu integration
		if config.infobartunerstate.extensions_menu_show.value or config.infobartunerstate.extensions_menu_setup.value:
			# Add to extension menu
			addExtension()
		else:
			# Remove from extension menu
			removeExtension()

	def bindInfoBar(self):
		# Reimport InfoBar to force update of the class instance variable
		# Rebind only if it isn't done already 
		from Screens.InfoBar import InfoBar
		if InfoBar.instance:
			self.infobar = InfoBar.instance
			bindShow = False
			bindHide = False
			if hasattr(InfoBar.instance, "onShow"):
				if self.__onInfoBarEventShow not in InfoBar.instance.onShow:
					InfoBar.instance.onShow.append(self.__onInfoBarEventShow)
				bindShow = True
			if hasattr(InfoBar.instance, "onHide"):
				if self.__onInfoBarEventHide not in InfoBar.instance.onHide:
					InfoBar.instance.onHide.append(self.__onInfoBarEventHide)
				bindHide = True
			if bindShow and bindHide:
				# Bind was successful
				self.forceBindInfoBarTimer.stop()

	def unbindInfoBar(self):
		if self.infobar:
			if hasattr(self.infobar, "onShow"):
				if self.__onInfoBarEventShow in self.infobar.onShow:
					self.infobar.onShow.remove(self.__onInfoBarEventShow)
			if hasattr(self.infobar, "onHide"):
				if self.__onInfoBarEventHide in self.infobar.onHide:
					self.infobar.onHide.remove(self.__onInfoBarEventHide)

	def __onInfoBarEventShow(self):
		self.show()

	def __onInfoBarEventHide(self):
		self.hide()
