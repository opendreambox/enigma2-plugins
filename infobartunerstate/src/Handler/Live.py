# -*- coding: utf-8 -*-from
# by betonme @2015

from time import time
from enigma import iPlayableService
from ServiceReference import ServiceReference

# Config
from Components.config import *

# Plugin internal
from Plugins.Extensions.InfoBarTunerState.__init__ import _
from Plugins.Extensions.InfoBarTunerState.PluginBase import PluginBase
from Plugins.Extensions.InfoBarTunerState.Helper import getTunerByPlayableService, getNumber, getChannel, getEventData


# Config options
config.infobartunerstate.plugin_live         = ConfigSubsection()
config.infobartunerstate.plugin_live.enabled = ConfigYesNo(default = False)


class Live(PluginBase):
	def __init__(self):
		PluginBase.__init__(self)
		self.tunerstate = None
		self.eservicereference_string = ""

	################################################
	# To be implemented by subclass
	def getText(self):
		return "Live"

	def getType(self):
		from Plugins.Extensions.InfoBarTunerState.InfoBarTunerState import LIVE
		return LIVE

	def getOptions(self):
		return [(_("Show live tuner"), config.infobartunerstate.plugin_live.enabled),]

	def appendEvent(self):
		if config.infobartunerstate.plugin_live.enabled.value:
			from NavigationInstance import instance
			if instance is not None:
				if self.onEvent not in instance.event:
					instance.event.append(self.onEvent)

	def removeEvent(self):
		from NavigationInstance import instance
		if instance is not None:
			# Recording Events
			# If we append our function, we will never see the timer state StateEnded for repeating timer
			if self.onEvent in instance.event:
				instance.event.remove(self.onEvent)

	def onInit(self):
		if config.infobartunerstate.plugin_live.enabled.value:
			from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
			if gInfoBarTunerState:
				
				self.tunerstate = gInfoBarTunerState.addEntry("Live", self.getPluginName(), self.getType(), self.getText())

	def onEvent(self, ev):
		#print "IBTS Live onEvent ev", ev, str(self.tunerstate)
		if ev == iPlayableService.evUpdatedEventInfo or ev == iPlayableService.evUpdatedInfo:
			
			if self.tunerstate:
				tunerstate = self.tunerstate
				
				from NavigationInstance import instance
				if instance:
					
					changed = False
					
					eservicereference = instance.getCurrentlyPlayingServiceReference()
					eservicereference_string = str(eservicereference)
					
					# Avoid recalculations
					if self.eservicereference_string != eservicereference_string:
						tunerstate.number = None
						tunerstate.channel = ""
						
						tunerstate.tuner, tunerstate.tunertype, tunerstate.tunernumber = "", "", None
						tunerstate.name, tunerstate.begin, tunerstate.end = "", 0, 0
						
						self.eservicereference_string = eservicereference_string
						
					if not tunerstate.number:
						tunerstate.number = getNumber(eservicereference)
						changed = True
					if not tunerstate.channel:
						tunerstate.channel = getChannel(eservicereference)
						changed = True
						
					iplayableservice = instance.getCurrentService()
					
					if not tunerstate.tuner or not tunerstate.tunertype or not tunerstate.tunernumber:
						tunerstate.tuner, tunerstate.tunertype, tunerstate.tunernumber = getTunerByPlayableService(iplayableservice)
						changed = True
					
					if not tunerstate.name or not tunerstate.begin or not tunerstate.end:
						tunerstate.name, tunerstate.begin, tunerstate.end = getEventData(iplayableservice)
						changed = True
					
					if changed:
						from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
						gInfoBarTunerState.updateMetrics()
