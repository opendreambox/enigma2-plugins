#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Coded by betonme (c) 2011 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=162629
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

import socket

# Config
from Components.config import *

# Screen
from Components.NimManager import nimmanager
from enigma import eServiceCenter, eServiceReference, eEPGCache
from enigma import iServiceInformation, iPlayableService, iRecordableService, iPlayableServicePtr, iRecordableServicePtr
from ServiceReference import ServiceReference


#######################################################
# Global helper functions
def getTunerName(slot_number):
	name = ""
	try:
		name = str(nimmanager.getNimSlotInputName( int(slot_number) ))
	except:
		pass
	if name == "":
		name = str(chr( int(slot_number) + ord('A') ))
	return name

def normTuner(data):
	if isinstance(data, dict ):
		tuner_type = str(data.get("tuner_type", ""))
		slot_number = data.get("slot_number", -1)
		if slot_number is None or slot_number < 0:
			slot_number = data.get("tuner_number", -1)
		if slot_number is not None and slot_number > -1:
			return ( getTunerName(slot_number), tuner_type, slot_number )
		else:
			return ( "", tuner_type, slot_number )
	return ( "", "", None )

def getTunerByServiceReferenceOLD(eservicereference):
	if isinstance(eservicereference, eServiceReference):
		serviceHandler = eServiceCenter.getInstance()
		serviceInfo = serviceHandler.info(eservicereference)
		data = serviceInfo and serviceInfo.getInfoObject(eservicereference, iServiceInformation.sTransponderData)
		return normTuner(data)
	return ( "", "", None )

def getTunerByServiceReference(servicereference):
	if isinstance(servicereference, ServiceReference):
		info = servicereference.info()
		data = info and info.getInfoObject(servicereference.ref, iServiceInformation.sTransponderData)
		return normTuner(data)
	return ( "", "", None )

def getTunerByPlayableService(iservice):
	if isinstance(iservice, ( iPlayableService, iRecordableService, iPlayableServicePtr, iRecordableServicePtr ) ):
		feinfo = iservice and iservice.frontendInfo()
		data = feinfo and feinfo.getFrontendData()
		return normTuner(data)
	return ( "", "", None )

def getNumber(eservicereference):
	if isinstance(eservicereference, eServiceReference):
		
		from Screens.InfoBar import InfoBar
		Servicelist = None
		if InfoBar and InfoBar.instance:
			Servicelist = InfoBar.instance.servicelist
		
		mask = (eServiceReference.isMarker | eServiceReference.isDirectory)
		number = 0
		
		bouquets = Servicelist and Servicelist.getBouquetList()
		if bouquets:
			
			#TODO get alternative for actbouquet
			actbouquet = Servicelist.getRoot()
			serviceHandler = eServiceCenter.getInstance()
			for name, bouquet in bouquets:
				
				if not bouquet.valid(): #check end of list
					break
				
				if bouquet.flags & eServiceReference.isDirectory:
					
					servicelist = serviceHandler.list(bouquet)
					if not servicelist is None:
						
						while True:
							service = servicelist.getNext()
							if not service.valid(): #check end of list
								break
							playable = not (service.flags & mask)
							if playable:
								number += 1
							if actbouquet:
								if actbouquet == bouquet and eservicereference == service:
									return number
							elif eservicereference == service:
								return number
	return None

def getChannel(eservicereference):
	if isinstance(eservicereference, eServiceReference):
		servicereference = ServiceReference(eservicereference)
		if servicereference:
			return servicereference.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
	return ""

def getEventData(iservice):
	if isinstance(iservice, ( iPlayableService, iRecordableService, iPlayableServicePtr, iRecordableServicePtr ) ):
		info = iservice and iservice.info()
		event = info and info.getEvent(0)
		if event:
			name = event.getEventName() or ""
			begin = event.getBeginTime() or 0
			duration = event.getDuration() or 0
			end = begin + duration or 0
			return (name,begin,end)
	return ("",0,0)

def getEventName(eservicereference):
	if isinstance(eservicereference, eServiceReference):
		epg = eEPGCache.getInstance()
		event = epg and epg.lookupEventTime(eservicereference, -1, 0)
		if event: 
			return event.getEventName()
	return ""

def getClient(ip):
	try:
		host = ip and socket.gethostbyaddr( ip )
		if host:
			return host[0].split('.')[0]
	except:
		pass
	return ""


#######################################################
# Not used yet
def readBouquetList(self):
	serviceHandler = eServiceCenter.getInstance()
	refstr = '1:134:1:0:0:0:0:0:0:0:FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet'
	bouquetroot = eServiceReference(refstr)
	self.bouquetlist = {}
	list = serviceHandler.list(bouquetroot)
	if list is not None:
		self.bouquetlist = list.getContent("CN", True)

