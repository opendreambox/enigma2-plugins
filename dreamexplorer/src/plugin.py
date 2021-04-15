#######################################################################
#
#    Dream Explorer 3 for DreamOS by dre (c) 2021
#    Coded by Vali (c)2009-2011
#    New version by dre (c) 2016
#    Support: board.dreamboxtools.de
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

from Components.config import config, ConfigSubsection, ConfigText, ConfigOnOff
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from Components.MultiContent import MultiContentEntryText
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from DreamExplorerFileList import DreamExplorerFileList
from Plugins.Plugin import PluginDescriptor
from ServiceReference import ServiceReference
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.EventView import EventViewSimple
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists, pathExists, createDir
from Tools.HardwareInfo import HardwareInfo
from Tools.NumericalTextInput import NumericalTextInput

from enigma import eConsoleAppContainer, eServiceReference, getPrevAsciiCode, getDesktop
from os import chmod, stat, walk
from os.path import basename
from subprocess import call, check_output

try:
	from Plugins.Extensions.PicturePlayer.plugin import Pic_Thumb, Pic_Full_View
	PicturePlayerInstalled = True
except:
	PicturePlayerInstalled = False

try:
	from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
	DVDPlayerInstalled = True
except:
	DVDPlayerInstalled = False

try:
	from Plugins.Extensions.MerlinMusicPlayer2.plugin import MerlinMusicPlayer2Screen, Item
	MMPlayerInstalled = True
except:
	MMPlayerInstalled = False
	
config.plugins.DreamExplorer = ConfigSubsection()
config.plugins.DreamExplorer.startDir = ConfigText(default="/")
config.plugins.DreamExplorer.useMediaFilter = ConfigOnOff(default=False)


