# -*- coding: utf-8 -*-from
# by betonme @2015

from time import time

# Config
from Components.config import *

from enigma import eEPGCache

# Plugin internal
from Plugins.Extensions.InfoBarTunerState.__init__ import _
from Plugins.Extensions.InfoBarTunerState.PluginBase import PluginBase
from Plugins.Extensions.InfoBarTunerState.Helper import getTunerByPlayableService, getNumber, getChannel


# Config options
config.infobartunerstate.plugin_records         = ConfigSubsection()
config.infobartunerstate.plugin_records.enabled = ConfigYesNo(default = True)


def getTimerID(timer):
	#return str( timer.name ) + str( timer.repeatedbegindate ) + str( timer.service_ref ) + str( timer.justplay )
	return str( timer )

def getTimer(id):
	from NavigationInstance import instance
	if instance is not None:
		for timer in instance.RecordTimer.timer_list:
			#print "timerlist:", getTimerID( timer )
			if getTimerID( timer ) == id:
				return timer
	return None

def getProcessedTimer(id):
	from NavigationInstance import instance
	if instance is not None:
		for timer in instance.RecordTimer.processed_timers:
			#print "timerlist:", getTimerID( timer )
			if getTimerID( timer ) == id:
				return timer
	return None

class Records(PluginBase):
	def __init__(self):
		PluginBase.__init__(self)

	################################################
	# To be implemented by subclass
	def getText(self):
		return "Record"

	def getType(self):
		from Plugins.Extensions.InfoBarTunerState.InfoBarTunerState import INFO, RECORD, STREAM, FINISHED
		return RECORD

	def getOptions(self):
		return [(_("Show record(s)"), config.infobartunerstate.plugin_records.enabled),]

	def appendEvent(self):
		if config.infobartunerstate.plugin_records.enabled.value:
			from NavigationInstance import instance
			if instance is not None:
				# Recording Events
				# If we append our function, we will never see the timer state StateEnded for repeating timer
				if self.onEvent not in instance.RecordTimer.on_state_change:
					instance.RecordTimer.on_state_change.insert(0, self.onEvent)

	def removeEvent(self):
		from NavigationInstance import instance
		if instance is not None:
			# Recording Events
			# If we append our function, we will never see the timer state StateEnded for repeating timer
			if self.onEvent in instance.RecordTimer.on_state_change:
				instance.RecordTimer.on_state_change.remove(self.onEvent)

	def onInit(self):
		if config.infobartunerstate.plugin_records.enabled.value:
			from NavigationInstance import instance
			if instance is not None:
				for timer in instance.RecordTimer.timer_list:
					if timer.isRunning() and not timer.justplay:
						self.onEvent(timer)

	def onEvent(self, timer):
		if not timer.justplay:
			#print "IBTS Timer Event "+ str(timer.state) + ' ' + str(timer.repeated)
			#TODO
			# w.processRepeated()
			# w.state = TimerEntry.StateWaiting
			if timer.state == timer.StatePrepared:
				print "IBTS Records StatePrepared"
				pass
			
			elif timer.state == timer.StateRunning:
				id = getTimerID( timer )
				print "IBTS Records StateRunning ID " + id
				
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				if gInfoBarTunerState and not gInfoBarTunerState.hasEntry(id):
					
					#TEST Bug Repeating timer blocking tuner and are not marked as finished
					#timer.timeChanged = self.__OnTimeChanged
					
					name = timer.name
					
					begin = timer.begin
					end = timer.end
					endless = timer.autoincrease
					
					# Is this really necessary?
					try: timer.Filename
					except: timer.calculateFilename()
					filename = timer.Filename
					
					irecordservice = timer.record_service
					servicereference = timer.service_ref
					
					# Delete references to avoid blocking tuners
					del timer
					
					tuner, tunertype, tunernumber = getTunerByPlayableService(irecordservice)
					
					number = getNumber(servicereference.ref)
					channel = getChannel(servicereference.ref)
					
					gInfoBarTunerState.addEntry(id, self.getPluginName(), self.getType(), self.getText(), tuner, tunertype, tunernumber, name, number, channel, begin, end, endless, filename)
					gInfoBarTunerState.onEvent()
			
			# Finished repeating timer will report the state StateEnded+1 or StateWaiting
			else:
				id = getTimerID( timer )
				print "IBTS Records StateEnded ID " + id
				
				# Delete references to avoid blocking tuners
				del timer
				
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				if gInfoBarTunerState:
					gInfoBarTunerState.finishEntry(id)
					gInfoBarTunerState.onEvent()

	def update(self, id, tunerstate):
		
		#TODO Avolid blocking - avoid using getTimer to update the timer times use timer.time_changed if possible
		
		timer = getTimer( id )
		if timer:
			tunerstate.name = timer.name
			
			tunerstate.begin = timer.begin
			tunerstate.end = timer.end
			
			if hasattr(timer, 'vpsplugin_enabled') and timer.vpsplugin_enabled:
			#and hasattr(timer, 'vpsplugin_overwrite') and timer.vpsplugin_overwrite:
				tunerstate.endless = False
				epgcache = eEPGCache.getInstance()
				
				if timer.eit:
					print "IBTS Records event by lookupEventId"
					event = epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
				
				if not event:
					print "IBTS Records event by lookupEventTime"
					event = epgcache.lookupEventTime( timer.service_ref.ref, timer.begin + 5 );
				
				if event:
					print "IBTS Records event"
					begin = event.getBeginTime() or 0
					duration = event.getDuration() or 0
					tunerstate.end  = begin + duration
					
					if not tunerstate.end:
						print "IBTS Records no end"
						tunerstate.endless = True
				else:
					tunerstate.endless = timer.autoincrease
			else:
				tunerstate.endless = timer.autoincrease
			
			irecordservice = timer.record_service
			servicereference = timer.service_ref
			
			# Delete references to avoid blocking tuners
			del timer
			
			if not tunerstate.tuner or not tunerstate.tunertype or not tunerstate.tunernumber:
				tunerstate.tuner, tunerstate.tunertype, tunerstate.tunernumber = getTunerByPlayableService(irecordservice)
			
			if not tunerstate.number:
				tunerstate.number = getNumber(servicereference.ref)
			if not tunerstate.channel:
				tunerstate.channel = getChannel(servicereference.ref)
			
			return True
		
		else:
			# This can happen, if the time has been changed or if the timer does not exist anymore
			
			self.onInit()
			
			return False
