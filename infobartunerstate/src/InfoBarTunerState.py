# -*- coding: utf-8 -*-
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
import math
import os

from collections import defaultdict
from operator import attrgetter, itemgetter
try:
	from itertools import izip_longest as zip_longest # py2x
except:
	from itertools import zip_longest # py3k

# Plugin
from Plugins.Plugin import PluginDescriptor

# Config
from Components.config import *

# Screen
from Components.Label import Label
from Components.Language import *
from Components.NimManager import nimmanager
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.Screen import Screen
from Screens.InfoBar import InfoBar
from Screens.InfoBarGenerics import InfoBarShowHide
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from time import strftime, time, localtime, mktime
from datetime import datetime, timedelta

from enigma import iServiceInformation, ePoint, eSize, getDesktop, iFrontendInformation
from enigma import eTimer
from enigma import iPlayableService, iRecordableService
from enigma import eActionMap, eListboxPythonMultiContent, eListboxPythonStringContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER

from skin import parseColor, parseFont

# Plugin internal
from InfoBarHandler import InfoBarHandler, overwriteInfoBar, recoverInfoBar
from ExtensionHandler import addExtension, removeExtension
from InfoBarTunerStatePlugins import InfoBarTunerStatePlugins

# Extenal plugins
#try:
#	from Plugins.Extensions.2IB import SecondInfoBar
#	SecondInfobarAvailable = True
#except:
SecondInfobarAvailable = False


# Type Enum
# 1. Used for pixmap mapping
# 2. Used to set priority for calling the plugins onShow event: Higher numbers will be served first
UNKNOWN, INFO, TIMER, LIVE, RECORD, STREAM, FINISHED = range( 7 )

# Constants
INFINITY =  u"\u221E".encode("utf-8")


