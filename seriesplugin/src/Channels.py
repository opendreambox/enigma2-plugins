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

# Config
from Components.config import config

#from enigma import eEPGCache, eServiceReference, eServiceCenter
from ServiceReference import ServiceReference

from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction

# XML
from xml.etree.cElementTree import ElementTree, tostring, parse, Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Plugin internal
from . import _
from Logger import splog

try:
	#Python >= 2.7
	from collections import OrderedDict
except:
	from OrderedDict import OrderedDict


CompiledRegexpSeries = re.compile('(.*)[ _][Ss]{,1}\d{1,2}[EeXx]\d{1,2}.*')  #Only for S01E01 OR 01x01 + optional title
def removeEpisodeInfo(text):
	# Very basic Series Episode remove function
	m = CompiledRegexpSeries.match(text)
	if m:
		#splog(m.group(0))     # Entire match
		#splog(m.group(1))     # First parenthesized subgroup
		if m.group(1):
			text = m.group(1)
	return text


ChannelReplaceDict = OrderedDict([
	('\(S\)', ''),
	('HD', ''),
	('III', 'drei'),
	('II',  'zwei'),
	#('I',   'eins'),
	('ARD', 'DasErste'),
	('\+', 'Plus'),
	('0', 'null'),
	('1', 'eins'),
	('2', 'zwei'),
	('3', 'drei'),
	('4', 'vier'),
	('5', 'fuenf'),
	('6', 'sechs'),
	('7', 'sieben'),
	('8', 'acht'),
	('9', 'neun'),
	('\xc3\xa4', 'ae'),
	('\xc3\xb6', 'oe'),
	('\xc3\xbc', 'ue'),
	('\xc3\x84', 'ae'),
	('\xc3\x96', 'oe'),
	('\xc3\x9c', 'ue'),
	('\xc3\x9f', 'ss'),
])
CompiledRegexpChannelUnify = re.compile('|'.join(ChannelReplaceDict))
CompiledRegexpChannelRemoveSpecialChars = re.compile('[^a-zA-Z0-9]')
def unifyChannel(text):
	def translate(match):
		m = match.group(0)
		return ChannelReplaceDict.get(m, m)
	
	text = CompiledRegexpChannelUnify.sub(translate, text)
	text = text.decode("utf-8").encode("latin1")
	text = CompiledRegexpChannelRemoveSpecialChars.sub('', text)
	return text.strip().lower()


channels = {}  # channels[reference] = ( name, [ (name1, uname1), (name2, uname2), ... ] )
channels_changed = False
	
