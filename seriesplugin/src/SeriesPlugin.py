# by betonme @2012

import re
import os, sys, traceback
from time import localtime, strftime
from datetime import datetime

# Localization
from . import _

from datetime import datetime

from Components.config import config

from enigma import eServiceReference, iServiceInformation, eServiceCenter, ePythonMessagePump
from ServiceReference import ServiceReference

# Plugin framework
from Modules import Modules

# Tools
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

# Plugin internal
from IdentifierBase import IdentifierBase
from ManagerBase import ManagerBase
from GuideBase import GuideBase
from Channels import ChannelsBase, removeEpisodeInfo, lookupServiceAlternatives
from Logger import splog
from CancelableThread import QueueWithTimeOut, CancelableThread, synchronized, myLock

from ThreadQueue import ThreadQueue
from threading import Thread
from enigma import ePythonMessagePump


try:
	if(config.plugins.autotimer.timeout.value == 1):
		config.plugins.autotimer.timeout.value = 5
		config.plugins.autotimer.save()
except Exception as e:
	pass


# Constants
AUTOTIMER_PATH  = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/AutoTimer/" )
SERIESPLUGIN_PATH  = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/" )


# Globals
instance = None

CompiledRegexpNonDecimal = re.compile(r'[^\d]+')

def dump(obj):
	for attr in dir(obj):
		splog( "config.plugins.seriesplugin.%s = %s" % (attr, getattr(obj, attr)) )


def getInstance():
	global instance
	
	if instance is None:
		
		from plugin import VERSION
		
		splog("SERIESPLUGIN NEW INSTANCE " + VERSION)
		
		try:


			from Tools.HardwareInfo import HardwareInfo
			splog( "DeviceName " + HardwareInfo().get_device_name().strip() )
		except:
			pass
		
		try:
			from Components.About import about
			splog( "EnigmaVersion " + about.getEnigmaVersionString().strip() )
			splog( "ImageVersion " + about.getVersionString().strip() )
		except:
			pass
		
		try:
			#http://stackoverflow.com/questions/1904394/python-selecting-to-read-the-first-line-only
			splog( "dreamboxmodel " + open("/proc/stb/info/model").readline().strip() )
			splog( "imageversion " + open("/etc/image-version").readline().strip() )
			splog( "imageissue " + open("/etc/issue.net").readline().strip() )
		except:
			pass
		
		try:
			for key, value in config.plugins.seriesplugin.dict().iteritems():
				splog( "config.plugins.seriesplugin.%s = %s" % (key, str(value.value)) )
		except Exception as e:
			pass
		
		#try:
		#	if os.path.exists(SERIESPLUGIN_PATH):
		#		dirList = os.listdir(SERIESPLUGIN_PATH)
		#		for fname in dirList:
		#			splog( fname, datetime.fromtimestamp( int( os.path.getctime( os.path.join(SERIESPLUGIN_PATH,fname) ) ) ).strftime('%Y-%m-%d %H:%M:%S') )
		#except Exception as e:
		#	pass
		#try:
		#	if os.path.exists(AUTOTIMER_PATH):
		#		dirList = os.listdir(AUTOTIMER_PATH)
		#		for fname in dirList:
		#			splog( fname, datetime.fromtimestamp( int( os.path.getctime( os.path.join(AUTOTIMER_PATH,fname) ) ) ).strftime('%Y-%m-%d %H:%M:%S') )
		#except Exception as e:
		#	pass
		
		instance = SeriesPlugin()
		#instance[os.getpid()] = SeriesPlugin()
		splog( strftime("%a, %d %b %Y %H:%M:%S", localtime()) )
	
	return instance

def resetInstance():
	#Rename to closeInstance
	global instance
	if instance is not None:
		splog("SERIESPLUGIN INSTANCE STOP")
		instance.stop()
		instance = None
	from Cacher import cache
	global cache
	cache = {}


def refactorTitle(org, data):
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
			#if season == 0 and episode == 0:
			#	return config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'title': title, 'series': series} )
			#else:
			return config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
		else:
			return org
	else:
		return org

