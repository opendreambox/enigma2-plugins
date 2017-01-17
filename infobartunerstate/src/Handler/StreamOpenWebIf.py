# -*- coding: utf-8 -*-from
# by betonme @2015

import sys

from time import time

from ServiceReference import ServiceReference

# Config
from Components.config import *

# Plugin internal
from Plugins.Extensions.InfoBarTunerState.PluginBase import PluginBase
from Plugins.Extensions.InfoBarTunerState.Helper import getTunerByPlayableService, getNumber, getChannel, getClient, getEventName


HAS_OPENWEBIF = False
try:
	from Plugins.Extensions.OpenWebif.controllers.stream import StreamAdapter
	HAS_OPENWEBIF = True
except:
	StreamAdapter = None


# Config options
config.infobartunerstate.plugin_openwebif         = ConfigSubsection()
config.infobartunerstate.plugin_openwebif.enabled = ConfigYesNo(default = False)


def getStreamID(stream):
	if HAS_OPENWEBIF:		
		try:
			return str(stream.streamIndex) + str(stream.clientIP)
		except:
			pass
	return ""

def getStream(id):
	if HAS_OPENWEBIF:
		try:
			from Plugins.Extensions.OpenWebif.controllers.stream import streamList
		except:
			streamList = []
		for stream in streamList:
			if stream:
				if getStreamID(stream) == id:
					return stream
	return None


class StreamOpenWebIf(PluginBase):
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
		return [(_("Show transcoded stream(s) (OpenWebIf)"), config.infobartunerstate.plugin_openwebif.enabled),]

	def appendEvent(self):
		if config.infobartunerstate.plugin_openwebif.enabled.value:
			if HAS_OPENWEBIF:
				try:
					from Plugins.Extensions.OpenWebif.controllers.stream import streamStates
					if self.onEvent not in streamStates:
						streamStates.append(self.onEvent)
				except:
					pass

	def removeEvent(self):
		if HAS_OPENWEBIF:
			try:
				from Plugins.Extensions.OpenWebif.controllers.stream import streamStates
				if self.onEvent in streamStates:
					streamStates.remove(self.onEvent)
			except:
				pass

	def onInit(self):
		if config.infobartunerstate.plugin_openwebif.enabled.value:
			if HAS_OPENWEBIF:
				try:
					from Plugins.Extensions.WebInterface.WebScreens import streamList
				except:
					streamList = []
				#TODO file streaming actually not supported
				for stream in streamList:
					# Check if screen exists
					if stream and stream.request and 'file' not in stream.request.args:
						self.onEvent(StreamAdapter.EV_BEGIN, stream)

	def onEvent(self, event, stream):
		print "IBTS Stream Event OpenWebIf"
		if StreamAdapter and stream:
			if (event == StreamAdapter.EV_BEGIN):
				id = getStreamID(stream)
				print "IBTS Stream Event OpenWebIf Start " + id
				
				irecordservice = stream.getService()
				
				eservicereference = stream.ref
				
				# Extract parameters
				ip = stream.clientIP
				
				# Delete references to avoid blocking tuners
				del stream
				
				tuner, tunertype, tunernumber = getTunerByPlayableService(irecordservice) 
				
				name = getEventName(eservicereference)
				
				number =  getNumber(eservicereference)
				channel = getChannel(eservicereference)
				
				client = getClient(ip)
				
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				if gInfoBarTunerState:
					gInfoBarTunerState.addEntry(id, self.getPluginName(), self.getType(), self.getText(), tuner, tunertype, tunernumber, name, number, channel, time(), 0, True, "", client, ip)
					gInfoBarTunerState.onEvent()
			
			elif event == StreamAdapter.EV_STOP:
				
				# Remove Finished Stream
				id = getStreamID(stream)
				print "IBTS Stream Event OpenWebIf End " + id
				
				# Delete references to avoid blocking tuners
				del stream
				
				from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
				if gInfoBarTunerState:
					gInfoBarTunerState.finishEntry(id)
					gInfoBarTunerState.onEvent()

	def update(self, id, tunerstate):
		
		stream = getStream( id )
		if stream:
		
			ref = stream.ref
			
			del stream
			
			tunerstate.name = getEventName(ref)
			
			return True
			
		else:
			
			# Stream is not active anymore
			return None
