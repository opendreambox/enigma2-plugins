# -*- coding: utf-8 -*-from
# by betonme @2015

import pprint

from time import time

# Config
from Components.config import *

# Plugin internal
from Plugins.Extensions.InfoBarTunerState.__init__ import _
from Plugins.Extensions.InfoBarTunerState.PluginBase import PluginBase
from Plugins.Extensions.InfoBarTunerState.Helper import getTunerByPlayableService, getNumber, getChannel


# Config options
config.infobartunerstate.plugin_timers         = ConfigSubsection()
config.infobartunerstate.plugin_timers.enabled = ConfigYesNo(default = True)
config.infobartunerstate.plugin_timers.number_pending_timers     = ConfigSelectionNumber(0, 10, 1, default = 1)
config.infobartunerstate.plugin_timers.pending_hours             = ConfigSelectionNumber(0, 1000, 1, default = 0)


def getTimer(id):
	from NavigationInstance import instance
	if instance is not None:
		for timer in instance.RecordTimer.timer_list + instance.RecordTimer.processed_timers:
			#print "timerlist:", getTimerID( timer )
			if getTimerID( timer ) == id:
				return timer
	return None

def getTimerID(timer):
	#return str( timer.name ) + str( timer.repeatedbegindate ) + str( timer.service_ref ) + str( timer.justplay )
	return "next_"+str( timer )

def getNextPendingRecordTimers(pending_limit):
	from NavigationInstance import instance
	timer_list = []
	if instance is not None:
		now = time()
		for timer in instance.RecordTimer.timer_list:
			next_act = timer.getNextActivation()
			if timer.justplay:
				continue
			if timer.isRunning() and not timer.repeated:
				continue
			if next_act < now:
				continue
			if pending_limit and pending_limit < timer.begin:
				continue
			if timer.begin:
				if not timer.isRunning():
					begin = timer.begin
					end = timer.end
				else:
					begin, end = processRepeated(timer)
				timer_list.append( timer )
	return sorted( timer_list, key=lambda x: (x.begin) )

# Adapted from TimerEntry
def addOneDay(timedatestruct):
	oldHour = timedatestruct.tm_hour
	newdate =  (datetime(timedatestruct.tm_year, timedatestruct.tm_mon, timedatestruct.tm_mday, timedatestruct.tm_hour, timedatestruct.tm_min, timedatestruct.tm_sec) + timedelta(days=1)).timetuple()
	if localtime(mktime(newdate)).tm_hour != oldHour:
		return (datetime(timedatestruct.tm_year, timedatestruct.tm_mon, timedatestruct.tm_mday, timedatestruct.tm_hour, timedatestruct.tm_min, timedatestruct.tm_sec) + timedelta(days=2)).timetuple()
	return newdate

def processRepeated(timer, findRunningEvent = False):
	begin = timer.begin
	end = timer.end
		
	if (timer.repeated != 0):
		now = int(time()) + 1

		#to avoid problems with daylight saving, we need to calculate with localtime, in struct_time representation
		localrepeatedbegindate = localtime(timer.repeatedbegindate)
		localbegin = localtime(begin)
		localend = localtime(end)
		localnow = localtime(now)

		day = []
		flags = timer.repeated
		for x in (0, 1, 2, 3, 4, 5, 6):
			if (flags & 1 == 1):
				day.append(0)
				print "Day: " + str(x)
			else:
				day.append(1)
			flags = flags >> 1

		# if day is NOT in the list of repeated days
		# OR if the day IS in the list of the repeated days, check, if event is currently running... then if findRunningEvent is false, go to the next event
		while ((day[localbegin.tm_wday] != 0) or (mktime(localrepeatedbegindate) > mktime(localbegin))  or
			((day[localbegin.tm_wday] == 0) and ((findRunningEvent and localend < localnow) or ((not findRunningEvent) and localbegin < localnow)))):
			localbegin = addOneDay(localbegin)
			localend = addOneDay(localend)
			
		#we now have a struct_time representation of begin and end in localtime, but we have to calculate back to (gmt) seconds since epoch
		begin = int(mktime(localbegin))
		end = int(mktime(localend))
		if begin == end:
			end += 1
	
	return begin, end


class Timers(PluginBase):
	def __init__(self):
		PluginBase.__init__(self)
		self.nextids = []

	################################################
	# To be implemented by subclass
	def getText(self):
		return "Timer"

	def getType(self):
		from Plugins.Extensions.InfoBarTunerState.InfoBarTunerState import TIMER
		return TIMER

	def getOptions(self):
		return [
					(_("Show pending timer(s)"),                      config.infobartunerstate.plugin_timers.enabled),
					(_("Number of pending timer(s)"),                 config.infobartunerstate.plugin_timers.number_pending_timers),
					(_("Show pending records only within x hour(s)"), config.infobartunerstate.plugin_timers.pending_hours),
				]

	def onShow(self, tunerstates):
		if config.infobartunerstate.plugin_timers.enabled.value:
			number_pending_timers = int( config.infobartunerstate.plugin_timers.number_pending_timers.value )
			#print "IBTS number_pending_timers", number_pending_timers
			
			toremove = self.nextids[:]
			
			if number_pending_timers:
				pending_seconds = int( config.infobartunerstate.plugin_timers.pending_hours.value ) * 3600
				pending_limit = (time() + pending_seconds) if pending_seconds else 0
				#print "IBTS pending_limit", pending_limit
				
				timer_list = getNextPendingRecordTimers(pending_limit)[:number_pending_timers]
				#pprint.pprint(timer_list)
				
				if timer_list:
					
					timer_list.reverse()
					
					for i, timer in enumerate(timer_list):
						
						if timer:
							
							id = getTimerID( timer )
							#print "IBTS toadd", id
							
							# Only add timer if not recording
							from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
							if gInfoBarTunerState.hasEntry(id):
								
								# Delete references to avoid blocking tuners
								del timer
								
							else:
							
								name = timer.name
								servicereference = timer.service_ref
								
								# Is this really necessary?
								try: timer.Filename
								except: timer.calculateFilename()
								
								try: filename = timer.Filename
								except: filename = timer.name
								
								begin = timer.begin
								end = timer.end
								endless = timer.autoincrease
								
								# Delete references to avoid blocking tuners
								del timer
								
								number = getNumber(servicereference.ref)
								channel = getChannel(servicereference.ref)
								
								self.nextids.append(id)
								gInfoBarTunerState.addEntry(id, self.getPluginName(), self.getType(), self.getText(), "", "", None, name, number, channel, begin, end, endless, filename)
							
							if id in toremove:
								toremove.remove(id)
				
				# Close all not touched next timers
				if toremove:
					from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
					#print "IBTS toremove"
					#pprint.pprint(toremove)
					for id in toremove:
						#print "IBTS toremove", id
						if id in self.nextids:
							self.nextids.remove(id)
						gInfoBarTunerState.removeEntry(id)

	def update(self, id, tunerstate):
		
		#print "IBTS Timers update ID", id
		
		if id in self.nextids:
			
			timer = getTimer( id )
			if timer:
				
				tunerstate.name = timer.name
				
				tunerstate.begin = timer.begin
				tunerstate.end = timer.end
				tunerstate.endless = timer.autoincrease
				
				servicereference = timer.service_ref
				
				del timer
				
				if not tunerstate.number:
					tunerstate.number = getNumber(servicereference.ref)
				if not tunerstate.channel:
					tunerstate.channel = getChannel(servicereference.ref)
				
				return True
			else:
				return None
		else:
			return None
