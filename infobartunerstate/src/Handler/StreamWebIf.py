# -*- coding: utf-8 -*-from
# by betonme @2015

import string
import sys

from time import time

from ServiceReference import ServiceReference

# Config
from Components.config import *

# Plugin internal
from Plugins.Extensions.InfoBarTunerState.__init__ import _
from Plugins.Extensions.InfoBarTunerState.PluginBase import PluginBase
from Plugins.Extensions.InfoBarTunerState.Helper import getTunerByPlayableService, getNumber, getChannel, getClient, getEventName


HAS_WEBIF = False
try:
	from Plugins.Extensions.WebInterface.WebScreens import StreamingWebScreen 
	HAS_WEBIF = True
except:
	StreamingWebScreen = None


# Config options
config.infobartunerstate.plugin_webif         = ConfigSubsection()
config.infobartunerstate.plugin_webif.enabled = ConfigYesNo(default = False)


def getStreamID(stream):
	if HAS_WEBIF:
		try:
			return str(stream.screenIndex) + str(stream.clientIP)
		except:
			pass
	return ""

def getStream(id):
	if HAS_WEBIF:
		try:
			from Plugins.Extensions.WebInterface.WebScreens import streamingScreens 
		except:
			streamingScreens = []
		for stream in streamingScreens:
			if stream:
				if getStreamID(stream) == id:
					return stream
	return None


class StreamWebIf(PluginBase):
	def __init__(self):
		PluginBase.__init__(self)

	################################################
	# To be implemented by subclass
	def getText(self):
		return "Stream"

	def getType(self):
		from Plugins.Extensions.InfoBarTunerState.InfoBarTunerState import INFO, RECORD, STREAM, FINISHED
		# Pixmap number to be displayed as icon
		return STREAM

	def getOptions(self):
		return [(_("Show stream(s) (WebIf)"), config.infobartunerstate.plugin_webif.enabled),]

	def appendEvent(self):
		if config.infobartunerstate.plugin_webif.enabled.value:
			if HAS_WEBIF:
				try:
					from Plugins.Extensions.WebInterface.WebScreens import streamingEvents
					if self.onEvent not in streamingEvents:
						streamingEvents.append(self.onEvent)
				except:
					pass

	def removeEvent(self):
		if HAS_WEBIF:
			try:
				from Plugins.Extensions.WebInterface.WebScreens import streamingEvents
				if self.onEvent in streamingEvents:
					streamingEvents.remove(self.onEvent)
			except:
				pass

	def onInit(self):
		if config.infobartunerstate.plugin_webif.enabled.value:
			if HAS_WEBIF:
				try:
					from Plugins.Extensions.WebInterface.WebScreens import streamingScreens
				except:
					streamingScreens = []
				#TODO file streaming actually not supported
				for stream in streamingScreens:
					# Check if screen exists
					if stream and stream.request and 'file' not in stream.request.args:
						self.onEvent(StreamingWebScreen.EVENT_START, stream)

	def onEvent(self, event, stream):
		if StreamingWebScreen and stream:
			if (event == StreamingWebScreen.EVENT_START):
				id = getStreamID(stream)
				print "IBTS Stream Event WebIf Start " + id
				
				irecordservice = stream.getRecordService()
				
				eservicereference = stream.getRecordServiceRef()
				
				# Extract parameters
				ip = str(stream.clientIP)
				if ip and ':' in ip and '.' in ip:
					# Mixed style ::ffff:192.168.64.27
					ip = string.split(str(stream.clientIP), ':')[-1]
				
				# Delete references to avoid blocking tuners
				del stream
				
				tuner, tunertype, tunernumber = getTunerByPlayableService( irecordservice ) 
				
				name = getEventName(eservicereference)
				
				number = getNumber(eservicereference)
				channel = getChannel(eservicereference)
				
				client = getClient(ip)
				
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				gInfoBarTunerState.addEntry(id, self.getPluginName(), self.getType(), self.getText(), tuner, tunertype, tunernumber, name, number, channel, time(), 0, True, "", client, ip)
				gInfoBarTunerState.onEvent()
				
			elif event == StreamingWebScreen.EVENT_END:
				
				# Remove Finished Stream
				id = getStreamID(stream)
				print "IBTS Stream Event WebIf End " + id
				
				# Delete references to avoid blocking tuners
				del stream
				
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				gInfoBarTunerState.finishEntry(id)
				gInfoBarTunerState.onEvent()

	def update(self, id, tunerstate):
		
		stream = getStream( id )
		if stream:
		
			eservicereference = stream.getRecordServiceRef()
			
			del stream
			
			tunerstate.name = getEventName(eservicereference)
			
			if not tunerstate.number:
				tunerstate.number = getNumber(eservicereference)
			if not tunerstate.channel:
				tunerstate.channel = getChannel(eservicereference)
			
			return True
			
		else:
			
			# Stream is not active anymore				
			return None