def Plugins(path, **kwargs):
	return [
		PluginDescriptor(name=_("Dream Explorer"), description=_("A file explorer for DreamOS"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="dreamexplorer.png", fnc=main),
		PluginDescriptor(name=_("Dream Explorer"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
	]


def main(session, **kwargs):
	session.open(DreamExplorer3)

######## DREAM-EXPLORER START #######################


class DreamExplorer3(Screen):
	if getDesktop(0).size().width() >= 1920:
		skin = """
		<screen name="DreamExplorer3" position="center,60" size="1840,1020" title="Dream Explorer 3">
			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,3" size="1840,2" zPosition="5" scale="stretch" />
			<widget name="filelist" position="0,5" scrollbarMode="showOnDemand" size="1840,880" zPosition="4" iconSet="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons" />
			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,885" size="1840,2" zPosition="5" scale="stretch" />
			
			<eLabel font="Regular;20" position="10,895" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;20" position="340,895" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;20" position="670,895" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;20" position="1000,895" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;20" position="1330,895" size="60,30" text="MENU" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>

			<eLabel font="Regular;25" halign="left" position="80,890" size="250,40" text="Delete" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="410,890" size="250,40" text="Create" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="740,890" size="250,40" text="Move/Copy" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="1070,890" size="250,40" text="Rename" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="1400,890" size="250,40" text="Options" transparent="1" valign="center" zPosition="6"/>
			
			<eLabel font="Regular;20" position="10,940" size="60,30" text="INFO" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="340,940" size="60,30" text="AUDIO" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="670,940" size="60,30" text="PVR" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="1000,940" size="60,30" text="B+" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="1330,940" size="60,30" text="B-" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			

			<eLabel font="Regular;25" halign="left" position="80,935" size="250,40" text="Info" transparent="1" valign="center" zPosition="6"/>
			<widget name="filtertext" font="Regular;25" halign="left" position="410,935" size="250,40" transparent="1" valign="center" zPosition="6"/>			
			<eLabel font="Regular;25" halign="left" position="740,935" size="250,40" text="Bookmarks" transparent="1" valign="center" zPosition="6"/>
			<widget name="namedate" font="Regular;25" halign="left" position="1070,935" size="250,40" transparent="1" valign="center" zPosition="6"/>
			<widget name="ascdesc" font="Regular;25" halign="left" position="1400,935" size="250,40" transparent="1" valign="center" zPosition="6"/>

			<eLabel font="Regular;20" position="10,985" size="60,30" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="340,985" size="60,30" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<widget name="texticon" font="Regular;20" position="670,985" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>			
			<widget name="playicon" font="Regular;20" position="1000,985" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>	
			
			<widget name="oktext" font="Regular;25" halign="left" position="80,980" size="250,40" transparent="1" valign="center" zPosition="6" />
			<eLabel font="Regular;25" halign="left" position="410,980" size="250,40" text="Close Plugin" transparent="1" valign="center" zPosition="6"/>
			<widget name="chmodtext" font="Regular;25" halign="left" position="740,980" size="250,40" transparent="1" valign="center" zPosition="6"/>
			<widget name="playtext" font="Regular;25" halign="left" position="1070,980" size="250,40" transparent="1" valign="center" zPosition="6"/>
		</screen>"""
	else:
		skin = """
		<screen name="DreamExplorer3" position="center,50" size="1230,650" title="Dream Explorer 3">
			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,3" size="1230,2" zPosition="5" scale="stretch" />
			<widget name="filelist" position="0,5" scrollbarMode="showOnDemand" size="1230,540" iconSet="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons" />
			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,545" size="1230,2" zPosition="5" scale="stretch" />
			
			<eLabel font="Regular;12" position="10,555" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;12" position="240,555" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;12" position="470,555" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;12" position="700,555" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;12" position="930,555" size="40,20" text="MENU" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>

			<eLabel font="Regular;16" halign="left" position="55,550" size="180,30" text="Delete" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="285,550" size="180,30" text="Create" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="515,550" size="180,30" text="Move/Copy" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="745,550" size="180,30" text="Rename" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="975,550" size="180,30" text="Options" transparent="1" valign="center" zPosition="6"/>
			
			<eLabel font="Regular;12" position="10,590" size="40,20" text="INFO" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;12" position="240,590" size="40,20" text="AUDIO" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;12" position="470,590" size="40,20" text="PVR" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;12" position="700,590" size="40,20" text="B+" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;12" position="930,590" size="40,20" text="B-" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			

			<eLabel font="Regular;16" halign="left" position="55,585" size="180,30" text="Info" transparent="1" valign="center" zPosition="6"/>
			<widget name="filtertext" font="Regular;16" halign="left" position="285,585" size="180,30" transparent="1" valign="center" zPosition="6"/>			
			<eLabel font="Regular;16" halign="left" position="515,585" size="180,30" text="Bookmarks" transparent="1" valign="center" zPosition="6"/>
			<widget name="namedate" font="Regular;16" halign="left" position="745,585" size="180,30" transparent="1" valign="center" zPosition="6"/>
			<widget name="ascdesc" font="Regular;16" halign="left" position="975,585" size="180,30" transparent="1" valign="center" zPosition="6"/>

			<eLabel font="Regular;12" position="10,625" size="40,20" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;12" position="240,625" size="40,20" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<widget name="texticon" font="Regular;12" position="470,625" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>			
			<widget name="playicon" font="Regular;12" position="700,625" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>	
			
			<widget name="oktext" font="Regular;16" halign="left" position="55,620" size="180,30" transparent="1" valign="center" zPosition="6" />
			<eLabel font="Regular;16" halign="left" position="285,620" size="180,30" text="Close Plugin" transparent="1" valign="center" zPosition="6"/>
			<widget name="chmodtext" font="Regular;16" halign="left" position="515,620" size="180,30" transparent="1" valign="center" zPosition="6"/>
			<widget name="playtext" font="Regular;16" halign="left" position="745,620" size="180,30" transparent="1" valign="center" zPosition="6"/>
		</screen>"""

	def __init__(self, session, args=None):
		self.skin = DreamExplorer3.skin
		Screen.__init__(self, session)
		self.session = session
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.command = ["ls"]
		self.selectedDir = "/tmp/"
		# DarkVolli 20120702: add filetype wmv
		self.mediaPattern = "^.*\.(ts|m2ts|mp3|wav|ogg|jpg|jpeg|jpe|png|bmp|mpg|mpeg|mkv|mp4|mov|divx|avi|mp2|m4a|flac|ifo|vob|iso|sh|flv|3gp|mod|wmv)"
		
		startDirectory = None
		if pathExists(config.plugins.DreamExplorer.startDir.value):
			startDirectory = config.plugins.DreamExplorer.startDir.value
		
		self.useMediaFilter = config.plugins.DreamExplorer.useMediaFilter.value

		if self.useMediaFilter == False:
			self["filelist"] = DreamExplorerFileList(directory=startDirectory, showDirectories=True, showFiles=True, matchingPattern=None)
		else:
			self["filelist"] = DreamExplorerFileList(directory=startDirectory, showDirectories=True, showFiles=True, matchingPattern=self.mediaPattern)
			
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "MenuActions", "EPGSelectActions", "InfobarActions", "InfobarAudioSelectionActions", "InfobarSeekActions"],
		{
			"ok": self.executeAction,
			"back": self.exitPlugin,
			"green": self.showCreateOptions,
			"red": self.deleteItem,
			"blue": self.renameItem,
			"yellow": self.openCopyMoveManager,
			"menu": self.showContextMenu,
			"info": self.showInfo,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"nextBouquet": self.sortByNameOrDate,
			"prevBouquet": self.sortAscOrDesc,
			"video": self.openBookmarkManager,
			"text": self.chmodItem,
			"audioSelection": self.toggleMediaFilter,
			"playpauseService": self.showThumbnails,
		}, -1)
		
		self["NumberActions"] = NumberActionMap(["NumberActions"],
		{
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal,			
		})
		
		self["oktext"] = Label(_("Change directory"))
		self["chmodtext"] = Label(_("Set permissions"))
		self["filtertext"] = Label(_("Enable media filter"))
		self["namedate"] = Label(_("Sort by date"))
		self["ascdesc"] = Label(_("Sort desc"))
		
		self["texticon"] = Label("TEXT")
		self["playicon"] = Label("PLAY")
		self["playtext"] = Label(_("Show thumbnails"))

		if not PicturePlayerInstalled:
			self["playicon"].hide()
			self["playtext"].setText("")
		
		self.cmd = ""
		self.useMediaFilter = False
		
		self.numericalTextInput = NumericalTextInput()
		self.numericalTextInput.setUseableChars(u'.1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')
		
		self.container = eConsoleAppContainer()
		self.appClosed_conn = self.container.appClosed.connect(self.runFinished)
		self.dataavail_conn = self.container.dataAvail.connect(self.getData)
		self["filelist"].onSelectionChanged.append(self.setOkText)	
		self.onLayoutFinish.append(self.setOkText)	
		self.updateLocationInfo()

	def chmodItem(self):
		if not self["filelist"].canDescent():
			self.session.openWithCallback(self.chmodCallback, ChoiceBox, title=_("Please select new permissions..."), list=[(_("Read, write, execute (755)"), 0755), (_("Read, write (644)"), 0644)])
			
	def chmodCallback(self, answer):
		if answer:
			chmod(self["filelist"].getFilenameWithPath(), answer[1])
		self["filelist"].refresh()

	def toggleMediaFilter(self):
		if self.useMediaFilter:
			self.useMediaFilter = False
			config.plugins.DreamExplorer.useMediaFilter.value = False
			self["filelist"].matchingPattern = None
			self["filtertext"].setText(_("Enable media filter"))
		else:
			self.useMediaFilter = True
			config.plugins.DreamExplorer.useMediaFilter.value = True
			self["filelist"].matchingPattern = self.mediaPattern
			self["filtertext"].setText(_("Disable media filter"))
		
		config.plugins.DreamExplorer.useMediaFilter.save()
		self["filelist"].refresh()
		self.updateLocationInfo()		

	def showThumbnails(self):
		if PicturePlayerInstalled:
			pictureList = self["filelist"].getFilteredFileList("picture", True)
			# pictureList must be converted into a fake filelistEntryComponent entry to picture player to work properly
			self.session.open(Pic_Thumb, [[(x, False), "", ""] for x in pictureList], 0, self["filelist"].getCurrentDirectory())			

	def keyNumberGlobal(self, number):
		unichar = self.numericalTextInput.getKey(number)
		charstr = unichar.encode("utf-8")
		if len(charstr) == 1:
			self["filelist"].moveToChar(charstr[0])

	def keyAsciiCode(self):
		unichar = unichr(getPrevAsciiCode())
		charstr = unichar.encode("utf-8")
		if len(charstr) == 1:
			self["filelist"].moveToChar(charstr[0])

	def setOkText(self):
		okText = ""
		playText = ""
		if self["filelist"].canDescent():
			okText = _("Change directory")
			chmodText = ""
		else:
			filename = self["filelist"].getFilename()
			if filename is not None:
				fileExtensionType = self["filelist"].getFileExtensionType()
				
				if fileExtensionType == "music":
					okText = _("Play song")
				elif fileExtensionType == "picture":
					okText = _("Show picture")
					if PicturePlayerInstalled:
						playText = _("Show thumbnails")
				elif fileExtensionType == "movie":
					okText = _("Play movie")
				elif fileExtensionType == "package":
					okText = _("Install package")
				elif fileExtensionType == "archive":
					okText = _("Uncompress archive")
				elif fileExtensionType == "script":
					okText = _("Run script")
				elif self["filelist"].isSymLink():
					okText = _("Follow symlink")
				else:
					okText = _("Open in vEditor2")
			chmodText = _("Set permissions")
		self["oktext"].setText(okText)
		if okText == "":
			self["texticon"].hide()
		else:
			self["texticon"].show()			
		self["chmodtext"].setText(chmodText)
		self["playtext"].setText(playText)
		if playText == "":
			self["playicon"].hide()
		else:
			self["playicon"].show()
			
	def showCreateOptions(self):
		target = self["filelist"].getFilenameWithPath()
		targetFileDir = self["filelist"].getPathForFile()
		if target is None:
			target = self["filelist"].getPathForFile()

		self.session.openWithCallback(self.getSelection, ChoiceBox, title=_("Please select action..."), list=[(_("Create file in %s" % (targetFileDir)), "createFile"), (_("Create directory in %s" % (targetFileDir)), "createDir"), (_("Create symlink to %s" % (target)), "createSymlink")])
		
	def getSelection(self, selection):
		if selection:
			if selection[1] == "createFile":
				element = "file"
				target = self["filelist"].getPathForFile()
				titletext = _("Create %s in %s with name:" % (element, target))
			elif selection[1] == "createDir":
				element = "directory"
				target = self["filelist"].getPathForFile()
				titletext = _("Create %s in %s with name:" % (element, target))
			elif selection[1] == "createSymlink":
				element = "symlink"
				target = self["filelist"].getFilenameWithPath()
				if target is None:
					target = self["filelist"].getPathForFile()
				titletext = _("Create %s to %s with name:" % (element, target))
				
			self.session.openWithCallback(boundFunction(self.createItem, element), InputBox, title=titletext, text=_("Name"))

	def createItem(self, type, elementName):
		if elementName:
			self.executionData = ""
			newElement = "%s%s" % (self["filelist"].getPathForFile(), elementName)
			
			if type == "symlink":
				self.symlinkName = elementName
				self.openCopyMoveManager(True)
			else:			
				if type == "file":
					self.cmd = 'touch %s' % (newElement)
					self.actionText = _("Creation of file %s" % (newElement))
						
				elif type == "directory":
					self.cmd = 'mkdir %s' % (newElement)
		
					self.actionText = _("Creation of directory %s" % (newElement))
					self.container.execute(self.cmd)		
	
				self.container.execute(self.cmd)
			
	def executeAction(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateLocationInfo()
		else:
			filenameWithPath = self["filelist"].getFilenameWithPath()
			filename = self["filelist"].getFilename()

			if filenameWithPath != None:
				fileExtension = self["filelist"].getFileExtension()

				if fileExtension == "ts":
					fileRef = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + filenameWithPath)
					self.session.open(MoviePlayer, fileRef)
					
				elif fileExtension in ["mpg", "mpeg", "mkv", "m2ts", "vob", "mod", "avi", "mp4", "divx", "mov", "flv", "3gp", "wmv"]:
					fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filenameWithPath)
					self.session.open(MoviePlayer, fileRef)

				elif fileExtension in ["mp3", "wav", "ogg", "m4a", "mp2", "flac"]:
					if MMPlayerInstalled:
						SongList, SongIndex = self.searchMusic()
						self.session.openWithCallback(self.restartService, MerlinMusicPlayer2Screen, SongList, SongIndex, False, self.currentService, None)
					else:
						fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filenameWithPath)
						m_dir = self["filelist"].getCurrentDirectory()
						self.session.open(MusicExplorer, fileRef, m_dir, filenameWithPath)

				elif fileExtension in ["jpg", "jpeg", "jpe", "png", "bmp"]:
					if self["filelist"].getCurrentIndex() != 0:
						if PicturePlayerInstalled:
							pictureList = self["filelist"].getFilteredFileList("picture", True)
							# pictureList must be converted into a fake filelistEntryComponent entry to picture player to work properly
							self.session.open(Pic_Full_View, [[(x, False), "", ""] for x in pictureList], 0, self["filelist"].getCurrentDirectory())
								
				elif fileExtension == "mvi":
					self.session.nav.stopService()
					self.session.openWithCallback(self.restartService, MviExplorer, filenameWithPath)
					
				elif filename.lower() == "video_ts.ifo":
					if DVDPlayerInstalled:
						if (self["filelist"].getCurrentDirectory()).lower().endswith("video_ts/"):
							self.session.openWithCallback(self.restartService, DVDPlayer, dvd_filelist=[self["filelist"].getCurrentDirectory()])
							
				elif fileExtension == "iso":
					if DVDPlayerInstalled:
						self.session.openWithCallback(self.restartService, DVDPlayer, dvd_filelist=[filenameWithPath])
						
				elif filename.lower().endswith(".bootlogo.tar.gz"):
					self.command = ["mount -rw /boot -o remount", "sleep 3", "tar -xzvf " + filenameWithPath + " -C /", "mount -ro /boot -o remount"]
					askList = [(_("Cancel"), "NO"), (_("Install bootlogo"), "YES")]
					msg = self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Please select action for\n%s?" % (filename)), list=askList)
					msg.setTitle(_("Dream Explorer 3"))
					
				elif fileExtension in ["gz", "bz2"]:
					if filename.lower()[-6:-3] == "tar":
						if fileExtension == "gz":
							self.command = ["tar -xzvf " + filenameWithPath + " -C /"]
						elif fileExtension == "bz2":
							self.command = ["tar -xjvf " + filenameWithPath + " -C /"]
						
						msg = self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Please select action for\n%s?" % (filename)), list=[(_("Cancel"), "NO"), (_("Extract archive"), "YES")])
						msg.setTitle(_("Dream Explorer 3"))

				elif fileExtension == "deb":
					self.command = ["apt-get update && dpkg -i %s && apt-get -f install" % (filenameWithPath)]
					askList = [(_("Cancel"), "NO"), (_("Install package"), "YES")]
					msg = self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Please select action for\n%s?" % (filename)), list=askList)
					msg.setTitle(_("Dream Explorer 3"))
					
				elif fileExtension == "sh":
					self.command = [filenameWithPath]
					askList = [(_("Cancel"), "NO"), (_("View script"), "VIEW"), (_("Execute script"), "YES")]
					self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Please select action for\n%s?" % (filename)), list=askList)
				else:
					xfile = stat(filenameWithPath)
					if (xfile.st_size < 1024000):
						self.session.open(vEditor2, filenameWithPath)
					else:
						self.session.open(MessageBox, _("File is too big to display content"), MessageBox.TYPE_INFO, windowTitle=_("Dream Explorer 3"))

	def restartService(self):
		if self.session.nav.getCurrentlyPlayingServiceReference() is None:
			self.session.nav.playService(self.currentService)

	def updateLocationInfo(self):
		filterText = _("[All files]")
		if self.useMediaFilter:
			filterText = _("[Media files]")
		self.setTitle("Dream Explorer 3 - %s %s" % (filterText, self["filelist"].getCurrentDirectory()))

	def showContextMenu(self):
		contextList = []
		if self["filelist"].canDescent():
			if self["filelist"].getCurrentIndex() != 0 or self["filelist"].getCurrent()[0] == '<%s>' % (_("List of Storage Devices")):
				contextList.extend((
					(_("Set as start directory"), "SETSTARTDIR"),
				))
		contextList.extend((
			(_("About"), "ABOUT"),
		))
		
		self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Options:\n"), list=contextList, windowTitle=_("Dream Explorer 3"))

	def executeSelected(self, answer):
		answer = answer and answer[1]
		if answer == "YES":
			self.session.open(Console, cmdlist=self.command)
		elif answer == "VIEW":
			viewfile = stat(self.command[0])
			if (viewfile.st_size < 61440):
				self.session.open(vEditor2, self.command[0])
		elif answer == "SETSTARTDIR":
			startDir = self["filelist"].getSelection()[1]
			if startDir is None:
				startDir = self["filelist"].getCurrentDirectory()
				
			self.session.openWithCallback(self.callbackSetStartDir, MessageBox, _("Do you want to set\n%s\nas start directory?" % (startDir)), MessageBox.TYPE_YESNO, windowTitle=_("Dream Explorer 3"))
		elif answer == "ABOUT":
 			self.session.open(MessageBox, _("Dreambox Explorer II created by Vali (2010)\nDream Explorer 3 by Dre (2021)\n\nSupport: board.dreamboxtools.de"), MessageBox.TYPE_INFO, windowTitle=_("Info"))

	def up(self):
		self["filelist"].up()
		self.updateLocationInfo()

	def down(self):
		self["filelist"].down()
		self.updateLocationInfo()

	def left(self):
		self["filelist"].pageUp()
		self.updateLocationInfo()

	def right(self):
		self["filelist"].pageDown()
		self.updateLocationInfo()

	def showInfo(self):
		if self["filelist"].canDescent():
			if self["filelist"].getCurrentIndex() == 0:
				try:
					out_line = check_output(['uptime'])
					ret = "at" + out_line + "\n"

					with open('/proc/meminfo', 'r') as f:
						for line in f.readlines():
							tokens = line.split()
							if tokens[0] in ('MemTotal:', 'MemFree:'):
								ret += line
					ret += "\n"

					with open('/proc/stat', 'r') as f:
						for line in f.readlines():
							tokens = line.split()
							if tokens[0] == 'procs_running':
								ret += _("Running processes: ") + tokens[1]
				except:
					ret = "N/A"			
			
				msg = self.session.open(MessageBox, _("Dreambox model: %s\n\n%s" % (HardwareInfo().get_device_name(), ret)), MessageBox.TYPE_INFO, windowTitle=_("Dream Explorer 3"))
		elif self["filelist"].getFileExtensionType() == "service":
			self.session.open(SystemdViewer, self["filelist"].getFilename(), self["filelist"].getFilenameWithPath())
		else:
			evt, serviceref = self["filelist"].getTSEvent()
			if evt is not None:
				self.session.open(EventViewSimple, evt, ServiceReference(serviceref))

	def openBookmarkManager(self):
		self.session.openWithCallback(self.setDirectory, BookmarkManager)
		
	def setDirectory(self, dir=False):
		if dir:
			self["filelist"].changeDirectory(dir)

	def getData(self, data):
		self.executionData += data

	def runFinished(self, retval):
		resultText = ""
		if retval != 0:
			resultText = _("failed\n%s" % (self.executionData))
			state = False
		else:
			resultText = _("successful")
			state = True	
		
		self.session.open(MessageBox, "%s %s" % (self.actionText, resultText), MessageBox.TYPE_INFO if state else MessageBox.TYPE_ERROR, timeout=0)
		
		self["filelist"].refresh()
			
	def deleteItem(self):
		if self.useMediaFilter:
			msg = self.session.open(MessageBox, _('Turn off the media-filter first.'), MessageBox.TYPE_INFO, windowTitle=_("Dream Explorer 3"))
			return
			
		if not(self["filelist"].canDescent()):
			self.item = self["filelist"].getFilenameWithPath()
			self.type = "file"
			self.typetext = _("file")
			
		elif (self["filelist"].getCurrentIndex() != 0) and (self["filelist"].canDescent()):
			self.item = self["filelist"].getSelection()[1]
			self.type = "directory"
			self.typetext = _("directory")
		else:
			return
			
		msg = self.session.openWithCallback(self.callbackDeleteItem, MessageBox, _("Do you really want to delete:\n" + self.item), MessageBox.TYPE_YESNO, windowTitle=_("Dream Explorer 3 - Delete %s..." % (self.type)))

	def callbackDeleteItem(self, answer):
		if answer is True:
			if self.type == "directory":
				self.cmd = "rm -rf '%s'" % (self.item)
			elif self.type == "file":
				self.cmd = "rm -f '%s'" % (self.item)

			self.actionText = _("Deletion of %s %s" % (self.type, self.item))		
			self.container.execute(self.cmd)

	def renameItem(self):
		if self.useMediaFilter:
			msg = self.session.open(MessageBox, _('Turn off the media-filter first.'), MessageBox.TYPE_INFO, windowTitle=_("Dream Explorer 3"))
			return
			
		if not(self["filelist"].canDescent()):
			item = self["filelist"].getFilename()
			self.type = "file"
			self.typetext = _("file")
		elif self["filelist"].getCurrentIndex() != 0 and self["filelist"].canDescent():
			item = self["filelist"].getSelection()[0]
			self.type = "directory"
			self.typetext = _("directory")
		else:
			return
			
		self.session.openWithCallback(self.callbackRenameItem, InputBox, title=_("Current name: %s" % (item)), windowTitle=_("Rename %s..." % (self.typetext)), text=item)

	def callbackRenameItem(self, answer):
		if answer is not None:
			path = self["filelist"].getCurrentDirectory()
			if self.type == "file":
				oldName = self["filelist"].getFilenameWithPath()
			elif self.type == "directory":
				oldName = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			newName = path + answer

			self.cmd = 'mv %s %s' % (oldName, newName)
			
			self.actionText = _("Renaming of %s to %s" % (oldName, newName))
			self.container.execute(self.cmd)
			
	def openCopyMoveManager(self, setSymLink=False):
		if self.useMediaFilter:
			msg = self.session.open(MessageBox, _('Turn off the media-filter first.'), MessageBox.TYPE_INFO, windowTitle=_("Dream Explorer 3"))
			return
			
		if not(self["filelist"].canDescent()):
			source = self["filelist"].getFilenameWithPath()
		elif (self["filelist"].getCurrentIndex() != 0) and (self["filelist"].canDescent()): #NEW
			source = self["filelist"].getSelection()[1]
		else:
			return
		
		if setSymLink:
			mode = "symlink"
			showFiles = False
		else:
			mode = "copymove"
			showFiles = False
			self.symlinkName = None
		self.session.openWithCallback(self.callbackCopyMoveManager, FolderSelection, source, self.symlinkName, showFiles=showFiles, mode=mode)

	def callbackCopyMoveManager(self, answer):
		if answer is not None:
			self.actionText = answer[0]
			self.cmd = answer[1]
			
			self.container.execute(self.cmd)

	def callbackSetStartDir(self, answerSD):
		if answerSD is True:
			startDir = self["filelist"].getSelection()[1]
			if startDir is None:
				startDir = self["filelist"].getCurrentDirectory()
			config.plugins.DreamExplorer.startDir.value = startDir
			config.plugins.DreamExplorer.startDir.save()

	def sortByNameOrDate(self):
		# SORT_NAME_ASC
		if self["filelist"].getSortType() == DreamExplorerFileList.SORT_NAME_ASC:
			# SORT_DATE_ASC
			self["filelist"].setSortType(DreamExplorerFileList.SORT_DATE_ASC)
			self["namedate"].setText(_("Sort by name"))
		# SORT_NAME_DESC
		elif self["filelist"].getSortType() == DreamExplorerFileList.SORT_NAME_DESC:
			# SORT_DATE_DESC
			self["filelist"].setSortType(DreamExplorerFileList.SORT_DATE_DESC)
			self["namedate"].setText(_("Sort by name"))
		# SORT_DATE_ASC
		elif self["filelist"].getSortType() == DreamExplorerFileList.SORT_DATE_ASC:
			# SORT_NAME_ASC
			self["filelist"].setSortType(DreamExplorerFileList.SORT_NAME_ASC)
			self["namedate"].setText(_("Sort by date"))
		# SORT_DATE_DESC
		elif self["filelist"].getSortType() == DreamExplorerFileList.SORT_DATE_DESC:
			# SORT_NAME_DESC
			self["filelist"].setSortType(DreamExplorerFileList.SORT_NAME_DESC)
			self["namedate"].setText(_("Sort by date"))

		self["filelist"].sortList()
		self["filelist"].setList()
			
	def sortAscOrDesc(self):
		if self["filelist"].getSortType() == DreamExplorerFileList.SORT_NAME_DESC:
			self["filelist"].setSortType(DreamExplorerFileList.SORT_NAME_ASC)
			self["ascdesc"].setText(_("Sort desc"))
		elif self["filelist"].getSortType() == DreamExplorerFileList.SORT_DATE_DESC:
			self["filelist"].setSortType(DreamExplorerFileList.SORT_DATE_ASC)
			self["ascdesc"].setText(_("Sort desc"))
		elif self["filelist"].getSortType() == DreamExplorerFileList.SORT_NAME_ASC:
			self["filelist"].setSortType(DreamExplorerFileList.SORT_NAME_DESC)
			self["ascdesc"].setText(_("Sort asc"))
		elif self["filelist"].getSortType() == DreamExplorerFileList.SORT_DATE_ASC:
			self["filelist"].setSortType(DreamExplorerFileList.SORT_DATE_DESC)
			self["ascdesc"].setText(_("Sort asc"))

		self["filelist"].sortList()
		self["filelist"].setList()
	
	def searchMusic(self):
		slist = []
		foundIndex = 0
		index = 0
		musicList = self["filelist"].getFilteredFileList("music")
		for song in musicList:
			slist.append((Item(text=song[0], filename=song[2]),))
			if self["filelist"].getFilename() == song[0]:
				foundIndex = index
			index = index + 1
		return slist, foundIndex

	def exitPlugin(self):
		self.close()

