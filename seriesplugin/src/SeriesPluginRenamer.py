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

import os
import re
from glob import glob #Py3 ,escape

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

CompiledRegexpGlobEscape = re.compile('([\[\]\?*])')  # "[\\1]"


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
	splog("SPR: rename:", data)
	
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
			splog("SPR: title",title)
			if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
				descr = refactorDescription(olddescr, data)
			else:
				descr = olddescr
			splog("SPR: descr",descr)
			
			metafile = open(meta_file, "w")
			metafile.write("%s%s\n%s\n%s" % (sid, title, descr, rest))
			metafile.close()
	except Exception as e:
		splog("SPR: renameMeta:", e)

def renameFile(service, name, data, tidy=False):
	try:
		servicepath = service.getPath()
		splog("SPR: servicepath", servicepath)
		
		path = os.path.dirname(servicepath)
		file_name = os.path.basename(os.path.splitext(servicepath)[0])
		splog("SPR: file_name", file_name)
		
		splog("SPR: name     ", name)
		# Refactor title
		if config.plugins.seriesplugin.rename_tidy.value or tidy:
			name = refactorTitle(name, data)
		else:
			name = refactorTitle(file_name, data)
		splog("SPR: name     ", name)
		#if config.recording.ascii_filenames.value:
		#	filename = ASCIItranslit.legacyEncode(filename)
		if config.plugins.seriesplugin.rename_legacy.value:
			name = newLegacyEncode(name)
			splog("SPR: name     ", name)
		
		src = os.path.join(path, file_name)
		splog("SPR: servicepathSrc", src)
		dst = os.path.join(path, name)
		splog("SPR: servicepathDst", dst)

		#Py3 for f in glob( escape(src) + "*" ):
		glob_src = CompiledRegexpGlobEscape.sub("[\\1]", src)
		splog("SPR: glob_src      ", glob_src)
		for f in glob( glob_src + "*" ):
			splog("SPR: servicepathRnm", f)
			to = f.replace(src, dst)
			splog("SPR: servicepathTo ", to)
			if not os.path.exists(to):
				os.rename(f, to)
			elif config.plugins.seriesplugin.rename_existing_files.value:
				splog("SPR: Destination file alreadey exists", to, " - Append _")
				renameFile(service, name + "_", data, True)
				break
			else:
				splog("SPR: Destination file alreadey exists", to, " - Skip rename")
	except Exception as e:
		splog("SPR: renameFile:", e)


from ThreadQueue import ThreadQueue
from threading import Thread
from enigma import ePythonMessagePump

class SeriesPluginRenameService(Thread):
	
	def __init__(self):
		Thread.__init__(self)
		self.__running = False
		self.__messages = ThreadQueue()
		self.__messagePump = ePythonMessagePump()

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
			
			splog("SPR: run")
			seriesPlugin = getInstance()
			self.serviceHandler = eServiceCenter.getInstance()
			
			if isinstance(service, eServiceReference):
				service = service
			elif isinstance(service, ServiceReference):
				service = service.ref
			else:
				splog("SPR: Wrong instance")
				self.__messages.push(service)
				self.__messagePump.send(0)
				self.__running = False
				Thread.__init__(self)
				return
			
			if not os.path.exists( service.getPath() ):
				splog("SPR: File not exists: " + service.getPath())
				self.__messages.push(service)
				self.__messagePump.send(0)
				self.__running = False
				Thread.__init__(self)
				return
			
			info = self.serviceHandler.info(service)
			if not info:
				splog("SPR: No info available: " + service.getPath())
				self.__messages.push(service)
				self.__messagePump.send(0)
				self.__running = False
				Thread.__init__(self)
				return 
			
			name = service.getName() or info.getName(service) or ""
			#splog("SPR: name", name)
			
			short = ""
			begin = None
			end = None
			duration = 0
			
			event = info.getEvent(service)
			if event:
				short = event.getShortDescription()
				begin = event.getBeginTime()
				duration = event.getDuration() or 0
				end = begin + duration or 0
				# We got the exact start times, no need for margin handling
			
			if not begin:
				begin = info.getInfo(service, iServiceInformation.sTimeCreate) or -1
				if begin != -1:
					end = begin + (info.getLength(service) or 0)
				else:
					end = os.path.getmtime(service.getPath())
					begin = end - (info.getLength(service) or 0)
				#MAYBE we could also try to parse the filename
				# We don't know the exact margins, we will assume the E2 default margins
				begin + (int(config.recording.margin_before.value) * 60)
				end - (int(config.recording.margin_after.value) * 60)
			
			rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
			#channel = ServiceReference(rec_ref_str).getServiceName()
			
			splog("SPR: getEpisode:", name, begin, end)
			seriesPlugin.getEpisode(
					boundFunction(self.serviceCallback, service, name, short),
					name, begin, end, rec_ref_str, elapsed=True
				)

	def serviceCallback(self, service, name, short, data=None):
		splog("SPR: serviceCallback", name, data)
		
		result = None
		
		if data and len(data) == 4:
			if rename(service, name, short, data):
				# Rename was successfully
				result = None
		elif data:
			result = service.getPath() + " : " + str( data )
		else:
			result = service.getPath()
		
		self.__messages.push(result)
		self.__messagePump.send(0)

		self.__running = False
		Thread.__init__(self)
		splog("SPR: Service done")

		
