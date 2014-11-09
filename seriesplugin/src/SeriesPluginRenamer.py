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

import os
import re
import glob

# for localized messages
from . import _

# Config
from Components.config import config

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

from Tools.BoundFunction import boundFunction
from Tools.ASCIItranslit import ASCIItranslit

from enigma import eServiceCenter, iServiceInformation, eServiceReference
from ServiceReference import ServiceReference

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription   #, refactorRecord
from Logger import splog


CompiledRegexpNonAlphanum = re.compile(r'[^[a-zA-Z0-9_]]+')


# By Bin4ry
def newLegacyEncode(string):
	string2 = ""
	for z, char in enumerate(string.decode("utf-8")):
		i = ord(char)
		if i < 33:
			string2 += " "
		elif i in ASCIItranslit:
			# There is a bug in the E2 ASCIItranslit some (not all) german-umlaut(a) -> AE
			if char.islower():
				string2 += ASCIItranslit[i].lower()
			else:
				string2 += ASCIItranslit[i]
				
		else:
			try:
				string2 += char.encode('ascii', 'strict')
			except:
				string2 += " "
	return string2

def rename(service, name, short, data):
	# Episode data available
	splog(data)
	
	#MAYBE Check if it is already renamed?
	try:
		# Before renaming change content
		renameMeta(service, data)
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":

			if config.plugins.seriesplugin.rename_file.value == True:
				renameFile(service, name, data)
		#if config.plugins.seriesplugin.pattern_record.value and not config.plugins.seriesplugin.pattern_record.value == "Off":
		#	renameFile(service, name, data)
		return True
	except:
		#pass
		raise
	return False

# Adapted from MovieRetitle setTitleDescr
def renameMeta(service, data):
	try:
		#TODO Use MetaSupport EitSupport classes from EMC ?
		if service.getPath().endswith(".ts"):
			meta_file = service.getPath() + ".meta"
		else:
			meta_file = service.getPath() + ".ts.meta"
		
		# Create new meta for ts files
		if not os.path.exists(meta_file):
			if os.path.isfile(service.getPath()):
				_title = os.path.basename(os.path.splitext(service.getPath())[0])
			else:
				_title = service.getName()
			_sid = ""
			_descr = ""
			_time = ""
			_tags = ""
			metafile = open(meta_file, "w")
			metafile.write("%s\n%s\n%s\n%s\n%s" % (_sid, _title, _descr, _time, _tags))
			metafile.close()
		
		if os.path.exists(meta_file):
			metafile = open(meta_file, "r")
			sid = metafile.readline()
			oldtitle = metafile.readline().rstrip()
			olddescr = metafile.readline().rstrip()
			rest = metafile.read()
			metafile.close()
			
			if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
				title = refactorTitle(oldtitle, data)
			else:
				title = oldtitle
			splog(title)
			if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
				descr = refactorDescription(olddescr, data)
			else:
				descr = olddescr
			splog(descr)
			
			metafile = open(meta_file, "w")
			metafile.write("%s%s\n%s\n%s" % (sid, title, descr, rest))
			metafile.close()
	except Exception as e:
		splog(e)

def renameFile(service, name, data):
	try:
		servicepath = service.getPath()
		splog("servicepath", servicepath)
		servicepath = CompiledRegexpNonAlphanum.sub('', servicepath)
		splog("servicepathRegexp", servicepath)
		
		path = os.path.dirname(servicepath)
		file_name = os.path.basename(os.path.splitext(servicepath)[0])
		
		# Refactor title
		if config.plugins.seriesplugin.tidy_rename.value:
			name = refactorTitle(name, data)
		else:
			name = refactorTitle(file_name, data)
		# Refactor record file name
		#name = refactorRecord(file_name, data)
		name = newLegacyEncode(name)
		
		src = os.path.join(path, file_name)
		splog("servicepathSrc", src)
		dst = os.path.join(path, name)
		splog("servicepathDst", dst)

		for f in glob.glob(os.path.join(path, src + "*")):
			os.rename(f, f.replace(src, dst))
	except Exception as e:
		splog(e)

from ThreadQueue import ThreadQueue
from threading import Thread
from enigma import ePythonMessagePump

