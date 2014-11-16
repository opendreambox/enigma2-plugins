# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=TBD
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

from . import _

import os, sys, traceback

from Components.config import config

from Screens.MessageBox import MessageBox

#import requests


def splog(*args):
	strargs = ""
	for arg in args:
		if strargs: strargs += " "
		strargs += str(arg)
	print strargs
	
	if config.plugins.seriesplugin.write_log.value:
		strargs += "\n"
		
		# Append to file
		f = None
		try:
			f = open(config.plugins.seriesplugin.log_file.value, 'a')
			f.write(strargs)
			if sys.exc_info()[0]:
				print "Unexpected error:", sys.exc_info()[0]
				traceback.print_exc(file=f)
		except Exception as e:
			print "SeriesPlugin splog exception " + str(e)
		finally:
			if f:
				f.close()
	
	if sys.exc_info()[0]:
		print "Unexpected error:", sys.exc_info()[0]
		traceback.print_exc(file=sys.stdout)
	
	sys.exc_clear()


class Logger(object):
	def sendLog(self):
		print "[SP sendLog]"
		
		return
		
		#TODO MAYBE LATER
		######################################################
		
		
		# Check preconditions
		if not config.plugins.seriesplugin.write_log.value:
			self.session.open(
				MessageBox,
				_("Enable Logging"),
				type = MessageBox.TYPE_ERROR
			)
			return
		if not config.plugins.seriesplugin.log_file.value:
			self.session.open(
				MessageBox,
				_("Specify log file"),
				type = MessageBox.TYPE_ERROR
			)
			return
		
		# Avoid "Dreambox User" and "myemail@home.com"
		if not(
				( str(config.plugins.seriesplugin.log_reply_user.value) != str(config.plugins.seriesplugin.log_reply_user.default) ) or
				( str(config.plugins.seriesplugin.log_reply_mail.value) != str(config.plugins.seriesplugin.log_reply_mail.default) )
			):
			self.session.open(
				MessageBox,
				_("Enter user name or user mail"),
				type = MessageBox.TYPE_ERROR
			)
			return
		
		if not os.path.exists(config.plugins.seriesplugin.log_file.value):
			self.session.open(
				MessageBox,
				_("No log file found"),
				type = MessageBox.TYPE_ERROR
			)
			return
		
		MSG_TEXT = "Please consider:\n" \
					+ _("I've to spend my free time for this support!\n\n") \
					+ _("Have You already checked the problem list:\n") \
					+ _("Is the information available at Wunschliste.de / Fernsehserien.de? \n") \
					+ _("Does the start time match? \n")
		
		self.session.openWithCallback(
				self.confirmSend,
				MessageBox,
				MSG_TEXT,
				type = MessageBox.TYPE_YESNO,
				timeout = 60,
				default = False
			)

	def confirmSend(self, confirmed):
		if not confirmed:
			return
		
		#TODO SEND IT HERE