seriespluginrenameservice = SeriesPluginRenameService()

#######################################################
# Rename movies
class SeriesPluginRenamer(object):
	def __init__(self, session, services, *args, **kwargs):
		
		splog("SPR: SeriesPluginRenamer")
		
		if services and not isinstance(services, list):
			services = [services]	
		
		splog("SPR: len()", len(services))
		
		self.services = services
		
		self.data = []
		self.counter = 0
		self.__pump_recv_msg_conn = None
		
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
			try:
				self.__pump_recv_msg_conn = seriespluginrenameservice.MessagePump.recv_msg.connect(self.gotThreadMsg_seriespluginrenameservice) # interconnect to thread start
			except:
				seriespluginrenameservice.MessagePump.recv_msg.get().append(self.gotThreadMsg_seriespluginrenameservice) # interconnect to thread start
			seriespluginrenameservice.Start(self.services)

	def gotThreadMsg_seriespluginrenameservice(self, msg):
		msg = seriespluginrenameservice.Message.pop()
		splog("SPR: gotThreadMsg", msg)
		self.renamerCallback(msg)
		self.__pump_recv_msg_conn = None
		try:
			seriespluginrenameservice.MessagePump.recv_msg.get().remove(self.gotThreadMsg_seriespluginrenameservice) # interconnect to thread stop
		except:
			pass

	def renamerCallback(self, result=None):
		splog("SPR: renamerCallback", result)
		
		if result and isinstance(result, basestring):
			self.data.append( result )
		
		if config.plugins.seriesplugin.rename_popups.value or config.plugins.seriesplugin.rename_popups_success.value:
			
			self.counter = self.counter +1
			
			if self.data or config.plugins.seriesplugin.rename_popups_success.value:
			
				# Maybe there is a better way to avoid multiple Popups
				from SeriesPlugin import seriespluginworker
				
				splog("SPR: renamerCallback getListLength", not seriespluginworker or seriespluginworker.getListLength(), not seriespluginworker or seriespluginworker.isListEmpty() )
				
				if not seriespluginworker or seriespluginworker.isListEmpty():
					if self.data:
						AddPopup(
							"SeriesPlugin:\n" + _("Record rename has been finished with %d errors:\n") % (len(self.data)) +"\n" +"\n".join(self.data),
							MessageBox.TYPE_ERROR,
							int(config.plugins.seriesplugin.rename_popups_timeout.value),
							'SP_PopUp_ID_RenameFinished'
						)
					else:
						AddPopup(
							"SeriesPlugin:\n" + _("%d records renamed successfully") % (self.counter),
							MessageBox.TYPE_INFO,
							int(config.plugins.seriesplugin.rename_popups_timeout.value),
							'SP_PopUp_ID_RenameFinished'
						)
					self.data = []
					self.counter = 0
