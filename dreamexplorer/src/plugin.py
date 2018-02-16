#######################################################################
#
#    Dream-ExplorerII for Dreambox-Enigma2
#    Coded by Vali (c)2009-2011
#    New version by dre (c) 2016
#    Support: www.dreambox-tools.info
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

from os import chmod, listdir, mkdir, rename, stat, symlink, walk
from os.path import basename, join
from subprocess import call, check_output
from time import localtime, strftime

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.Console import Console
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.EventView import EventViewSimple
from Components.ActionMap import ActionMap
from Components.MultiContent import MultiContentEntryText
from Components.Label import Label
from Components.Sources.List import List
from Components.config import config, ConfigSubsection, ConfigText, ConfigOnOff
from Tools.Directories import fileExists, pathExists
from Tools.HardwareInfo import HardwareInfo
from ServiceReference import ServiceReference
from myFileList import FileList as myFileList
from Screens.InputBox import InputBox
from enigma import eConsoleAppContainer, eServiceReference, eServiceCenter

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
	from Plugins.Extensions.MerlinMusicPlayer.plugin import MerlinMusicPlayerScreen, Item
	MMPlayerInstalled = True
except:
	MMPlayerInstalled = False
	
config.plugins.DreamExplorer = ConfigSubsection()
config.plugins.DreamExplorer.startDir = ConfigText(default="/")
config.plugins.DreamExplorer.useMediaFilter = ConfigOnOff(default=False)
config.plugins.DreamExplorer.CopyDest = ConfigText(default="/")

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return [
		PluginDescriptor(name=_("Dream-Explorer"), description=_("Explore your Dreambox."), where = [PluginDescriptor.WHERE_PLUGINMENU], icon="dreamexplorer.png", fnc=main),
		PluginDescriptor(name=_("Dream-Explorer"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
	]

def main(session, **kwargs):
	session.open(DreamExplorerII)

######## DREAM-EXPLORER START #######################
class DreamExplorerII(Screen):
	skin = """
		<screen position="center,center" size="900,500" title="Dream-Explorer">
			<widget name="filelist" position="0,0" scrollbarMode="showOnDemand" size="890,450" zPosition="4"/>
			<eLabel backgroundColor="#555555" position="5,470" size="890,2" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="~/res/red.png" position="0,475" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="~/res/green.png" position="155,475" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="~/res/yellow.png" position="310,475" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="~/res/blue.png" position="465,475" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="~/res/menu.png" position="620,475" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="~/res/info.png" position="775,475" size="35,25" zPosition="5"/>
			<eLabel font="Regular;18" halign="left" position="35,475" size="120,25" text="Delete" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;18" halign="left" position="190,475" size="120,25" text="Rename" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;18" halign="left" position="345,475" size="120,25" text="Move/Copy" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;18" halign="left" position="500,475" size="120,25" text="Bookmarks" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;18" halign="left" position="655,475" size="120,25" text="Options" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;18" halign="left" position="810,475" size="90,25" text="Info" transparent="1" valign="center" zPosition="6"/>
		</screen>"""

	def __init__(self, session, args = None):
		self.skin = DreamExplorerII.skin
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.sesion = session
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.boxtype = HardwareInfo().get_device_name()
		self.command = [ "ls" ]
		self.selectedDir = "/tmp/"
		self.bookmarks = []
		# DarkVolli 20120702: add filetype wmv
		self.mediaPattern = "^.*\.(ts|m2ts|mp3|wav|ogg|jpg|jpeg|jpe|png|bmp|mpg|mpeg|mkv|mp4|mov|divx|avi|mp2|m4a|flac|ifo|vob|iso|sh|flv|3gp|mod|wmv)"
		if pathExists(config.plugins.DreamExplorer.startDir.value):
			startDirectory = config.plugins.DreamExplorer.startDir.value
		else:
			startDirectory = None

		if config.plugins.DreamExplorer.useMediaFilter.value == False:
			self.useMediaFilter = False
			self["filelist"] = myFileList(startDirectory, showDirectories = True, showFiles = True, matchingPattern = None, useServiceRef = False)
		else:
			self.useMediaFilter = True
			self["filelist"] = myFileList(startDirectory, showDirectories = True, showFiles = True, matchingPattern = self.mediaPattern, useServiceRef = False)
			
		self["TEMPfl"] = myFileList("/", matchingPattern = "(?i)^.*\.(jpeg|jpg|jpe|png|bmp)")
		
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "MenuActions", "EPGSelectActions", "InfobarActions"],
		{
			"ok": self.executeAction,
			"back": self.exitPlugin,
			"green": self.renameItem,
			"red": self.deleteItem,
			"blue": self.showBookmarks,
			"yellow": self.openCopyMoveManager,
			"menu": self.showContextMenu,
			"info": self.showInfo,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"nextBouquet": self.sortName,
			"prevBouquet": self.sortDate,
		}, -1)
		
		self.cmd= ""
		
		self.container = eConsoleAppContainer()
		self.appClosed_conn = self.container.appClosed.connect(self.runFinished)		
		
		self.onLayoutFinish.append(self.readBookmarks)

	def executeAction(self):
		global DVDPlayerInstalled
		global PicturePlayerInstalled
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateLocationInfo()
		else:
			filename = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			testFileName = self["filelist"].getFilename()
			testFileName = testFileName.lower()

			if filename != None:
				extensionlist = testFileName.split('.')
				extension = extensionlist[-1].lower()
				if len(extensionlist) > 1:
					tar = extensionlist[-2].lower()

				if extension == "ts":
					fileRef = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + filename)
					self.session.open(MoviePlayer, fileRef)
					
				elif extension in ["mpg","mpeg","mkv","m2ts","vob","mod","avi","mp4","divx","mov","flv","3gp","wmv"]:
					fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
					self.session.open(MoviePlayer, fileRef)

				elif extension in ["mp3","wav","ogg","m4a","mp2","flac"]:
					if MMPlayerInstalled:
						SongList,SongIndex = self.searchMusic()
						try:
							self.session.openWithCallback(self.restartService, MerlinMusicPlayerScreen, SongList, SongIndex, False, self.currentService, None)
						except:
							self.session.open(MessageBox, _("Incompatible MerlinMusicPlayer version!"), MessageBox.TYPE_INFO)
					else:
						fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
						m_dir = self["filelist"].getCurrentDirectory()
						self.session.open(MusicExplorer, fileRef, m_dir, testFileName)

				elif extension in ["jpg","jpeg","jpe","png","bmp"]:
					if self["filelist"].getSelectionIndex()!=0:
						if PicturePlayerInstalled:
							self["TEMPfl"].changeDir(self["filelist"].getCurrentDirectory())
							self.session.open(Pic_Full_View, self["TEMPfl"].getFileList(), 0, self["filelist"].getCurrentDirectory())
						
						
				elif extension == "mvi":
					self.session.nav.stopService()
					self.session.openWithCallback(self.restartService, MviExplorer, filename)
					
				elif testFileName == "video_ts.ifo":
					if DVDPlayerInstalled:
						if (self["filelist"].getCurrentDirectory()).lower().endswith("video_ts/"):
							self.session.openWithCallback(self.restartService, DVDPlayer, dvd_filelist=[self["filelist"].getCurrentDirectory()])
							
				elif extension == "iso":
					if DVDPlayerInstalled:
						self.session.openWithCallback(self.restartService, DVDPlayer, dvd_filelist=[filename])
						
				elif testFileName.endswith(".bootlogo.tar.gz"):
					self.command = ["mount -rw /boot -o remount", "sleep 3","tar -xzvf " + filename + " -C /", "mount -ro /boot -o remount"]
					askList = [(_("Cancel"), "NO"),(_("Install new bootlogo..."), "YES2ALL")]
					msg = self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Bootlogo-package:\n"+filename), list=askList)
					msg.setTitle(_("Dream-Explorer : Install..."))
					
				elif extension in ["gz","bz2"] and tar == "tar":
					if extension == "gz":
						self.command = [ "tar -xzvf " + filename + " -C /" ]
					elif extension == "bz2":
						self.command = [ "tar -xjvf " + filename + " -C /" ]
						
					msg = self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("%s-archive:\n%s" %(extension, filename)), list=[(_("Cancel"), "NO"),(_("Install this package"), "YES")])
					msg.setTitle(_("Dream-Explorer : Install..."))

				elif extension == "deb":
					self.command = [ "apt-get update && dpkg -i " + filename ]
					askList = [(_("Cancel"), "NO"),(_("Install this package"), "YES")]
					msg = self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("DEB-package:\n"+filename), list=askList)
					msg.setTitle(_("Dream-Explorer : Install..."))
					
				elif testFileName.endswith(".sh"):
					self.command = [ filename ]
					askList = [(_("Cancel"), "NO"),(_("View this shell-script"), "VIEW"),(_("Execute script"), "YES")]
					self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Do you want to execute %s?\n" %(filename)), list=askList)
					
				else:
					xfile=stat(filename)
					if (xfile.st_size < 1024000):
						self.session.open(vEditor, filename)
					else:
						self.session.open(MessageBox, _("File is too big to display content"), MessageBox.TYPE_INFO, windowTitle=_("Dream-Explorer"))

	def restartService(self):
		if self.session.nav.getCurrentlyPlayingServiceReference() is None:
			self.session.nav.playService(self.currentService)

	def readBookmarks(self):
		self.updateLocationInfo()
		if fileExists("/etc/myBookmarks"):
			try:
				file = open("/etc/myBookmarks", "r")
			except:
				msg = self.session.open(MessageBox, _("Error reading bookmarks"), MessageBox.TYPE_ERROR)
				msg.setTitle(_("Dream-Explorer"))
			if file is not None:
				for line in file:
					self.bookmarks.append(line)
				file.close()

	def updateLocationInfo(self):
		try:
			if self.useMediaFilter:
				self.setTitle(_("[Media files] " + self["filelist"].getCurrentDirectory()))
			else:
				self.setTitle(_("[All files] " + self["filelist"].getCurrentDirectory()))	
		except:
			self.setTitle(_("Dream-Explorer"))

	def showContextMenu(self):
		if self.useMediaFilter:
			mftext= _("Disable media filter")
		else:
			mftext= _("Enable media filter")
		contextList = [
			(_("Cancel"), "NO"),
			(mftext, "FILTER"),
			(_("Sort by name (bouquet+)"), "SORTNAME"),
			(_("Sort by date (bouquet-)"), "SORTDATE")
		]
		if self["filelist"].canDescent():
			if self["filelist"].getSelectionIndex()!=0:
				self.selectedDir = self["filelist"].getSelection()[0]
				if self.selectedDir + "\n" in self.bookmarks:
					contextList.extend((
						(_("Remove directory from Bookmarks"), "DELLINK"),
					))
				else:
					contextList.extend((
						(_("Add directory to Bookmarks"), "ADDLINK"),
					))
				contextList.extend((
					(_("Create new file"), "NEWFILE"),
					(_("Create new directory"), "NEWDIR"),
					(_("Create softlink to selected"), "SYMLINKDIR"),
					(_("Set start directory"), "SETSTARTDIR"),
				))
		else:
			contextList.extend((
				(_("Preview all pictures"), "PLAYDIRPICTURE"),
				(_("Create new file"), "NEWFILE"),
				(_("Create new directory"), "NEWDIR"),
				(_("Create softlink to selected"), "SYMLINK"),
				(_("Set archive mode (644)"), "CHMOD644"),
				(_("Set executable mode (755)"), "CHMOD755"),
			))
		contextList.extend((
			(_("About"), "ABOUT"),
		))
		
		self.session.openWithCallback(self.executeSelected, ChoiceBox, title=_("Options:\n"), list=contextList, windowTitle=_("Dream-Explorer"))

	def executeSelected(self, answer):
		global PicturePlayerInstalled
		answer = answer and answer[1]
		if answer == "YES":
			self.session.open(Console, cmdlist = [ self.command[0] ])
		elif answer == "YES2ALL":
			self.session.open(Console, cmdlist = self.command)
		elif answer == "VIEW":
			viewfile=stat(self.command[0])
			if (viewfile.st_size < 61440):
				self.session.open(vEditor, self.command[0])
		elif answer == "PLAYDIRPICTURE":
			if PicturePlayerInstalled:
				self["TEMPfl"].changeDir(self["filelist"].getCurrentDirectory())
				self.session.open(Pic_Thumb, self["TEMPfl"].getFileList(), 0, self["filelist"].getCurrentDirectory())
			else:
				msg = self.session.open(MessageBox, _("PicturePlayer not available."), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
		elif answer == "ADDLINK" or answer == "DELLINK":
			try:
				file = open("/etc/myBookmarks", "w")
			except:
				msg = self.session.open(MessageBox, _("Error writing bookmarks"), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
			if file is not None:
				if answer == "ADDLINK":
					self.bookmarks.append(self.selectedDir+"\n")
				else:
					self.bookmarks.remove(self.selectedDir+"\n")
				
				for bookmark in self.bookmarks:
					file.write(bookmark)
				file.close()

		elif answer == "FILTER":
			if self.useMediaFilter:
				self.useMediaFilter=False
				config.plugins.DreamExplorer.useMediaFilter.value = False
				self["filelist"].matchingPattern = None
			else:
				self.useMediaFilter=True
				config.plugins.DreamExplorer.useMediaFilter.value = True
				self["filelist"].matchingPattern = self.mediaPattern

			config.plugins.DreamExplorer.useMediaFilter.save()
			self["filelist"].refresh()
			self.updateLocationInfo()

		elif answer == "NEWFILE":
			self.session.openWithCallback(self.callbackNewFile, InputBox, title=_(self["filelist"].getCurrentDirectory()), windowTitle=_("Create new file in..."), text="name")
		elif answer == "NEWDIR":
			self.session.openWithCallback(self.callbackNewDir, InputBox, title=_(self["filelist"].getCurrentDirectory()), windowTitle=_("Create new directory in..."), text="name")
		elif answer == "SETSTARTDIR":
			newStartDir = self["filelist"].getSelection()[0]
			msg = self.session.openWithCallback(self.callbackSetStartDir,MessageBox,_("Do you want to set\n"+newStartDir+"\nas start directory?"), MessageBox.TYPE_YESNO, windowTitle=_("Dream-Explorer..."))
		elif answer == "SORTNAME":
			list = self.sortName()
		elif answer == "SORTDATE":
			list = self.sortDate()
		elif answer == "ABOUT":
 			msg = self.session.open(MessageBox, _("Dreambox-Explorer\noriginal version by Vali (2010)\nnew version by Dre (2016)\n\nSupport & help: board.dreambox-tools.info"), MessageBox.TYPE_INFO, windowTitle=_("Info..."))
		elif answer == "SYMLINK":
			if not(self.useMediaFilter):
				target = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
				self.session.openWithCallback(self.callbackCopyMoveManager, SymlinkScreen, target, self["filelist"].getFilename())
		elif answer == "SYMLINKDIR":
			if not(self.useMediaFilter):
				target = self["filelist"].getFilename()
				linkname = self["filelist"].getFilename().split("/")[-2]
				self.session.openWithCallback(self.callbackCopyMoveManager, SymlinkScreen, target, linkname)				
		elif answer == "CHMOD644":
			chmod(self["filelist"].getCurrentDirectory() + self["filelist"].getFilename(), 0644)
		elif answer == "CHMOD755":
			chmod(self["filelist"].getCurrentDirectory() + self["filelist"].getFilename(), 0755)

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

	def formatSize(self, size):
		if (size < 1024):
			formattedSize = str(size)+_(" B")
		elif (size < 1048576):
			formattedSize = str(size/1024)+_(" KB")
		else:
			formattedSize = str(size/1048576)+_(" MB")
		return formattedSize

	def showInfo(self):
		if self["filelist"].canDescent():
			if self["filelist"].getSelectionIndex()!=0:
				curSelDir = self["filelist"].getSelection()[0]
				dir_stats = stat(curSelDir)
				dir_infos = "size "+str(self.formatSize(dir_stats.st_size))+"    "
				dir_infos = dir_infos+"last-mod "+strftime("%d.%m.%Y %H:%M:%S",localtime(dir_stats.st_mtime))+"    "
				dir_infos = dir_infos+"mode "+str(dir_stats.st_mode)
				self.setTitle(_(dir_infos))
			else:
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
			
				msg = self.session.open(MessageBox, _("Dreambox model: " + self.boxtype + "\n\n" + ret), MessageBox.TYPE_INFO, windowTitle=_("Dream-Explorer"))
		else:
			curSelFile = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			file_stats = stat(curSelFile)
			file_infos = "size "+str(self.formatSize(file_stats.st_size))+"    "
			file_infos = file_infos+"last-mod "+strftime("%d.%m.%Y %H:%M:%S",localtime(file_stats.st_mtime))+"    "
			file_infos = file_infos+"mode "+str(file_stats.st_mode)
			self.setTitle(_(file_infos))
			if curSelFile.endswith(".ts"):
				serviceref = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + curSelFile)
				serviceHandler = eServiceCenter.getInstance()
				info = serviceHandler.info(serviceref)
				evt = info.getEvent(serviceref)
				if evt:
					self.session.open(EventViewSimple, evt, ServiceReference(serviceref))

	def setBookmark(self, answer):
		answer = answer and answer[1]
		try:
			if answer[0] == "/":
				self["filelist"].changeDir(answer[:-1])
				self.updateLocationInfo()
		except:
			pass

	def showBookmarks(self):
		bookmarklist = [(_("Cancel"), "BACK")]
		for bookmark in self.bookmarks:
			bookmarklist.append((_(bookmark), bookmark))
		self.session.openWithCallback(self.setBookmark, ChoiceBox, title=_("My Bookmarks"), list=bookmarklist, windowTitle=_("Dream-Explorer"))

	def runFinished(self, retval):
		if retval != 0:
			msg = self.session.open(MessageBox,_("%s \nfailed!" % self.cmd), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
		else:
			msg = self.session.open(MessageBox,_("%s \nexecuted!" % self.cmd), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"), timeout=3)
			
		self["filelist"].refresh()
			
	def deleteItem(self):
		if self.useMediaFilter:
			msg = self.session.open(MessageBox,_('Turn off the media-filter first.'), MessageBox.TYPE_INFO, windowTitle=_("Dream-Explorer..."))
			return
			
		if not(self["filelist"].canDescent()):
			self.item = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			self.type = "file"
			self.typetext = _("file")
			
		elif (self["filelist"].getSelectionIndex()!=0) and (self["filelist"].canDescent()):
			self.item = self["filelist"].getSelection()[0]
			self.type = "directory"
			self.typetext = _("directory")
		else:
			return
			
		msg = self.session.openWithCallback(self.callbackDeleteItem,MessageBox,_("Do you really want to delete:\n"+self.item), MessageBox.TYPE_YESNO, windowTitle=_("Dream-Explorer - Delete %s..." %(self.type)))

	def callbackDeleteItem(self, answer):
		if answer is True:
			if self.type == "directory":
				self.cmd = "rm -rf '%s'" %(self.item)
			elif self.type == "file":
				self.cmd = "rm -f '%s'" %(self.item)
			
			self.container.execute(self.cmd)

	def renameItem(self):
		if self.useMediaFilter:
			msg = self.session.open(MessageBox,_('Turn off the media-filter first.'), MessageBox.TYPE_INFO, windowTitle=_("Dream-Explorer..."))
			return
			
		if not(self["filelist"].canDescent()):
			self.item = self["filelist"].getFilename()
			self.type = "file"
			self.typetext = _("file")
		elif self["filelist"].getSelectionIndex()!=0 and self["filelist"].canDescent():
			self.item = self["filelist"].getSelection()[0]
			self.type = "directory"
			self.typetext = _("directory")
		else:
			return
			
		self.session.openWithCallback(self.callbackRenameItem, InputBox, title=_("Old:  "+ self.item), windowTitle=_("Rename %s..." %(self.typetext)), text=self.item)

	def callbackRenameItem(self, answer):
		if answer is not None:
			if self.type == "file":
				path = self["filelist"].getCurrentDirectory()
				source = path + self.item
				dest = path + answer
			elif self.type == "directory":
				source = self.item
				dest = answer
				
			try:
				rename(source, dest)
			except:
				msg = self.session.open(MessageBox,_("Rename: %s \nfailed!" % answer), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
			self["filelist"].refresh()

	def callbackNewFile(self, answer):
		if answer is None:
			return
		dest = self["filelist"].getCurrentDirectory()
		if (" " in answer) or (" " in dest) or (answer==""):
			msg = self.session.open(MessageBox,_("File name error !"), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
			return
		else:
			order = dest + answer
			try:
				open(order, 'a').close()
				self["filelist"].refresh()
			except:
				msg = self.session.open(MessageBox,_("%s \nfailed!" % order), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
				self["filelist"].refresh()

	def callbackNewDir(self, answer):
		if answer is None:
			return
		dest = self["filelist"].getCurrentDirectory()
		if (" " in answer) or (" " in dest) or (answer==""):
			msg = self.session.open(MessageBox,_("Directory name error !"), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
			return
		else:
			order = dest + answer
			try:
				if not pathExists(order):
					mkdir(order)
				self["filelist"].refresh()
			except:
				msg = self.session.open(MessageBox,_("%s \nfailed!" % order), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
				self["filelist"].refresh()

	def openCopyMoveManager(self):
		if self.useMediaFilter:
			msg = self.session.open(MessageBox,_('Turn off the media-filter first.'), MessageBox.TYPE_INFO, windowTitle=_("Dream-Explorer..."))
			return
			
		if not(self["filelist"].canDescent()):
			source = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
		elif (self["filelist"].getSelectionIndex()!=0) and (self["filelist"].canDescent()): #NEW
			source = self["filelist"].getSelection()[0]
		else:
			return
		self.session.openWithCallback(self.callbackCopyMoveManager, CopyMoveManager, source)

	def callbackCopyMoveManager(self, answer):
		self["filelist"].refresh()

	def callbackSetStartDir(self, answerSD):
		if answerSD is True:
			config.plugins.DreamExplorer.startDir.value = self["filelist"].getSelection()[0]
			config.plugins.DreamExplorer.startDir.save()

	def sortName(self):
		list = self["filelist"].sortName()
		self.setTitle(_("[sort by Name] " + self["filelist"].getCurrentDirectory()))

	def sortDate(self):
		list = self["filelist"].sortDate()
		self.setTitle(_("[sort by Date] " + self["filelist"].getCurrentDirectory()))

	def searchMusic(self):
		slist = []
		foundIndex = 0
		index = 0
		files = listdir(self["filelist"].getCurrentDirectory())
		files.sort()
		for name in files:
			testname = name.lower()
			if testname.endswith(".mp3") or name.endswith(".m4a") or name.endswith(".ogg") or name.endswith(".flac"):
				slist.append((Item(text = name, filename = join(self["filelist"].getCurrentDirectory(),name)),))
				if self["filelist"].getFilename() == name:
					foundIndex = index
				index = index + 1
		return slist,foundIndex

	def exitPlugin(self):
		if self.useMediaFilter:
			config.plugins.DreamExplorer.useMediaFilter.value = True
		else:
			config.plugins.DreamExplorer.useMediaFilter.value = False
		config.plugins.DreamExplorer.useMediaFilter.save()

		self.close()

######## DREAM-EXPLORER END ####################### 

class vEditor(Screen):
	skin = """
		<screen position="center,center" size="900,500" title="File-Explorer">
			<widget source="filedata" render="Listbox" position="0,0" size="900,500" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template":[
									MultiContentEntryText(pos=(0,0), size=(900,25), text=0),					],
					"fonts": [gFont("Regular",20)],
					"itemHeight": 25
					}
				</convert>
			</widget>			
		</screen>"""

	def __init__(self, session, file):
		self.skin = vEditor.skin
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.session = session
		self.file_name = file
		self.list = []
		self["filedata"] = List(self.list)
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.editLine,
			"back": self.exitEditor
		}, -1)
		self.selLine = None
		self.oldLine = None
		self.isChanged = False
		
		self.getFileContent()

	def exitEditor(self):
		if self.isChanged:
			warningtext = "\nhas been changed! Do you want to save it?\n\nWARNING!"
			warningtext = warningtext + "\n\nThe editor is beta (not fully tested)."
			warningtext = warningtext + "\nThe author is NOT responsible\nfor any data lost!"
			msg = self.session.openWithCallback(self.saveFile, MessageBox,_(self.file_name+warningtext), MessageBox.TYPE_YESNO, windowTitle=_("Dream-Explorer..."))
		else:
			self.close()

	def getFileContent(self):
		try:
			flines = open(self.file_name, "r")
			self.templist = flines.readlines()

			for entry in self.templist:
				self.list.append([entry])
			flines.close()

			self.setTitle(self.file_name)
			self["filedata"].setList(self.list)
		except:
			pass

	def editLine(self):
		self.selLine = self["filedata"].index
		
		self.oldLine = self.list[self.selLine][0]
		editableText = self.oldLine.strip("\n")
		self.session.openWithCallback(self.callbackEditLine, InputBox, title=_("Old:\n %s" %(self.oldLine)), windowTitle=_("Edit line: %d" %(self.selLine+1)), text=editableText)

	def callbackEditLine(self, newline):
		if newline is not None:
			self.isChanged = True
			self.list[self.selLine][0] = "%s\n" %(newline)
			self["filedata"].setList(self.list)
		self.selLine = None
		self.oldLine = None

	def saveFile(self, answer):
		if answer is True:
			try:
				eFile = open(self.file_name, "w")
				for x in self.list:
					eFile.writelines(x)
				eFile.close()
			except:
				pass
		self.close()

class MviExplorer(Screen):
	skin = """
		<screen position="-300,-300" size="10,10" title="mvi-Explorer">
		</screen>"""
	def __init__(self, session, file):
		self.skin = MviExplorer.skin
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.file_name = file
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.close,
			"back": self.close
		}, -1)
		self.onLayoutFinish.append(self.showMvi)
		
	def showMvi(self):
		call(['showiframe', self.file_name])

class MoviePlayer(MP_parent):
	def __init__(self, session, service):
		self.session = session
		MP_parent.__init__(self, self.session, service)

	def leavePlayer(self):
		try: 
			self.updateMovieData() # Merlin only feature
		except: pass
		self.is_closing = True
		self.close()

	def leavePlayerConfirmed(self, answer):
		pass

	def doEofInternal(self, playing):
		try: 
			self.updateMovieData() # Merlin only feature
		except: pass
		if not self.execing:
			return
		if not playing :
			return
		self.leavePlayer()

	def showMovies(self):
		try: 
			self.updateMovieData() # Merlin only feature
		except: pass
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
		self.skin_path = plugin_path
		self.MusicDir = MusicDir
		self.musicList = []
		self.Mindex = 0
		self.curFile = theFile
		self.searchMusic()
		self.onLayoutFinish.append(self.showMMI)

	def showMMI(self):
		call(['showiframe', '%s/res/music.mvi' % plugin_path])

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
		if len(self.musicList)>2:
			if self.Mindex<(len(self.musicList)-1):
				self.Mindex = self.Mindex + 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox,_('No more playable files.'), MessageBox.TYPE_INFO, windowTitle=_("Dream-Explorer"))

	def seekBack(self):
		if len(self.musicList)>2:
			if self.Mindex>0:
				self.Mindex = self.Mindex - 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox,_('No more playable files.'), MessageBox.TYPE_INFO, windowTitle=_("Dream-Explorer"))

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.seekFwd()

class CopyMoveManager(Screen):
	skin = """
			<screen position="center,center" size="900,500" title="Select target location...">
				<widget name="Warning" font="Regular;20" halign="center" position="0,0" size="900,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="TargetDir" position="0,100" scrollbarMode="showOnDemand" size="900,325" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,470" size="890,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="~/res/red.png" position="0,475" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="~/res/yellow.png" position="310,475" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,475" size="120,25" text="Move" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,475" size="120,25" text="Copy" transparent="1" valign="center" zPosition="6"/>
			</screen>"""

	def __init__(self, session, source = "/tmp/none"):
		self.skin = CopyMoveManager.skin
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.sesion = session
		self.source = source
		self["Warning"] = Label(_("WARNING! You're about to move or copy\n" + source + "\nto:"))
		self["TargetDir"] = myFileList(config.plugins.DreamExplorer.CopyDest.value, showDirectories = True, showFiles = False, matchingPattern = "^.*\.*", useServiceRef = False)
		
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.enterFolder,
			"back": self.exit,
			"red": self.moveFile,
			"yellow": self.copyFile
		}, -1)
		
		self.cmd= ""
		
		self.container = eConsoleAppContainer()
		self.appClosed_conn = self.container.appClosed.connect(self.runFinished)
		
		self.onLayoutFinish.append(self.enterFolder)

	def runFinished(self, retval):
		if retval != 0:
			msg = self.session.open(MessageBox,_("%s \nfailed!" % self.cmd), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
		else:
			msg = self.session.open(MessageBox,_("%s \nexecuted!" % self.cmd), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"), timeout=3)
			
		self.close(" ")

	
	def enterFolder(self):
		if self["TargetDir"].canDescent():
			self["TargetDir"].descent()

	def exit(self):
		self.close(" ")

	def copyFile(self):
		if self["TargetDir"].getSelectionIndex()!=0:
			dest = self["TargetDir"].getSelection()[0]
			if self.source[len(self.source)-1] == '/':
				self.cmd = "cp -af %s %s" %(self.source, dest)
			else:
				self.cmd = "cp %s %s" %(self.source, dest)

			config.plugins.DreamExplorer.CopyDest.value = dest
			config.plugins.DreamExplorer.CopyDest.save()

			self.container.execute(self.cmd)

	def moveFile(self):
		if self["TargetDir"].getSelectionIndex()!=0:
			dest = self["TargetDir"].getSelection()[0]
			if self.source[len(self.source)-1] == '/':
				self.cmd = "mv -f %s %s" %(self.source, dest)
			else:
				self.cmd = "mv -f %s %s" %(self.source, dest)

			config.plugins.DreamExplorer.CopyDest.value = dest
			config.plugins.DreamExplorer.CopyDest.save()
			
			self.container.execute(self.cmd)

class SymlinkScreen(Screen):
	skin = """
			<screen position="center,center" size="900,500" title="Create a symlink...">
				<widget name="Warning" font="Regular;20" halign="center" position="0,0" size="900,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="Target" position="0,100" scrollbarMode="showOnDemand" size="900,325" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,470" size="890,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="~/res/red.png" position="0,475" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="~/res/yellow.png" position="310,475" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,475" size="180,25" text="Change symlink name" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,475" size="220,25" text="Create softlink" transparent="1" valign="center" zPosition="6"/>
			</screen>"""
			
	def __init__(self, session, target="/tmp", linkname=None, isDir=False):
		self.skin = SymlinkScreen.skin
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.session = session
		self.target = target
		self.linkname = linkname
		self["Warning"] = Label("")
		self["Target"] = myFileList('/', showDirectories=True, showFiles=True, matchingPattern = None, useServiceRef = False)
		self["Target"].onSelectionChanged.append(self.updateText)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.enterFolder,
			"back": self.exit,
			"red": self.changeSymlinkName,
			"yellow": self.createSymlink
		}, -1)
		
		self.updateText()

	def updateText(self):
		if self["Target"].getSelectionIndex() == 0:
			self.current = "/"
		elif self["Target"].canDescent():
			self.current = self["Target"].getFilename()
		else:
			self.current = self["Target"].getCurrentDirectory()
		self["Warning"].setText(_("You're about to create a symlink to %s\nfrom\n%s%s" %(self.target, self.current, self.linkname)))

	def changeSymlinkName(self):
		self.session.openWithCallback(self.callbackSetSymlinkName, InputBox, title=_("Define the new symlink name here:"), windowTitle=_("Dream Explorer..."), text=self.linkname)

	def callbackSetSymlinkName(self, answer):
		if answer is None:
			return
		if (" " in answer) or (answer==""):
			msg = self.session.open(MessageBox,_("Symlink name error!"), MessageBox.TYPE_ERROR, windowTitle=_("Dream-Explorer"))
			return
		else:
			self.linkname = answer
			self.updateText()

	def enterFolder(self):
		if self["Target"].canDescent():
			self["Target"].descent()

	def exit(self):
		self.close(" ")

	def createSymlink(self):
		if basename(self.linkname) == self.linkname:
			symlink(self.target, join(self.current, self.linkname))
		self.close(" ")