def lookupServiceAlternatives(service):
	global channels, channels_changed
	
	splog("lookupServiceAlternatives service", service)
	ref = str(service)
	ref = re.sub('::.*', ':', ref)
	splog("lookupServiceAlternatives ref", ref)
	#splog("lookupServiceAlternatives channels before", channels)
	splog("lookupServiceAlternatives ref in channels", ref in channels)
	if ref in channels:
		name, alternatives = channels.get(ref)
	else:
		name = ServiceReference(ref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
		alternatives = [ ( name, unifyChannel(name) ), ]
		channels[ref] = ( name, alternatives )
		channels_changed = True
	
	splog("lookupServiceAlternatives channels")
	for channel in channels:
		splog(channel)
	splog("lookupServiceAlternatives alternatives")
	for alternative in alternatives:
		splog(alternative)
	
	return alternatives

def compareChannels(locals, remote, service):
	#global channels
	
	uremote = unifyChannel(remote)		
	splog(locals, remote, uremote, len(uremote))
	
	for name, uname in locals:
		if uname == uremote:
			# The channels are equal
			return True
		elif uname in uremote or uremote in uname:
			# Parts of the channels are equal
			return True
		#elif uname == "":
		#	# The local channel is empty
		#	return True
		elif "unknown" in uname:
			# The local channel is unknown
			return True

		# Ask the user only if we are called from SeriesPluginInfoScreen
		from SeriesPluginInfoScreen import instance
		if config.plugins.seriesplugin.channel_popups.value and instance:
			names = [ name for name, uname in locals ]
			instance.session.openWithCallback(
				boundFunction(channelEqual, locals, remote, uremote, service),
				MessageBox,
				"SeriesPlugin:\n"+ _("Are these channels equal?")+ "\n"+ str(remote)+ "\n"+str(names),
				type = MessageBox.TYPE_YESNO
			)
	return False

def channelEqual(locals, remote, uremote, service, equal):
	global channels, channels_changed
	
	if equal:
		# Add remote to alternative channels
		for reference, namealternatives in channels.iteritems():
			name, alternatives = namealternatives
			splog("locals, alternatives:", locals, alternatives)
			if alternatives == locals:
				ref = str(service)
				ref = re.sub('::.*', ':', ref)
				name = ServiceReference(ref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
				
				# Maybe we should append the new entry
				channels[ref] = ( name, [(remote, uremote)] )
				channels_changed = True
				splog("SP channel added ", channels)
				break
		# The channel will be saved, restart the last request
		#TODO show message ?!?


class ChannelsFile(object):

	def __init__(self):
		self.mtime = -1
		self.cache = ""

	def readXML(self):
		path = config.plugins.seriesplugin.channel_file.value
		
		# Abort if no config found
		if not os.path.exists(path):
			splog("No configuration file present")
			return None
		
		# Parse if mtime differs from whats saved
		mtime = os.path.getmtime(path)
		if mtime == self.mtime:
			# No changes in configuration, won't read again
			return self.cache
		
		# Parse XML
		try:
			etree = parse(path).getroot()
		except Exception as e:
			splog("Exception in readXML: " + str(e))
			etree = None
			mtime = -1
		
		# Save time and cache file content
		self.mtime = mtime
		self.cache = etree
		return self.cache

	def writeXML(self, etree):
		path = config.plugins.seriesplugin.channel_file.value
		
		def indent(elem, level=0):
			i = "\n" + level*"  "
			if len(elem):
				if not elem.text or not elem.text.strip():
					elem.text = i + "  "
				if not elem.tail or not elem.tail.strip():
					elem.tail = i
				for elem in elem:
					indent(elem, level+1)
				if not elem.tail or not elem.tail.strip():
					elem.tail = i
			else:
				if level and (not elem.tail or not elem.tail.strip()):
					elem.tail = i
		
		indent(etree)
		data = tostring(etree, 'utf-8')
		
		f = None
		try:
			f = open(path, 'w')
			if data:
				f.writelines(data)
		except Exception as e:
			splog("Exception in writeXML: " + str(e))
		finally:
			if f is not None:
				f.close()
		
		# Save time and cache file content
		self.mtime = os.path.getmtime( path )
		self.cache = etree


class ChannelsBase(ChannelsFile):

	def __init__(self):
		ChannelsFile.__init__(self)
		
		global channels, channels_changed
		channels = {}  # channels[reference] = ( name, [ (name1, uname1), (name2, uname2), ... ] )
		channels_changed = False
		
		self.loadXML()
	
	def loadXML(self):
		global channels
		
		# Read xml config file
		root = self.readXML()
		if root:
			channels = {}
			
			# Parse Config
			def parse(root):
				channels = {}
				if root:
					for element in root.findall("Channel"):
						name = element.get("name", "")
						reference = element.get("reference", "")
						if name and reference:
							#alternatives = []
							alternatives = [(name, unifyChannel(name))]
							for alternative in element.findall("Alternative"):
								alternatives.append( ( alternative.text , unifyChannel(alternative.text) ) )
							channels[reference] = (name, list(set(alternatives)))
				return channels
			
			channels = parse( root )
			splog("loadXML channels", channels)
		else:
			channels = {}

	def saveXML(self):
		global channels, channels_changed
		
		if channels_changed:
			
			# Generate List in RAM
			root = None
			splog("saveXML channels", channels)
			
			# Build Header
			from plugin import NAME, VERSION
			root = Element(NAME)
			root.set('version', VERSION)
			root.append(Comment(_("Don't edit this manually unless you really know what you are doing")))
			
			# Build Body
			def build(root, channels):
				if channels:
					for reference, namealternatives in channels.iteritems():
						name, alternatives = namealternatives
						# Add channel
						element = SubElement( root, "Channel", name = stringToXML(name), reference = stringToXML(reference) )
						# Add alternatives
						if alternatives:
							for name, uname in alternatives:
								#SubElement( element, "Alternative", identifier = stringToXML(NOTUSED) ).text = stringToXML(name)
								SubElement( element, "Alternative" ).text = stringToXML(name)
				return root
			
			root = build( root, channels )
			
			self.writeXML( root )
