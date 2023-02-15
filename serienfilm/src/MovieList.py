# -*- coding: utf-8 -*-

from enigma import eEnv, eListbox, iServiceInformation, eServiceReference, eServiceCenter, eSize, getDesktop
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.TemplatedMultiContentComponent import TemplatedMultiContentComponent
from Components.UsageConfig import defaultMoviePath
from ServiceReference import ServiceReference
from Tools.Directories import fileExists
from Tools.FuzzyDate import FuzzyTime
from Tools.LoadPixmap import LoadPixmap

from skin import loadPixmap as skinLoadPixmap

from glob import glob
import os.path


class SfItemIter(object):
	def __init__(self, sfitem):
		self._item = sfitem
		self.index = 0

	def __next__(self):
		if self.index == 8:
			raise StopIteration
		self.index += 1
		return self._item.list[self.index - 1]

class SfItem(object):
	def __init__(self, entryType, pixmap, sfindex, title, description, service, duration=-1):
		self.type = entryType
		self.pixmap = pixmap
		self.sfindex = sfindex if sfindex else ""
		self.title = title
		self.description = description
		self.service = service
		self.duration = duration

	def getList(self):
		return [self.type, self.pixmap, self.sfindex, self.title, self.description, self.service, self.duration]

	def __iter__(self):
		return SfItemIter(self)

	# required for eListboxPythonMultiContent which uses PySequence_Fast
	def __getitem__(self, index):
		return self.list[index]

	# required for eListboxPythonMultiContent which uses PySequence_Size / PySequence_Length
	def __len__(self):
		return len(self.list)

	list = property(getList)