######## DREAM-EXPLORER END ####################### 


class BookmarkManager(Screen):
	if getDesktop(0).size().width() >= 1920:
		skin = """
		<screen name="BookmarkManager" position="center,center" size="1000,630" title="Bookmark Manager">
			<widget name="folders" position="0,5" size="600,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />
			<widget name="filelist" position="0,45" scrollbarMode="showOnDemand" size="600,480" zPosition="4" iconSet="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons" />
			<widget name="bookmarks" position="600,5" size="400,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />
			<widget source="bookmarklist" render="Listbox" position="600,45" size="400,480" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template":
						[
							MultiContentEntryText(pos=(10,0), size=(380,40), font=0, text=0),
						],
					"fonts": [gFont("Regular",28)],
					"itemHeight": 40
					}
				</convert>
			</widget>
			<eLabel font="Regular;20" position="0,540" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;20" position="240,540" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;20" position="480,540" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;20" position="720,540" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;20" position="0,580" size="40,20" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="240,580" size="40,20" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<widget name="deleteBookmark" font="Regular;25" halign="left" position="50,535" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget  name="addBookmark" font="Regular;25" halign="left" position="290,535" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget name="saveBookmarks" font="Regular;25" halign="left" position="530,535" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget name="toggleList" font="Regular;25" halign="left" position="770,535" size="180,40" transparent="1" valign="center" zPosition="6"/>	
			<widget name="ok" font="Regular;25" halign="left" position="50,575" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget  name="exit" font="Regular;25" halign="left" position="290,575" size="180,40" transparent="1" valign="center" zPosition="6"/>
		</screen>
		"""
	else:
		skin = """
		<screen name="BookmarkManager" position="center,center" size="1000,630" title="Bookmark Manager">
			<widget name="folders" position="0,5" size="600,40" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />
			<widget name="filelist" position="0,45" scrollbarMode="showOnDemand" size="600,480" zPosition="4" iconSet="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons" />
			<widget name="bookmarks" position="600,5" size="400,40" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />
			<widget source="bookmarklist" render="Listbox" position="600,45" size="400,480" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template":
						[
							MultiContentEntryText(pos=(10,0), size=(380,30), font=0, text=0),
						],
					"fonts": [gFont("Regular",18)],
					"itemHeight": 30
					}
				</convert>
			</widget>
			<eLabel font="Regular;12" position="0,540" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;12" position="260,540" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;12" position="520,540" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;12" position="780,540" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;12" position="0,580" size="60,30" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;12" position="260,580" size="60,30" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<widget name="deleteBookmark" font="Regular;16" halign="left" position="70,535" size="180,30" transparent="1" valign="center" zPosition="6"/>
			<widget  name="addBookmark" font="Regular;16" halign="left" position="330,535" size="180,30" transparent="1" valign="center" zPosition="6"/>
			<widget name="saveBookmarks" font="Regular;16" halign="left" position="590,535" size="180,30" transparent="1" valign="center" zPosition="6"/>
			<widget name="toggleList" font="Regular;16" halign="left" position="850,535" size="180,30" transparent="1" valign="center" zPosition="6"/>	
			<widget name="ok" font="Regular;16" halign="left" position="70,575" size="180,30" transparent="1" valign="center" zPosition="6"/>
			<widget  name="exit" font="Regular;16" halign="left" position="330,575" size="180,30" transparent="1" valign="center" zPosition="6"/>
		</screen>
		"""		

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
		{
			"ok": self.changeDirOrSelectBookmark,
			"cancel": self.close,
			"green": self.addToBookmarks,
			"red": self.removeFromBookmarks,
			"blue": self.toggleList,
			"yellow": self.saveBookmarks,
			"down": self.moveDown,
			"up": self.moveUp,
			"left": self.pageUp,
			"right": self.pageDown,
		}, -1)
		
		self.currentList = "bookmarklist"
		
		self["filelist"] = DreamExplorerFileList(list_type=DreamExplorerFileList.LIST_TYPE_NODETAILS, directory="/", showDirectories=True, showFiles=False, matchingPattern=None, showDetails=False)
		
		self["folders"] = Label(_("Folders"))
		self["bookmarks"] = Label(_("Bookmarks"))
		self["deleteBookmark"] = Label(_("Delete bookmark"))
		self["addBookmark"] = Label(_("Add bookmark"))
		self["addBookmark"].hide()
		self["saveBookmarks"] = Label(_("Save bookmarks"))
		self["toggleList"] = Label(_("Toggle list"))
		self["ok"] = Label(_("Open bookmark"))
		self["exit"] = Label(_("Close"))
		
		self["bookmarklist"] = List()
		
		self.readBookmarks()
		
		self.onLayoutFinish.append(self.setListState)

	def moveUp(self):
		if self.currentList == "bookmarklist":
			self[self.currentList].moveSelection("moveUp")
		else:
			self[self.currentList].up()
		
	def moveDown(self):
		if self.currentList == "bookmarklist":
			self[self.currentList].moveSelection("moveDown")
		else:
			self[self.currentList].down()

	def pageUp(self):
		if self.currentList == "bookmarklist":
			self[self.currentList].moveSelection("pageUp")
		else:
			self[self.currentList].pageUp()
		
	def pageDown(self):
		if self.currentList == "bookmarklist":
			self[self.currentList].moveSelection("pageDown")
		else:
			self[self.currentList].pageDown()	
		
	def setListState(self):
		self["filelist"].setSelectionEnabled(False)
		self["bookmarklist"].setSelectionEnabled(True)
		
	def changeDirOrSelectBookmark(self):
		if self.currentList == "filelist":
			if self["filelist"].canDescent():
				self["filelist"].descent()
		else:
			cur = self["bookmarklist"].getCurrent()
			if cur is not None:			
				self.close(cur[0])
	
	def addToBookmarks(self):
		cur = self["filelist"].getCurrent()
		if cur is not None:
			if not cur[1] in self.bookmarks:
				if cur[1] is not None:
					self.bookmarks.append(cur[1])
				
					self.updateBookmarks()
				else:
					self.session.open(MessageBox, _("Only directories can be bookmarked"), MessageBox.TYPE_INFO, timeout=3)
			else:
				self.session.open(MessageBox, _("Diretory is already in bookmarks"), MessageBox.TYPE_INFO, timeout=3)
		
	def removeFromBookmarks(self):
		cur = self["bookmarklist"].getCurrent()
		if cur is not None:
			self.bookmarks.remove(cur[0])
			
		self.updateBookmarks()
			
	def updateBookmarks(self):
		self.bookmarklist = []
		for bookmark in self.bookmarks:
			self.bookmarklist.append((bookmark,))		
			
		self["bookmarklist"].setList(self.bookmarklist)
		
	def readBookmarks(self):
		if not pathExists("/etc/enigma2/DreamExplorer"):
			createDir("/etc/enigma2/DreamExplorer")
		
		if fileExists("/etc/enigma2/DreamExplorer/bookmarks"):
			with open("/etc/enigma2/DreamExplorer/bookmarks", 'r') as file:
				self.bookmarks = file.read().splitlines()
		
		self.updateBookmarks()
		
	def toggleList(self):
		if self.currentList == "bookmarklist":
			self[self.currentList].setSelectionEnabled(False)
			self.currentList = "filelist"
			self[self.currentList].setSelectionEnabled(True)
			self["addBookmark"].show()
			self["deleteBookmark"].hide()
			self["ok"].setText(_("Change directory"))
		else:
			self[self.currentList].setSelectionEnabled(False)
			self.currentList = "bookmarklist"
			self[self.currentList].setSelectionEnabled(True)
			self["addBookmark"].hide()
			self["deleteBookmark"].show()
			self["ok"].setText(_("Open bookmark"))

	def saveBookmarks(self):
		with open("/etc/enigma2/DreamExplorer/bookmarks", "w+") as file:
			for bookmark in self.bookmarks:
				file.write(bookmark + "\n")


