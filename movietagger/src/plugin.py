from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MovieList import MovieList
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.MultiContent import MultiContentEntryText
from enigma import eServiceReference, eListboxPythonMultiContent, eServiceCenter, gFont, iServiceInformation, getDesktop, RT_HALIGN_LEFT, RT_VALIGN_CENTER, RT_HALIGN_CENTER
from skin import TemplatedListFonts, componentSizes, parseColor

from Tools.Directories import pathExists, resolveFilename, SCOPE_HDD, SCOPE_PLUGINS

VERSION = "1.4"


class MovieTagger(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		skin = """
			<screen position="center,70" size="600,460" title="Movie Tagger" >
				<widget name="moviename" position="10,0" size="580,60" valign="top" font="Regular;25"/>
				<ePixmap pixmap="skin_default/div-h.png" position="0,62" zPosition="1" size="600,2" />
				<widget name="assignedTags" position="10,65" size="260,30" valign="top" halign="left" zPosition="2" foregroundColor="white" font="Regular;23"/>
				<widget name="cTaglist" position="10,100" size="260,250" scrollbarMode="showOnDemand"/>
				<widget name="definedTags" position="300,65" size="290,30" valign="top" halign="left" zPosition="2" foregroundColor="white" font="Regular;23"/>
				<widget name="aTaglist" position="290,100" size="290,250" scrollbarMode="showOnDemand" />

				<ePixmap pixmap="skin_default/div-h.png" position="0,358" zPosition="1" size="600,2" />
				<widget name="usedTag" position="10,365" size="185,50" valign="top" halign="center" zPosition="2" foregroundColor="#ffff00" font="Regular;21"/>
				<widget name="userTag" position="200,365" size="185,50" valign="top" halign="center" zPosition="2" foregroundColor="#ff0000" font="Regular;21"/>
				<widget name="preTag" position="400,365" size="190,50" valign="top" halign="center" zPosition="2" foregroundColor="#00ff00" font="Regular;21"/>

				<ePixmap pixmap="skin_default/buttons/red.png" position="0,420" zPosition="0" size="140,40" transparent="1" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="155,420" zPosition="0" size="140,40" transparent="1" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,420" zPosition="0" size="140,40" transparent="1" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="455,420" zPosition="0" size="140,40" transparent="1" alphatest="on" />

				<widget name="buttonred" position="0,420" size="140,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;18"/>
				<widget name="buttongreen" position="155,420" size="140,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;18"/>
				<widget name="buttonyellow" position="305,420" size="140,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;18"/>
				<widget name="buttonblue" position="455,420" size="140,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;18"/>
			</screen>"""
	else:
		skin = """
			<screen position="center,70" size="1000,690" title="Movie Tagger" >
				<widget name="moviename" position="10,0" size="980,80" valign="top" font="Regular;30"/>
				<ePixmap pixmap="skin_default/div-h.png" position="0,82" zPosition="1" size="1000,2" />

				<widget name="assignedTags" position="10,90" size="490,30" valign="top" halign="left" zPosition="2" foregroundColor="white" font="Regular;26"/>

				<widget name="cTaglist" position="10,120" size="490,440" scrollbarMode="showOnDemand"/>

				<widget name="definedTags" position="500,90" size="490,30" valign="top" halign="left" zPosition="2" foregroundColor="white" font="Regular;26"/>

				<widget name="aTaglist" position="500,120" size="980,440" scrollbarMode="showOnDemand"/>

				<ePixmap pixmap="skin_default/div-h.png" position="0,578" zPosition="1" size="1000,2" />
				<widget name="usedTag" position="5,600" size="330,50" valign="top" halign="center" zPosition="2" foregroundColor="#ffff00" font="Regular;26"/>
				<widget name="userTag" position="335,600" size="330,50" valign="top" halign="center" zPosition="2" foregroundColor="#ff0000" font="Regular;26"/>
				<widget name="preTag" position="665,600" size="330,50" valign="top" halign="center" zPosition="2" foregroundColor="#00ff00" font="Regular;26"/>

				<ePixmap pixmap="skin_default/buttons/red.png" position="20,650" zPosition="0" size="235,40" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="265,650" zPosition="0" size="235,40" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="510,650" zPosition="0" size="235,40" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="755,650" zPosition="0" size="235,40" transparent="1" alphatest="on" scale="stretch" />

				<widget name="buttonred" position="20,650" size="235,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;24"/>
				<widget name="buttongreen" position="265,650" size="235,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;24"/>
				<widget name="buttonyellow" position="510,650" size="235,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;24"/>
				<widget name="buttonblue" position="755,650" size="235,40" valign="center" halign="center" zPosition="2" foregroundColor="white" transparent="1" font="Regular;24"/>
			</screen>"""

	currList = None

	def __init__(self, session, service):
		self.session = session
		self.service = service
		self.serviceHandler = eServiceCenter.getInstance()
		self.info = self.serviceHandler.info(self.service)

		self.skin = MovieTagger.skin
		Screen.__init__(self, session)
		self["moviename"] = Label(self.info.getName(self.service))
		self["assignedTags"] = Label("AssignedTags")
		self["definedTags"] = Label("DefinedTags")
		self["usedTag"] = Label("UsedTag")
		self["userTag"] = Label("UserTag")
		self["preTag"] = Label("PreTag")
		self["buttonred"] = Label("red")
		self["buttongreen"] = Label("green")
		self["buttonyellow"] = Label("yellow")
		self["buttonblue"] = Label("blue")
		self["cTaglist"] = TagMenuList([])
		self["aTaglist"] = TagMenuList([])
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"],
			{
			"back": self.close,
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
			}, -1)
		self.pretags = self.loadPreTags("/etc/enigma2/movietags") or self.loadPreTags(resolveFilename(SCOPE_PLUGINS, "Extensions/MovieTagger/movietags"))
		self.updateCurrentTagList()
		self.updateAllTagList()
		self.currList = self["aTaglist"]
		self.onLayoutFinish.append(self.keyBlue)

	def loadPreTags(self, filename):
		try:
			with open(filename, "r") as f:
				pretags = sorted(f.read().splitlines())
		except:
			print "pretags file %s does not exist" % filename
			return []
		else:
			print "pretags loaded from %s:" % filename, pretags
			return pretags

	def updateCurrentTagList(self):
		print "updating cTagList"
		self.serviceHandler = eServiceCenter.getInstance()
		self.info = self.serviceHandler.info(self.service)
		self.tags = self.info.getInfoString(self.service, iServiceInformation.sTags).split(' ')
		self.tags.sort()
		currentTagsList = [(x,) for x in self.tags]
		self["cTaglist"].setList(currentTagsList)

	def updateAllTagList(self):
		root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
		ml = MovieList(root)
		ml.load(root, None)
		xtmp = []
		xtmp.extend(ml.tags)
		self.usedTags = xtmp

		e = self.pretags + [x for x in ml.tags if x not in self.pretags]

		taglist = []
		for i in e:
			taglist.append(self.getFlags(i))
		taglist.sort()
		self["aTaglist"].setList(taglist)

	def addTag(self, tagname):
		try:
			self.tags.index(tagname)
		except ValueError:
			self.tags.append(tagname)
			if len(self.tags) > 1:
				self.setTags(" ".join(self.tags))
			else:
				self.setTags(tagname)
		self.updateCurrentTagList()
		self.updateAllTagList()

	def removeTag(self, tagname):
		newtags = []
		for i in self.tags:
			if i is not tagname:
				newtags.append(i)
		self.setTags(" ".join(newtags))
		self.updateCurrentTagList()
		self.updateAllTagList()

	def setTags(self, tagstring, service=False, userNotice=True):
		if service is False:
			serviceRef = self.service
		else:
			serviceRef = service

		service_name = serviceRef.toString().split(":")[-1]
		filename = service_name + ".meta"
		metadata = self.readMETAData(filename)
		if metadata is not False:
			metadata.append(tagstring.strip())
			return self.writeMETAData(filename, metadata)
		else:
			if userNotice is True:
				self.session.open(MessageBox, _("Can't write movietags, because no meta-file found!"), MessageBox.TYPE_ERROR)
			return False

	def readMETAData(self, filename):
		if pathExists(filename):
			fp = open(filename, "r")
			data = []
			data.append(fp.readline())
			data.append(fp.readline())
			data.append(fp.readline())
			data.append(fp.readline())
			fp.close()
			return data
		else:
			return False

	def writeMETAData(self, filename, metadata):
		if pathExists(filename):
			fp = open(filename, "w")
			fp.write(metadata[0])
			fp.write(metadata[1])
			fp.write(metadata[2])
			fp.write(metadata[3])
			fp.write(metadata[4])
			fp.close()
			return True
		else:
			return False

	def clearAllTags(self, yesno):
		if yesno is True:
			self.serviceHandler = eServiceCenter.getInstance()
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
			list = self.serviceHandler.list(root)
			if list is None:
				pass
			else:
				while 1:
					serviceref = list.getNext()
					if not serviceref.valid():
						break
					if serviceref.flags & eServiceReference.mustDescent:
						continue
					self.setTags("", service=serviceref, userNotice=False)
		self.updateCurrentTagList()
		self.updateAllTagList()

	def getFlags(self, tag):
		usedTags = tag in self.usedTags
		preTags = tag in self.pretags
		print usedTags, preTags
		userTags = False
		if not preTags and usedTags:
			userTags = True
		return (tag, usedTags, preTags, userTags)

	def keyRed(self):
		if self.currList is self["cTaglist"]:
			print "removing Tag", self["cTaglist"].getCurrent()[0]
			self.removeTag(self["cTaglist"].getCurrent()[0])

		elif self.currList is self["aTaglist"]:
			print "adding Tag", self["aTaglist"].getCurrent()[0]
			self.addTag(self["aTaglist"].getCurrent()[0])

	def keyGreen(self):
		if self.currList is self["cTaglist"]:
			self.session.openWithCallback(self.newTagEntered, InputBox, title=_('Whitepace will be replaced by "_"'), windowTitle=_("Enter the new Tag"))

	def keyYellow(self):
		if self.currList is self["aTaglist"]:
			self.session.openWithCallback(self.clearAllTags, MessageBox, _("Clear all Tags?\n\nThis will delete ALL tags in ALL recodings!\nAre you sure?"), MessageBox.TYPE_YESNO)

	def keyBlue(self):
		self.setTitle(' '.join((_("Movie Tagger"), _("Ver."), VERSION)))
		self["assignedTags"].setText(_("Assigned Tags"))
		self["definedTags"].setText(_("Specified Tags"))
		self["usedTag"].setText(_("Used Tag"))
		self["userTag"].setText(_("User-specific Tag"))
		self["preTag"].setText(_("Predefined Tag"))
		if self.currList is self["aTaglist"] or self.currList is None:
			self["aTaglist"].selectionEnabled(0)
			self["cTaglist"].selectionEnabled(1)
			self["buttonred"].setText(_("Remove Tag"))
			self["buttongreen"].setText(_("Add new Tag"))
			self["buttonyellow"].setText("")
			self["buttonblue"].setText(_("Toggle List"))
			self.currList = self["cTaglist"]
		else:
			self["aTaglist"].selectionEnabled(1)
			self["cTaglist"].selectionEnabled(0)
			self["buttonred"].setText(_("Add Tag"))
			self["buttongreen"].setText("")
			self["buttonyellow"].setText(_("Clear all Tags"))
			self["buttonblue"].setText(_("Toggle List"))
			self.currList = self["aTaglist"]

	def up(self):
		self.currList.up()

	def down(self):
		self.currList.down()

	def left(self):
		self.currList.pageUp()

	def right(self):
		self.currList.pageDown()

	def newTagEntered(self, newTag):
		if newTag >= 0:
			self.addTag(newTag.strip().replace(" ", "_"))


