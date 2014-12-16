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
#from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ControllerBase import ControllerBase

# Plugin specific
from time import localtime, strftime
from enigma import eTimer


# Constants
SUBJECT = _("Standby Notification")


class StandbyNotification(ControllerBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		ControllerBase.__init__(self)
		
		# Default configuration
		self.setOption( 'send_after_bootup',    NoSave(ConfigYesNo( default = False )), _("Send notification after bootup") )
		self.setOption( 'send_before_shutdown', NoSave(ConfigYesNo( default = False )), _("Send notification before shutdown") )
		self.setOption( 'send_before_standby',  NoSave(ConfigYesNo( default = True )),  _("Send notification before standby") )
		self.setOption( 'send_after_standby',   NoSave(ConfigYesNo( default = True )),  _("Send notification after standby") )
		
	def leaveStandby(self, dummy=None):
		#print "!!!!!!!!!!!!!!!!!leave standby"
		
		if self.getValue('send_after_standby'):
			text = _("Enigma2 wakeup after Standby")
		
			# Push mail
			from Plugins.Extensions.PushService.plugin import gPushService
			if gPushService:
				gPushService.push(self, SUBJECT, text)
	
	def standbyCountChanged(self, configElement=None):
		#print "!!!!!!!!!!!!!!!!!enter standby num", configElement.value
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.leaveStandby)
		
		if self.getValue('send_before_standby'):
			text = _("Enigma2 going into Standby")
		
			# Push mail
			from Plugins.Extensions.PushService.plugin import gPushService
			if gPushService:
				gPushService.push(self, SUBJECT, text)
	
	def begin(self):
		# Is called after starting PushService
		
		if self.getValue('send_after_bootup'):
			text = _("Enigma2 booted")
		
			# Push mail
			from Plugins.Extensions.PushService.plugin import gPushService
			if gPushService:
				gPushService.push(self, SUBJECT, text)
		
		from Components.config import config
		config.misc.standbyCounter.addNotifier(self.standbyCountChanged, initial_call = False)

	def end(self):
		# Is called after stopping PushSerive
		
		if self.getValue('send_before_shutdown'):
			text = _("Enigma2 shutdown initiated")
		
			# Push mail
			from Plugins.Extensions.PushService.plugin import gPushService
			if gPushService:
				gPushService.push(self, SUBJECT, text)
	
	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		callback()