class vEditor2(Screen):
	if getDesktop(0).size().width() >= 1920:
		skin = """
		<screen name="vEditor2" position="center,50" size="1500,975" title="vEditor2">
			<widget source="filedata" render="Listbox" position="0,0" size="1500,875" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template":[
									MultiContentEntryText(pos=(0,0), size=(900,35), text=0),					],
					"fonts": [gFont("Regular",30)],
					"itemHeight": 35
					}
				</convert>
			</widget>
			<eLabel font="Regular;20" position="10,890" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;20" position="360,890" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;20" position="710,890" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;20" position="1060,890" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="80,885" size="250,40" text="Delete line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="430,885" size="250,40" text="Add line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="780,885" size="250,40" text="Edit line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;20" position="10,925" size="60,30" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="360,925" size="60,30" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>	
			<eLabel font="Regular;25" halign="left" position="80,920" size="250,40" text="Edit line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;25" halign="left" position="430,920" size="250,40" text="Close editor" transparent="0" valign="center" zPosition="6"/>	
		</screen>"""
	else:
		skin = """
		<screen name="vEditor2" position="center,50" size="1200,650" title="vEditor2">
			<widget source="filedata" render="Listbox" position="0,0" size="1200,575" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template":[
									MultiContentEntryText(pos=(0,0), size=(900,30), text=0),					],
					"fonts": [gFont("Regular",18)],
					"itemHeight": 25
					}
				</convert>
			</widget>
			<eLabel font="Regular;12" position="10,585" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;12" position="250,585" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;12" position="490,585" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;12" position="740,585" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="60,585" size="180,30" text="Delete line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="300,585" size="180,30" text="Add line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="540,585" size="180,30" text="Edit line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;12" position="10,620" size="40,20" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;16" position="250,620" size="40,20" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>	
			<eLabel font="Regular;16" halign="left" position="60,615" size="180,30" text="Edit line" transparent="0" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="300,615" size="180,30" text="Close editor" transparent="0" valign="center" zPosition="6"/>	
		</screen>"""

	def __init__(self, session, filename):
		Screen.__init__(self, session)
		self.session = session
		self.filename = filename
		self.list = []
		self["filedata"] = List(self.list)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.editLine,
			"back": self.exitEditor,
			"red": self.deleteLine,
			"green": self.addLine,
			"yellow": self.editLine,
		}, -1)
		
		self.lineIndex = 0
		self.oldLine = ""
		self.isChanged = False
		
		self.getFileContent()

	def addLine(self):
		self.lineIndex = self["filedata"].getIndex()
		self.session.openWithCallback(self.insertLine, InputBox, title=_("New line:"), windowTitle=_("Insert line after line %d" % (self.lineIndex + 1)), text="")
		
	def insertLine(self, newline):
		if newline is not None:
			self.list.insert(self.lineIndex + 1, ["%s\n" % (newline)])
			self["filedata"].updateList(self.list)
			self.isChanged = True

	def deleteLine(self):
		cur = self["filedata"].getCurrent()
		if cur is not None:
			self.list.remove(cur)
			self["filedata"].updateList(self.list)
			self.isChanged = True
		
	def exitEditor(self):
		if self.isChanged:
			msg = self.session.openWithCallback(self.saveFile, MessageBox, _("You have changed %s. Do you want to save your changes?" % (self.filename)), MessageBox.TYPE_YESNO, windowTitle=_("Dream Explorer 3"))
		else:
			self.close()

	def getFileContent(self):
		with open(self.filename, "r") as f:
			self.list = [[line] for line in f.readlines()]

		self.setTitle("vEditor2 - %s" % (self.filename))
		self["filedata"].setList(self.list)

	def editLine(self):
		self.lineIndex = self["filedata"].getIndex()
		
		if self["filedata"].getCurrent() is not None:
			self.rowContent = self["filedata"].getCurrent()[0]
			editableText = self.rowContent.strip("\n")
			self.session.openWithCallback(self.callbackEditLine, InputBox, title=_("Current content: %s" % (self.rowContent)), windowTitle=_("Edit line: %d" % (self.lineIndex + 1)), text=editableText)

	def callbackEditLine(self, newline):
		if newline is not None:
			self.isChanged = True
			self.list[self.lineIndex][0] = "%s\n" % (newline)
			self["filedata"].updateList(self.list)

	def saveFile(self, answer):
		if answer is True:
			with open(self.filename, "w") as f:
				f.writelines([x[0] for x in self.list])
		self.close()