def refactorDescription(org, data):
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
			#if season == 0 and episode == 0:
			#	description = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'title': title, 'series': series} )
			#else:
			description = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			description = description.replace("\n", " ")
			return description
		else:
			return org
	else:
		return org
		
class ThreadItem:
	def __init__(self, identifier = None, callback = None, name = None, begin = None, end = None, service = None, channels = None):
		self.identifier = identifier
		self.callback = callback
		self.name = name
		self.begin = begin
		self.end = end
		self.service = service
		self.channels = channels

class SeriesPluginWorker(Thread):

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

	def Start(self, item):
		if not self.__running:
			self.__running = True
			splog("SeriesPluginRenamer")
			#self.__item = item
			self.__list = [item]
			self.start() # Start blocking code in Thread
		else:
			self.__list.append(item)
	
	def run(self):
	
		while self.__list:
			item = self.__list.pop(0)
			splog('SeriesPluginWorker is processing: ', item.identifier)
			# do processing stuff here
			result = None
			
			try:
				result = item.identifier.getEpisode(
					item.name, item.begin, item.end, item.service, item.channels
				)
			except Exception, e:
				splog("SeriesPluginWorker Identifier Exception:", str(e))
				
				# Exception finish job with error
				result = str(e)
			
			try:
				splog("SeriesPluginWorker result")
				if result and len(result) == 4:
					season, episode, title, series = result
					season = int(CompiledRegexpNonDecimal.sub('', season))
					episode = int(CompiledRegexpNonDecimal.sub('', episode))
					title = title.strip()
					splog("SeriesPluginWorker result callback")
					self.__messages.push((2, item.callback, season, episode, title, series,))
					self.__messagePump.send(0)
				else:
					splog("SeriesPluginWorker result failed")
					self.__messages.push((1, item.callback, result))
					self.__messagePump.send(0)
			except Exception, e:
				splog("SeriesPluginWorker Callback Exception:", str(e))
			
			config.plugins.seriesplugin.lookup_counter.value += 1
			config.plugins.seriesplugin.lookup_counter.save()
			
		self.__messages.push((0, result,))
		self.__messagePump.send(0)
		self.__running = False
		Thread.__init__(self)
		splog('SeriesPluginWorker] list is emty, done')

#TBD Because of E2 Update 05.2013
#			if (config.plugins.seriesplugin.lookup_counter.value == 10) \
#				or (config.plugins.seriesplugin.lookup_counter.value == 100) \
#				or (config.plugins.seriesplugin.lookup_counter.value % 1000 == 0):
#				from plugin import ABOUT
#				about = ABOUT.format( **{'lookups': config.plugins.seriesplugin.lookup_counter.value} )
#				AddPopup(
#					about,
#					MessageBox.TYPE_INFO,
#					0,
#					'SP_PopUp_ID_About'
#				)

seriespluginworker = SeriesPluginWorker()