class TagMenuList(MenuList):
	SKIN_COMPONENT_KEY = "MovieTaggerTagMenuList"
	SKIN_COMPONENT_KEY_ITEM_HEIGHT = "itemHeight"
	SKIN_COMPONENT_KEY_ITEM_WIDTH = "itemWidth"
	SKIN_COMPONENT_KEY_XINDICATOR_WIDTH = "xIndicatorWidth"
	SKIN_COMPONENT_KEY_XINDICATOR_OFFSET = "xIndicatorOffset"
	SKIN_COMPONENT_KEY_XOFFSET = "xOffset"
	# skinner: if you want different colors for "X" please define color usedTagColor, userTagColor, preTagColor in <colors>

	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)

		isFHD = False
		sz_w = getDesktop(0).size().width()
		if sz_w >= 1920:
			isFHD = True

		sizes = componentSizes[TagMenuList.SKIN_COMPONENT_KEY]
		self.componentItemHeight = sizes.get(TagMenuList.SKIN_COMPONENT_KEY_ITEM_HEIGHT, 40 if isFHD else 25)
		self.componentItemWidth = sizes.get(TagMenuList.SKIN_COMPONENT_KEY_ITEM_WIDTH, 490 if isFHD else 290)
		self.xOffset = sizes.get(TagMenuList.SKIN_COMPONENT_KEY_XOFFSET, 10 if isFHD else 5)
		self.xIndicatorWidth = sizes.get(TagMenuList.SKIN_COMPONENT_KEY_XINDICATOR_WIDTH, 40 if isFHD else 20)
		self.xIndicatorOffset = sizes.get(TagMenuList.SKIN_COMPONENT_KEY_XINDICATOR_OFFSET, 370 if isFHD else 230)
		try:
			self.usedTagColor = parseColor("usedTagColor").argb()
		except:
			self.usedTagColor = 0x00ffff00
		try:
			self.userTagColor = parseColor("userTagColor").argb()
		except:
			self.userTagColor = 0x00FF0000
		try:
			self.preTagColor = parseColor("preTagColor").argb()
		except:
			self.preTagColor = 0x0000FF00

		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setFont(1, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		self.l.setItemHeight(self.componentItemHeight)
		self.l.setBuildFunc(self.buildTagMenuListEntry)

	def buildTagMenuListEntry(self, tagName, isUsedTag=False, isUserTag=False, isPreTag=False):
		res = [tagName]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.xOffset, 0, self.componentItemWidth, self.componentItemHeight, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, tagName))

		if isUsedTag:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.xIndicatorOffset, 0, self.xIndicatorWidth, self.componentItemHeight, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER, "X", self.usedTagColor))
		if isUserTag:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.xIndicatorOffset + self.xIndicatorWidth, 0, self.xIndicatorWidth, self.componentItemHeight, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER, "X", self.userTagColor))
		if isPreTag:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.xIndicatorOffset + (2 * self.xIndicatorWidth), 0, self.xIndicatorWidth, self.componentItemHeight, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER, "X", self.preTagColor))

		return res

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)


def main(session, service, **kwargs):
	try:
		session.open(MovieTagger, service)
	except Exception, e:
		raise e


def Plugins(path, **kwargs):
 	return PluginDescriptor(name="Movie Tagger", description=_("Movie Tagger..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main)