#######################################################
# Logical background task
class InfoBarTunerState(InfoBarTunerStatePlugins, InfoBarHandler):
	def __init__(self, session):
		InfoBarTunerStatePlugins.__init__(self)
		InfoBarHandler.__init__(self)
		self.session = session
		
		self._shown = False
		
		self.info = None
		
		#TODO showTimer is used to avoid several recalls
		#TODO find another solution, e.g.
		# if IBTS is already shown, skip
		self.showTimer = eTimer()
		try:
			self.showTimer_conn = self.showTimer.timeout.connect(self.timerShow)
		except:
			self.showTimer.callback.append(self.timerShow)
		
		self.hideTimer = eTimer()
		try:
			self.hideTimer_conn = self.hideTimer.timeout.connect(self.timerHide)
		except:
			self.hideTimer.callback.append(self.timerHide)
		
		self.updateTimer = eTimer()
		try:
			self.updateTimer_conn = self.updateTimer.timeout.connect(self.timerUpdate)
		except:
			self.updateTimer.callback.append(self.timerUpdate)
		
		self.entries = defaultdict(list)
		
		# Get Initial Skin parameters
		win = self.session.instantiateDialog(TunerStateBase)
		self.positionx = win.instance.position().x()
		self.positiony = win.instance.position().y()
		self.height = win.instance.size().height()
		self.spacing = win.spacing
		self.padding = win.padding
		
		desktopSize = getDesktop(0).size()
		self.desktopwidth = desktopSize.width()
		
		#TODO is it possible to create copies of a screen to avoid recreation
		win.close()
		
		# Bind recording and streaming events
		self.appendEvents()
		
		#TODO PiP
		#self.session.
		#InfoBar.instance.session
		#pip.currentService = service
		#pip.pipservice = iPlayableService
		#Events:
		#eventNewProgramInfo
		#decoder state

	def appendEvents(self):
		for plugin in self.getPlugins():
			plugin.appendEvent()

	def removeEvents(self):
		for plugin in self.getPlugins():
			plugin.removeEvent()
	
	def onInit(self):
		for plugin in self.getPlugins():
			plugin.onInit()
	
	#TODO Config show on timer time changed
	#def __OnTimeChanged(self):
	#	self.show(True)
	
	def hasEntry(self, id):
		return id in self.entries
	
	def addEntry(self, id, plugin, type, text, tuner="", tunertype="", tunernumber=None, name="", number=None, channel="", begin=0, end=0, endless=False, filename="", client="", ip="", port=""):
		print "IBTS addEntry", id
		win = self.session.instantiateDialog(TunerState, plugin, type, text, tuner, tunertype, tunernumber, name, number, channel, begin, end, endless, filename, client, ip, port)
		self.entries[id] = win
		return win
	
	def updateEntry(self, id, type, begin, end, endless):
		if id in self.entries:
			win = self.entries[id]
			win.updateType( type )
			win.updateTimes( begin, end, endless )
			win.update()
	
	def finishEntry(self, id):
		print "IBTS finishEntry", id
		if id in self.entries:
			win = self.entries[id]
			win.updateTimes( None, time(), False )
			win.updateType( FINISHED )
			win.update()
	
	def updateName(self, id, name):
		if id in self.entries:
			win = self.entries[id]
			win.updateName( name )
	
	def updateNumberChannel(self, id, number, channel):
		if id in self.entries:
			win = self.entries[id]
			win.updateNumberChannel( number, channel)
	
	def updateFilename(self, id, filename):
		if id in self.entries:
			win = self.entries[id]
			win.updateFilename( filename )
	
	def removeEntry(self, id):
		if id in self.entries:
			win = self.entries[id]
			win.remove()
	
	def timerShow(self):
		print "IBTS timerShow"
		self.tunerShow()
	
	def timerHide(self):
		print "IBTS timerHide"
		self.tunerHide()
	
	def timerUpdate(self):
		print "IBTS timerUpdate"
		self.update()
	
	def onEvent(self):
		if config.infobartunerstate.show_events.value:
			self.show(True, True)
	
	def show(self, autohide=False, forceshow=False):
		print "IBTS show ", autohide, forceshow
		
		if self._shown:
			return
		
		#TEST
		#if SecondInfobarAvailable:
		#	try:
		#		if self.infobar.SIBdialog.shown:
		#			print "IBTS SecondInfobar is shown"
		#			return
		#	except Exception, e:
		#		print "InfoBarTunerState show SIB exception " + str(e)
		
		allowclosing = True
		if self.updateTimer.isActive() and autohide:
			# Avoid closing if the update timer is active
			allowclosing = False
		if self.showTimer.isActive():
			self.showTimer.stop()
		
		if forceshow:
			self.tunerShow(forceshow=forceshow)
		else:
			# Start show timer as on time shot
			self.showTimer.start( 10, True )
			
			# Start update timer as cyclic timer
			self.updateTimer.start( 60 * 1000 )
			
		if allowclosing:
			if autohide or self.session.current_dialog is None or not issubclass(self.session.current_dialog.__class__, InfoBarShowHide):
				# Start timer to avoid permanent displaying
				# Do not start timer if no timeout is configured
				#timeout = int(config.infobartunerstate.infobar_timeout.value) or int(config.usage.infobar_timeout.index)
				timeout = int(config.usage.infobar_timeout.index)
				if timeout > 0:
					if self.hideTimer.isActive():
						self.hideTimer.stop()
					self.hideTimer.startLongTimer( timeout )
				if self.updateTimer.isActive():
					self.updateTimer.stop()
		else:
			if self.hideTimer.isActive():
				self.hideTimer.stop()

	def toggle(self):
		print "IBTS toggle"
		if self._shown is False:
			self.show()
		else:
			self.hide()

	
	def handleFinished(self):
		if self.entries:
			
			# Delete entries:
			#  if entry reached timeout
			#  if number of entries is reached
			numberfinished = 0
			for id, win in sorted( self.entries.items(), key=lambda x: (x[1].end), reverse=True ):
				if win.type == FINISHED:
					numberfinished += 1
				if win.toberemoved == True \
					or win.type == FINISHED and numberfinished > int( config.infobartunerstate.number_finished_entries.value ):
					# Delete Stopped Timers
					win.hide()
					self.session.deleteDialog(win)
					del self.entries[id]

	def updateMetrics(self):
		if self.entries:
		
			# Dynamic column resizing and repositioning
			widths = []
			for id, win in self.entries.items():
				win.update()
				
				# Calculate field width
				widths = map( lambda (w1, w2): max( w1, w2 ), zip_longest( widths, win.widths ) )
			
			# Get initial padding / offset position and apply user offset
			padding = self.padding + int(config.infobartunerstate.offset_padding.value)
			#print "IBTS px, self.padding, config.padding", px, self.padding, int(config.infobartunerstate.offset_padding.value)
			
			# Calculate field spacing
			spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
			#print "IBTS spacing, self.spaceing, config.spacing", spacing, self.spacing, int(config.infobartunerstate.offset_spacing.value)
			#widths = [ width+spacing if width>0 else 0 for width in widths ]
			
			# Apply user offsets
			posx = self.positionx + int(config.infobartunerstate.offset_horizontal.value)
			#print "IBTS posx, self.positionx, config.offset_horizontal", posx, self.positionx, int(config.infobartunerstate.offset_horizontal.value)
			posy = self.positiony + int(config.infobartunerstate.offset_vertical.value)
			height = self.height
			#print "IBTS widths", widths
			
			# Handle maximum width
			overwidth = posx + sum(widths) + len([w for w in widths if w]) * spacing + padding - self.desktopwidth + int(config.infobartunerstate.offset_rightside.value)
			#print "IBTS overwidth", overwidth
			
			# Order windows
			wins = sorted( self.entries.itervalues(), key=lambda x: (x.type, x.endless, x.begin), reverse=config.infobartunerstate.list_goesup.value )
			
			# Resize, move and show windows
			for win in wins:
				win.move( posx, posy )
				win.reorder( widths, overwidth )
				if config.infobartunerstate.list_goesup.value == False:
					posy += height
				else:
					posy -= height
				# Show windows
				win.show()

	def tunerShow(self, forceshow=False):
		print "IBTS tunerShow"
		self._shown = True
		
		for plugin in self.getPlugins():
			plugin.onShow(self.entries)
		
		if self.entries:
			# There are active entries
			
			# Close info screen
			if self.info:
				self.info.hide()
			
			# Only show the Tuner information dialog,
			# if no screen is displayed or the InfoBar is visible
			#TODO Info can also be showed if info.rectangle is outside currentdialog.rectangle
			#if self.session.current_dialog is None \
			#	or isinstance(self.session.current_dialog, InfoBar):
			#MAYBE Tuner Informationen werden zusammen mit der EMCMediaCenter InfoBar angezeigt
			#or isinstance(self.session.current_dialog, EMCMediaCenter):
			
			self.handleFinished()
			
			# Update window content
			for id, win in self.entries.items():
				if self.isPlugin(win.plugin):
					result = self.getPlugin(win.plugin).update(id, win)
					if result is None:
						win.updateTimes( None, time(), False )
						win.updateType( FINISHED )
			
			self.updateMetrics()
			
		elif forceshow:
			# No entries available
			try:
				if not self.info:
					self.info = self.session.instantiateDialog( TunerStateInfo, _("Nothing running") )
				self.info.show()
				print "IBTS self.info.type", self.info.type
			except Exception, e:
				print "InfoBarTunerState show exception " + str(e)

	def update(self):
		print "IBTS update"
		self.tunerShow()

	def hide(self):
		print "IBTS hide"
		if self.updateTimer.isActive():
			self.updateTimer.stop()
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		self.hideTimer.start( 10, True )

	def tunerHide(self):
		print "IBTS tunerHide"
		for win in self.entries.itervalues():
			win.hide()
		if self.info:
			self.info.hide()
		self._shown = False

	def close(self):
		print "IBTS close"
		recoverInfoBar()
		removeExtension()
		self.unbindInfoBar()
		self.removeEvents()
		self.tunerHide()
		for id, win in self.entries.items():
			win.hide()
			self.session.deleteDialog(win)
			del self.entries[id]
		from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
		global gInfoBarTunerState
		gInfoBarTunerState = None


