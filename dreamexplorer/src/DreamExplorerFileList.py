#  Coded by dre (c) 2021
#  E-Mail: dre@dreamboxtools.de
#  Support: board.dreamboxtools.de
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Property GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Property GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Property GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.

from __future__ import print_function

from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.Harddisk import harddiskmanager
from Components.TemplatedMultiContentComponent import TemplatedMultiContentComponent
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import getSize, prettySize

from enigma import RT_VALIGN_CENTER, RT_HALIGN_RIGHT, eServiceReference, eServiceCenter, gFont, iServiceInformation, getDesktop, eListbox

from os import path as os_path, listdir, lstat as os_lstat
from re import compile as re_compile
import stat as stat_stat
from time import localtime, strftime

EXTENSIONS = {
		"m4a": "music",
		"mp2": "music",
		"mp3": "music",
		"wav": "music",
		"wma": "music",
		"ogg": "music",
		"flac": "music",
		"jpg": "picture",
		"jpeg": "picture",
		"jpe": "picture",
		"png": "picture",
		"bmp": "picture",
		"mvi": "picture",
		"dat": "movie",
		"ts": "movie",
		"avi": "movie",
		"divx": "movie",
		"m4v": "movie",		
		"mpg": "movie",
		"mpeg": "movie",
		"mkv": "movie",
		"mp4": "movie",
		"mov": "movie",
		"m2ts": "movie",
		"flv": "movie",
		"wmv": "movie",
		"vob": "movie",
		"ifo": "movie",
		"iso": "movie",
		"3gp": "movie",
		"mod": "movie",
		"deb": "package",
		"gz": "archive",
		"bz2": "archive",
		"sh": "script",
		"service":"service",
	}