class MviExplorer(Screen):
	skin = """
		<screen position="-300,-300" size="10,10" title="mvi-Explorer">
		</screen>"""

	def __init__(self, session, file):
		self.skin = MviExplorer.skin
		Screen.__init__(self, session)
		self.filename = file
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.close,
			"back": self.close
		}, -1)
		self.onLayoutFinish.append(self.showMvi)
		
	def showMvi(self):
		call(['showiframe', self.filename])


class MoviePlayer(MP_parent):
	def __init__(self, session, service):
		self.session = session
		MP_parent.__init__(self, self.session, service)

	def leavePlayer(self):
		try: 
			self.updateMovieData() # Merlin only feature
		except:
			pass
		self.is_closing = True
		self.close()

	def leavePlayerConfirmed(self, answer):
		pass

	def doEofInternal(self, playing):
		try: 
			self.updateMovieData() # Merlin only feature
		except:
			pass
		if not self.execing:
			return
		if not playing:
			return
		self.leavePlayer()

	def showMovies(self):
		try: 
			self.updateMovieData() # Merlin only feature
		except:
			pass
		self.close()


class MusicExplorer(MoviePlayer):
	skin = """
	<screen backgroundColor="#50070810" flags="wfNoBorder" name="MusicExplorer" position="center,center" size="720,30">
		<widget font="Regular;24" halign="right" position="50,0" render="Label" size="100,30" source="session.CurrentService" transparent="1" valign="center" zPosition="1">
			<convert type="ServicePosition">Remaining</convert>
		</widget>
		<widget font="Regular;24" position="170,0" render="Label" size="650,30" source="session.CurrentService" transparent="1" valign="center" zPosition="1">
			<convert type="ServiceName">Name</convert>
		</widget>
	</screen>"""

	def __init__(self, session, service, MusicDir, theFile):
		self.session = session
		MoviePlayer.__init__(self, session, service)
		self.MusicDir = MusicDir
		self.musicList = []
		self.Mindex = 0
		self.curFile = theFile
		self.searchMusic()
		self.onLayoutFinish.append(self.showMMI)

	def showMMI(self):
		call(['showiframe', '/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons/music.mvi'])

	def searchMusic(self):
		midx = 0
		for root, dirs, files in walk(self.MusicDir):
			for name in files:
				name = name.lower()
				if name.endswith(".mp3") or name.endswith(".mp2") or name.endswith(".ogg") or name.endswith(".wav") or name.endswith(".flac") or name.endswith(".m4a"):
					self.musicList.append(name)
					if self.curFile in name:
						self.Mindex = midx
					midx = midx + 1

	def seekFwd(self):
		if len(self.musicList) > 2:
			if self.Mindex < (len(self.musicList) - 1):
				self.Mindex = self.Mindex + 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox, _('No more playable files.'), MessageBox.TYPE_INFO, windowTitle=_("Dream Explorer 3"))

	def seekBack(self):
		if len(self.musicList) > 2:
			if self.Mindex > 0:
				self.Mindex = self.Mindex - 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox, _('No more playable files.'), MessageBox.TYPE_INFO, windowTitle=_("Dream Explorer 3"))

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.seekFwd()


