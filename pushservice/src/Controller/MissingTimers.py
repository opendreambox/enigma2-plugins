#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
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
from Components.config import ConfigYesNo, NoSave

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ControllerBase import ControllerBase

# Plugin specific
import NavigationInstance
from time import localtime, strftime, mktime
from datetime import date, timedelta

# Constants
SUBJECT = _("Missing timer")
BODY    = _("There are no timer for tomorrow - %s")


class MissingTimers(ControllerBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		ControllerBase.__init__(self)

	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		timers = 0
		tomorrow_begin = mktime( ( date.today() + timedelta(days=1) ).timetuple() )
		tomorrow_end   = tomorrow_begin + 24*60*60
		
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			if not timer.disabled:
				timer_begin = timer.begin
				if tomorrow_begin <= timer_begin <= tomorrow_end:
					timers += 1
				
		if timers == 0:
			callback( SUBJECT, BODY % strftime(_("%Y.%m.%d"), localtime(tomorrow_begin)))
		else:
			callback()

	# Callback functions
	def callback(self):
		# Called after all services succeded
		return

	def errback(self):
		# Called after all services has returned, but at least one has failed
		return