class SeriesPlugin(Modules, ChannelsBase):

	def __init__(self):
		splog("SeriesPlugin")
		Modules.__init__(self)
		ChannelsBase.__init__(self)
		
		self.serviceHandler = eServiceCenter.getInstance()
		seriespluginworker.MessagePump.recv_msg.get().append(self.gotThreadMsg_seriespluginworker)
		#http://bugs.python.org/issue7980
		datetime.strptime('2012-01-01', '%Y-%m-%d')
			
		self.identifier_elapsed = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_elapsed.value )
		splog(self.identifier_elapsed)
		
		self.identifier_today = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_today.value )
		splog(self.identifier_today)
		
		self.identifier_future = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_future.value )
		splog(self.identifier_future)


	def stop(self):
		splog("SeriesPlugin stop")
		if config.plugins.seriesplugin.lookup_counter.isChanged():
			config.plugins.seriesplugin.lookup_counter.save()
		self.saveXML()
	
	################################################
	# Identifier functions
	def getIdentifier(self, future=False, today=False, elapsed=False):
		if elapsed:
			return self.identifier_elapsed and self.identifier_elapsed.getName()
		elif today:
			return self.identifier_today and self.identifier_today.getName()
		elif future:
			return self.identifier_future and self.identifier_future.getName()
		else:
			return None
	
	def getEpisode(self, callback, name, begin, end=None, service=None, future=False, today=False, elapsed=False):
		#available = False
		
		if config.plugins.seriesplugin.skip_during_records.value:
			try:
				import NavigationInstance
				if NavigationInstance.instance.RecordTimer.isRecording():
					print("[SeriesPlugin]: Skip check during running records")
					return
			except:
				pass
		
		name = removeEpisodeInfo(name)
		name = removeEpisodeInfo(name)
		if name.startswith("The ") or name.startswith("Der ") or name.startswith("Die ")or name.startswith("Das "):
			name = name[4:]
		
		begin = datetime.fromtimestamp(begin)
		end = datetime.fromtimestamp(end)
		
		if elapsed:
			identifier = self.identifier_elapsed
		elif today:
			identifier = self.identifier_today
		elif future:
			identifier = self.identifier_future
		else:
			identifier = None
		
		# Reset title search depth
		identifier.search_depth = 0;
		
		if identifier:
			channels = lookupServiceAlternatives(service)

			seriespluginworker.Start(ThreadItem(identifier = identifier, callback = callback, name = name, begin = begin, end = end, service = service, channels = channels))
			'''
			try:
				
				
				result = identifier.getEpisode(
								name, begin, end, service, channels
							)
				
				if result and len(result) == 4:
				
					season, episode, title, series = result
					season = int(CompiledRegexpNonDecimal.sub('', season))
					episode = int(CompiledRegexpNonDecimal.sub('', episode))
					#title = CompiledRegexpNonAlphanum.sub(' ', title)
					title = title.strip()
					splog("SeriesPlugin result callback")
					callback( (season, episode, title, series) )
					
					config.plugins.seriesplugin.lookup_counter.value += 1
					config.plugins.seriesplugin.lookup_counter.save()
					
				else:
					splog("SeriesPlugin result failed")
					callback( result )
					
			except Exception as e:
				splog("SeriesPlugin Callback Exception:", str(e))
				callback( str(e) )
			'''
			
#TBD Because of E2 Update 05.2013
		#from threading import currentThread
		#if currentThread().getName() == 'MainThread':
#			if (config.plugins.seriesplugin.lookup_counter.value == 10) \
#				or (config.plugins.seriesplugin.lookup_counter.value == 100) \
#				or (config.plugins.seriesplugin.lookup_counter.value % 1000 == 0):
#				from plugin import ABOUT
#				about = ABOUT.format( **{'lookups': config.plugins.seriesplugin.lookup_counter.value} )
#				AddPopup(
#					about,
#					MessageBox.TYPE_INFO,
#					0,
#					'SP_PopUp_ID_About'
#				)
			
			return identifier.getName()
			
		#if not available:
		else:
			callback( "No identifier available" )
			
	def gotThreadMsg_seriespluginworker(self, msg):
		msg = seriespluginworker.Message.pop()
		print ('gotThreadMsg_seriespluginrenameservice]msg: %s' %str(msg))
		if msg[0] == 2:
			callback = msg[1]
			if callable(callback):
				callback((msg[2],msg[3],msg[4],msg[5]))
		elif msg[0] == 1:
			callback = msg[1]
			if callable(callback):
				callback(msg[2])
		self.renamerCallback()


	def renamerCallback(self):
		if (config.plugins.seriesplugin.lookup_counter.value == 10) \
			or (config.plugins.seriesplugin.lookup_counter.value == 100) \
			or (config.plugins.seriesplugin.lookup_counter.value % 1000 == 0):
			from plugin import ABOUT
			about = ABOUT.format( **{'lookups': config.plugins.seriesplugin.lookup_counter.value} )
			AddPopup(
				about,
				MessageBox.TYPE_INFO,
				0,
				'SP_PopUp_ID_About'
			)

	def cancel(self):
		seriespluginworker.MessagePump.recv_msg.get().remove(self.gotThreadMsg_seriespluginrenameservice) # interconnect to thread stop
		self.stop()
