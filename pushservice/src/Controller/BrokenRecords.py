#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2016 <glaserfrank(at)gmail.com>
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
from Components.config import *

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ControllerBase import ControllerBase

# Plugin specific
from time import time
import os
import fnmatch

# Constants
SUBJECT = _("Broken records")
BODY    = _("There are broken records - %s")


class BrokenRecords(ControllerBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		ControllerBase.__init__(self)

	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		yesterday_end = time()
		yesterday_begin = yesterday_end - 24*60*60
		
		broken_records = []
		for root, dirnames, filenames in os.walk(config.usage.default_path.value):
			for filename in fnmatch.filter(filenames, '*.ts'):
				record_path = os.path.join(root, filename)
				record_end = os.path.getmtime(record_path)
				if yesterday_begin <= record_end <= yesterday_end:
					if os.path.getsize(record_path) < 10000000: # 10MB
						broken_records.append(record_path)
				
		if broken_records:
			callback( SUBJECT, BODY % "\n\n" + "\n".join( broken_records ) )
		else:
			callback()

	# Callback functions
	def callback(self):
		# Called after all services succeded
		return

	def errback(self):
		# Called after all services has returned, but at least one has failed
		return