class DreamExplorerFileList(TemplatedMultiContentComponent):
	COMPONENT_ID = "DreamExplorerFileList"
	LIST_TYPE_FULL = 1
	LIST_TYPE_NODETAILS = 2
	
	SORT_NAME_ASC = 1
	SORT_NAME_DESC = 2
	SORT_DATE_ASC = 3
	SORT_DATE_DESC = 4
	
	LIST_STYLES = {
		LIST_TYPE_FULL: "default",
		LIST_TYPE_NODETAILS: "nodetails",
	}
	
	if getDesktop(0).size().width() >= 1920:
		default_template = """{
			"templates":
			{
				"default":
				( 40,
					[
						MultiContentEntryPixmapAlphaBlend(pos=(5,5), size=(30,30), png=6),
						MultiContentEntryText(pos=(40,0), size=(600,40), flags=RT_VALIGN_CENTER, font=0, text=0),
						MultiContentEntryText(pos=(640,0), size=(200,40), flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, font=0, text=7),
						MultiContentEntryText(pos=(840,0), size=(260,40), flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, font=0, text=8),
						MultiContentEntryText(pos=(1100,0), size=(80,40), flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, font=0, text=9),
						MultiContentEntryText(pos=(1180,0), size=(650,40), flags=RT_VALIGN_CENTER, font=0, text=10),
					]
				),
				"nodetails":
				( 40,
					[
						MultiContentEntryPixmapAlphaBlend(pos=(5,5), size=(30,30), png=6),
						MultiContentEntryText(pos=(40,0), size=(600,40), flags=RT_VALIGN_CENTER, font=0, text=0),
					]
				),
			},
			"fonts":	
			[
				gFont("Regular", 28),
			]
		}"""
	else:
		default_template = """{
			"templates":
			{
				"default":
				( 30,
					[
						MultiContentEntryPixmapAlphaBlend(pos=(5,5), size=(20,20), png=6),
						MultiContentEntryText(pos=(30,0), size=(400,30), flags=RT_VALIGN_CENTER, font=0, text=0),
						MultiContentEntryText(pos=(430,0), size=(135,30), flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, font=0, text=7),
						MultiContentEntryText(pos=(565,0), size=(175,30), flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, font=0, text=8),
						MultiContentEntryText(pos=(740,0), size=(55,30), flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, font=0, text=9),
						MultiContentEntryText(pos=(795,0), size=(440,30), flags=RT_VALIGN_CENTER, font=0, text=10),
					]
				),
				"nodetails":
				( 30,
					[
						MultiContentEntryPixmapAlphaBlend(pos=(5,5), size=(20,20), png=6),
						MultiContentEntryText(pos=(30,0), size=(400,30), flags=RT_VALIGN_CENTER, font=0, text=0),
					]
				),
			},
			"fonts":	
			[
				gFont("Regular", 18),
			]
		}"""		

	def __init__(self, list_type=None, sortType=None, directory=None, showDirectories=True, showFiles=True, showMountpoints=True, matchingPattern=None, inhibitDirs=False, inhibitMounts=False, isTop=False, enableWrapAround=True, additionalExtensions=None, showDetails=True):
		TemplatedMultiContentComponent.__init__(self)
		self.list = []
		self.setListType(list_type or self.LIST_TYPE_FULL)
		self.sortType = sortType or self.SORT_NAME_ASC
		
		self.mountpoints = []
		self.current_directory = None
		self.current_mountpoint = None
		self.showDirectories = showDirectories
		self.showFiles = showFiles
		self.showMountpoints = showMountpoints
		self.matchingPattern = matchingPattern
		self.inhibitDirs = inhibitDirs or []
		self.inhibitMounts = inhibitMounts or []
		self.isTop = isTop
		self.additional_extensions = additionalExtensions
		self.showDetails = showDetails
		self.iconSet = "/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/icons"

		self.serviceHandler = eServiceCenter.getInstance()	
		
		self.refreshMountpoints()
		if directory is not None:
			self.changeDirectory(directory)

		self.l.setBuildFunc(self.buildEntry)
		
		self.onSelectionChanged = []

	def applySkin(self, desktop, parent):
		for attr in self.skinAttributes:
			if attr[0] == "iconSet":
				self.iconSet = attr[1]
		GUIComponent.applySkin(self, desktop, parent)
		self.applyTemplate()

	
	def redrawList(self):
		self.l.invalidate()

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	def setListType(self, type):
		self.list_type = type
		self.setTemplate(self.LIST_STYLES[type])

	def setSortType(self, type):
		self.sortType = type

	def getSortType(self):
		return self.sortType

	def setSelectionEnabled(self, enabled):
		self.instance.setSelectionEnable(enabled)		

	def setList(self):
		self.l.setList(self.list)
		
	def buildEntry(self, filename, path, pathFilename=None, isDir=False, isMovie=False, mediaType=None):
		png = None
		fileSize = ""
		fileAttrib = ""
		lastModified = ""
		realPath = ""

		res = []


		# info
		if not isDir:
			if self.showFiles:
				fileInfo = os_lstat(pathFilename)
				fileAttrib = oct(stat_stat.S_IMODE(fileInfo.st_mode))
				lastModified = strftime("%d.%m.%Y %H:%M:%S",localtime(fileInfo.st_mtime))
				fileSize = prettySize(getSize(pathFilename))
				isLink = stat_stat.S_ISLNK(fileInfo.st_mode)
				
				if os_path.islink(pathFilename):
					realPath = " >> %s" % (os_path.realpath(pathFilename))
		elif path is not None and filename not in ('<%s>' % (_("List of Storage Devices")), '<%s>' % (_("Parent Directory"))):
			try:
				fileInfo = os_lstat(path)
				fileAttrib = oct(stat_stat.S_IMODE(fileInfo.st_mode))
				if os_path.islink(path[:-1]):
					realPath = " >> %s" % (os_path.realpath(path[:-1]))
			except OSError:
				print("OSError occured")

		# icons
		if isDir:
			png = LoadPixmap(cached=True, path="%s/dir.png" % (self.iconSet))
		else:
			extension = filename.split('.')
			extension = extension[-1].lower()
			if EXTENSIONS.has_key(extension):
				png = LoadPixmap("%s/%s.png" % (self.iconSet, EXTENSIONS[extension]))
			elif isMovie:
				png = LoadPixmap("%s/movie.png" % (self.iconSet))

		
		if self.showDetails:
			res.extend((filename, path, pathFilename, isDir, isMovie, mediaType, png, fileSize, lastModified, fileAttrib, realPath))
		else:
			res.extend((filename, path, pathFilename, isDir, isMovie, mediaType, png))
		
		return res

	def down(self):
		self.instance.moveSelection(self.instance.moveDown)
		
	def up(self):
		self.instance.moveSelection(self.instance.moveUp)
		
	def pageDown(self):
		self.instance.moveSelection(self.instance.pageDown)
		
	def pageUp(self):
		self.instance.moveSelection(self.instance.pageUp)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)
		
	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()
		
	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l

	def getSelection(self):
		if self.l.getCurrentSelection() is None:
			return None
		return self.l.getCurrentSelection()
		
	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)
		instance.setContent(self.l)

	def preWidgetRemove(self, instance):
		self.selectionChanged_conn = None
		instance.setContent(None)

	def __len__(self):
		return len(self.list)

	def changeDirectory(self, directory, select=None):
		self.list = []
		
		# if we are just entering from the list of mount points:		
		if self.current_directory is None:
			if directory and self.showMountpoints:
				self.current_mountpoint = self.getMountpointLink(directory)
			else:
				self.current_mountpoint = None
		self.current_directory = directory
		directories = []
		files = []
		
		if directory is None and self.showMountpoints: # present available mountpoints
			for p in harddiskmanager.getMountedPartitions():
				path = os_path.join(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append((p.description, path, None, True, False, None)) 
			files = []
			directories = []
		elif directory is None:
			files = []
			directories = []
		else:
			if os_path.exists(directory):
				try:
					files = listdir(directory)
				except:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if os_path.isdir(directory + x):
						directories.append(directory + x + "/")
						files.remove(x)
		
		if directory is not None and self.showDirectories and not self.isTop:
			if directory == self.current_mountpoint and self.showMountpoints:
				self.list.append(("<%s>" % (_("List of Storage Devices")), None, None, True, False, None))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(("<%s>" % (_("Parent Directory")), '/'.join(directory.split('/')[:-2]) + '/', None, True, False, None))
				
		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					self.list.append((name, x, None, True, False, None))
		if self.showFiles:
			for x in files:
				path = directory + x
				name = x
				
				if (self.matchingPattern is None) or re_compile(self.matchingPattern).search(path):
					nx = None
					if (config.plugins.DreamExplorer.useMediaFilter.value == "on"):
						nx = self.getTSInfo(path)
						if nx is not None:
							name = nx

					extension = None
					extensionPos = name.rfind('.')
					if extensionPos != -1:
						extension = name[extensionPos + 1:].lower()
					mediaType = EXTENSIONS.get(extension)					
					if nx is None:
						fileInfo = os_lstat(path)
						lastModified = strftime("%d.%m.%Y %H:%M:%S",localtime(fileInfo.st_mtime))
						self.list.append((name, directory, path, False, False, mediaType))
					else:
						extname = name + " [" + self.getTSLength(path) + "]"
						self.list.append((extname, directory, path, False, True, mediaType))
						
		# let's sort the list to retain the last selection after directory change
		self.sortList()
				
		self.l.setList(self.list)
		
		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[1]
				
				if isinstance(p, eServiceReference):
					p = p.getPath()
					
				if p == select:
					self.moveToIndex(i)
					break
				i += 1

	def execBegin(self):
		harddiskmanager.on_partition_list_change.append(self.partitionListChanged)

	def execEnd(self):
		harddiskmanager.on_partition_list_change.remove(self.partitionListChanged)

	def partitionListChanged(self, action, device):
		self.refreshMountpoints()
		if self.current_directory is None:
			self.refresh()

	### file list ###
	def refresh(self, currentDir=None):
		self.changeDirectory(self.current_directory, self.getFilename())
		self.l.setList(self.list)

	def getFileList(self):
		return self.list
		
	def getFilteredFileList(self, mediaType, fileNameOnly=False):
		if fileNameOnly:
			return [x[0] for x in self.list if x[5] == mediaType]
		return [x for x in self.list if x[5] == mediaType]	

	def isSymLink(self):
		if self.getSelection() is None:
			return False
		if self.showDetails:
			if len(self.getSelection()) > 10:
				if self.getSelection()[10] != "":
					return True
		return False
	
	### filename ###

	def getFilename(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			x = x.getPath()
		return x

	def getFilenameWithPath(self):
		return self.l.getCurrentSelection()[2]

	def getFileExtensionType(self):
		fileExtension = self.getFileExtension()
		
		return EXTENSIONS.get(fileExtension)

	def getFileExtension(self):
		cur = self.getSelection()
		if cur is not None:
			filenameSplitList = cur[0].split('.')
			if len(filenameSplitList) > 1:
				return filenameSplitList[-1].lower()
		return None

	def getPathForFile(self):
		if self.l.getCurrentSelection() is not None:
			return self.l.getCurrentSelection()[1]
		return ""

	def getServiceRef(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()
		if isinstance(x, eServiceReference):
			return x
		return None

	def getServiceRefForPath(self, path):
		return eServiceReference("1:0:0:0:0:0:0:0:0:0:" + path)

	### directories ###

	def getCurrentDirectory(self):
		return self.current_directory

	def canDescent(self):
		if self.getSelection() is None:
			return False
		return self.getSelection()[3]

	def descent(self):
		if self.getSelection() is None:
			return

		self.changeDirectory(self.getSelection()[1], select=self.current_directory)

	def inParentDirs(self, dir, parents):
		dir = os_path.realpath(dir)
		for p in parents:
			if dir.startswith(p):
				return True
		return False

	### mount points ###

	def refreshMountpoints(self):
		self.mountpoints = [os_path.join(p.mountpoint, "") for p in harddiskmanager.getMountedPartitions()]
		self.mountpoints.sort(reverse=True)

	def getMountpoint(self, file):
		file = os_path.join(os_path.realpath(file), "")
		for m in self.mountpoints:
			if file.startswith(m):
				return m
		return False

	def getMountpointLink(self, file):
		if os_path.realpath(file) == file:
			return self.getMountpoint(file)
		else:
			if file[-1] == "/":
				file = file[:-1]
			mp = self.getMountpoint(file)
			last = file
			file = os_path.dirname(file)
			while last != "/" and mp == self.getMountpoint(file):
				last = file
				file = os_path.dirname(file)
			return os_path.join(last, "")

	### TS ###

	def getTSEvent(self, path=None):
		if path is None:
			path = self.getFilenameWithPath()
		if path.endswith(".ts"):
			serviceref = self.getServiceRefForPath(path)
			if not serviceref.valid():
				return None, serviceref
			info = self.serviceHandler.info(serviceref)
			if info is not None:			
				return (info.getEvent(serviceref), serviceref)
		return None, None
	
	def getTSInfo(self, path=None):
		if path is None:
			path = self.getFilenameWithPath()	
		if path.endswith(".ts"):
			serviceref = self.getServiceRefForPath(path)
			if not serviceref.valid():
				return None
			info = self.serviceHandler.info(serviceref)
			if info is not None:
				txt = info.getName(serviceref)
				description = info.getInfoString(serviceref, iServiceInformation.sDescription)
				if not txt.endswith(".ts"):
					if description is not "":
						return txt + ' - ' + description
					else:
						return txt
				else:
					evt = info.getEvent(serviceref)
					if evt:
						return evt.getEventName() + ' - ' + evt.getShortDescription()
					else:
						return None

	def getTSLength(self, path=None):
		if path is None:
			path = self.getFilenameWithPath()
		tslen = ""
		if path.endswith(".ts"):
			serviceref = self.getServiceRefForPath(path)
			info = self.serviceHandler.info(serviceref)
			tslen = info.getLength(serviceref)
			if tslen > 0:
				tslen = "%d:%02d" % (tslen / 60, tslen % 60)
			else:
				tslen = ""
		return tslen

	### sort ###
	def byNameFunc(self, a, b):
		if self.sortType == self.SORT_NAME_DESC:
			return cmp(b[3], a[3]) or cmp(b[0], a[0])
		else:
			return cmp(b[3], a[3]) or cmp(a[0], b[0])

	def byDateFunc(self, a, b):
		try:
			stat1 = os_lstat(self.current_directory + a[0])
			stat2 = os_lstat(self.current_directory + b[0])
		except:
			return 0

		if self.sortType == self.SORT_DATE_DESC:
			return cmp(b[3], a[3]) or cmp(stat2.st_ctime, stat1.st_ctime)
		else:
			return cmp(b[3], a[3]) or cmp(stat1.st_ctime, stat2.st_ctime)
		
	def sortList(self):
		if self.getSortType() in (self.SORT_NAME_ASC, self.SORT_NAME_DESC):
			self.list.sort(self.byNameFunc)
		else:
			self.list.sort(self.byDateFunc)

		for i in range(len(self.list)):
			if self.list[i][0] == "<%s>" % (_("Parent Directory")) or self.list[i][0] == "<%s>" % (_("List of Storage Devices")):
				entry = self.list.pop(i)
				self.list.insert(0, entry)
				break

	### move by char ###
			
	def moveToChar(self, char):
		index = self.getFirstMatchingEntry(char)
		self.instance.moveSelectionTo(index)

	def getFirstMatchingEntry(self, char):
		for i in range(len(self.list)):
			if self.list[i][0].upper().startswith(char):
				return i
		return 0
