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
 
 
# Constants
 
SUBJECT = _("List of Files")
 
 
 
 
class ListDir(ControllerBase):
 
        ForceSingleInstance = True
 
        def __init__(self):
                # Is called on instance creation
                ControllerBase.__init__(self)
                self.movielist= []
 
                # Default configuration
                self.setOption( 'path',     NoSave(ConfigText(   default = "/media/hdd/movie/", fixed_size = False )), _("Where to check") )
		self.setOption( 'ext',     NoSave(ConfigText(   default = ".ts", fixed_size = False )), _("file extension") )
 
 
        def run(self, callback, errback):
                # At the end a plugin has to call one of the functions: callback or errback
                # Callback should return with at least one of the parameter: Header, body (List of Files)
                # If empty or none is returned, nothing will be sent
                path = self.getValue('path')
		ext = self.getValue('ext')                
		movielist = []
                for file in os.listdir( path ):
                        if file.endswith( ext ):
                                movielist.append(file)
                body = "The following files were found: \n" + "\n".join(movielist)
               
		if movielist:
			callback( SUBJECT, body )
		else:
			callback()