class FolderSelection(Screen):
	if getDesktop(0).size().width() >= 1920:
		skin = """
			<screen name="FolderSelection" position="center,center" size="800,600" title="Select target location...">
				<widget name="infotext" font="Regular;25" halign="center" position="0,0" size="800,100" transparent="0" valign="center" zPosition="4"/>
				<widget name="TargetDir" position="0,100" scrollbarMode="showOnDemand" size="800,400" zPosition="4" iconSet="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons" />
				<eLabel backgroundColor="#555555" position="5,505" size="790,2" zPosition="5"/>

				<eLabel font="Regular;20" position="10,515" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
				<eLabel font="Regular;20" position="340,515" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
				<widget name="redtext" font="Regular;25" halign="left" position="80,510" size="250,40" transparent="0" valign="center" zPosition="6"/>
				<widget name="greentext" font="Regular;25" halign="left" position="410,510" size="250,40" transparent="0" valign="center" zPosition="6"/>
			</screen>"""
	else:
		skin = """
			<screen name="FolderSelection" position="center,center" size="800,600" title="Select target location...">
				<widget name="infotext" font="Regular;18" halign="center" position="0,0" size="800,100" transparent="0" valign="center" zPosition="4"/>
				<widget name="TargetDir" position="0,100" scrollbarMode="showOnDemand" size="800,390" zPosition="4" iconSet="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons" />
				<eLabel backgroundColor="#555555" position="5,505" size="790,2" zPosition="5"/>

				<eLabel font="Regular;20" position="10,515" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
				<eLabel font="Regular;20" position="340,515" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
				<widget name="redtext" font="Regular;18" halign="left" position="60,510" size="250,30" transparent="0" valign="center" zPosition="6"/>
				<widget name="greentext" font="Regular;18" halign="left" position="390,510" size="250,30" transparent="0" valign="center" zPosition="6"/>
			</screen>"""		
			
	def __init__(self, session, item="/tmp", linkname=None, isDir=False, showFiles=False, mode=None):
		Screen.__init__(self, session)
		self.session = session
		self.item = item
		self.linkname = linkname
		self.mode = mode
		
		self["infotext"] = Label()
		self["redtext"] = Label()
		self["greentext"] = Label()

		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.enterFolder,
			"back": self.exit,
			"green": self.moveFile,
			"red": self.copyFile,
			"yellow": self.createSymlink,
			"blue": self.setSymlinkName,
		}, -1)

		self["TargetDir"] = DreamExplorerFileList(list_type=DreamExplorerFileList.LIST_TYPE_NODETAILS, directory=item, showDirectories=True, showFiles=showFiles, matchingPattern="^.*\.*", showDetails=False)

		if mode == "copymove":
			self["greentext"].setText(_("Move"))
			self["redtext"].setText(_("Copy"))
		elif mode == "symlink":
			self["actions"].actions.update({"green": self.createSymlink, "red": self.setSymlinkName})
			self["greentext"].setText(_("Create symlink"))
			self["redtext"].setText(_("Change symlink name"))
		self["TargetDir"].onSelectionChanged.append(self.setInfoText)

		self.cmd = ""
		self.actionText = ""
		
		self.onLayoutFinish.append(self.enterFolder)
		self.setTitle(_("Select target location..."))

	def setInfoText(self):
		if self.mode == "copymove":
			self["infotext"].setText(_("Copy/move\n%s\nto %s:") % (self.item, self["TargetDir"].getPathForFile()))
		elif self.mode == "symlink":
			self["infotext"].setText(_("Create symlink %s\nin %s to %s") % (self.linkname, self["TargetDir"].getPathForFile(), self.item))

	def enterFolder(self):
		if self["TargetDir"].canDescent():
			self["TargetDir"].descent()

	def exit(self):
		self.close(None)

	def copyFile(self):
		if self["TargetDir"].getCurrentIndex() != 0:
			dest = self["TargetDir"].getSelection()[1]
			self.actionText = _("Copying %s to %s" % (self.item, dest))
			if self.item[-1:] == '/':
				self.cmd = "cp -afr %s %s" % (self.item, dest)
			else:
				self.cmd = "cp %s %s" % (self.item, dest)

			self.close((self.actionText, self.cmd))

	def moveFile(self):
		if self["TargetDir"].getCurrentIndex() != 0:
			dest = self["TargetDir"].getSelection()[1]
			self.actionText = _("Moving %s to %s" % (self.item, dest))
			self.cmd = "mv -f %s %s" % (self.item, dest)

			self.close((self.actionText, self.cmd))
	
	def createSymlink(self):
		if basename(self.linkname) == self.linkname:
			symlinkdir = self["TargetDir"].getCurrent()[1]
			
			self.actionText = _("Creation of symlink %s in %s to %s" % (self.linkname, symlinkdir, self.item))
			self.cmd = "ln -s %s %s/%s" % (self.item, symlinkdir, self.linkname)
			self.close((self.actionText, self.cmd))
		
	def setSymlinkName(self):
		self.session.openWithCallback(self.callbackSetSymlinkName, InputBox, title=_("Set symlink name:"), windowTitle=_("Dream Explorer 3"), text=self.linkname)
		
	def callbackSetSymlinkName(sefl, answer):
		if answer:
			self.linkname = answer


