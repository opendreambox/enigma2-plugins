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
from Components.config import ConfigYesNo, ConfigText, ConfigNumber, NoSave

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ControllerBase import ControllerBase

# Plugin specific
import os
from time import localtime, strftime, time


# Constants
SUBJECT = _("Free space warning")
BODY    = _("Free disk space limit has been reached:\n") \
				+ _("Path:  %s\n") \
				+ _("Limit: %d GB\n") \
				+ _("Left:  %s")

#Adapted from: from Components.Harddisk import findMountPoint
def mountpoint(path):
	path = os.path.realpath(path)
	if os.path.ismount(path) or len(path)==0: return path
	return mountpoint(os.path.dirname(path))
			
def getDevicebyMountpoint(hdm, mountpoint):
	for x in hdm.partitions[:]:
		if x.mountpoint == mountpoint:
			return x.device
	return None

def getHDD(hdm, part):
	for hdd in hdm.hdd:
		if hdd.device == part[:3]:
			return hdd
	return None

def timerToString(timer):
	return str(timer.name) + "\t" \
			+ strftime(_("%Y.%m.%d %H:%M"), localtime(timer.begin)) + " - " \
			+ strftime(_("%H:%M"), localtime(timer.end)) + "\t" \
			+ str(timer.service_ref and timer.service_ref.getServiceName() or "") \
			+ "\t" + str(timer.tags)


class FreeSpace(ControllerBase):
	
	ForceSingleInstance = False
	
	def __init__(self):
		# Is called on instance creation
		ControllerBase.__init__(self)
		
		# Default configuration
		self.setOption( 'wakehdd',  NoSave(ConfigYesNo(  default = False )),                                  _("Allow HDD wake up") )
		self.setOption( 'path',     NoSave(ConfigText(   default = "/media/hdd/movie", fixed_size = False )), _("Where to check free space") )
		self.setOption( 'limit',    NoSave(ConfigNumber( default = 100 )),                                    _("Free space limit in GB") )
		self.setOption( 'listtimer',NoSave(ConfigYesNo(  default = False )),                                  _("List upcoming timer") )
	
	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		path = self.getValue('path')
		limit = self.getValue('limit')
		
		if not self.getValue('wakehdd'):

			# User specified to avoid HDD wakeup if it is sleeping
			from Components.Harddisk import harddiskmanager
			dev = getDevicebyMountpoint( harddiskmanager, mountpoint(path) )
			if dev is not None:
				hdd = getHDD( harddiskmanager, dev )
				if hdd is not None:
					if hdd.isSleeping():
						# Don't wake up HDD
						print _("[FreeSpace] HDD is idle: ") + str(path)
						callback()
		
		# Check free space on path
		if os.path.exists( path ):
			stat = os.statvfs( path )
			free = ( stat.f_bavail if stat.f_bavail!=0 else stat.f_bfree ) * stat.f_bsize / 1024 / 1024 # MB
			if limit > (free/1024): #GB
				if free >= 10*1024:	#MB
					free = "%d GB" %(free/1024)
				else:
					free = "%d MB" %(free)
				# Not enough free space
				text = ""
				if self.getValue('listtimer'):
					text = "\r\n\r\n" 
					text += _("Next timer:") 
					text += "\r\n"
					import NavigationInstance
					now = time()
					next_day = now + 86400 # Add one day
					for t in NavigationInstance.instance.RecordTimer.timer_list + NavigationInstance.instance.RecordTimer.processed_timers:
						if not t.disabled and not t.justplay and now < t.begin and t.end < next_day:
							text += "\t" + timerToString(t)  + "\r\n"
					
				callback( SUBJECT, BODY % (path, limit, free) + text )
			else:
				# There is enough free space
				callback()