#######################################################
# Base screen class, contains all skin relevant parts
class TunerStateBase(Screen):
	# Skin will only be read once
	skinfile = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/InfoBarTunerState/skin.xml" )
	skin = open(skinfile).read()

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "TunerState"
		
		self["Background"] = Pixmap()
		self["Type"] = MultiPixmap()
		self["Progress"] = ProgressBar()
		
		for i in xrange( len( config.infobartunerstate.fields.dict() ) ):
		#for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			label = Label()
			#fieldid = "Field"+str(i)
			self[ "Field"+str(i) ] = label
		
		self.padding = 0
		self.spacing = 0
		
		self.widths = []
		
		self.typewidth = 0
		self.progresswidth = 0
		
		self.toberemoved = False
		
		self.onLayoutFinish.append(self.layoutFinished)

	def applySkin(self):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "padding":
					self.padding = int(value)
				elif attrib == "spacing":
					self.spacing = int(value)
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return Screen.applySkin(self)

	def layoutFinished(self):
		#TODO Possible to read in applySkin
		self.typewidth = self["Type"].instance.size().width()
		self.progresswidth = self["Progress"].instance.size().width()

	def reorder(self, widths, overwidth=0):
		# Get initial padding / offset position and apply user offset
		padding = self.padding + int(config.infobartunerstate.offset_padding.value)
		#print "IBTS px, self.padding, config.padding", px, self.padding, int(config.infobartunerstate.offset_padding.value)
		
		# Calculate field spacing
		spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
		#print "IBTS spacing, self.spaceing, config.spacing", spacing, self.spacing, int(config.infobartunerstate.offset_spacing.value)
		
		px = padding
		py = 0
		sh = self.instance.size().height()
		#print self.widths
		
		fieldwidths = config.infobartunerstate.fieldswidth.dict().values()
		
		for i, (c, width) in enumerate( zip( config.infobartunerstate.fields.dict().values(), widths ) ):
			fieldid = "Field"+str(i)
			field = c.value
			if field == "TypeIcon":
				self["Type"].instance.move( ePoint(px, py) )
			
			elif field == "TimerProgressGraphical":
				#self[field].instance.resize( eSize(width, sh) )
				# Center the progress field vertically
				y = int( ( sh - self["Progress"].instance.size().height() ) / 2 )
				self["Progress"].instance.move( ePoint(px, y) )
			
			elif field == "Name":
				if config.infobartunerstate.variable_field_width.value:
					width -= max(0, overwidth)
				else:
					width -= overwidth
				self[fieldid].instance.resize( eSize(width, sh) )
				self[fieldid].instance.move( ePoint(px, py) )
			
			#elif field == "None":
			#	pass
			
			else:
				self[fieldid].instance.resize( eSize(width, sh) )
				self[fieldid].instance.move( ePoint(px, py) )
			
			#TODO I think we could simplify this
			# Avoid unnecesarry resize and move operations
			#for j, fieldwidth in enumerate( config.infobartunerstate.fieldswidth.dict().values() ):
			#	if i == j and int(fieldwidth.value) > 0 and not (field == "TimerProgressGraphical" or field == "TypeIcon" or field == "None"):
			if fieldwidths:
				fieldwidth = int( fieldwidths[i].value )
				if fieldwidth > 0 and not (field == "TimerProgressGraphical" or field == "TypeIcon" or field == "None"):
					# Handle new maximum width
					if width > 0:
						overwidth +=  fieldwidth - width
					else:		
						overwidth +=  fieldwidth - width + spacing
					width = fieldwidth
					self[fieldid].instance.resize( eSize(width, sh) )
					self[fieldid].instance.move( ePoint(px, py) )
					
			if width:
				px += width + spacing
			
		# Set background
		bw = self["Background"].instance.size().width()
		# Avoid background start position is within our window
		bw = px-bw if px-bw<0 else 0
		self["Background"].instance.move( ePoint(bw, py) )
		self.instance.resize( eSize(px, sh) )

	def move(self, posx, posy):
		self.instance.move(ePoint(posx, posy))

	def remove(self):
		self.toberemoved = True 