class SfMovieList(TemplatedMultiContentComponent):
	COMPONENT_ID = "SfMovieList"

	SORT_ALPHANUMERIC = 1
	SORT_RECORDED = 2

	LISTTYPE_FULL = 1 << 0
	LISTTYPE_COMPACT = 1 << 1
	LISTTYPE_COMPACT_SERVICE = 1 << 2
	LISTTYPE_COMPACT_TAGS = 1 << 3
	LISTTYPE_MINIMAL = 1 << 4

	LIST_TEMPLATES = {
		LISTTYPE_FULL		: "default",
		LISTTYPE_MINIMAL	: "minimal",
	}

	HIDE_DESCRIPTION = 1
	SHOW_DESCRIPTION = 2

	SHOW_NO_TIMES = 0
	SHOW_RECORDINGTIME = 1
	SHOW_DURATION = 2
	SHOW_DIRECTORIES = 4

	# sfitem types:
	REAL_DIR = 1
	REAL_UP = 2
	VIRT_DIR = 4
	VIRT_UP = 8
	VIRT_ENTRY = (VIRT_DIR | VIRT_UP)

	MAXTIME = 0x7fffffff

	gsflists = []

	default_template_720 = 	"""{ "templates" :
			{
				"default": (75, [
							MultiContentEntryPixmapAlphaTest(pos=(5,5), size=(65,65), png=0),
							MultiContentEntryText(pos=(5,5), size=(65,65), font=0, flags=RT_HALIGN_LEFT, text=1),
							MultiContentEntryText(pos=(75,0), size=(width,30), font=0, flags=RT_HALIGN_LEFT, text=2),
							MultiContentEntryText(pos=(75,30), size=(width,20), font=2, flags=RT_HALIGN_LEFT, text=3,color=0xa0a0a0),
							MultiContentEntryText(pos=(75,50), size=(150,20), font=1, flags=RT_HALIGN_LEFT, text=4,color=0xa0a0a0),
							MultiContentEntryText(pos=(250,50), size=(180,20), font=1, flags=RT_HALIGN_RIGHT, text=5,color=0xa0a0a0),
							MultiContentEntryText(pos=(width-250,50), size=(180,20), font=1, flags=RT_HALIGN_RIGHT, text=6,color=0xa0a0a0),
							MultiContentEntryText(pos=(width-60,50), size=(60,20), font=1, flags=RT_HALIGN_RIGHT, text=7,color=0xa0a0a0)
						]),
				"compact": (40, [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), size=(40,40), png=0),
							MultiContentEntryText(pos=(0,0), size=(40,40), font=0, flags=RT_HALIGN_LEFT, text=1),
							MultiContentEntryText(pos=(45,0), size=(90,20), font=1, flags=RT_HALIGN_LEFT, text=2),
							MultiContentEntryText(pos=(145,0), size=(width-160,20), font=1, flags=RT_HALIGN_LEFT, text=3),
							MultiContentEntryText(pos=(45, 20), size=((width-45)/2,20), font=2, flags=RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, text=4,color=0xa0a0a0),
							MultiContentEntryText(pos=(45+(width-45)/2, 20), size=((width-40)/2,20), font=2, flags=RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM, text=5,color=0xa0a0a0),
							MultiContentEntryText(pos=(width-60, 0), size=(60,20), font=1, flags=RT_HALIGN_RIGHT, text=6)
						]),
				"minimal": (25, [
							MultiContentEntryPixmapAlphaTest(pos=(0,0), size=(25,25), png=0),
							MultiContentEntryText(pos=(0, 0), size=(25, 25), font=0, flags=RT_HALIGN_LEFT, text=1),
							MultiContentEntryText(pos=(25, 0), size=(110, 25), font=0, flags=RT_HALIGN_RIGHT, text=2),
							MultiContentEntryText(pos=(140, 0), size=(width-185, 25), font=0, flags=RT_HALIGN_LEFT, text=3),
							MultiContentEntryText(pos=(width-60, 0), size=(60, 25), font=0, flags=RT_HALIGN_RIGHT, text=4)
						])
			},
			"fonts" : [gFont("Regular", 22), gFont("Regular", 18), gFont("Regular", 14)]
		}"""

	default_template_1080 = """{ "templates" :
			{
				"default": (100, [
					MultiContentEntryPixmapAlphaTest(pos=(5,5), size=(90,90), png=0),
					MultiContentEntryText(pos=(5,5), size=(90,90), font=0, flags=RT_HALIGN_LEFT, text=1),
					MultiContentEntryText(pos=(100,0), size=(width,35), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_TOP, text=2),
					MultiContentEntryText(pos=(100,35), size=(width,28), font=2, flags=RT_HALIGN_LEFT, text=3,color=0xa0a0a0),
					MultiContentEntryText(pos=(100,65), size=(200,30), font=2, flags=RT_HALIGN_LEFT, text=4,color=0xa0a0a0),
					MultiContentEntryText(pos=(300,65), size=(180,30), font=1, flags=RT_HALIGN_RIGHT, text=5,color=0xa0a0a0),
					MultiContentEntryText(pos=(width-300,65), size=(300,30), font=1, flags=RT_HALIGN_RIGHT, text=6,color=0xa0a0a0),
					MultiContentEntryText(pos=(width-120,65), size=(120,30), font=1, flags=RT_HALIGN_RIGHT, text=7,color=0xa0a0a0)
				]),
				"compact": (80, [
					MultiContentEntryPixmapAlphaTest(pos=(5,5), size=(70,70), png=0),
					MultiContentEntryText(pos=(5,5), size=(70,70), font=0, flags=RT_HALIGN_LEFT, text=1),
					MultiContentEntryText(pos=(80,5), size=(140,35), font=1, flags=RT_HALIGN_LEFT, text=2),
					MultiContentEntryText(pos=(230,5), size=(width-360,35), font=1, flags=RT_HALIGN_LEFT, text=3),
					MultiContentEntryText(pos=(80,40), size=((width-80)/2,35), font=1, flags=RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, text=4, color=0xa0a0a0),
					MultiContentEntryText(pos=(width-(width-80)/2, 40), size=((width-80)/2,35), font=1, flags=RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM, text=5, color=0xa0a0a0),
					MultiContentEntryText(pos=(width-120, 5), size=(120,35), font=1, flags=RT_HALIGN_RIGHT, text=6)
				]),
				"minimal": (40, [
					MultiContentEntryPixmapAlphaTest(pos=(0,0), size=(40,40), png=0),
					MultiContentEntryText(pos=(0, 0), size=(40,40), font=1, flags=RT_HALIGN_LEFT, text=1),
					MultiContentEntryText(pos=(40, 3), size=(150, 34), font=1, flags=RT_HALIGN_RIGHT, text=2),
					MultiContentEntryText(pos=(210, 3), size=(width-340, 34), font=1, flags=RT_HALIGN_LEFT, text=3),
					MultiContentEntryText(pos=(width-120, 3), size=(120, 34), font=1, flags=RT_HALIGN_RIGHT, text=4)
				])
			},
			"fonts" : [gFont("Regular", 30), gFont("Regular", 28), gFont("Regular", 26)]
		}"""

	default_template = default_template_720 if getDesktop(0).size().height() == 720 else default_template_1080

	def __init__(self, root, list_type=None, sort_type=None, show_times=None, sftitle_episode_separator = None, MovieSelectionSelf = None):
		TemplatedMultiContentComponent.__init__(self)