class SystemdViewer(Screen):
	if getDesktop(0).size().width() >= 1920:
		skin = """
		<screen name="SystemdViewer" position="center,60" size="1800,1010" title="SystemD Viewer">
			<widget name="enabledlabel" position="0,5" size="300,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="enabledtext" position="300,5" size="300,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="activelabel" position="600,5" size="300,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="activetext" position="900,5" size="300,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="failedlabel" position="1200,5" size="300,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="failedtext" position="1500,5" size="300,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />

			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,50" size="1800,2" zPosition="5" scale="stretch" />

			<widget name="statuslabel" position="0,55" size="1800,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />						
			<widget name="statustext" position="0,100" size="1800,400" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />
						
			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,505" size="1800,2" zPosition="5" scale="stretch" />
			
			<widget name="servicelabel" position="0,510" size="1800,40" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />
			<widget name="servicetext" position="0,555" size="1800,400" font="Regular;28" foregroundColor="#f0f0f0" transparent="1" halign="left" />


			<eLabel font="Regular;20" position="0,965" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;20" position="260,965" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;20" position="520,965" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;20" position="780,965" size="60,30" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;20" position="1040,965" size="60,30" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;20" position="1300,965" size="60,30" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			
			<widget name="deleteBookmark" font="Regular;25" halign="left" position="70,960" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget  name="editService" font="Regular;25" halign="left" position="330,960" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget name="toggleLabel" font="Regular;25" halign="left" position="590,960" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget name="enableDisableService" font="Regular;25" halign="left" position="850,960" size="180,40" transparent="1" valign="center" zPosition="6"/>	
			<widget name="ok" font="Regular;25" halign="left" position="1110,960" size="180,40" transparent="1" valign="center" zPosition="6"/>
			<widget  name="exit" font="Regular;25" halign="left" position="1370,960" size="180,40" transparent="1" valign="center" zPosition="6"/>
		</screen>
		"""
	else:
		skin = """
		<screen name="SystemdViewer" position="center,50" size="1260,660" title="SystemD Viewer">
			<widget name="enabledlabel" position="0,5" size="210,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="enabledtext" position="210,5" size="210,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="activelabel" position="420,5" size="210,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="activetext" position="630,5" size="210,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="failedlabel" position="840,5" size="210,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" />
			<widget name="failedtext" position="1050,5" size="210,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" />

			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,40" size="1260,2" zPosition="5" scale="stretch" />

			<widget name="statuslabel" position="0,45" size="1200,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />						
			<widget name="statustext" position="0,80" size="1200,240" font="Regular;16" foregroundColor="#f0f0f0" transparent="1" halign="left" />
						
			<ePixmap alphatest="on" pixmap="/usr/share/enigma2/skin_default/div-h.png" position="0,335" size="1260,2" zPosition="5" scale="stretch" />
			
			<widget name="servicelabel" position="0,340" size="1200,30" font="Regular;18" foregroundColor="#f0f0f0" transparent="1" halign="left" valign="center" />
			<widget name="servicetext" position="0,375" size="1200,240" font="Regular;16" foregroundColor="#f0f0f0" transparent="1" halign="left" />


			<eLabel font="Regular;12" position="0,635" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f50000" zPosition="6"/>
			<eLabel font="Regular;12" position="210,635" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#009f00" zPosition="6"/>
			<eLabel font="Regular;12" position="420,635" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#f5f500" zPosition="6"/>
			<eLabel font="Regular;12" position="630,635" size="40,20" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#0000f9" zPosition="6"/>
			<eLabel font="Regular;12" position="840,635" size="40,20" text="OK" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			<eLabel font="Regular;12" position="1050,635" size="40,20" text="EXIT" transparent="0" valign="center" halign="center" foregroundColor="#ffffff" backgroundColor="#787878" zPosition="6"/>
			
			<widget name="deleteBookmark" font="Regular;16" halign="left" position="50,630" size="150,30" transparent="1" valign="center" zPosition="6"/>
			<widget  name="editService" font="Regular;16" halign="left" position="260,630" size="150,30" transparent="1" valign="center" zPosition="6"/>
			<widget name="toggleLabel" font="Regular;16" halign="left" position="470,630" size="150,30" transparent="1" valign="center" zPosition="6"/>
			<widget name="enableDisableService" font="Regular;16" halign="left" position="680,630" size="150,30" transparent="1" valign="center" zPosition="6"/>	
			<widget name="ok" font="Regular;16" halign="left" position="890,630" size="150,30" transparent="1" valign="center" zPosition="6"/>
			<widget  name="exit" font="Regular;16" halign="left" position="1100,630" size="150,30" transparent="1" valign="center" zPosition="6"/>
		</screen>
		"""	
	
	def __init__(self, session, serviceFile=None, serviceFileWithPath=None):
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
		{
			"ok": self.editService,
			"cancel": self.close,
			"green": self.editService,
			"red": self.close,
			"blue": self.enableDisableService,
			"yellow": self.toggleLabel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
		}, -1)
		
		self.serviceFile = serviceFile
		self.serviceFileWithPath = serviceFileWithPath
		
		self["enabledlabel"] = Label(_("Start at boot"))
		self["enabledtext"] = Label()
		self["activelabel"] = Label(_("Currently"))
		self["activetext"] = Label()
		self["failedlabel"] = Label(_("State"))
		self["failedtext"] = Label()
		self["servicelabel"] = Label("Service")
		self["servicetext"] = ScrollLabel()
		self["statuslabel"] = Label("Log")
		self["statustext"] = ScrollLabel()
		self["deleteBookmark"] = Label()
		self["editService"] = Label(_("Edit service"))
		self["toggleLabel"] = Label(_("Toggle label"))
		self["enableDisableService"] = Label()
		self["ok"] = Label(_("Edit service"))
		self["exit"] = Label(_("Close"))
		
		self.setTitle(_("SystemD Viewer - %s" % (self.serviceFile)))
		
		self.container = eConsoleAppContainer()
		self.appClosed_conn = self.container.appClosed.connect(self.runFinished)
		self.dataavail_conn = self.container.dataAvail.connect(self.getData)
		self.executionData = ""
		self.serviceIsEnabled = False
		self.enableDisablePossible = False
		self.activeLabel = "servicetext"

		self.cmdList = ["systemctl is-enabled %s" % (self.serviceFile), "systemctl is-active %s" % (self.serviceFile), "systemctl is-failed %s" % (self.serviceFile), "systemctl status %s" % (self.serviceFile), "systemctl enable %s" % (self.serviceFile), "systemctl disable %s" % (self.serviceFile)]
		self.getServiceInfo()
			
		self.onLayoutFinish.append(self.readServiceFile)

	def up(self):
		self[self.activeLabel].pageUp()

	def down(self):
		self[self.activeLabel].pageDown()

	def left(self):
		self[self.activeLabel].pageUp()

	def right(self):
		self[self.activeLabel].pageDown()

	def toggleLabel(self):
		if self.activeLabel == "servicetext":
			self.activeLabel = "statustext"
		else:
			self.activeLabel = "servicetext"

	def editService(self):
		self.session.open(vEditor2, self.serviceFileWithPath)

	def getServiceInfo(self):
		self.run = 0
		self.maxRun = 4
		self.container.execute(self.cmdList[self.run])

	def enableDisableService(self):
		if self.enableDisablePossible:
			if self.serviceIsEnabled:
				cmd = "systemctl disable %s" % (self.serviceFile)
				self.run = 5
				self.maxRun = 5
			else:
				cmd = "systemctl enable %s" % (self.serviceFile)
				self.run = 4
				self.maxRun = 4
		
			self.container.execute(self.cmdList[self.run])	
		
	def readServiceFile(self):
		if self.serviceFile is not None:
			with open(self.serviceFileWithPath, "r") as f:
				content = f.read()
				
			self["servicetext"].setText(content)
			
	def getData(self, data):
		self.executionData += data.strip()

	def runFinished(self, retval):
		if retval != 0:
			if self.run == 0:
				self["enabledtext"].setText(_("%s" % (self.executionData)))
				if self.executionData == "enabled":
					self["enableDisableService"].setText(_("Disable service"))
					self.enableDisablePossible = True
					self.serviceIsEnabled = True
				elif self.executionData == "disabled":
					self["enableDisableService"].setText(_("Enable service"))
					self.enableDisablePossible = True
					self.serviceIsEnabled = False
				else:
					self["enableDisableService"].setText("")
					self.enableDisablePossible = False
			elif self.run == 1:
				self["activetext"].setText(_("%s" % (self.executionData)))
			elif self.run == 2:
				self["failedtext"].setText(_("%s" % (self.executionData)))
			elif self.run == 3:
				self["statustext"].setText(_("%s" % (self.executionData)))
			elif self.run == 4:
				self.run = -1
				self.session.open(MessageBox, _("Service %s could not be enabled" % (self.serviceFile)), MessageBox.TYPE_ERROR, timeout=0)
			elif self.run == 5:
				self.run = -1
				self.session.open(MessageBox, _("Service %s could not be disabled" % (self.serviceFile)), MessageBox.TYPE_ERROR, timeout=0)
				
		else:
			if self.run == 0:
				self["enabledtext"].setText(_("%s" % (self.executionData)))
				if self.executionData == "enabled":
					self["enableDisableService"].setText(_("Disable service"))
					self.enableDisablePossible = True
					self.serviceIsEnabled = True
				elif self.executionData == "disabled":
					self["enableDisableService"].setText(_("Enable service"))
					self.enableDisablePossible = True
					self.serviceIsEnabled = False
				else:
					self["enableDisableService"].setText("")
					self.enableDisablePossible = False		
			elif self.run == 1:
				self["activetext"].setText(_("%s" % (self.executionData)))
			elif self.run == 2:
				self["failedtext"].setText(_("%s" % (self.executionData)))
			elif self.run == 3:
				self["statustext"].setText(_("%s" % (self.executionData)))
			elif self.run == 4:
				self.run = -1
				self.session.open(MessageBox, _("Service %s enabled" % (self.serviceFile)), MessageBox.TYPE_INFO, timeout=0)
			elif self.run == 5:
				self.run = -1
				self.session.open(MessageBox, _("Service %s disabled" % (self.serviceFile)), MessageBox.TYPE_INFO, timeout=0)
				
		self.executionData = ""
		if self.run == -1:
			self.getServiceInfo()
		else:
			self.run += 1				
			if self.run < len(self.cmdList) and self.run < self.maxRun:
				self.container.execute(self.cmdList[self.run])
	
