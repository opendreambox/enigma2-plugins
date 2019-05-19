#######################################################################
#
#    Vali's File-List with some extendet functions
#    based on FileList(Enigma-2)
#
#    Coded by Vali (c)2009-2011
#    New version by dre (c) 2016
#    Main idea and getTSLength/getTSInfo/Sort functions by DarkVolli
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

from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, eServiceReference, eServiceCenter, gFont, iServiceInformation
from skin import componentSizes, TemplatedListFonts
from Components.Harddisk import harddiskmanager
from Components.MenuList import MenuList
from Tools.LoadPixmap import LoadPixmap

from re import compile as re_compile
from os import path as os_path, listdir, stat as os_stat

from Components.config import config


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
		"ipk": "package",
		"gz": "package",
		"bz2": "package",
		"sh": "script"
	}

def FileEntryComponent(name, absolute = None, isDir = False, isMovie=False):
	sizes = componentSizes[componentSizes.FILE_LIST]
	tx = sizes.get("textX", 35)
	ty = sizes.get("textY", 0)
	tw = sizes.get("textWidth", 1000)
	th = sizes.get("textHeight", 25)
	pxw = sizes.get("pixmapWidth", 20)
	pxh = sizes.get("pixmapHeight", 20)
	
	res = [ (absolute, isDir) ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, tx, ty, tw, th, 0, RT_HALIGN_LEFT, name))
	if isDir:
		png = LoadPixmap(cached=True, path="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/dir.png")
	else:
		extension = name.split('.')
		extension = extension[-1].lower()
		if extension in EXTENSIONS:
			png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/" + EXTENSIONS[extension] + ".png")
		elif isMovie:
			png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/movie.png")
		else:
			png = None
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 10, (th-pxh)/2, pxw, pxh, png))
		
	return res

class FileList(MenuList):
	def __init__(self, directory, showDirectories = True, showFiles = True, showMountpoints = True, matchingPattern = None, useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = True, additionalExtensions = None):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.additional_extensions = additionalExtensions
		self.mountpoints = []
		self.current_directory = None
		self.current_mountpoint = None
		self.useServiceRef = useServiceRef
		self.showDirectories = showDirectories
		self.showMountpoints = showMountpoints
		self.showFiles = showFiles
		self.isTop = isTop
		# example: matching .nfi and .ts files: "^.*\.(nfi|ts)"		
		self.matchingPattern = matchingPattern
		self.inhibitDirs = inhibitDirs or []
		self.inhibitMounts = inhibitMounts or []
		
		self.refreshMountpoints()
		self.changeDir(directory)
		
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		itemHeight = componentSizes.itemHeight(componentSizes.FILE_LIST, 25)
		self.l.setItemHeight(itemHeight)
		self.serviceHandler = eServiceCenter.getInstance()

	def refreshMountpoints(self):
		self.mountpoints = [os_path.join(p.mountpoint, "") for p in harddiskmanager.getMountedPartitions()]
		self.mountpoints.sort(reverse = True)

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

	def getSelection(self):
		if self.l.getCurrentSelection() is None:
			return None
		return self.l.getCurrentSelection()[0]

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		if not l or l[0][1] == True:
			return None
		else:
			return self.serviceHandler.info(l[0][0]).getEvent(l[0][0])

	def getFileList(self):
		return self.list

	def inParentDirs(self, dir, parents):
		dir = os_path.realpath(dir)
		for p in parents:
			if dir.startswith(p):
				return True
		return False

	def changeDir(self, directory, select = None):
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
					self.list.append(FileEntryComponent(name = p.description, absolute = path, isDir = True))
			files = [ ]
			directories = [ ]
		elif directory is None:
			files = [ ]
			directories = [ ]
		elif self.useServiceRef:
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			list = serviceHandler.list(root)
			
			while 1:
				s = list.getNext()
				if not s.valid():
					del list
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
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
				self.list.append(FileEntryComponent(name = "<" +_("List of Storage Devices") + ">", absolute = None, isDir = True))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(directory.split('/')[:-2]) + '/', isDir = True))
				
		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					self.list.append(FileEntryComponent(name = name, absolute = x, isDir = True))
					
		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = directory + x
					name = x
				
				if (self.matchingPattern is None) or re_compile(self.matchingPattern).search(path):
					nx = None
					if (config.plugins.DreamExplorer.useMediaFilter.value == "on"):
						nx = self.getTSInfo(path)
						if nx is not None:
							name = nx
					
					if nx is None:
						self.list.append(FileEntryComponent(name = name, absolute = x , isDir = False))
					else:
						extname = name + " [" + self.getTSLength(path) + "]"
						self.list.append(FileEntryComponent(name = extname, absolute = x, isDir = False, isMovie=True)) 
						
		self.l.setList(self.list)
		
		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[0][0]
				
				if isinstance(p, eServiceReference):
					p = p.getPath()
					
				if p == select:
					self.moveToIndex(i)
				i += 1

	def getCurrentDirectory(self):
		return self.current_directory

	def canDescent(self):
		if self.getSelection() is None:
			return False
		return self.getSelection()[1]

	def descent(self):
		if self.getSelection() is None:
			return
		self.changeDir(self.getSelection()[0], select = self.current_directory)

	def getFilename(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			x = x.getPath()
		return x

	def getServiceRef(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			return x
		return None

	def execBegin(self):
		harddiskmanager.on_partition_list_change.append(self.partitionListChanged)

	def execEnd(self):
		harddiskmanager.on_partition_list_change.remove(self.partitionListChanged)

	def refresh(self):
		self.changeDir(self.current_directory, self.getFilename())

	def partitionListChanged(self, action, device):
		self.refreshMountpoints()
		if self.current_directory is None:
			self.refresh()
	
	def getTSInfo(self, path):
		if path.endswith(".ts"):
			serviceref = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + path)
			if not serviceref.valid():
				return None
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(serviceref)
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

	def getTSLength(self, path):
		tslen = ""
		if path.endswith(".ts"):
			serviceref = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + path)
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(serviceref)
			tslen = info.getLength(serviceref)
			if tslen > 0:
				tslen = "%d:%02d" % (tslen / 60, tslen % 60)
			else:
				tslen = ""
		return tslen

	def byNameFunc(self, a, b):
		return cmp(b[0][1], a[0][1]) or cmp(a[1][7], b[1][7])

	def sortName(self):
		self.list.sort(self.byNameFunc)
		#self.l.invalidate()
		self.l.setList(self.list)
		self.moveToIndex(0)

	def byDateFunc(self, a, b):
		try:
			stat1 = os_stat(self.current_directory + a[0][0])
			stat2 = os_stat(self.current_directory + b[0][0])
		except:
			return 0
		return cmp(b[0][1], a[0][1]) or cmp(stat2.st_ctime, stat1.st_ctime)

	def sortDate(self):
		self.list.sort(self.byDateFunc)
		#self.l.invalidate()
		self.l.setList(self.list)
		self.moveToIndex(0)