#		print "[SF-Plugin] class SF:MovieList init, lstt=%x, srt=%x, sht=%s, sft=>%s<, root=%s" % ( list_type, sort_type, show_times, str(sftitle_episode_separator), str(root))
		self.show_times = show_times or self.SHOW_DURATION | self.SHOW_DIRECTORIES
		self.sort_type = sort_type or self.SORT_RECORDED
		self.sftitle_episode_separator = sftitle_episode_separator

		self.tags = set()
		self.list = None
		self.sflists = None
		self.MovieSelectionSelf = MovieSelectionSelf
		self.MselTitle = ""

		self.l.setBuildFunc(self.buildMovieListEntry)
		self.setListType(list_type or self.LISTTYPE_MINIMAL)
		if root is not None:
			self.reload(root)

		self._realFolderPixmap = LoadPixmap(cached=True, path=eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/SerienFilm/icons/folder.svg'))
		self._virtualFolderPixmap = LoadPixmap(cached=True, path=eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/SerienFilm/icons/folder_virtual.svg'))
		self._folderUpPixmap = LoadPixmap(cached=True, path=eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/SerienFilm/icons/folder_up.svg'))

		self.onSelectionChanged = [ ]

	def _loadPixmap(self, desktop, skinValue):
		value = skinValue.split(",")
		if len(value) == 3:
			path, width, height = value
			self._virtualFolderPixmap = skinLoadPixmap(path, desktop, eSize(int(width), int(height)))
		else:
			self._virtualFolderPixmap = skinLoadPixmap(path, desktop)

	def applySkin(self, desktop, parent):
		GUIComponent.applySkin(self, desktop, parent)
		if self.skinAttributes:
			for (attrib, value) in self.skinAttributes:
				if attrib == "sfPixmapFolder":
					self._realFolderPixmap = self._loadPixmap(value, desktop)
				elif attrib == "sfPixmapVirtualFolder":
					self._virtualFolderPixmap = self._loadPixmap(value, desktop)
				elif attrib == "sfPixmapFolderUp":
					self._folderUpPixmap = self._loadPixmap(value, desktop)
		self.applyTemplate(additional_locals={"width" : self.l.getItemSize().width()-30})

	def redrawList(self):
		self.l.setList(self.list)

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
#			print "[SF-Plugin] MovieList.selectionChanged: " + str(x)
			x()

	def setListType(self, type):
		self.list_type = type
		self.setTemplate(self.LIST_TEMPLATES.get(type, "compact"))
		self.redrawList()

	def setShowTimes(self, val):
		self.show_times = val

	def setSortType(self, type):
		self.sort_type = type

	def setTitleEpiSep(self, sftitle_episode_separator):
		self.sftitle_episode_separator = sftitle_episode_separator

	#
	# | name of movie              |
	#
	def buildMovieListEntry(self, serviceref, info, begin, sfitem):
		duration = sfitem.duration
		if sfitem.duration <= 0 and config.usage.load_length_of_movies_in_moviellist.value: #recalc len when not already done
			cur_idx = self.l.getCurrentSelectionIndex()
			x = self.list[cur_idx]
			duration = x[1].getLength(x[0]) #recalc the movie length...
			self.list[cur_idx][3].duration = duration	#update entry in list... so next time we don't need to recalc

		if duration > 0:
			duration = "%d:%02d" % (duration / 60, duration % 60)
		else:
			duration = ""

		res = [sfitem.pixmap, sfitem.sfindex]
		begin_string = ""
		date_string = ""

		if not sfitem.type & (self.VIRT_UP | self.REAL_UP):
			if begin > 0:
				t = FuzzyTime(begin)
				begin_string = ", ".join(t)
				date_string = t[0]
		tags = info.getInfoString(serviceref, iServiceInformation.sTags)

		service = "" if sfitem.service.startswith("SFLIDX") else sfitem.service
		if self.list_type & SfMovieList.LISTTYPE_FULL:
			res.extend([sfitem.title, sfitem.description, begin_string, service, tags, duration])
		elif self.list_type == SfMovieList.LISTTYPE_COMPACT_SERVICE:
			res.extend([date_string, sfitem.title, service, sfitem.description, duration])
		elif self.list_type == SfMovieList.LISTTYPE_COMPACT_TAGS:
			res.extend([date_string, sfitem.title, tags, sfitem.description, duration])
		else:
			res.extend([date_string, sfitem.title, duration])

		return res

	def moveToIndex(self, index):
		if index <0:
			index += len(self.list)			# standard python list behaviour
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return l and l[0] and l[1] and l[1].getEvent(l[0])

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		self.selectionChanged_conn = instance.selectionChanged.connect(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		self.selectionChanged_conn = None

	def reload(self, root = None, filter_tags = None):
		if root is not None:
			self.load(root, filter_tags)
		else:
			self.load(self.root, filter_tags)
		self.l.setList(self.list)

	def removeService(self, service):
		for l in self.list[:]:
			repnr = sfitem = None
			if l[0] == service:
				sfitem = l[3]
				if not service.flags & eServiceReference.canDescent and sfitem.sfindex and sfitem.sfindex[0] == "#":
					repnr = int(sfitem.sfindex[1:])
				self.list.remove(l)
				break
		self.l.setList(self.list)
		if len(self.list) == 1 and self.list[0][3].type & self.VIRT_UP:	# last movie of a series is gone
			service = self.list[0][0]
			self.moveTo(service, True)
			assert service.flags == eServiceReference.canDescent
			self.removeService(service)
			return
		if repnr is None:
			return
		repeats = 0		# update repeatcount "#x" of surviving movies
		ele0 = 0
#		print "[SF-Plugin] removeService: searching " + sfitem[2]
		for i in range(1, len(self.list)):
			m = self.list[i]
			t = m[3]
#			print "[SF-Plugin] removeService try: %x, %s -- %s" % (m[0].flags,  str(t[1]), str(t[2]))
			if not m[0].flags & eServiceReference.canDescent and t.title == sfitem.title and t.sfindex and t.sfindex[0] == "#":
				repeats += 1
				rc = int(t.sfindex[1:])
				if rc > repnr:
					rc -= 1
					t.sfindex = "#" + str(rc)
#					print "[SF-Plugin] removeService: %s --> %s" % (t[2], t[1])
				if rc == 0:
					ele0 = i
		if ele0 > 0 and repeats == 1:
			self.list[ele0][3].sfindex = None	# remove "#0" from only lonely surviving movie
#			print "[SF-Plugin] removeService: remove #0 from " + self.list[ele0][3].title


	def __len__(self):
		return len(self.list)


	def playDirectory(self, serviceref):
		if serviceref.type == (eServiceReference.idUser | eServiceReference.idDVB) and serviceref.flags == eServiceReference.canDescent:
			self.moveTo(serviceref)		# virtual Directory
			return ""
		if serviceref.flags & eServiceReference.mustDescent:
			info = self.serviceHandler.info(serviceref)
			if info is None:
				name = ""
			else:
				name = info.getName(serviceref)
#			print "[SF-Plugin] MovieList.playDirectory: %s nicht spielbar" ,(name)
			return name

	def realDirUp(self, root):
		parent = None
		info = self.serviceHandler.info(root)
		pwd = info and info.getName(root)
		defM = defaultMoviePath()
		print "[SF-Plugin] MovieList.realDirUp: pwd = >%s<" % (str(pwd))
		if pwd and os.path.exists(pwd) and os.path.exists(defM) and not os.path.samefile(pwd, defM):
			parentdir = pwd[:pwd.rfind("/", 0, -1)] + "/"
			parent = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + parentdir)
			info = self.serviceHandler.info(parent)
			if info is not None:
				txt = info.getName(parent)																# Titel
				service = ServiceReference(info.getInfoString(parent, iServiceInformation.sServiceref)).getServiceName()	# Sender
				description = info.getInfoString(parent, iServiceInformation.sDescription)				# Beschreibung
#				begin = info.getInfo(root, iServiceInformation.sTimeCreate)
				begin = self.MAXTIME
				parent.flags=eServiceReference.flagDirectory | eServiceReference.sort1
				sfitem = SfItem(self.REAL_DIR | self.REAL_UP, self._folderUpPixmap, "", "  0", txt, service, 1)	# "  0" sorts before VIRT_UP
				return ((parent, info, begin, sfitem))



	def load(self, root, filter_tags):
		# this lists our root service, then building a 
		# nice list

		self.serviceHandler = eServiceCenter.getInstance()
		parentLstEntry = self.realDirUp(root)

		self.rootlst = [ ]

		self.root = root
		list = self.serviceHandler.list(root)
		if list is None:
			print "[SF-Plugin] listing of movies failed"
			list = [ ]	
			return
		tags = set()

		rootinfo = self.serviceHandler.info(root)
		pwd = rootinfo and rootinfo.getName(root)

		while 1:
			serviceref = list.getNext()
			if not serviceref.valid():
				break
			pixmap = None
			entryType = 0
			if serviceref.flags & eServiceReference.mustDescent:
				if not self.show_times & self.SHOW_DIRECTORIES:
					continue				# hide Directories
				entryType = self.REAL_DIR		# show Directories
				pixmap = self._realFolderPixmap

			info = self.serviceHandler.info(serviceref)
			if info is None:
				continue
			title = info.getName(serviceref)
			if serviceref.flags & eServiceReference.mustDescent:
				files = [ f for f in glob(os.path.join(title, "*")) if fileExists(f) ]
				# skip empty directories
				if not files:
					continue
				# use mtime of latest recording
				begin = sorted((os.path.getmtime(x) for x in files))[-1]
				if pwd and title.startswith(pwd):
					title = title[len(pwd):]
				if title.endswith(os.path.sep):
					title = title[:-len(os.path.sep)]
			else:
				begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)
			this_tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')

			# convert space-seperated list of tags into a set
			if this_tags == ['']:
				this_tags = []
			this_tags = set(this_tags)
			tags |= this_tags

			# filter_tags is either None (which means no filter at all), or 
			# a set. In this case, all elements of filter_tags must be present,
			# otherwise the entry will be dropped.			
			if filter_tags is not None and not this_tags.issuperset(filter_tags):
				continue

			service = ServiceReference(info.getInfoString(serviceref, iServiceInformation.sServiceref)).getServiceName()	# Sender
			description = info.getInfoString(serviceref, iServiceInformation.sDescription)
			sfindex = ""
			sfItem = SfItem(entryType, pixmap, sfindex, title, description, service, -1)

			self.rootlst.append((serviceref, info, begin, sfItem))

		self.rootlst.sort(key=lambda x: -x[2])						# movies of same name stay sortet by time
		self.rootlst.sort(key=lambda x: (x[3].title+x[3].description).lower())
		self.list = self.rootlst
		self.createSublists()


		if self.sort_type == self.SORT_RECORDED:
			self.sortLists()

		# finally, store a list of all tags which were found. these can be presented
		# to the user to filter the list
		self.tags = tags
		if parentLstEntry:
#			print "[SF-Plugin] SF:MovieList.load: parentLstEntry %s" % (self.debPrtEref(parentLstEntry[0]))
			self.list.insert(0, parentLstEntry)

	def moveTo(self, serviceref, descend_virtdirs=True, search_all_lists=True):
		count = 0
		for x in self.list:
			if x[0] == serviceref:

				if descend_virtdirs:
					l = self.list[count]
					sfitem = l[3]
					if sfitem.type & self.VIRT_ENTRY:
						assert sfitem.service[:6] == "SFLIDX"
						self.list = self.sflists[int(sfitem.service[6:])]
						self.l.setList(self.list)
						self.MovieSelectionSelf.setTitle(self.MselTitle)
					if sfitem.type & self.VIRT_DIR:
						count = 0							# select VIRT_UP in sublist
						self.MovieSelectionSelf.setTitle("%s: %s" % (_("Series"), sfitem.title))
					elif sfitem.type & self.VIRT_UP:
						rv = self.moveTo(serviceref, False)
						return rv

				self.instance.moveSelectionTo(count)
				return True
			count += 1
	# InfoBar:leavePlayerConfirmed(movielist) should find movies in virtual directories
		if search_all_lists and descend_virtdirs and self.sflists:
			savelist = self.list
			for l in self.sflists:
				if l == savelist:
					continue
				self.list = l
				self.l.setList(l)
				if self.moveTo(serviceref, descend_virtdirs=True, search_all_lists=False):
					return True
			self.list = savelist
			self.l.setList(self.list)

# enigmas list:		(serviceref, info, begin, len)	# len is replaced by sfitem
# sfitem:			[type, pixmap, txt, description, service, len]

# pixmap:			pixmap (DIR_UP...) or String (#0, #1 ... for multiple recordings)
# SFLIDX0...999		entry# in serlst, 0 == rootlist


	def serflm(self, film, episode):
		fdate = film[2]
		sfitem = film[3]
		dsc = sfitem.description
		service = sfitem.service
		epi = len(episode) == 2 and episode[1]
		if epi:
			txt = ": ".join((epi, dsc))
		else:
			txt = dsc or service
		if self.serdate < fdate:
			self.serdate = fdate
		sfitem.title = txt
		sfitem.description = dsc
		return film

	def update_repcnt(self, serlst, repcnt):
		for i in range(repcnt + 1):
			serlst[-( i+1 )][3].sfindex =  "#" + str(i)

	def createSublists(self):
		self.serdate = 0
		serie = serlst = None
		self.sflists = [self.rootlst]
		txt = ("", "")
		rootlidx = repcnt = 0
		global gsflists
		sflidx = 0
		if self.sftitle_episode_separator:
			splitTitle = lambda s: s.split(self.sftitle_episode_separator, 1)
		else:
			splitTitle = lambda s: [s]
#		print "[SF-Plugin] MovieList.createSublists: self.sftitle_episode_separator = %d = >%s<" % (len(self.sftitle_episode_separator), self.sftitle_episode_separator)
		for item in self.rootlst[:]:
			sfitem = item[3]
			ts = splitTitle(sfitem.title)
			if txt[0] == ts[0]:
				if txt[0] != serie:				# neue Serie
					sflidx += 1
					serie = txt[0]
					ser_serviceref = eServiceReference(eServiceReference.idUser | eServiceReference.idDVB, 
							eServiceReference.canDescent, "SFLIDX" + str(sflidx))
					ser_info = self.serviceHandler.info(ser_serviceref)
					# VIRT_UP should sort first, but after REAL_UP: MAXTIME-1 resp. "  1"
					# [type, pixmap, sfindex, txt, description, service, -1]
					serlst = [(ser_serviceref, ser_info, SfMovieList.MAXTIME-1,
						SfItem(self.VIRT_UP, self._folderUpPixmap, "", "  1", txt[0], "SFLIDX0", 1))]
					self.sflists.append(serlst)
					serlst.append(self.serflm(self.rootlst[rootlidx-1], txt))
					parent_list_index = rootlidx-1
				film = self.rootlst.pop(rootlidx)
				rootlidx -= 1
				film = self.serflm(film, ts)
				samefilm = False
				if serlst:
					if serlst and film[3].description != "" and film[3].title == serlst[-1][3].title:	# perhaps same Movie?
						event1 = film[1].getEvent(film[0])
						event2 = serlst[-1][1].getEvent(serlst[-1][0])
						if event1 and event2 and event1.getExtendedDescription() == event2.getExtendedDescription():
							samefilm = True
					if samefilm:
						repcnt += 1
					elif repcnt:
						self.update_repcnt(serlst, repcnt)
						repcnt = 0
					serlst.append(film)
			elif serlst:
				self.rootlst[parent_list_index] = (ser_serviceref, ser_info, self.serdate, 
					SfItem(self.VIRT_DIR, self._virtualFolderPixmap, "", txt[0], "", "SFLIDX" + str(sflidx), 1))
				self.serdate = 0
				if repcnt:
					self.update_repcnt(serlst, repcnt)
					repcnt = 0
				serlst = None
			rootlidx += 1
			txt = ts
		if serlst:
			self.rootlst[parent_list_index] = (ser_serviceref, ser_info, self.serdate, 
				SfItem(self.VIRT_DIR, self._virtualFolderPixmap, "", txt[0], "", "SFLIDX" + str(sflidx), 1))
			if repcnt:
				self.update_repcnt(serlst, repcnt)
#		print "[SF-Plugin] sflist has %d entries" % (len(self.sflists))
		gsflists = self.sflists

	def sortLists(self):
		if self.sort_type == self.SORT_ALPHANUMERIC:
			key = lambda x: (x[3].title+x[3].description).lower()
		else: key=lambda x: -x[2]
		if self.sflists:
			for list in self.sflists:
				list.sort(key=key)
			return True

	def toggleSort(self):
		save_list = self.list
		current = self.getCurrent()
		self.sort_type ^= (self.SORT_ALPHANUMERIC | self.SORT_RECORDED)
		self.sortLists()
		self.list = save_list
		self.l.setList(self.list)				# redraw
		self.moveTo(current, False)

	def saveTitle(self, title):
		self.MselTitle = title

	def getVirtDirList(self, name):
		return name[:6] == "SFLIDX" and self.sflists[int(name[6:])]

	@staticmethod
	def getVirtDirStatistics(name):
		if name[:6] == "SFLIDX":
			list = gsflists[int(name[6:])]
			repcnt = 0
			for l in list:
				sfitem = l[3]
				if sfitem.sfindex and sfitem.sfindex[0:1] != "#0":
					repcnt += 1
			s = "%d %s" % (len(list)-1, _("Movies"))
			if repcnt:
				s += ", %d %s" % (repcnt, _("duplicated"))
			return s