#######################################################
# Displaying screen class, show nothing running
class TunerStateInfo(TunerStateBase):
	#TODO reuse TunerState and avoid a clone class
	def __init__(self, session, name):
		TunerStateBase.__init__(self, session)
		
		self.plugin = "Info"
		self.type = INFO
		self.name = name
		self.tunernumber = None
		
		if not config.infobartunerstate.background_transparency.value:
			self["Background"].show()
		else:
			self["Background"].hide()
		
		self["Progress"].hide()
		
		#for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
		for i in xrange( len( config.infobartunerstate.fields.dict() ) ):
			fieldid = "Field"+str(i)
			
			if fieldid == "Field0":
				#self[field].setText( str(self.name).encode("utf-8") )
				self[fieldid].setText( str(self.name) )
		
		self.onLayoutFinish.append(self.popup)

	def popup(self):
		print "IBTS popup"
		
		self["Type"].setPixmapNum(3)
		
		widths = []
		widths.append( self.typewidth )
		
		height = self.instance.size().height()
		
		#for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
		for i in xrange( len( config.infobartunerstate.fields.dict() ) ):
			fieldid = "Field"+str(i)
			
			#Workaround#1 Set default size
			self[fieldid].instance.resize( eSize(1000, height) )
			
			width = max(self[fieldid].instance.calculateSize().width(), 0)
			#print width
			
			#Workaround#2 Expand the calculate size
			width = int( width * 1.10 )
			
			#self[field].instance.resize( eSize(width, height) )
			
			widths.append( width )
		
		self.widths = widths
		
		#spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
		#widths = [ width+spacing if width>0 else 0 for width in widths ]
		
		posx = self.instance.position().x() + int(config.infobartunerstate.offset_horizontal.value) 
		posy = self.instance.position().y() + int(config.infobartunerstate.offset_vertical.value)
		
		self.move( posx, posy )
		self.reorder(widths)


