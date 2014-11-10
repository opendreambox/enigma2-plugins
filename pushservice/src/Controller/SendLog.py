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
from Components.config import ConfigYesNo, ConfigText, NoSave

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ControllerBase import ControllerBase

# Plugin specific
import os
import re
import fnmatch

# Constants
SUBJECT = _("Found Log(s)")
BODY    = _("Log(s) are attached")


class SendLog(ControllerBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		ControllerBase.__init__(self)
		self.logfiles = []

		# Default configuration
		self.setOption( 'path',            NoSave(ConfigText(  default = "/media/hdd/", fixed_size = False )), _("Path to check") )
		self.setOption( 'file_pattern',    NoSave(ConfigText(  default = "*.log", fixed_size = False )), _("Filename pattern (No RegExp)") )
		self.setOption( 'content_pattern', NoSave(ConfigText(  default = ".*", fixed_size = False )), _("Content pattern (RegExp)") )
		self.setOption( 'scan_subs',       NoSave(ConfigYesNo( default = False )), _("Scan subfolders") )
		self.setOption( 'rename_logs',     NoSave(ConfigYesNo( default = False )), _("Rename log(s)") )
		self.setOption( 'delete_logs',     NoSave(ConfigYesNo( default = False )), _("Delete log(s)") )

	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		self.logfiles = []
		path = self.getValue('path')
		file_pattern = self.getValue('file_pattern')
		content_pattern = self.getValue('content_pattern')
		prog = re.compile(content_pattern)

		if self.getValue('scan_subs'):
			for root, dirnames, filenames in os.walk(path):
				for filename in fnmatch.filter(filenames, file_pattern):
					logfile = os.path.join( root, filename )
					if( content_pattern == ".*" ):
						self.logfiles.append( logfile )
					else:
						infile = open(logfile,"r")
						for line in infile:
							if prog.match(line):
								self.logfiles.append( logfile )
								break
						infile.close()
		else:
			filenames = os.listdir( path )
			for filename in fnmatch.filter(filenames, file_pattern):
				logfile = os.path.join( path, filename )
				if( content_pattern == ".*" ):
					self.logfiles.append( logfile )
				else:
					infile = open(logfile,"r")
					for line in infile:
						if prog.match(line):
							self.logfiles.append( logfile )
							break
					infile.close()
		
		if self.logfiles:
			callback( SUBJECT, BODY, self.logfiles )
		else:
			callback()

	# Callback functions
	def callback(self):
		# Called after all services succeded
		if self.getValue('delete_logs'):
			# Delete logfiles
			for logfile in self.logfiles[:]:
				if os.path.exists( logfile ):
					os.remove( logfile )
				self.logfiles.remove( logfile )
		elif self.getValue('rename_logs'):
			# Rename logfiles to avoid resending it
			for logfile in self.logfiles[:]:
				if os.path.exists( logfile ):
					# Adapted from autosubmit - instead of .sent we will use .pushed
					currfilename = str(os.path.basename(logfile))
					newfilename = "/media/hdd/" + currfilename + ".pushed"
					os.rename(logfile,newfilename)
				self.logfiles.remove( logfile )

	def errback(self):
		# Called after all services has returned, but at least one has failed
		self.logfiles = []