class SeriesPluginRenameService(Thread):
	
	def __init__(self):
		Thread.__init__(self)
		self.__running = False
		self.__messages = ThreadQueue()
		self.__messagePump = ePythonMessagePump()
		self.__beginn = None
		self.__end = None

	def __getMessagePump(self):
		return self.__messagePump
	MessagePump = property(__getMessagePump)

	def __getMessageQueue(self):
		return self.__messages
	Message = property(__getMessageQueue)

	def __getRunning(self):
		return self.__running
	isRunning = property(__getRunning)

	def Start(self, services):
	
		if not self.__running:
			self.__running = True
			self.__services = services
			self.start() # Start blocking code in Thread 
			
	def run(self):
		
		for service in self.__services:
			splog("SeriesPluginRenamer")
			self.seriesPlugin = getInstance()
			self.serviceHandler = eServiceCenter.getInstance()
			
			if isinstance(service, eServiceReference):
				self.service = service
			elif isinstance(service, ServiceReference):
				self.service = service.ref
			else:
				splog(_("SeriesPluginRenamer: Wrong instance"))
				self.__messages.push(service)
				self.__messagePump.send(0)
				self.__running = False
				Thread.__init__(self)
				return
			
			if not os.path.exists( service.getPath() ):
				splog(_("SeriesPluginRenamer: File not exists: ") + service.getPath())
				self.__messages.push(service)
				self.__messagePump.send(0)
				self.__running = False
				Thread.__init__(self)
				return
			
			info = self.serviceHandler.info(service)
			if not info:
				splog(_("SeriesPluginRenamer: No info available: ") + service.getPath())
				self.__messages.push(service)
				self.__messagePump.send(0)
				self.__running = False
				Thread.__init__(self)
				return 
			
			self.name = service.getName() or info.getName(service) or ""
			splog("name", self.name)
			
			self.short = ""
			
			event = info.getEvent(service)
			if event:
				self.short = event.getShortDescription()
				self.__beginn = event.getBeginTime()
				duration = event.getDuration() or 0
				self.__end = self.__beginn + duration or 0
				# We got the exact start times, no need for margin handling
			
			if not self.__beginn:
				self.__beginn = info.getInfo(service, iServiceInformation.sTimeCreate) or -1
				if self.__beginn != -1:
					self.__end = self.__beginn + (info.getLength(service) or 0)
				else:
					self.__end = os.path.getmtime(service.getPath())
					self.__beginn = self.__end - (info.getLength(service) or 0)
				#MAYBE we could also try to parse the filename
				# We don't know the exact margins, we will assume the E2 default margins
				self.__beginn + (int(config.recording.margin_before.value) * 60)
				self.__end - (int(config.recording.margin_after.value) * 60)
			
			self.__rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
			#channel = ServiceReference(rec_ref_str).getServiceName()
		
			
			
			self.seriesPlugin.getEpisode(
					self.serviceCallback, 
					#self.name, begin, end, channel, elapsed=True
					#self.name, begin, end, eServiceReference(rec_ref_str), elapsed=True
					self.name, self.__beginn, self.__end, self.__rec_ref_str, elapsed=True
				)

	def serviceCallback(self, data=None):
		splog("SeriesPluginRenamer serviceCallback")
		splog(data)
		
		result = None
		
		if data and len(data) == 4:
			if rename(self.service, self.name, self.short, data):
				# Rename was successfully
				result = None
		elif data:
			result = self.service.getPath() + " : " + str( data )
		else:
			result = self.service.getPath()
		
		self.__messages.push(result)
		self.__messagePump.send(0)

		self.__running = False
		Thread.__init__(self)
		print ('SeriesPluginRenameService]done')

		
seriespluginrenameservice = SeriesPluginRenameService()

#######################################################
# Rename movies
class SeriesPluginRenamer(object):
	def __init__(self, session, services, *args, **kwargs):
		
		if services and not isinstance(services, list):
			services = [services]	
		
		self.services = services
		
		self.failed = []
		self.returned = 0
		
		session.openWithCallback(
			self.confirm,
			MessageBox,
			_("Do You want to start renaming?"),
			MessageBox.TYPE_YESNO,
			timeout = 15,
			default = True
		)

	def confirm(self, confirmed):
		if confirmed and self.services:
			seriespluginrenameservice.MessagePump.recv_msg.get().append(self.gotThreadMsg_seriespluginrenameservice) # interconnect to thread start
			seriespluginrenameservice.Start(self.services)

	def gotThreadMsg_seriespluginrenameservice(self, msg):
		msg = seriespluginrenameservice.Message.pop()
		print ('gotThreadMsg_seriespluginrenameservice]msg: %s' %str(msg))
		self.renamerCallback(msg)
		seriespluginrenameservice.MessagePump.recv_msg.get().remove(self.gotThreadMsg_seriespluginrenameservice) # interconnect to thread stop

	def renamerCallback(self, result=None):
		self.returned += 1
		if result and isinstance(result, basestring):
			#Maybe later self.failed.append( name + " " + begin.strftime('%y.%m.%d %H-%M') + " " + channel )
			self.failed.append( result )
		if self.failed:
			AddPopup(
				_("Movie rename has been finished with %d errors:\n") % (len(self.failed)) + "\n".join(self.failed),
				MessageBox.TYPE_ERROR,
				0,
				'SP_PopUp_ID_RenameFinished'
			)
		else:
			AddPopup(
				_("Movie rename has been finished successfully"),
				MessageBox.TYPE_INFO,
				0,
				'SP_PopUp_ID_RenameFinished'
			)
