# -*- coding: utf-8 -*-from
# by betonme @2015

from time import time
from ServiceReference import ServiceReference
from enigma import eDVBResourceManager

# Config
from Components.config import *

# Plugin internal
from Plugins.Extensions.InfoBarTunerState.__init__ import _
from Plugins.Extensions.InfoBarTunerState.PluginBase import PluginBase
from Plugins.Extensions.InfoBarTunerState.Helper import getTunerByPlayableService, getNumber, getChannel, getEventData, getTunerName


# Config options
config.infobartunerstate.plugin_unknown         = ConfigSubsection()
config.infobartunerstate.plugin_unknown.enabled = ConfigYesNo(default = False)


class Unknown(PluginBase):
	def __init__(self):
		PluginBase.__init__(self)
		self.conn = None
		self.mask = 0
		self.tuners = []
		self.tunerstates = []

	################################################
	# To be implemented by subclass
	def getText(self):
		return "Unknown"

	def getType(self):
		from Plugins.Extensions.InfoBarTunerState.InfoBarTunerState import UNKNOWN
		return UNKNOWN

	def getOptions(self):
		return [(_("Show undefined service(s)"), config.infobartunerstate.plugin_unknown.enabled),]

	def appendEvent(self):
		if config.infobartunerstate.plugin_unknown.enabled.value:
			res_mgr = eDVBResourceManager.getInstance()
			if res_mgr:
				try:
					# OE2.2
					self.conn = res_mgr.frontendUseMaskChanged.connect(self.onEvent)
				except:
					try:
						# OE2.0
						res_mgr.frontendUseMaskChanged.get().append(self.onEvent)
					except:
						pass

	def removeEvent(self):
		if self.conn:
			self.conn = None
		else:
			try:
				# OE2.0
				res_mgr.frontendUseMaskChanged.get().remove(self.onEvent)
			except:
				pass

	def onInit(self):
		if config.infobartunerstate.plugin_unknown.enabled.value:
			from NavigationInstance import instance
			if instance is not None:
				for timer in instance.RecordTimer.timer_list:
					if timer.isRunning() and not timer.justplay:
						self.onEvent(timer)

	def onEvent(self, mask):
		self.mask = mask
		self.tuners = []
		
		bit = 1;
		for tunernumber in range(8):
			#print "IBTS UNKNOWN ", tunernumber, bit, bool(mask & bit)
			if bool(mask & bit):
				#print "IBTS UNKNOWN append tuner", tunernumber
				self.tuners.append(tunernumber)
			bit = bit << 1
		
		# Remove live tuner
		if self.tuners:
			from NavigationInstance import instance
			iplayableservice = instance and instance.getCurrentService()
			if iplayableservice:
				tuner, tunertype, tunernumber = getTunerByPlayableService(iplayableservice)
				#print "IBTS UNKNOWN live tuner", tunernumber
				if tunernumber in self.tuners:
					#print "IBTS UNKNOWN remove tuner", tunernumber
					self.tuners.remove(tunernumber)
				else:
					del self.tuners[-1]
		
		if config.infobartunerstate.show_events.value:
			from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
			gInfoBarTunerState.onEvent()

	def onShow(self, tunerstates):
		if config.infobartunerstate.plugin_unknown.enabled.value:
			toadd = self.tuners[:]
			for id, tunerstate in tunerstates.items():
				if tunerstate.plugin == "Record" or tunerstate.plugin == "Stream":
					if tunerstate.tunernumber in toadd:
						#print "IBTS UNKNOWN toadd remove", tunerstate.tunernumber
						toadd.remove(tunerstate.tunernumber)
			
			# Check if we have to add an entry
			if toadd:
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				for tunernumber in toadd:
					
					id = "Unknown"+str(tunernumber)
					if gInfoBarTunerState and not gInfoBarTunerState.hasEntry(id):
						
						tuner = getTunerName(tunernumber)
						
						#print "IBTS UNKNOWN append ", tunernumber
						self.tunerstates.append(tunernumber)
						
						gInfoBarTunerState.addEntry(id, self.getPluginName(), self.getType(), self.getText(), tuner, tuner, tunernumber, _("Used by unknown service"), "-", "-", time() )
			
			# Check if we have to remove an entry
			if self.tunerstates:
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				
				for tunernumber in self.tunerstates:
				
					if tunernumber not in self.tuners:
						id = "Unknown"+str(tunernumber)
						
						#print "IBTS UNKNOWN remove ", tunernumber
						self.tunerstates.remove(tunernumber)
						
						gInfoBarTunerState.finishEntry(id)