#######################################################
# Displaying screen class, every entry is an instance of this class
class TunerState(TunerStateBase):
	def __init__(self, session, plugin, type, text, tuner, tunertype, tunernumber, name="", number=None, channel="", begin=0, end=0, endless=False, filename="", client="", ip="", port=""):
		#TODO use parameter ref instead of number and channel
		TunerStateBase.__init__(self, session)
		
		self.removeTimer = eTimer()
		try:
			self.removeTimer_conn = self.removeTimer.timeout.connect(self.remove)
		except:
			self.removeTimer.callback.append(self.remove)
		
		self.plugin = plugin
		
		self.type = type
		self.text = text
		
		self.tuner = tuner
		self.tunertype = tunertype
		self.tunernumber = tunernumber
		
		self.name = name
		
		self.number = number
		self.channel = channel
		
		self.filename = filename + ".ts"
		self.destination = filename and os.path.dirname( filename )
		
		self.filesize = None
		self.freespace = None
		
		self.client = client
		self.ip = ip
		self.port = port
		
		self.begin = begin
		self.end = end
		self.endless = endless
		
		self.timeleft = None
		self.timeelapsed = None
		self.duration = None
		self.progress = None
	
	def updateName(self, name):
		self.name = name

	def updateNumberChannel(self, number, channel):
		self.number = number
		self.channel = channel

	def updateFilename(self, filename):
		self.filename = filename + ".ts"

	def updateType(self, type):
		if self.type != type:
			self.type = type
		if self.type == FINISHED:
			print "IBTS updateType FINISHED"
			self.tuner = _("-")
			self.tunertype = _("-")
			# Check if timer is already started
			if not self.removeTimer.isActive():
				# Check if timeout is configured
				timeout = int(config.infobartunerstate.timeout_finished_entries.value)
				if timeout > 0:
					self.removeTimer.startLongTimer( timeout )

	def updateTimes(self, begin, end, endless):
		if begin is not None:
			self.begin = begin
		if end is not None:
			self.end = end
		if endless is not None:
			self.endless = endless

	def updateDynamicContent(self):
		
		# Time and progress
		now = time()
		begin = self.begin
		end = self.end
		
		duration = None
		timeleft = None
		timeelapsed = None
		progress = None
		
		duration = begin and end and end - begin
		if duration and duration < 0:
			duration = None
		
		if self.type == FINISHED:
			# Finished events
			timeelapsed = None #duration
		elif begin and end and begin < now:
			timeelapsed = min(now - begin, duration)
		else:
			# Future event
			timeelapsed = None
		
		if not self.endless and self.end:
			
			if self.type == FINISHED:
				# Finished events
				timeleft = None #0
			elif begin and end and begin < now:
				timeleft = max(end - now, 0)
			else:
				# Future event
				timeleft = None
			
			if timeelapsed and duration:
				# Adjust the watched movie length (98% of movie length) 
				# else we will never see the 100%
				# Alternative using math.ceil but then we won't see 0
				length = duration / 100.0 * 98.0
				# Calculate progress and round up
				progress = timeelapsed / length * 100.0
				# Normalize progress
				if progress < 0: progress = 0
				elif progress > 100: progress = 100
			else:
				progress = None
			
		self.duration    = duration and duration is not None and       int( math.ceil( ( duration ) / 60.0 ) )
		self.timeleft    = timeleft and timeleft is not None and       int( math.ceil( ( timeleft ) / 60.0 ) )
		self.timeelapsed = timeelapsed and timeelapsed is not None and int( math.ceil( ( timeelapsed ) / 60.0 ) )
		self.progress    = progress and progress is not None and       int( progress )
		#print "IBTS duration, timeleft, timeelapsed, progress", self.duration, self.timeleft, self.timeelapsed, self.progress
		
		
		#Adapted from: from Components.Harddisk import findMountPoint
		def mountpoint(path):
			path = os.path.realpath(path)
			if os.path.ismount(path) or len(path)==0: return path
			return mountpoint(os.path.dirname(path))
		
		def getDevicebyMountpoint(hdm, mountpoint):
			for x in hdm.partitions[:]:
				if x.mountpoint == mountpoint:
					return x.device
			return None
		
		def getHDD(hdm, part):
			for hdd in hdm.hdd:
				if hdd.device == part[:3]:
					return hdd
			return None
		
		def hddIsAvailable(path):
			# User specified to avoid HDD wakeup if it is sleeping
			from Components.Harddisk import harddiskmanager
			dev = getDevicebyMountpoint( harddiskmanager, mountpoint(path) )
			if dev is not None:
				hdd = getHDD( harddiskmanager, dev )
				if hdd is not None:
					if not hdd.isSleeping():
						return True
			return False
		
		# File site and free disk space
		filename = self.filename
		self.filesize = None
		self.freespace = None
		if filename:
			
			for c in config.infobartunerstate.fields.dict().itervalues():
				if c.value == "FileSize":
					break
				if c.value == "FreeSpace":
					break
			else:
				# We do not need to calculate the following values
				return
			
			# We need a replacement function for ismount
			# Bad workaround - skip all pathes which start with /mnt
			if config.infobartunerstate.skip_mounts.value and filename.startswith("/mnt/"): #os.path.ismount( filename ):
				pass
			
			elif config.infobartunerstate.wake_hdd.value or hddIsAvailable( filename ):
			
				if os.path.exists( filename ):
					filesize = os.path.getsize( filename ) 
					self.filesize = int( filesize / (1024*1024) )
					
					try:
						stat = os.statvfs( filename )
						self.freespace = int ( ( stat.f_bfree / 1000 * stat.f_bsize / 1000 ) / 1024 )
						#self.freespace = os.stat(filename).st_size/1048576)
					except OSError:
						pass

	def update(self):
		
		self.updateDynamicContent()
		
		height = self.instance.size().height()
		widths = []
		
		# Set background transparency
		if not config.infobartunerstate.background_transparency.value:
			self["Background"].show()
		else:
			self["Background"].hide()
		
		self["Type"].hide()
		self["Progress"].hide()
		
		for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			fieldid = "Field"+str(i)
			field = c.value
			text = ""
			#print "IBTS DEBUG", self.plugin, field
			
			if field == "TypeIcon":
				self["Type"].show()
				if self.type == TIMER:
					self["Type"].setPixmapNum(3)
				elif self.type == RECORD:
					self["Type"].setPixmapNum(0)
				elif self.type == FINISHED:
					self["Type"].setPixmapNum(2)
				elif self.type == INFO:
					self["Type"].setPixmapNum(3)
				elif self.type == LIVE:
					self["Type"].setPixmapNum(4)
				elif self.type == UNKNOWN:
					self["Type"].setPixmapNum(5)
				elif self.type == STREAM:
					self["Type"].setPixmapNum(1)
				else:
					widths.append( 0 )
					continue
				# No resize necessary
				widths.append( self.typewidth )
				continue
			
			elif field == "TypeText":
				text = _( self.text )
			
			elif field == "Tuner":
				if self.tuner:
					text = self.tuner
			
			elif field == "TunerType":
				if self.tunertype:
					text = self.tunertype
			
			elif field == "Number":
				if isinstance( self.number, int ):
					text = _("%d") % ( self.number )
				elif isinstance( self.number, basestring ):
					text = self.number
			
			elif field == "Channel":
				text = self.channel
			
			elif field == "Name":
				text = self.name
			
			elif field == "TimeLeft":
				if self.endless:
					# Add infinity symbol for indefinitely recordings
					text = INFINITY
				elif isinstance( self.timeleft, int ):
					# Show timeleft recording time
					text = _("%d Min") % ( self.timeleft )
			
			elif field == "TimeElapsed":
				if isinstance( self.timeelapsed, int ):
					text = _("%d Min") % ( self.timeelapsed )
			
			elif field == "TimeLeftDuration":
				# Calculate timeleft minutes
				if self.endless:
					# Add infinity symbol for indefinitely recordings
					text = INFINITY
				elif self.type is FINISHED:
					if isinstance( self.duration, int ):
						text = _("%d Min") % ( self.duration )
				elif isinstance( self.timeleft, int ):
					# Show timeleft recording time
					text = _("%d Min") % ( self.timeleft )
			
			elif field == "Begin":
				
				lbegin = self.begin and localtime( self.begin )
				text = lbegin and strftime( config.infobartunerstate.time_format_begin.value, lbegin )
			
			elif field == "End":
				lend = self.end and localtime( self.end )
				text = lend and strftime( config.infobartunerstate.time_format_end.value, lend )
			
			elif field == "BeginEnd":
				if self.progress is None:
					lbegin = self.begin and localtime( self.begin )
					text = lbegin and strftime( config.infobartunerstate.time_format_begin.value, lbegin )
				elif self.progress > 0:
					lend = self.end and localtime( self.end )
					text = lend and strftime( config.infobartunerstate.time_format_end.value, lend )
			
			elif field == "Duration":
				if isinstance( self.duration, int ):
					text = _("%d Min") % ( self.duration )
			
			elif field == "TimerProgressText":
				if isinstance( self.progress, int ):
					text = _("%d %%") % ( self.progress )
			
			elif field == "TimerProgressGraphical":
				if self.progress is not None:
					self["Progress"].setValue( self.progress )
					self["Progress"].show()
					# No resize necessary
					widths.append( self.progresswidth )
				else:
					if not config.infobartunerstate.placeholder_pogressbar.value:
						widths.append( 0 )
					else:	
						widths.append( self.progresswidth )
				continue
			
			elif field == "TimerDestination":
				text = self.destination
			
			elif field == "StreamClient":
				text = self.client or self.ip
			
			elif field == "StreamClientPort":
				if self.port:
					text = self.client or self.ip
					text += ":" + str(self.port)
			
			elif field == "DestinationStreamClient":
				text = self.destination or self.client or self.ip
			
			elif field == "FileSize":
				if isinstance( self.filesize, int ):
					text = _("%d MB") % ( self.filesize )
			
			elif field == "FreeSpace":
				if isinstance( self.freespace, int ):
					text = _("%d GB") % ( self.freespace )
			
			elif field == "None":
				# text is already initialized with ""
				pass
			
			# Set text, append field, resize field and append width
			self[fieldid].setText( text )
			
			# Set horizontal alignment
			if field == 'Number' or field == 'TimeLeftDuration' or field == 'TimeLeft' or field == 'TimeElapsed' or field == 'Duration' or field == 'TimerProgressText' or field == 'FileSize' or field == 'FreeSpace':
				self[fieldid].instance.setHAlign(2) # import _enigma # alignRight = _enigma.eLabel_alignRight
			
			#Workaround#1
			self[fieldid].instance.resize( eSize(1000, height) )
			
			width = max(self[fieldid].instance.calculateSize().width(), 0)
			#print width
			
			#Workaround#2: Width calculation seems to be not enough
			width = int( width * 1.10 )
			
			#Workaround#3: Calculation of left aligned fields seems to be broken
			if 0 < width and width < 30:
				width = 30
			#print "IBTS Update", field, width, self[fieldid].instance.calculateSize().width()
			
			#self[fieldid].instance.resize( eSize(width, height) )
			
			widths.append( width )
		
		self.widths = widths


