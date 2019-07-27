#######################################################################
#
#  MerlinSkinThemes for Dreambox/Enigma2/Dreambox OS
#  Coded by marthom (c)2012 - 2018
#
#  Support: board.dreambox.tools
#  E-Mail: marthom@dreambox-tools.info
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep MY license and inform me about the modifications by mail.
#
#######################################################################

from Plugins.Plugin import PluginDescriptor

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.Standby import TryQuitMainloop
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console

from skin import parseColor, TemplatedListFonts, componentSizes

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Button import Button
from Components.Input import Input
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.MenuList import MenuList
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigNumber, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen

from enigma import eListbox, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, getEnigmaVersionString

from Tools.HardwareInfo import HardwareInfo
from Tools.Directories import resolveFilename, SCOPE_SKIN, SCOPE_CURRENT_SKIN, SCOPE_PLUGINS, SCOPE_SYSETC, fileExists
from Tools.Notifications import AddPopup

import xml.etree.cElementTree as Tree
from xml.dom import minidom

import shutil
import os

# =========================================
PluginVersion = "v2.6.3"
Title = "MerlinSkinThemes "
Author = "by marthom"
# =========================================

SkinXML = config.skin.primary_skin.value
SkinFile = resolveFilename(SCOPE_SKIN) + SkinXML
SkinName = SkinXML[0:SkinXML.find("/")]
ThemeFile = resolveFilename(SCOPE_SKIN) + SkinName + "/themes.xml"
skin_user_xml = "/etc/enigma2/skin_user.xml"
enigmacontrol = "/var/lib/opkg/info/enigma2.control"
merlinChk = "/usr/share/enigma2/merlin_setup.xml"
GP3Chk = "/usr/lib/enigma2/python/Plugins/Bp/geminimain/gVersion.py"
GP4Chk = "/usr/lib/enigma2/python/Plugins/GP4/geminilocale/gVersion.py"
ImageCreater = "/usr/lib/enigma2/python/Components/ImageCreater.py"
PIL = "/usr/lib/python2.7/site-packages/PIL/Image.py"

# Liste der Vorschaubilder
myList = ["InfoBar", "Menu", "PluginBrowser", "ChannelSelection", "MovieSelection", "MoviePlayer", "SecondInfoBar", "GraphMultiEPG", "MessageBox", "InputBox", "ChoiceBox", "Mute", "Volume", "MerlinMusicPlayer2", "ExtLCDInfoBar", "ExtLCDEventView", "ExtLCDStandby", "ExtLCDMoviePlayer", "ExtLCDMMP2", "OLEDInfoBar", "OLEDEventView", "OLEDStandby", "OLEDMoviePlayer", "OLEDMMP2", "LCDInfoBar", "LCDEventView", "LCDStandby", "LCDMoviePlayer", "LCDMMP2"]

# Enigma2Version
E2ver = "not available"
if open("/proc/stb/info/model","rb").read() == "dm7080":
	if fileExists(enigmacontrol):
		file = open(enigmacontrol, 'r')
		while 1:
			line = file.readline()
			if not line:break
			if line[:9] == "Version: ":
				E2ver = line[9:-1]
		file.close()
else:
	E2ver = getEnigmaVersionString()

# Merlin
Merlin = False
if fileExists(merlinChk):
	Merlin = True

# GP3
GP3 = False
GP3ver = ""
if fileExists(GP3Chk):
	GP3 = True
	file = open(GP3Chk, 'r')
	data = ""
	while 1:
		line = file.readline()
		if not line:break
		data += line
	file.close()
	
	data = data.split("'")
	GP3ver = data[1]

# GP4
GP4 = False
GP4ver = ""
if fileExists(GP4Chk):
	GP4 = True
	file = open(GP4Chk, 'r')
	data = ""
	while 1:
		line = file.readline()
		if not line:break
		data += line
	file.close()
	
	data = data.split("'")
	GP4ver = data[1]

# ImageCreate
ImgCreate = False
if fileExists(ImageCreater) and fileExists(PIL):
	from Components.ImageCreater import imageCreater
	ImgCreate = True

# Arm/mipsel/aarch64
if HardwareInfo().get_device_name() in ('dm900', 'dm920'):
	ArchArm = True
	ArchMipsel = False
	Arch64 = False
else:
	if HardwareInfo().get_device_name() in ('one', 'two'):
		Arch64 = True
		ArchMipsel = False
		ArchArm = False
	else:
		ArchArm = False
		ArchMipsel = True
		Arch64 = False

print "------------------------------------------------"
print HardwareInfo().get_device_name()
print "------------------------------------------------"

# skin_user.xml
SkinUser = False
if fileExists(skin_user_xml):
	SkinUser = True
	
config.plugins.MerlinSkinThemes = ConfigSubsection()
config.plugins.MerlinSkinThemes.Skin = ConfigText(default=SkinName)
config.plugins.MerlinSkinThemes.selSkin = ConfigText(default=SkinName)
config.plugins.MerlinSkinThemes.ComponentTheme = ConfigText(default="")
config.plugins.MerlinSkinThemes.ColorTheme = ConfigText(default="")
config.plugins.MerlinSkinThemes.SkinPathTheme = ConfigText(default="")
config.plugins.MerlinSkinThemes.FontTheme = ConfigText(default="")
config.plugins.MerlinSkinThemes.BorderSetTheme = ConfigText(default="")
config.plugins.MerlinSkinThemes.WindowStyleScrollbarTheme = ConfigText(default="")
config.plugins.MerlinSkinThemes.InfoBar = ConfigText(default="")
config.plugins.MerlinSkinThemes.Menu = ConfigText(default="")
config.plugins.MerlinSkinThemes.PluginBrowser = ConfigText(default="")
config.plugins.MerlinSkinThemes.ChannelSelection = ConfigText(default="")
config.plugins.MerlinSkinThemes.MovieSelection = ConfigText(default="")
config.plugins.MerlinSkinThemes.MoviePlayer = ConfigText(default="")
config.plugins.MerlinSkinThemes.SecondInfoBar = ConfigText(default="")
config.plugins.MerlinSkinThemes.GraphMultiEPG = ConfigText(default="")
config.plugins.MerlinSkinThemes.MessageBox = ConfigText(default="")
config.plugins.MerlinSkinThemes.InputBox = ConfigText(default="")
config.plugins.MerlinSkinThemes.ChoiceBox = ConfigText(default="")
config.plugins.MerlinSkinThemes.Mute = ConfigText(default="")
config.plugins.MerlinSkinThemes.Volume = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_MIPSEL = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_ARM = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_AARCH64 = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_MIPSEL = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_ARM = ConfigText(default="")
config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_ARCH64 = ConfigText(default="")
config.plugins.MerlinSkinThemes.ExtLCDInfoBar = ConfigText(default="")
config.plugins.MerlinSkinThemes.ExtLCDEventView = ConfigText(default="")
config.plugins.MerlinSkinThemes.ExtLCDStandby = ConfigText(default="")
config.plugins.MerlinSkinThemes.ExtLCDMoviePlayer = ConfigText(default="")
config.plugins.MerlinSkinThemes.ExtLCDMMP2 = ConfigText(default="")
config.plugins.MerlinSkinThemes.OLEDInfoBar = ConfigText(default="")
config.plugins.MerlinSkinThemes.OLEDEventView = ConfigText(default="")
config.plugins.MerlinSkinThemes.OLEDStandby = ConfigText(default="")
config.plugins.MerlinSkinThemes.OLEDMoviePlayer = ConfigText(default="")
config.plugins.MerlinSkinThemes.OLEDMMP2 = ConfigText(default="")
config.plugins.MerlinSkinThemes.LCDInfoBar = ConfigText(default="")
config.plugins.MerlinSkinThemes.LCDEventView = ConfigText(default="")
config.plugins.MerlinSkinThemes.LCDStandby = ConfigText(default="")
config.plugins.MerlinSkinThemes.LCDMoviePlayer = ConfigText(default="")
config.plugins.MerlinSkinThemes.LCDMMP2 = ConfigText(default="")
config.plugins.MerlinSkinThemes.PNGTheme = ConfigText(default="")
config.plugins.MerlinSkinThemes.ShowPrevPNG = ConfigText(default="1")
config.plugins.MerlinSkinThemes.CornerRadius = ConfigText(default="")

class MerlinSkinThemes(Screen, HelpableScreen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="1920,1080" title="%s" backgroundColor="#00808080" >
			<widget name="DescLabel" position="10,10" size="1900,40" font="Regular;26" zPosition="2" valign="center" halign="center" />

			<widget name="ListLabel" position="10,60" size="945,40" font="Regular;26" zPosition="2" valign="center" halign="left" />
			<widget name="ImageInfo" position="965,60" size="945,40" font="Regular;26" zPosition="2" halign="left" />
			
			<widget name="SkinsList" position="10,110" size="945,910" scrollbarMode="showOnDemand" zPosition="1" />
			<widget name="config" position="10,110" size="945,910" scrollbarMode="showOnDemand" zPosition="1" /> 

			<widget name="SkinCopyright" position="965,110" size="945,200" font="Regular;18" zPosition="2" halign="left" />
			<widget name="Preview" position="965,320" size="945,700" alphatest="blend" />
			
			<widget name="key_red" position="10,1030" size="200,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<widget name="key_green" position="258,1030" size="200,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<widget name="key_yellow" position="506,1030" size="200,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<widget name="key_blue" position="755,1030" size="200,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />

			<ePixmap name="red" position="10,1030" zPosition="1" size="200,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="blend" />
			<ePixmap name="green" position="258,1030" zPosition="1" size="200,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="blend" />
			<ePixmap name="yellow" position="506,1030" zPosition="1" size="200,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="blend" />
			<ePixmap name="blue" position="755,1030" zPosition="1" size="200,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="blend" />
		</screen>"""% _("MerlinSkinThemes")

	ThemeName = ""
	selSkinName = ""
	selThemeFile = ""
	
	def __init__(self, session):
		print "[MST] " + PluginVersion + " running..."
		
		self.session = session
		
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		self.clist = []
		ConfigListScreen.__init__(self, self.clist)
		
		self.setTitle(Title + " " + PluginVersion + " - " + Author)

		if not SkinUser:
			self["ListLabel"] = Label(_("Skinlist") )
		else:
			self["ListLabel"] = Label(_("Skinlist") + " - ATTENTION: skin_user.xml found!!!")
		
		self["DescLabel"] = Label(Title + " " + PluginVersion + " " + Author)
		self["SkinCopyright"] = Label()
		self["Preview"] = Pixmap()
		self["ImageInfo"] = Label()
		
		self.curList = "SkinsList"
		
		self["key_red"] = Button(_("exit"))
		self["key_green"] = Button(_("switch to skin"))
		self["key_yellow"] = Button(_("save as design"))
		self["key_blue"] = Button(_(" "))
		
		self["SkinsList"] = GetSkinsList([])

		self.onSelectionChanged = [ ]
		
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red":     self.buttonRed,
			"green":   self.buttonGreen,
			"yellow":  self.buttonYellow,
		}, -1)
		
		self["DirectionActions"] = HelpableActionMap(self, "DirectionActions",
		{
			"up":		(self.up, _("Move cursor up")),
			"down":		(self.down, _("Move cursor down")),
			"left":		(self.left, _("Move cursor left")),
			"right":	(self.right, _("Move cursor right")),
		}, -1)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"ok":		(self.ok, _("")),
			"cancel":	(self.exit, _("Close plugin")),
		}, -1)

		self["TeleTextActions"] = HelpableActionMap(self, "TeleTextActions",
		{
			"help":		(self.Help, _("")),
			"info":		(self.Info, _("")),
		}, -1)

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
		{
			"menu":		(self.MSTMenu, _("")),
		}, -1)
		
		self.updateSkinList()
		
		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		self.onLayoutFinish.append(self.startRun)

	def startRun(self):
		self["SkinsList"].onSelectionChanged.append(self.changedSkinsList)

		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		self["config"].hide()
		
		try:
			self["SkinsList"].up()
			listend = self["SkinsList"].getSelectionIndex()
			self["SkinsList"].moveToIndex(0)
			activeItem = 0
			for index in range(listend):
				self["SkinsList"].moveToIndex(index)
				if self["SkinsList"].getCurrent()[1][7] == SkinName:
					activeItem = index
				
			self["SkinsList"].moveToIndex(activeItem)
		except:
			self["SkinsList"].moveToIndex(0)

		self.ImageInfo()
		if fileExists(MerlinSkinThemes.selSkinFile):
			self.CopyrightInfo()


	def readThemes(self):
		defaultdesign = None
		defaultcomponenttheme = None
		defaultcolortheme = None
		defaultskinpaththeme = None
		defaultfonttheme = None
		defaultbordersettheme = None
		defaultwindowstylescrollbartheme = None
		defaultinfobar = None
		defaultmenu = None
		defaultpluginbrowser = None
		defaultchannelselection = None
		defaultmovieselection = None
		defaultmovieplayer = None
		defaultsecondinfobar = None
		defaultgraphmultiepg = None
		defaulteventview = None
		defaultepgselection = None
		defaultmessagebox = None
		defaultinputbox = None
		defaultchoicebox = None
		defaultmute = None
		defaultvolume = None
		defaultmmp2 = None
		defaultmmp2mipsel = None
		defaultmmp2arm = None
		defaultmmp2saver = None
		defaultmmp2savermipsel = None
		defaultmmp2saverarm = None
		defaultmmp2saverarch64 = None
		defaultextlcdinfobar = None
		defaultextlcdeventview = None
		defaultextlcdstandby = None
		defaultextlcdmovieplayer = None
		defaultextlcdmmp2 = None
		defaultoledinfobar = None
		defaultoledeventview = None
		defaultoledstandby = None
		defaultoledmovieplayer = None
		defaultoledmmp2 = None
		defaultlcdinfobar = None
		defaultlcdeventview = None
		defaultlcdstandby = None
		defaultlcdmovieplayer = None
		defaultlcdmmp2 = None
		defaultpngtheme = None
		defaultcornerradius = None
		
		self.clist = []

		try:
			xml = Tree.parse(MerlinSkinThemes.selThemeFile)

			selSkinList = []
			selSkinList.append(MerlinSkinThemes.selSkinName)
			config.plugins.MerlinSkinThemes.selSkin = MyConfigSelection(default=MerlinSkinThemes.selSkinName, choices = selSkinList)
			self.clist.append(getConfigListEntry(_(" "), ))
			self.clist.append(getConfigListEntry("Skin", config.plugins.MerlinSkinThemes.selSkin))
			
			# Designs
			self.clist.append(getConfigListEntry(_(" "), ))
			self.clist.append(getConfigListEntry(_(" " + u'\u00b7' + " DESIGNS"), ))

			DesignList = []
			if xml.find("designs") is not None:
				DesignList.append("-none-")
				ds = xml.find("designs")
				for design in ds.findall("design"):
					DesignList.append(design.get("name"))
					defaultdesign = "-none-"

			if len(DesignList) > 0:
				self.MSTDesigns = MyConfigSelection(default=defaultdesign, choices = DesignList)
				config.plugins.MerlinSkinThemes.Design = self.MSTDesigns
				self.clist.append(getConfigListEntry("Design", self.MSTDesigns))
			else:
				self.MSTDesigns = MyConfigSelection(default=defaultdesign, choices = ["-none-"])
				config.plugins.MerlinSkinThemes.Design = self.MSTDesigns
				self.clist.append(getConfigListEntry("Design", self.MSTDesigns))

			# Themes
			self.clist.append(getConfigListEntry(_(" "), ))
			self.clist.append(getConfigListEntry(_(" " + u'\u00b7' + " THEMES"), ))

			# COLOR
			ColorThemeList = []
			if xml.find("colortheme") is not None:
				for theme in xml.findall("colortheme"):
					ColorThemeList.append(theme.get("name"))
					if theme.get("value") == "active":
						defaultcolortheme = theme.get("name")

			if len(ColorThemeList) > 0:
				self.TColor = MyConfigSelection(default=defaultcolortheme, choices = ColorThemeList)
				config.plugins.MerlinSkinThemes.ColorTheme = self.TColor
				self.clist.append(getConfigListEntry("ColorTheme", self.TColor))

			# SkinPathTheme
			SkinPathThemeList = []
			if xml.find("skinpaththemes") is not None:
				spt = xml.find("skinpaththemes")
				for theme in spt.findall("theme"):
					SkinPathThemeList.append(theme.get("name"))
					if theme.get("value") == "active":
						defaultskinpaththeme = theme.get("name")

			if len(SkinPathThemeList) > 0:
				self.SPath = MyConfigSelection(default=defaultskinpaththeme, choices = SkinPathThemeList)
				config.plugins.MerlinSkinThemes.SkinPathTheme = self.SPath
				self.clist.append(getConfigListEntry("SkinPathTheme", self.SPath))

			# FONT
			FontThemeList = []
			if xml.find("fonttheme") is not None:
				for theme in xml.findall("fonttheme"):
					FontThemeList.append(theme.get("name"))
					if theme.get("value") == "active":
						defaultfonttheme = theme.get("name")

			if len(FontThemeList) > 0:
				self.TFont = MyConfigSelection(default=defaultfonttheme, choices = FontThemeList)
				config.plugins.MerlinSkinThemes.FontTheme = self.TFont
				self.clist.append(getConfigListEntry("FontTheme", self.TFont))

			# BORDERSET
			BorderSetThemeList = []
			if xml.find("bordersettheme") is not None:
				for theme in xml.findall("bordersettheme"):
					BorderSetThemeList.append(theme.get("name"))
					if theme.get("value") == "active":
						defaultbordersettheme = theme.get("name")

			if len(BorderSetThemeList) > 0:
				self.TBorder = MyConfigSelection(default=defaultbordersettheme, choices = BorderSetThemeList)
				config.plugins.MerlinSkinThemes.BorderSetTheme = self.TBorder
				self.clist.append(getConfigListEntry("BorderSetTheme", self.TBorder))
				
			# WINDOSTYLESCROLLBAR
			WindowStyleScrollbarThemeList = []
			if xml.find("windowstylescrollbartheme") is not None:
				for theme in xml.findall("windowstylescrollbartheme"):
					WindowStyleScrollbarThemeList.append(theme.get("name"))
					if theme.get("value") == "active":
						defaultwindowstylescrollbartheme = theme.get("name")

			if len(WindowStyleScrollbarThemeList) > 0:
				self.TScroll = MyConfigSelection(default=defaultwindowstylescrollbartheme, choices = WindowStyleScrollbarThemeList)
				config.plugins.MerlinSkinThemes.WindowStyleScrollbarTheme = self.TScroll
				self.clist.append(getConfigListEntry("WindowStyleScrollbarTheme", self.TScroll))

			# PNG
			PNGThemeList = []
			if xml.find("pngtheme") is not None:
				for theme in xml.findall("pngtheme"):
					PNGThemeList.append(theme.get("name"))
					if theme.get("value") == "active":
						defaultpngtheme = theme.get("name")

			if len(PNGThemeList) > 0:
				self.TPNG = MyConfigSelection(default=defaultpngtheme, choices = PNGThemeList)
				config.plugins.MerlinSkinThemes.PNGTheme = self.TPNG
				self.clist.append(getConfigListEntry("PNGTheme", self.TPNG))

			# COMPONENTS
			ComponentsThemeList = []
			if xml.find("componenttheme") is not None:
				for theme in xml.findall("componenttheme"):
					ComponentsThemeList.append(theme.get("name"))
					if theme.get("value") == "active":
						defaultcomponenttheme = theme.get("name")

			if len(ComponentsThemeList) > 0:
				self.TComponent = MyConfigSelection(default=defaultcomponenttheme, choices = ComponentsThemeList)
				config.plugins.MerlinSkinThemes.ComponentTheme = self.TComponent
				self.clist.append(getConfigListEntry("ComponentTheme", self.TComponent))
			
			# SCREENS
			self.clist.append(getConfigListEntry(_(" "), ))
			self.clist.append(getConfigListEntry(_(" " + u'\u00b7' + " SCREENS"), ))

			if xml.find("screenthemes") is not None:
				#-----------
				# INFOBAR
				InfoBarList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "InfoBar":
						for themes in screens.findall("screentheme"):
							InfoBarList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultinfobar = themes.get("name")

				if len(InfoBarList) > 0:
					self.SInfobar = MyConfigSelection(default=defaultinfobar, choices = InfoBarList)
					config.plugins.MerlinSkinThemes.InfoBar = self.SInfobar
					self.clist.append(getConfigListEntry("InfoBar", self.SInfobar))

                               	#-----------
				# Menue
				MenuList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "Menu":
						for themes in screens.findall("screentheme"):
							MenuList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultmenu = themes.get("name")

				if len(MenuList) > 0:
					self.SMenu = MyConfigSelection(default=defaultmenu, choices = MenuList)
					config.plugins.MerlinSkinThemes.Menu = self.SMenu
					self.clist.append(getConfigListEntry("Menu", self.SMenu))

                               	#-----------
				# PluginBrowser
				PluginBrowserList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "PluginBrowser":
						for themes in screens.findall("screentheme"):
							PluginBrowserList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultpluginbrowser = themes.get("name")

				if len(PluginBrowserList) > 0:
					self.SPluginBrowser = MyConfigSelection(default=defaultpluginbrowser, choices = PluginBrowserList)
					config.plugins.MerlinSkinThemes.PluginBrowser = self.SPluginBrowser
					self.clist.append(getConfigListEntry("PluginBrowser", self.SPluginBrowser))

				#-----------
				# CHANNELSELECTION
				ChannelSelectionList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "ChannelSelection":
						for themes in screens.findall("screentheme"):
							ChannelSelectionList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultchannelselection = themes.get("name")

				if len(ChannelSelectionList) > 0:
					self.SChannelSel = MyConfigSelection(default=defaultchannelselection, choices = ChannelSelectionList)
					config.plugins.MerlinSkinThemes.ChannelSelection = self.SChannelSel
					self.clist.append(getConfigListEntry("ChannelSelection", self.SChannelSel))

				#-----------
				# MOVIESELECTION
				MovieSelectionList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "MovieSelection":
						for themes in screens.findall("screentheme"):
							MovieSelectionList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultmovieselection = themes.get("name")

				if len(MovieSelectionList) > 0:
					self.SMovieSel = MyConfigSelection(default=defaultmovieselection, choices = MovieSelectionList)
					config.plugins.MerlinSkinThemes.MovieSelection = self.SMovieSel
					self.clist.append(getConfigListEntry("MovieSelection", self.SMovieSel))

				#-----------
				# MOVIEPLAYER
				MoviePlayerList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "MoviePlayer":
						for themes in screens.findall("screentheme"):
							MoviePlayerList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultmovieplayer = themes.get("name")

				if len(MoviePlayerList) > 0:
					self.SMoviePlay = MyConfigSelection(default=defaultmovieplayer, choices = MoviePlayerList)
					config.plugins.MerlinSkinThemes.MoviePlayer = self.SMoviePlay		
					self.clist.append(getConfigListEntry("MoviePlayer", self.SMoviePlay))

				#-----------
				# SECONDINFOBAR
				SecondInfoBarList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "SecondInfoBar":
						for themes in screens.findall("screentheme"):
							SecondInfoBarList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultsecondinfobar = themes.get("name")

				if len(SecondInfoBarList) > 0:
					self.S2IB = MyConfigSelection(default=defaultsecondinfobar, choices = SecondInfoBarList)
					config.plugins.MerlinSkinThemes.SecondInfoBar = self.S2IB
					self.clist.append(getConfigListEntry("SecondInfoBar", self.S2IB))

				#-----------
				# GraphMultiEPG
				
				GraphMultiEPGList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "GraphMultiEPG":
						for themes in screens.findall("screentheme"):
							GraphMultiEPGList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultgraphmultiepg = themes.get("name")

				if len(GraphMultiEPGList) > 0:
					self.graphmultiepg = MyConfigSelection(default=defaultgraphmultiepg, choices = GraphMultiEPGList)
					config.plugins.MerlinSkinThemes.GraphMultiEPG = self.graphmultiepg
					self.clist.append(getConfigListEntry("GraphMultiEPG", self.graphmultiepg))

				#-----------
				# EventView
				EventViewList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "EventView":
						for themes in screens.findall("screentheme"):
							EventViewList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaulteventview = themes.get("name")

				if len(EventViewList) > 0:
					self.EventView = MyConfigSelection(default=defaulteventview, choices = EventViewList)
					config.plugins.MerlinSkinThemes.EventView = self.EventView
					self.clist.append(getConfigListEntry("EventView", self.EventView))

				#-----------
				# EPGSelection
				EPGSelectionList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "EPGSelection":
						for themes in screens.findall("screentheme"):
							EPGSelectionList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultepgselection = themes.get("name")

				if len(EPGSelectionList) > 0:
					self.EPGSelection = MyConfigSelection(default=defaultepgselection, choices = EPGSelectionList)
					config.plugins.MerlinSkinThemes.EPGSelection = self.EPGSelection
					self.clist.append(getConfigListEntry("EPGSelection", self.EPGSelection))

				#-----------
				# MESSAGEBOX
				MessageBoxList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "MessageBox":
						for themes in screens.findall("screentheme"):
							MessageBoxList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultmessagebox = themes.get("name")

				if len(MessageBoxList) > 0:
					self.SMsgBox = MyConfigSelection(default=defaultmessagebox, choices = MessageBoxList)
					config.plugins.MerlinSkinThemes.MessageBox = self.SMsgBox
					self.clist.append(getConfigListEntry("MessageBox", self.SMsgBox))

				#-----------
				# INPUTBOX
				InputBoxList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "InputBox":
						for themes in screens.findall("screentheme"):
							InputBoxList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultinputbox = themes.get("name")

				if len(InputBoxList) > 0:
					self.SInBox = MyConfigSelection(default=defaultinputbox, choices = InputBoxList)
					config.plugins.MerlinSkinThemes.InputBox = self.SInBox
					self.clist.append(getConfigListEntry("InputBox", self.SInBox))

				#-----------
				# CHOICEBOX
				ChoiceBoxList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "ChoiceBox":
						for themes in screens.findall("screentheme"):
							ChoiceBoxList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultchoicebox = themes.get("name")

				if len(ChoiceBoxList) > 0:
					self.SChoiceBox = MyConfigSelection(default=defaultchoicebox, choices = ChoiceBoxList)
					config.plugins.MerlinSkinThemes.ChoiceBox = self.SChoiceBox
					self.clist.append(getConfigListEntry("ChoiceBox", self.SChoiceBox))
					
				#-----------
				# MUTE
				MuteList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "Mute":
						for themes in screens.findall("screentheme"):
							MuteList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultmute = themes.get("name")

				if len(MuteList) > 0:
					self.SMute = MyConfigSelection(default=defaultmute, choices = MuteList)
					config.plugins.MerlinSkinThemes.Mute = self.SMute
					self.clist.append(getConfigListEntry("Mute", self.SMute))
					
				#-----------
				# VOLUME
				VolumeList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "Volume":
						for themes in screens.findall("screentheme"):
							VolumeList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultvolume = themes.get("name")

				if len(VolumeList) > 0:
					self.SVolume = MyConfigSelection(default=defaultvolume, choices = VolumeList)
					config.plugins.MerlinSkinThemes.Volume = self.SVolume
					self.clist.append(getConfigListEntry("Volume", self.SVolume))
					
				#-----------
				# MerlinMusicPlayer2Screen
				MMP2List = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "MerlinMusicPlayer2Screen":
						for themes in screens.findall("screentheme"):
							MMP2List.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultmmp2 = themes.get("name")

				if len(MMP2List) > 0:
					self.SMMP2 = MyConfigSelection(default=defaultmmp2, choices = MMP2List)
					config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen = self.SMMP2
					self.clist.append(getConfigListEntry("MerlinMusicPlayer2Screen", self.SMMP2))

				if ArchMipsel:
					#-----------
					# MerlinMusicPlayer2Screen_MIPSEL
					MMP2MipselList = []
					st = xml.find("screenthemes")
					for screens in st.findall("screens"):
						if screens.get("name") == "MerlinMusicPlayer2Screen_MIPSEL":
							for themes in screens.findall("screentheme"):
								MMP2MipselList.append(themes.get("name"))
								if themes.get("value") == "active":
									defaultmmp2mipsel = themes.get("name")

					if len(MMP2MipselList) > 0:
						self.SMMP2Mipsel = MyConfigSelection(default=defaultmmp2mipsel, choices = MMP2MipselList)
						config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_MIPSEL = self.SMMP2Mipsel
						self.clist.append(getConfigListEntry("MerlinMusicPlayer2Screen_MIPSEL", self.SMMP2Mipsel))

				if ArchArm:
					#-----------
					# MerlinMusicPlayer2Screen_ARM
					MMP2ArmList = []
					st = xml.find("screenthemes")
					for screens in st.findall("screens"):
						if screens.get("name") == "MerlinMusicPlayer2Screen_ARM":
							for themes in screens.findall("screentheme"):
								MMP2ArmList.append(themes.get("name"))
								if themes.get("value") == "active":
									defaultmmp2arm = themes.get("name")

					if len(MMP2ArmList) > 0:
						self.SMMP2Arm = MyConfigSelection(default=defaultmmp2arm, choices = MMP2ArmList)
						config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_ARM = self.SMMP2Arm
						self.clist.append(getConfigListEntry("MerlinMusicPlayer2Screen_ARM", self.SMMP2Arm))

				if Arch64:
					#-----------
					# MerlinMusicPlayer2Screen_AARCH64
					MMP2Arch64List = []
					st = xml.find("screenthemes")
					for screens in st.findall("screens"):
						if screens.get("name") == "MerlinMusicPlayer2Screen_AARCH64":
							for themes in screens.findall("screentheme"):
								MMP2Arch64List.append(themes.get("name"))
								if themes.get("value") == "active":
									defaultmmp2arch64 = themes.get("name")

					if len(MMP2Arch64List) > 0:
						self.SMMP2Arch64 = MyConfigSelection(default=defaultmmp2arch64, choices = MMP2Arch64List)
						config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_AARCH64 = self.SMMP2Arch64
						self.clist.append(getConfigListEntry("MerlinMusicPlayer2Screen_AARCH64", self.SMMP2Arch64))

				#-----------
				# MerlinMusicPlayer2ScreenSaver
				MMP2SaverList = []
				st = xml.find("screenthemes")
				for screens in st.findall("screens"):
					if screens.get("name") == "MerlinMusicPlayer2ScreenSaver":
						for themes in screens.findall("screentheme"):
							MMP2SaverList.append(themes.get("name"))
							if themes.get("value") == "active":
								defaultmmp2saver = themes.get("name")

				if len(MMP2SaverList) > 0:
					self.SMMP2Saver = MyConfigSelection(default=defaultmmp2saver, choices = MMP2SaverList)
					config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver = self.SMMP2Saver
					self.clist.append(getConfigListEntry("MerlinMusicPlayer2ScreenSaver", self.SMMP2Saver))

				if ArchMipsel:
					#-----------
					# MerlinMusicPlayer2ScreenSaver_MIPSEL
					MMP2SaverMipselList = []
					st = xml.find("screenthemes")
					for screens in st.findall("screens"):
						if screens.get("name") == "MerlinMusicPlayer2ScreenSaver_MIPSEL":
							for themes in screens.findall("screentheme"):
								MMP2SaverMipselList.append(themes.get("name"))
								if themes.get("value") == "active":
									defaultmmp2savermipsel = themes.get("name")

					if len(MMP2SaverMipselList) > 0:
						self.SMMP2SaverMipsel = MyConfigSelection(default=defaultmmp2savermipsel, choices = MMP2SaverMipselList)
						config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_MIPSEL = self.SMMP2SaverMipsel
						self.clist.append(getConfigListEntry("MerlinMusicPlayer2ScreenSaver_MIPSEL", self.SMMP2SaverMipsel))

				if ArchArm:
					#-----------
					# MerlinMusicPlayer2ScreenSaver_ARM
					MMP2SaverArmList = []
					st = xml.find("screenthemes")
					for screens in st.findall("screens"):
						if screens.get("name") == "MerlinMusicPlayer2ScreenSaver_ARM":
							for themes in screens.findall("screentheme"):
								MMP2SaverArmList.append(themes.get("name"))
								if themes.get("value") == "active":
									defaultmmp2saverarm = themes.get("name")

					if len(MMP2SaverArmList) > 0:
						self.SMMP2SaverArm = MyConfigSelection(default=defaultmmp2saverarm, choices = MMP2SaverArmList)
						config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_ARM = self.SMMP2SaverArm
						self.clist.append(getConfigListEntry("MerlinMusicPlayer2ScreenSaver_ARM", self.SMMP2SaverArm))

				if Arch64:
					#-----------
					# MerlinMusicPlayer2ScreenSaver_AARCH64
					MMP2SaverArch64List = []
					st = xml.find("screenthemes")
					for screens in st.findall("screens"):
						if screens.get("name") == "MerlinMusicPlayer2ScreenSaver_AARCH64":
							for themes in screens.findall("screentheme"):
								MMP2SaverArch64List.append(themes.get("name"))
								if themes.get("value") == "active":
									defaultmmp2saverarch64 = themes.get("name")

					if len(MMP2SaverArch64List) > 0:
						self.SMMP2SaverArch64 = MyConfigSelection(default=defaultmmp2saverarch64, choices = MMP2SaverArch64List)
						config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_AARCH64 = self.SMMP2SaverArch64
						self.clist.append(getConfigListEntry("MerlinMusicPlayer2ScreenSaver_AARCH64", self.SMMP2SaverArch64))

			# LCD Screens
			#-----------
			if xml.find("lcdscreenthemes") is not None:
				self.clist.append(getConfigListEntry(_(" "), ))
				self.clist.append(getConfigListEntry(_(" " + u'\u00b7' + " LCD SCREENS ID=1 (8000, 7020HD, 800HD, 7080) 132x64"), ))		
				# INFOBAR
				LCDInfoBarList = []
				st = xml.find("lcdscreenthemes")
				if st.find("screens[@name='InfoBarSummary']") is not None:
					lst = st.find("screens[@name='InfoBarSummary']")
					for th in lst.findall("lcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "InfoBarSummary" and screen.get("id") == "1":
								LCDInfoBarList.append(th.get("name"))
								if th.get("value") == "active":
									defaultlcdinfobar = th.get("name")

					if len(LCDInfoBarList) > 0:
						self.LSInfobar = MyConfigSelection(default=defaultlcdinfobar, choices = LCDInfoBarList)
						config.plugins.MerlinSkinThemes.LCDInfoBar = self.LSInfobar
						self.clist.append(getConfigListEntry("LCDInfoBar", self.LSInfobar))

				#-----------
				# EVENTVIEW
				LCDEventViewList = []
				if st.find("screens[@name='EventView_summary']") is not None:
					lst = st.find("screens[@name='EventView_summary']")
					for th in lst.findall("lcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "EventView_summary" and screen.get("id") == "1":
								LCDEventViewList.append(th.get("name"))
								if th.get("value") == "active":
									defaultlcdeventview = th.get("name")

					if len(LCDEventViewList) > 0:
						self.LSEventView = MyConfigSelection(default=defaultlcdeventview, choices = LCDEventViewList)
						config.plugins.MerlinSkinThemes.LCDEventView = self.LSEventView
						self.clist.append(getConfigListEntry("LCDEventView", self.LSEventView))

				#-----------
				# STANDBY
				LCDStandbyList = []
				if st.find("screens[@name='StandbySummary']") is not None:
					lst = st.find("screens[@name='StandbySummary']")
					for th in lst.findall("lcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "StandbySummary" and screen.get("id") == "1":
								LCDStandbyList.append(th.get("name"))
								if th.get("value") == "active":
									defaultlcdstandby = th.get("name")

					if len(LCDStandbyList) > 0:
						self.LSStandby = MyConfigSelection(default=defaultlcdstandby, choices = LCDStandbyList)
						config.plugins.MerlinSkinThemes.LCDStandby = self.LSStandby
						self.clist.append(getConfigListEntry("LCDStandby", self.LSStandby))
				
				#-----------
				# InfoBarMoviePlayerSummary
				LCDMoviePlayerList = []
				if st.find("screens[@name='InfoBarMoviePlayerSummary']") is not None:
					lst = st.find("screens[@name='InfoBarMoviePlayerSummary']")
					for th in lst.findall("lcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "InfoBarMoviePlayerSummary" and screen.get("id") == "1":
								LCDMoviePlayerList.append(th.get("name"))
								if th.get("value") == "active":
									defaultlcdmovieplayer = th.get("name")

					if len(LCDMoviePlayerList) > 0:
						self.LSMoviePlayer = MyConfigSelection(default=defaultlcdmovieplayer, choices = LCDMoviePlayerList)
						config.plugins.MerlinSkinThemes.LCDMoviePlayer = self.LSMoviePlayer
						self.clist.append(getConfigListEntry("LCDMoviePlayer", self.LSMoviePlayer))
						
				#-----------
				# MerlinMusicPlayer2LCDScreen
				LCDMMP2List = []
				if st.find("screens[@name='MerlinMusicPlayer2LCDScreen']") is not None:
					lst = st.find("screens[@name='MerlinMusicPlayer2LCDScreen']")
					for th in lst.findall("lcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "MerlinMusicPlayer2LCDScreen" and screen.get("id") == "1":
								LCDMMP2Lst.append(th.get("name"))
								if th.get("value") == "active":
									defaultlcdmmp2 = th.get("name")

					if len(LCDMMP2List) > 0:
						self.LSMMP2 = MyConfigSelection(default=defaultlcdmmp2, choices = LCDMMP2List)
						config.plugins.MerlinSkinThemes.LCDMMP2 = self.LSMMP2
						self.clist.append(getConfigListEntry("LCDMMP2", self.LSMMP2))
						
			# OLED Screens
			if xml.find("oledscreenthemes") is not None:
				self.clist.append(getConfigListEntry(_(" "), ))
				self.clist.append(getConfigListEntry(_(" " + u'\u00b7' + " OLED SCREENS ID=2 (800se, 820) 96x64"), ))		
				#-----------
				# INFOBAR
				OLEDInfoBarList = []
				st = xml.find("oledscreenthemes")
				if st.find("screens[@name='InfoBarSummary']") is not None:
					ost = st.find("screens[@name='InfoBarSummary']")
					for th in ost.findall("oledscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "InfoBarSummary" and screen.get("id") == "2":
								OLEDInfoBarList.append(th.get("name"))
								if th.get("value") == "active":
									defaultoledinfobar = th.get("name")

					if len(OLEDInfoBarList) > 0:
						self.OSInfobar = MyConfigSelection(default=defaultoledinfobar, choices = OLEDInfoBarList)
						config.plugins.MerlinSkinThemes.OLEDInfoBar = self.OSInfobar
						self.clist.append(getConfigListEntry("OLEDInfoBar", self.OSInfobar))

				#-----------
				# EVENTVIEW
				OLEDEventViewList = []
				if st.find("screens[@name='EventView_summary']") is not None:
					ost = st.find("screens[@name='EventView_summary']")
					for th in ost.findall("oledscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "EventView_summary" and screen.get("id") == "2":
								OLEDEventViewList.append(th.get("name"))
								if th.get("value") == "active":
									defaultoledeventview = th.get("name")

					if len(OLEDEventViewList) > 0:
						self.OSEventView = MyConfigSelection(default=defaultoledeventview, choices = OLEDEventViewList)
						config.plugins.MerlinSkinThemes.OLEDEventView = self.OSEventView
						self.clist.append(getConfigListEntry("OLEDEventView", self.OSEventView))

				#-----------
				# STANDBY
				OLEDStandbyList = []
				if st.find("screens[@name='StandbySummary']") is not None:
					ost = st.find("screens[@name='StandbySummary']")
					for th in ost.findall("oledscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "StandbySummary" and screen.get("id") == "2":
								OLEDStandbyList.append(th.get("name"))
								if th.get("value") == "active":
									defaultoledstandby = th.get("name")

					if len(OLEDStandbyList) > 0:
						self.OSStandby = MyConfigSelection(default=defaultoledstandby, choices = OLEDStandbyList)
						config.plugins.MerlinSkinThemes.OLEDStandby = self.OSStandby
						self.clist.append(getConfigListEntry("OLEDStandby", self.OSStandby))
						
				#-----------
				# InfoBarMoviePlayerSummary
				OLEDMoviePlayerList = []
				if st.find("screens[@name='InfoBarMoviePlayerSummary']") is not None:
					ost = st.find("screens[@name='InfoBarMoviePlayerSummary']")
					for th in ost.findall("oledscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "InfoBarMoviePlayerSummary" and screen.get("id") == "2":
								OLEDMoviePlayerList.append(th.get("name"))
								if th.get("value") == "active":
									defaultoledmovieplayer = th.get("name")

					if len(OLEDMoviePlayerList) > 0:
						self.OSMoviePlayer = MyConfigSelection(default=defaultoledmovieplayer, choices = OLEDMoviePlayerList)
						config.plugins.MerlinSkinThemes.OLEDMoviePlayer = self.OSMoviePlayer
						self.clist.append(getConfigListEntry("OLEDMoviePlayer", self.OSMoviePlayer))
						
				#-----------
				# MerlinMusicPlayer2OLCDScreen
				OLEDMMP2List = []
				if st.find("screens[@name='MerlinMusicPlayer2LCDScreen']") is not None:
					ost = st.find("screens[@name='MerlinMusicPlayer2LCDScreen']")
					for th in ost.findall("oledscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "MerlinMusicPlayer2LCDScreen" and screen.get("id") == "2":
								OLEDMMP2Lst.append(th.get("name"))
								if th.get("value") == "active":
									defaultoledmmp2 = th.get("name")

					if len(OLEDMMP2List) > 0:
						self.OSMMP2 = MyConfigSelection(default=defaultoledmmp2, choices = OLEDMMP2List)
						config.plugins.MerlinSkinThemes.OLEDMMP2 = self.OSMMP2
						self.clist.append(getConfigListEntry("OLEDMMP2", self.OSMMP2))
						
			# External LCD Screens
			#-----------
			if xml.find("extlcdscreenthemes") is not None:
				self.clist.append(getConfigListEntry(_(" "), ))
				self.clist.append(getConfigListEntry(_(" " + u'\u00b7' + " LCD SCREENS ID=3 (900ultraHD, 920ultraHD, Buck(380x210)...) 400x240"), ))		
				# INFOBAR
				ExtLCDInfoBarList = []
				st = xml.find("extlcdscreenthemes")
				if st.find("screens[@name='InfoBarSummary']") is not None:
					elst = st.find("screens[@name='InfoBarSummary']")
					for th in elst.findall("extlcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "InfoBarSummary" and screen.get("id") == "3":
								ExtLCDInfoBarList.append(th.get("name"))
								if th.get("value") == "active":
									defaultextlcdinfobar = th.get("name")

					if len(ExtLCDInfoBarList) > 0:
						self.ExtLSInfobar = MyConfigSelection(default=defaultextlcdinfobar, choices = ExtLCDInfoBarList)
						config.plugins.MerlinSkinThemes.ExtLCDInfoBar = self.ExtLSInfobar
						self.clist.append(getConfigListEntry("ExtLCDInfoBar", self.ExtLSInfobar))

				#-----------
				# EVENTVIEW
				ExtLCDEventViewList = []
				if st.find("screens[@name='EventView_summary']") is not None:
					elst = st.find("screens[@name='EventView_summary']")
					for th in elst.findall("extlcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "EventView_summary" and screen.get("id") == "3":
								ExtLCDEventViewList.append(th.get("name"))
								if th.get("value") == "active":
									defaultextlcdeventview = th.get("name")

					if len(ExtLCDEventViewList) > 0:
						self.ExtLSEventView = MyConfigSelection(default=defaultextlcdeventview, choices = ExtLCDEventViewList)
						config.plugins.MerlinSkinThemes.ExtLCDEventView = self.ExtLSEventView
						self.clist.append(getConfigListEntry("ExtLCDEventView", self.ExtLSEventView))

				#-----------
				# STANDBY
				ExtLCDStandbyList = []
				if st.find("screens[@name='StandbySummary']") is not None:
					elst = st.find("screens[@name='StandbySummary']")
					for th in elst.findall("extlcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "StandbySummary" and screen.get("id") == "3":
								ExtLCDStandbyList.append(th.get("name"))
								if th.get("value") == "active":
									defaultextlcdstandby = th.get("name")

					if len(ExtLCDStandbyList) > 0:
						self.ExtLSStandby = MyConfigSelection(default=defaultextlcdstandby, choices = ExtLCDStandbyList)
						config.plugins.MerlinSkinThemes.ExtLCDStandby = self.ExtLSStandby
						self.clist.append(getConfigListEntry("ExtLCDStandby", self.ExtLSStandby))

				#-----------
				# InfoBarMoviePlayerSummary
				ExtLCDMoviePlayerList = []
				if st.find("screens[@name='InfoBarMoviePlayerSummary']") is not None:
					elst = st.find("screens[@name='InfoBarMoviePlayerSummary']")
					for th in elst.findall("extlcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "InfoBarMoviePlayerSummary" and screen.get("id") == "3":
								ExtLCDMoviePlayerList.append(th.get("name"))
								if th.get("value") == "active":
									defaultextlcdmovieplayer = th.get("name")

					if len(ExtLCDMoviePlayerList) > 0:
						self.ExtLSMoviePlayer = MyConfigSelection(default=defaultextlcdmovieplayer, choices = ExtLCDMoviePlayerList)
						config.plugins.MerlinSkinThemes.ExtLCDMoviePlayer = self.ExtLSMoviePlayer
						self.clist.append(getConfigListEntry("ExtLCDMoviePlayer", self.ExtLSMoviePlayer))
						
				#-----------
				# MerlinMusicPlayer2EXTLCDScreen
				ExtLCDMMP2List = []
				if st.find("screens[@name='MerlinMusicPlayer2LCDScreen']") is not None:
					elst = st.find("screens[@name='MerlinMusicPlayer2LCDScreen']")
					for th in elst.findall("extlcdscreentheme"):
						for screen in th.findall("screen"):
							if screen.get("name") == "MerlinMusicPlayer2LCDScreen" and screen.get("id") == "3":
								ExtLCDMMP2List.append(th.get("name"))
								if th.get("value") == "active":
									defaultextlcdmmp2 = th.get("name")

					if len(ExtLCDMMP2List) > 0:
						self.ExtLSMMP2 = MyConfigSelection(default=defaultextlcdmmp2, choices = ExtLCDMMP2List)
						config.plugins.MerlinSkinThemes.ExtLCDMMP2 = self.ExtLSMMP2
						self.clist.append(getConfigListEntry("ExtLCDMMP2", self.ExtLSMMP2))
						
			# cornerRadius 
			if xml.find("cornerradius") is not None:
				self.clist.append(getConfigListEntry(_(" "), ))
				self.clist.append(getConfigListEntry(_(" " + u'\u00b7' + " CORNERRADIUS"), ))

				CornerRadiusList = []
				
				cr = xml.find("cornerradius")
				for cradius in cr.findall("radius"):
					CornerRadiusList.append(cradius.get("name"))
					if cradius.get("value") == "active":
						defaultcornerradius = cradius.get("name")

				if len(CornerRadiusList) > 0:
					self.CornerRadius = MyConfigSelection(default=defaultcornerradius, choices = CornerRadiusList)
					config.plugins.MerlinSkinThemes.CornerRadius = self.CornerRadius
					self.clist.append(getConfigListEntry("CornerRadius", self.CornerRadius))
						
		except:
			print "[MST] themes.xml in " + MerlinSkinThemes.selSkinName + " corrupt!"
			self.clist.append(getConfigListEntry(_(" "), ))
			self.clist.append(getConfigListEntry(_(">>> ERROR - themes.xml in " + MerlinSkinThemes.selSkinName + " corrupt! <<<"), ))
			
		self["config"].setList(self.clist)
		
	def buttonGreen(self):
		if self.curList == "SkinsList":
			# set new skin
			sel = self["SkinsList"].getCurrent()
			if sel[1][7] == "Default Skin":
				skinfile = "skin.xml"
			else:
				skinfile = "%s/skin.xml" % sel[1][7]

			# Dr. Best Infobar position
			if fileExists("/usr/share/enigma2/merlin_setup.xml"):
				config.merlin2.infobar_position_offset_x.value = 0
				config.merlin2.infobar_position_offset_x.save()
				config.merlin2.infobar_position_offset_y.value = 0
				config.merlin2.infobar_position_offset_y.save()
				config.merlin2.movieplayer_infobar_position_offset_x.value = 0
				config.merlin2.movieplayer_infobar_position_offset_x.save()
				config.merlin2.movieplayer_infobar_position_offset_y.value = 0
				config.merlin2.movieplayer_infobar_position_offset_y.save()
				
			config.skin.primary_skin.value = skinfile
			config.skin.primary_skin.save()
			restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply a new skin\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
			restartbox.setTitle(_("Restart GUI now?"))
		elif self.curList == "ConfigList":
			askBox = self.session.openWithCallback(self.askYN,MessageBox,_("[apply themes] needs time to build new settings\nDo you want to do this now?"), MessageBox.TYPE_YESNO)
			askBox.setTitle(_("Apply themes now?"))

	def askYN(self, answer):
		if answer is True:
			self.setThemes()
			if SkinName == MerlinSkinThemes.selSkinName:
				restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply a new skin\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
				restartbox.setTitle(_("Restart GUI now?"))
			
			else:
				self.session.open(MessageBox, _("Changes to skin " + MerlinSkinThemes.selSkinName + " ready!"), MessageBox.TYPE_INFO)
		#else:
		#	self.exit()

	def MSTScrFix(self, answer):
		if answer is True:
			curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
			rootSkin = curSkin.getroot()
			mstscreen = rootSkin.find("screen[@name='MerlinSkinThemes']")
			rootSkin.remove(mstscreen)

			self.XMLindent(rootSkin, 0)
			curSkin.write(MerlinSkinThemes.selSkinFile)
			
			self.updateSkinList()

			self.session.open(MessageBox, '<screen name="MerlinSkinThemes"...> was removed from selected skin.', MessageBox.TYPE_INFO)
			
	def buttonRed(self):
		self.exit()
		
	def buttonYellow(self):
		if self.curList == "SkinsList":
			if self["SkinsList"].getCurrent()[3][7] == "no themes.xml":
				self.createThemes()

			if self["SkinsList"].getCurrent()[3][7] == "no skin.xml":
				self.delSkinDir()
				
		elif self.curList == "ConfigList":
			if self["config"].getCurrent()[0] == "Design":
				# delete design
				self.deleteDesign()
			
			else:
				# save as design
				self.session.openWithCallback(self.saveDesign, InputBox, title=_("Please enter designname!"))
			
	def saveDesign(self, designname):
		if designname is not None:
		
			designname = designname.strip()
			
			curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
			xmlroot = curTree.getroot()
			
			if xmlroot.find("designs") is None:
				xmldesigns = Tree.SubElement(xmlroot, "designs")
			else:
				xmldesigns = xmlroot.find("designs")

			# check if design exists
			if xmldesigns.find("design[@name='" + designname + "']") is not None:
				xmldesigns.remove(xmldesigns.find("design[@name='" + designname + "']"))
				
			# write/rewrite design
			xmldesign = Tree.SubElement(xmldesigns, "design", {"name": designname, "value": "active"})
				
			if xmlroot.find("colortheme[@name='" + config.plugins.MerlinSkinThemes.ColorTheme.value + "']") is not None:
				if xmldesign.find("ColorTheme") is not None:
					td = xmldesign.find("ColorTheme")
					td.set("name", config.plugins.MerlinSkinThemes.ColorTheme.value)
				else:
					Tree.SubElement(xmldesign, "ColorTheme", {"name": config.plugins.MerlinSkinThemes.ColorTheme.value})
				
			if xmlroot.find("fonttheme[@name='" + config.plugins.MerlinSkinThemes.FontTheme.value + "']") is not None:
				if xmldesign.find("FontTheme") is not None:
					td = d.find("FontTheme")
					td.set("name", config.plugins.MerlinSkinThemes.FontTheme.value)
				else:
					Tree.SubElement(xmldesign, "FontTheme", {"name": config.plugins.MerlinSkinThemes.FontTheme.value})
			
			if xmlroot.find("bordersettheme") is not None:
				if xmldesign.find("BorderSetTheme") is not None:
					td = d.find("BorderSetTheme")
					td.set("name", config.plugins.MerlinSkinThemes.BorderSetTheme.value)
				else:
					Tree.SubElement(xmldesign, "BorderSetTheme", {"name": config.plugins.MerlinSkinThemes.BorderSetTheme.value})
			
			if xmlroot.find("windowstylescrollbartheme") is not None:
				if xmldesign.find("WindowStyleScrollbarTheme") is not None:
					td = d.find("WindowStyleScrollbarTheme")
					td.set("name", config.plugins.MerlinSkinThemes.WindowStyleScrollbarTheme.value)
				else:
					Tree.SubElement(xmldesign, "WindowStyleScrollbarTheme", {"name": config.plugins.MerlinSkinThemes.WindowStyleScrollbarTheme.value})
			
			if xmlroot.find("componenttheme") is not None:
				if xmldesign.find("ComponentTheme") is not None:
					td = d.find("ComponentTheme")
					td.set("name", config.plugins.MerlinSkinThemes.ComponentTheme.value)
				else:
					Tree.SubElement(xmldesign, "ComponentTheme", {"name": config.plugins.MerlinSkinThemes.ComponentTheme.value})
			
			if xmlroot.find("pngtheme[@name='" + config.plugins.MerlinSkinThemes.PNGTheme.value + "']") is not None:
				if xmldesign.find("PNGTheme") is not None:
					td = xmldesign.find("PNGTheme")
					td.set("name", config.plugins.MerlinSkinThemes.PNGTheme.value)
				else:
					Tree.SubElement(xmldesign, "PNGTheme", {"name": config.plugins.MerlinSkinThemes.PNGTheme.value})

			# SkinPathThemes
			if xmlroot.find("skinpaththemes") is not None:
				t = xmlroot.find("skinpaththemes")
				
				if t.find("theme[@name='" + config.plugins.MerlinSkinThemes.SkinPathTheme.value + "']") is not None:
					if xmldesign.find("SkinPathTheme") is not None:
						td = xmldesign.find("SkinPathTheme")
						td.set("name", config.plugins.MerlinSkinThemes.SkinPathTheme.value)
					else:
						Tree.SubElement(xmldesign, "SkinPathTheme", {"name": config.plugins.MerlinSkinThemes.SkinPathTheme.value})
					
			# Screens
			if xmlroot.find("screenthemes") is not None:
				t = xmlroot.find("screenthemes")
				
				if t.find("screens[@name='InfoBar']") is not None:
					ts = t.find("screens[@name='InfoBar']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.InfoBar.value + "']") is not None:
						Tree.SubElement(xmldesign, "InfoBar", {"name": config.plugins.MerlinSkinThemes.InfoBar.value})

				if t.find("screens[@name='Menu']") is not None:
					ts = t.find("screens[@name='Menu']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.Menu.value + "']") is not None:
						Tree.SubElement(xmldesign, "Menu", {"name": config.plugins.MerlinSkinThemes.Menu.value})

				if t.find("screens[@name='PluginBrowser']") is not None:
					ts = t.find("screens[@name='PluginBrowser']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.PluginBrowser.value + "']") is not None:
						Tree.SubElement(xmldesign, "PluginBrowser", {"name": config.plugins.MerlinSkinThemes.PluginBrowser.value})
	
				if t.find("screens[@name='ChannelSelection']") is not None:
					ts = t.find("screens[@name='ChannelSelection']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.ChannelSelection.value + "']") is not None:
						Tree.SubElement(xmldesign, "ChannelSelection", {"name": config.plugins.MerlinSkinThemes.ChannelSelection.value})
						
				if t.find("screens[@name='MovieSelection']") is not None:
					ts = t.find("screens[@name='MovieSelection']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MovieSelection.value + "']") is not None:
						Tree.SubElement(xmldesign, "MovieSelection", {"name": config.plugins.MerlinSkinThemes.MovieSelection.value})
						
				if t.find("screens[@name='MoviePlayer']") is not None:
					ts = t.find("screens[@name='MoviePlayer']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MoviePlayer.value + "']") is not None:
						Tree.SubElement(xmldesign, "MoviePlayer", {"name": config.plugins.MerlinSkinThemes.MoviePlayer.value})
						
				if t.find("screens[@name='SecondInfoBar']") is not None:
					ts = t.find("screens[@name='SecondInfoBar']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.SecondInfoBar.value + "']") is not None:
						Tree.SubElement(xmldesign, "SecondInfoBar", {"name": config.plugins.MerlinSkinThemes.SecondInfoBar.value})

				if t.find("screens[@name='GraphMultiEPG']") is not None:
					ts = t.find("screens[@name='GraphMultiEPG']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.GraphMultiEPG.value + "']") is not None:
						Tree.SubElement(xmldesign, "GraphMultiEPG", {"name": config.plugins.MerlinSkinThemes.GraphMultiEPG.value})
						
				if t.find("screens[@name='EventView']") is not None:
					ts = t.find("screens[@name='EventView']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.EventView.value + "']") is not None:
						Tree.SubElement(xmldesign, "EventView", {"name": config.plugins.MerlinSkinThemes.EventView.value})
						
				if t.find("screens[@name='EPGSelection']") is not None:
					ts = t.find("screens[@name='EPGSelection']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.EPGSelection.value + "']") is not None:
						Tree.SubElement(xmldesign, "EPGSelection", {"name": config.plugins.MerlinSkinThemes.EPGSelection.value})
						
				if t.find("screens[@name='MessageBox']") is not None:
					ts = t.find("screens[@name='MessageBox']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MessageBox.value + "']") is not None:
						Tree.SubElement(xmldesign, "MessageBox", {"name": config.plugins.MerlinSkinThemes.MessageBox.value})
						
				if t.find("screens[@name='InputBox']") is not None:
					ts = t.find("screens[@name='InputBox']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.InputBox.value + "']") is not None:
						Tree.SubElement(xmldesign, "InputBox", {"name": config.plugins.MerlinSkinThemes.InputBox.value})
						
				if t.find("screens[@name='ChoiceBox']") is not None:
					ts = t.find("screens[@name='ChoiceBox']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.ChoiceBox.value + "']") is not None:
						Tree.SubElement(xmldesign, "ChoiceBox", {"name": config.plugins.MerlinSkinThemes.ChoiceBox.value})
						
				if t.find("screens[@name='Mute']") is not None:
					ts = t.find("screens[@name='Mute']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.Mute.value + "']") is not None:
						Tree.SubElement(xmldesign, "Mute", {"name": config.plugins.MerlinSkinThemes.Mute.value})
						
				if t.find("screens[@name='Volume']") is not None:
					ts = t.find("screens[@name='Volume']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.Volume.value + "']") is not None:
						Tree.SubElement(xmldesign, "Volume", {"name": config.plugins.MerlinSkinThemes.Volume.value})

				if t.find("screens[@name='MerlinMusicPlayer2Screen']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2Screen']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2Screen", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen.value})

				if t.find("screens[@name='MerlinMusicPlayer2Screen_MIPSEL']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2Screen_MIPSEL']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_MIPSEL.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2Screen_MIPSEL", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_MIPSEL.value})

				if t.find("screens[@name='MerlinMusicPlayer2Screen_ARM']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2Screen_ARM']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_ARM.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2Screen_ARM", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_ARM.value})

				if t.find("screens[@name='MerlinMusicPlayer2Screen_AARCH64']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2Screen_AARCH64']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_AARCH64.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2Screen_AARCH64", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_AARCH64.value})

				if t.find("screens[@name='MerlinMusicPlayer2ScreenSaver']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2ScreenSaver']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2ScreenSaver", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver.value})

				if t.find("screens[@name='MerlinMusicPlayer2ScreenSaver_MIPSEL']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2ScreenSaver_MIPSEL']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_MIPSEL.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2ScreenSaver_MIPSEL", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_MIPSEL.value})

				if t.find("screens[@name='MerlinMusicPlayer2ScreenSaver_ARM']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2ScreenSaver_ARM']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_ARM.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2ScreenSaver_ARM", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_ARM.value})

				if t.find("screens[@name='MerlinMusicPlayer2ScreenSaver_AARCH64']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2ScreenSaver_AARCH64']")
					if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_AARCH64.value + "']") is not None:
						Tree.SubElement(xmldesign, "MerlinMusicPlayer2ScreenSaver_AARCH64", {"name": config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_AARCH64.value})

			# LCD Screens
			if xmlroot.find("lcdscreenthemes") is not None:
				t = xmlroot.find("lcdscreenthemes")
				
				if t.find("screens[@name='InfoBarSummary']") is not None:
					ts = t.find("screens[@name='InfoBarSummary']")
					if ts.find("lcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.LCDInfoBar.value + "']") is not None:
						Tree.SubElement(xmldesign, "LCDInfoBar", {"name": config.plugins.MerlinSkinThemes.LCDInfoBar.value})

				if t.find("screens[@name='EventView_summary']") is not None:
					ts = t.find("screens[@name='EventView_summary']")
					if ts.find("lcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.LCDEventView.value + "']") is not None:
						Tree.SubElement(xmldesign, "LCDEventView", {"name": config.plugins.MerlinSkinThemes.LCDEventView.value})

				if t.find("screens[@name='StandbySummary']") is not None:
					ts = t.find("screens[@name='StandbySummary']")
					if ts.find("lcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.LCDStandby.value + "']") is not None:
						Tree.SubElement(xmldesign, "LCDStandby", {"name": config.plugins.MerlinSkinThemes.LCDStandby.value})

				if t.find("screens[@name='InfoBarMoviePlayerSummary']") is not None:
					ts = t.find("screens[@name='InfoBarMoviePlayerSummary']")
					if ts.find("lcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.LCDMoviePlayer.value + "']") is not None:
						Tree.SubElement(xmldesign, "LCDMoviePlayer", {"name": config.plugins.MerlinSkinThemes.LCDMoviePlayer.value})

				if t.find("screens[@name='MerlinMusicPlayer2LCDScreen']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2LCDScreen']")
					if ts.find("lcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.LCDMMP2.value + "']") is not None:
						Tree.SubElement(xmldesign, "LCDMMP2", {"name": config.plugins.MerlinSkinThemes.LCDMMP2.value})
						
			# OLED Screens
			if xmlroot.find("oledscreenthemes") is not None:
				t = xmlroot.find("oledscreenthemes")
				
				if t.find("screens[@name='InfoBarSummary']") is not None:
					ts = t.find("screens[@name='InfoBarSummary']")
					if ts.find("oledscreentheme[@name='" + config.plugins.MerlinSkinThemes.OLEDInfoBar.value + "']") is not None:
						Tree.SubElement(xmldesign, "OLEDInfoBar", {"name": config.plugins.MerlinSkinThemes.OLEDInfoBar.value})

				if t.find("screens[@name='EventView_summary']") is not None:
					ts = t.find("screens[@name='EventView_summary']")
					if ts.find("oledscreentheme[@name='" + config.plugins.MerlinSkinThemes.OLEDEventView.value + "']") is not None:
						Tree.SubElement(xmldesign, "OLEDEventView", {"name": config.plugins.MerlinSkinThemes.OLEDEventView.value})

				if t.find("screens[@name='StandbySummary']") is not None:
					ts = t.find("screens[@name='StandbySummary']")
					if ts.find("oledscreentheme[@name='" + config.plugins.MerlinSkinThemes.OLEDStandby.value + "']") is not None:
						Tree.SubElement(xmldesign, "OLEDStandby", {"name": config.plugins.MerlinSkinThemes.OLEDStandby.value})

				if t.find("screens[@name='InfoBarMoviePlayerSummary']") is not None:
					ts = t.find("screens[@name='InfoBarMoviePlayerSummary']")
					if ts.find("oledscreentheme[@name='" + config.plugins.MerlinSkinThemes.OLEDMoviePlayer.value + "']") is not None:
						Tree.SubElement(xmldesign, "OLEDMoviePlayer", {"name": config.plugins.MerlinSkinThemes.OLEDMoviePlayer.value})

				if t.find("screens[@name='MerlinMusicPlayer2LCDScreen']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2LCDScreen']")
					if ts.find("oledscreentheme[@name='" + config.plugins.MerlinSkinThemes.OLEDMMP2.value + "']") is not None:
						Tree.SubElement(xmldesign, "OLEDMMP2", {"name": config.plugins.MerlinSkinThemes.OLEDMMP2.value})
						
			# External LCD Screens
			if xmlroot.find("extlcdscreenthemes") is not None:
				t = xmlroot.find("extlcdscreenthemes")
				
				if t.find("screens[@name='InfoBarSummary']") is not None:
					ts = t.find("screens[@name='InfoBarSummary']")
					if ts.find("extlcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.ExtLCDInfoBar.value + "']") is not None:
						Tree.SubElement(xmldesign, "ExtLCDInfoBar", {"name": config.plugins.MerlinSkinThemes.ExtLCDInfoBar.value})

				if t.find("screens[@name='EventView_summary']") is not None:
					ts = t.find("screens[@name='EventView_summary']")
					if ts.find("extlcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.ExtLCDEventView.value + "']") is not None:
						Tree.SubElement(xmldesign, "ExtLCDEventView", {"name": config.plugins.MerlinSkinThemes.ExtLCDEventView.value})

				if t.find("screens[@name='StandbySummary']") is not None:
					ts = t.find("screens[@name='StandbySummary']")
					if ts.find("extlcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.ExtLCDStandby.value + "']") is not None:
						Tree.SubElement(xmldesign, "ExtLCDStandby", {"name": config.plugins.MerlinSkinThemes.ExtLCDStandby.value})

				if t.find("screens[@name='InfoBarMoviePlayerSummary']") is not None:
					ts = t.find("screens[@name='InfoBarMoviePlayerSummary']")
					if ts.find("extlcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.ExtLCDMoviePlayer.value + "']") is not None:
						Tree.SubElement(xmldesign, "ExtLCDMoviePlayer", {"name": config.plugins.MerlinSkinThemes.ExtLCDMoviePlayer.value})

				if t.find("screens[@name='MerlinMusicPlayer2LCDScreen']") is not None:
					ts = t.find("screens[@name='MerlinMusicPlayer2LCDScreen']")
					if ts.find("extlcdscreentheme[@name='" + config.plugins.MerlinSkinThemes.ExtLCDMMP2.value + "']") is not None:
						Tree.SubElement(xmldesign, "ExtLCDMMP2", {"name": config.plugins.MerlinSkinThemes.ExtLCDMMP2.value})


			# cornerRadius
			if xmlroot.find("cornerradius") is not None:
				if xmldesign.find("CornerRadius") is not None:
					td = xmldesign.find("CornerRadius")
					td.set("name", config.plugins.MerlinSkinThemes.CornerRadius.value)
				else:
					Tree.SubElement(xmldesign, "CornerRadius", {"name": config.plugins.MerlinSkinThemes.CornerRadius.value})
						
			self.XMLindent(xmlroot, 0)
			
			curTree.write(MerlinSkinThemes.selThemeFile)
				
			self.readThemes()
				
	def deleteDesign(self):
		if self.MSTDesigns.value == "-none-":
			self.session.open(MessageBox,_("nothing to delete"), MessageBox.TYPE_ERROR)
		else:
			curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
			xmlroot = curTree.getroot()
			designs = xmlroot.find("designs")
			for design in designs.findall("design"):
				if design.get("name") == config.plugins.MerlinSkinThemes.Design.value:
					designs.remove(design)
			
					self.XMLindent(xmlroot, 0)

					curTree.write(MerlinSkinThemes.selThemeFile)
		
					self.readThemes()
						
	def setDesign(self):
		curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
		xmlroot = curTree.getroot()
		designs = xmlroot.find("designs")
		for design in designs.findall("design"):
			if design.get("name") == config.plugins.MerlinSkinThemes.Design.value:
				if design.find("ColorTheme") is not None:
					tmp = design.find("ColorTheme")
					try:
						self.TColor.setValue(tmp.get("name"))
					except:
						print "[MST] TColor not found"
					
				if design.find("SkinPathTheme") is not None:
					tmp = design.find("SkinPathTheme")
					try:
						self.SPath.setValue(tmp.get("name"))
					except:
						print "[MST] SPath not found"

				if design.find("FontTheme") is not None:
					tmp = design.find("FontTheme")
					try:
						self.TFont.setValue(tmp.get("name"))
					except:
						print "[MST] TFont not found"

				if design.find("BorderSetTheme") is not None:
					tmp = design.find("BorderSetTheme")
					try:
						self.TBorder.setValue(tmp.get("name"))
					except:
						print "[MST] TBorder not found"
					
				if design.find("WindowStyleScrollbarTheme") is not None:
					tmp = design.find("WindowStyleScrollbarTheme")
					#print "[MST] TScroll: %s" % self["config"].getCurrent()[1].getChoices()
					#print "[MST] TScroll: %s" % self["config"].getCurrent()[0]
					#print "[MST] TScroll len: %s" % len(self["config"].getCurrent()[1].getChoices())

					#print "[MST] BEVOR"
					#print "[MST] TScroll: %s" % self.TScroll.getChoices()
					#print "[MST] TScroll default: %s" % tmp.get("name")
					#print "[MST] TScroll index: %s" % self.TScroll.getChoices().index(tmp.get("name"))
					#print "[MST] TScroll len: %s" % len(self.TScroll.getChoices())
					
					try:
						self.TScroll.setValue(tmp.get("name"))
					except:
						print "[MST] TScroll not found"
					
				if design.find("ComponentTheme") is not None:
					tmp = design.find("ComponentTheme")
					try:
						self.TComponent.setValue(tmp.get("name"))
					except:
						print "[MST] TComponent not found"
					
				if design.find("PNGTheme") is not None:
					tmp = design.find("PNGTheme")
					try:
						self.TPNG.setValue(tmp.get("name"))
					except:
						print "[MST] TPNG not found"
				
				# Screens
				if design.find("InfoBar") is not None:
					tmp = design.find("InfoBar")
					try:
						self.SInfobar.setValue(tmp.get("name"))
					except:
						print "[MST] SInfobar not found"

				if design.find("Menu") is not None:
					tmp = design.find("Menu")
					try:
						self.SMenu.setValue(tmp.get("name"))
					except:
						print "[MST] SMenu not found"

				if design.find("PluginBrowser") is not None:
					tmp = design.find("PluginBrowser")
					try:
						self.SPluginBrowser.setValue(tmp.get("name"))
					except:
						print "[MST] SPluginBrowser not found"
					
				if design.find("ChannelSelection") is not None:
					tmp = design.find("ChannelSelection")
					try:
						self.SChannelSel.setValue(tmp.get("name"))
					except:
						print "[MST] SChannelSel not found"
					
				if design.find("MovieSelection") is not None:
					tmp = design.find("MovieSelection")
					try:
						self.SMovieSel.setValue(tmp.get("name"))
					except:
						print "[MST] SMovieSel not found"
					
				if design.find("MoviePlayer") is not None:
					tmp = design.find("MoviePlayer")
					try:
						self.SMoviePlay.setValue(tmp.get("name"))
					except:
						print "[MST] SMoviePlayer not found"
					
				if design.find("SecondInfoBar") is not None:
					tmp = design.find("SecondInfoBar")
					try:
						self.S2IB.setValue(tmp.get("name"))
					except:
						print "[MST] S2IB not found"
					
				if design.find("GraphMultiEPG") is not None:
					tmp = design.find("GraphMultiEPG")
					try:
						self.graphmultiepg.setValue(tmp.get("name"))
					except:
						print "[MST] GMEPG not found"
					
				if design.find("EventView") is not None:
					tmp = design.find("EventView")
					try:
						self.EventView.setValue(tmp.get("name"))
					except:
						print "[MST] EventView not found"
					
				if design.find("EPGSelection") is not None:
					tmp = design.find("EPGSelection")
					try:
						self.EPGSelection.setValue(tmp.get("name"))
					except:
						print "[MST] EPGSelection not found"
					
				if design.find("MessageBox") is not None:
					tmp = design.find("MessageBox")
					try:
						self.SMsgBox.setValue(tmp.get("name"))
					except:
						print "[MST] SMsgBox not found"
					
				if design.find("InputBox") is not None:
					tmp = design.find("InputBox")
					try:
						self.SInBox.setValue(tmp.get("name"))
					except:
						print "[MST] SInBox not found"
					
				if design.find("ChoiceBox") is not None:
					tmp = design.find("ChoiceBox")
					try:
						self.SChoiceBox.setValue(tmp.get("name"))
					except:
						print "[MST] SChoiceBox not found"

				if design.find("Mute") is not None:
					tmp = design.find("Mute")
					try:
						self.SMute.setValue(tmp.get("name"))
					except:
						print "[MST] SMute not found"

				if design.find("Volume") is not None:
					tmp = design.find("Volume")
					try:
						self.SVolume.setValue(tmp.get("name"))
					except:
						print "[MST] SVolume not found"

				if design.find("MerlinMusicPlayer2Screen") is not None:
					tmp = design.find("MerlinMusicPlayer2Screen")
					try:
						self.SMMP2.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2 not found"

				if design.find("MerlinMusicPlayer2Screen_MIPSEL") is not None:
					tmp = design.find("MerlinMusicPlayer2Screen_MIPSEL")
					try:
						self.SMMP2Mipsel.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2Mipsel not found"

				if design.find("MerlinMusicPlayer2Screen_ARM") is not None:
					tmp = design.find("MerlinMusicPlayer2Screen_ARM")
					try:
						self.SMMP2Arm.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2Arm not found"

				if design.find("MerlinMusicPlayer2Screen_AARCH64") is not None:
					tmp = design.find("MerlinMusicPlayer2Screen_AARCH64")
					try:
						self.SMMP2Arch64.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2Arch64 not found"

				if design.find("MerlinMusicPlayer2ScreenSaver") is not None:
					tmp = design.find("MerlinMusicPlayer2ScreenSaver")
					try:
						self.SMMP2Saver.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2Saver not found"

				if design.find("MerlinMusicPlayer2ScreenSaver_MIPSEL") is not None:
					tmp = design.find("MerlinMusicPlayer2ScreenSaver_MIPSEL")
					try:
						self.SMMP2SaverMipsel.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2SaverMipsel not found"

				if design.find("MerlinMusicPlayer2ScreenSaver_ARM") is not None:
					tmp = design.find("MerlinMusicPlayer2ScreenSaver_ARM")
					try:
						self.SMMP2SaverArm.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2SaverArm not found"

				if design.find("MerlinMusicPlayer2ScreenSaver_AARCH64") is not None:
					tmp = design.find("MerlinMusicPlayer2ScreenSaver_AARCH64")
					try:
						self.SMMP2SaverArch64.setValue(tmp.get("name"))
					except:
						print "[MST] SMMP2SaverArch64 not found"

				# LCD
				if design.find("LCDInfoBar") is not None:
					tmp = design.find("LCDInfoBar")
					try:
						self.LSInfobar.setValue(tmp.get("name"))
					except:
						print "[MST] LSInfobar not found"
					
				if design.find("LCDEventView") is not None:
					tmp = design.find("LCDEventView")
					try:
						self.LSEventView.setValue(tmp.get("name"))
					except:
						print "[MST] LSEventView not found"
					
				if design.find("LCDStandby") is not None:
					tmp = design.find("LCDStandby")
					try:
						self.LSStandby.setValue(tmp.get("name"))
					except:
						print "[MST] LSStandby not found"
					
				if design.find("LCDMoviePlayer") is not None:
					tmp = design.find("LCDMoviePlayer")
					try:
						self.LSMoviePlayer.setValue(tmp.get("name"))
					except:
						print "[MST] LSMoviePlayer not found"
					
				if design.find("LCDMMP2") is not None:
					tmp = design.find("LCDMMP2")
					try:
						self.LSMMP2.setValue(tmp.get("name"))
					except:
						print "[MST] LSMMP2 not found"
					
				# OLED
				if design.find("OLEDInfoBar") is not None:
					tmp = design.find("OLEDInfoBar")
					try:
						self.OSInfobar.setValue(tmp.get("name"))
					except:
						print "[MST] OSInfobar not found"
					
				if design.find("OLEDEventView") is not None:
					tmp = design.find("OLEDEventView")
					try:
						self.OSEventView.setValue(tmp.get("name"))
					except:
						print "[MST] OSEventView not found"
					
				if design.find("OLEDStandby") is not None:
					tmp = design.find("OLEDStandby")
					try:
						self.OSStandby.setValue(tmp.get("name"))
					except:
						print "[MST] OSStandby not found"
					
				if design.find("OLEDMoviePlayer") is not None:
					tmp = design.find("OLEDMoviePlayer")
					try:
						self.OSMoviePlayer.setValue(tmp.get("name"))
					except:
						print "[MST] OSMoviePlayer not found"
					
				if design.find("OLEDMMP2") is not None:
					tmp = design.find("OLEDMMP2")
					try:
						self.OSMMP2.setValue(tmp.get("name"))
					except:
						print "[MST] OSMMP2 not found"
					
				# External LCD
				if design.find("ExtLCDInfoBar") is not None:
					tmp = design.find("ExtLCDInfoBar")
					try:
						self.ExtLSInfobar.setValue(tmp.get("name"))
					except:
						print "[MST] ExtLSInfobar not found"
					
				if design.find("ExtLCDEventView") is not None:
					tmp = design.find("ExtLCDEventView")
					try:
						self.ExtLSEventView.setValue(tmp.get("name"))
					except:
						print "[MST] ExtLSEventView not found"
					
				if design.find("ExtLCDStandby") is not None:
					tmp = design.find("ExtLCDStandby")
					try:
						self.ExtLSStandby.setValue(tmp.get("name"))
					except:
						print "[MST] ExtLSStandby not found"
					
				if design.find("ExtLCDMoviePlayer") is not None:
					tmp = design.find("ExtLCDMoviePlayer")
					try:
						self.ExtLSMoviePlayer.setValue(tmp.get("name"))
					except:
						print "[MST] ExtLSMoviePlayer not found"
					
				if design.find("ExtLCDMMP2") is not None:
					tmp = design.find("ExtLCDMMP2")
					try:
						self.ExtLSMMP2.setValue(tmp.get("name"))
					except:
						print "[MST] ExtLSMMP2 not found"
					
				# refresh Screen
				self["config"].setList(self.clist)
				#self["config"].hide()
				#self["config"].show()
			
				if design.find("CornerRadius") is not None:
					tmp = design.find("CornerRadius")
					try:
						self.CornerRadius.setValue(tmp.get("name"))
					except:
						print "[MST] CornerRadius not found"
						
	def ok(self):
		if self.curList == "SkinsList":
			if self["SkinsList"].getCurrent()[3][7] == "":
				self.curList = "ConfigList"
				
				if not SkinUser:
					self["ListLabel"].setText(_("Configlist") )
				else:
					self["ListLabel"].setText(_("Configlist") + " - ATTENTION: skin_user.xml found!!!")

				if fileExists(MerlinSkinThemes.selSkinFile):
					self.CopyrightInfo()
					
				self.readThemes()

				if self["config"].getCurrent()[0] == "Design":
					self["key_green"].setText(_("apply themes"))
					self["key_yellow"].setText(_("delete design"))
				elif self["config"].getCurrent()[0] == "Skin":
					self["key_green"].setText(_("apply themes"))
					self["key_yellow"].setText(_("save as design"))
				else:
					self["key_green"].setText(_("apply themes"))
					self["key_yellow"].setText(_("save as design"))
				
				self["key_green"].show()
				self["key_yellow"].show()
				
				self["SkinsList"].hide()
				self["config"].show()
				
				config.plugins.MerlinSkinThemes.Skin.value = self["SkinsList"].getCurrent()[1][7]
				
			else:
				self.CopyrightInfo()
				self.session.open(MessageBox,_("No themes.xml or skin.xml found.\nPlease select a valid skin including themes.xml"), MessageBox.TYPE_ERROR, title=_("Error"))
				
		else:
			self.curList = "SkinsList"
			
			if not SkinUser:
				self["ListLabel"].setText(_("Skinlist") )
			else:
				self["ListLabel"].setText(_("Skinlist") + " - ATTENTION: skin_user.xml found!!!")
 			
			self["SkinCopyright"].setText("")
			
			self["key_green"].setText(_("switch to skin"))
			self["key_green"].hide()
			self["key_yellow"].setText(_(""))
			self["key_yellow"].hide()

			#t1 = time.time()
			self.updateSkinList()
			#t2 = time.time()
			#print "[MST] updateSkinList: ", t2 - t1
		
			self["SkinsList"].show()
			self["config"].hide()

			if fileExists(MerlinSkinThemes.selSkinFile):
				self.CopyrightInfo()
			
	def up(self):
		if self.curList == "SkinsList":
			self[self.curList].up()

			if fileExists(MerlinSkinThemes.selSkinFile):
				self.CopyrightInfo()
			
		else:
			self["config"].instance.moveSelection(self["config"].instance.moveUp)
			if self["config"].getCurrent()[0] == "Design":
				self["key_green"].setText(_("apply themes"))
				self["key_yellow"].setText(_("delete design"))
			elif self["config"].getCurrent()[0] == "Skin":
				self["key_green"].setText(_("apply themes"))
				self["key_yellow"].setText(_("save as design"))
			else:
				self["key_green"].setText(_("apply themes"))
				self["key_yellow"].setText(_("save as design"))
	
	def down(self):
		if self.curList == "SkinsList":
			self[self.curList].down()

			if fileExists(MerlinSkinThemes.selSkinFile):
				self.CopyrightInfo()
			
		else:
			self["config"].instance.moveSelection(self["config"].instance.moveDown)
			if self["config"].getCurrent()[0] == "Design":
				self["key_green"].setText(_("apply themes"))
				self["key_yellow"].setText(_("delete design"))
			elif self["config"].getCurrent()[0] == "Skin":
				self["key_green"].setText(_("apply themes"))
				self["key_yellow"].setText(_("save as design"))
			else:
				self["key_green"].setText(_("apply themes"))
				self["key_yellow"].setText(_("save as design"))
	
	def left(self):
		if self.curList == "SkinsList":
			self[self.curList].pageUp()
		else:
			ConfigListScreen.keyLeft(self)

			if self["config"].getCurrent()[0] in myList:
				# PreviewPNG anzeigen
				pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + self["config"].getCurrent()[0] + "/" + self["config"].getCurrent()[1].value + ".png"

				if not fileExists(pngpath):
					pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

				self["Preview"].instance.setPixmapFromFile(pngpath)
				self["Preview"].show()

			if self["config"].getCurrent()[0] == "Design":
				if config.plugins.MerlinSkinThemes.Design.value == "-none-":
					self.readThemes()
				else:
					# PreviewPNG anzeigen
					pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + config.plugins.MerlinSkinThemes.Design.value + ".png"

					if not fileExists(pngpath):
						pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

					self["Preview"].instance.setPixmapFromFile(pngpath)
					self["Preview"].show()
					
					self.setDesign()
	
	def right(self):
		if self.curList == "SkinsList":
			self[self.curList].pageDown()
		else:
			ConfigListScreen.keyRight(self)

			if self["config"].getCurrent()[0] in myList:
				# PreviewPNG anzeigen
				pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + self["config"].getCurrent()[0] + "/" + self["config"].getCurrent()[1].value + ".png"

				if not fileExists(pngpath):
					pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

				self["Preview"].instance.setPixmapFromFile(pngpath)
				self["Preview"].show()

			if self["config"].getCurrent()[0] == "Design":
				if config.plugins.MerlinSkinThemes.Design.value == "-none-":
					self.readThemes()
				else:
					# PreviewPNG anzeigen
					pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + config.plugins.MerlinSkinThemes.Design.value + ".png"

					if not fileExists(pngpath):
						pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

					self["Preview"].instance.setPixmapFromFile(pngpath)
					self["Preview"].show()

					self.setDesign()
	
	def changedSkinsList(self):
		self["SkinCopyright"].setText("")
		
		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		#if fileExists(MerlinSkinThemes.selSkinFile):
		#	self.CopyrightInfo()
			
		if config.plugins.MerlinSkinThemes.ShowPrevPNG.value == "1":
			self.loadPreview()
		
		if self["SkinsList"].getCurrent()[2][7] == "active skin":
			self["key_green"].hide()
		else:
			self["key_green"].show()

		if self["SkinsList"].getCurrent()[3][7] == "no skin.xml":
			self["key_green"].hide()

			self["key_yellow"].show()
			self["key_yellow"].setText(_("delete"))
			
		elif self["SkinsList"].getCurrent()[3][7] == "no themes.xml":
			self["key_green"].show()
			
			self["key_yellow"].show()
			self["key_yellow"].setText(_("create themes"))
			
		else:
			self["key_yellow"].show()

			self["key_yellow"].hide()
			#self.readThemes()
			
	def updateSkinList(self):
		self["SkinsList"].buildList()

	def setThemes(self):
		# set all "inactive", set new theme "active"
		curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
		rootTheme = curTree.getroot()

		curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
		rootSkin = curSkin.getroot()
		
		if rootTheme.find("colortheme") is not None:
			for theme in rootTheme.findall("colortheme"):
				if theme.get("name") == config.plugins.MerlinSkinThemes.ColorTheme.value:
					theme.set("value", "active")

					# colors
					SkinColors = rootSkin.find("colors")

					# delete old colors
					for color in SkinColors.findall("color"):
						SkinColors.remove(color)
					
					# Set new colors
					ThemeColors = theme.find("colors")
					
					for color in ThemeColors.findall("color"):
						name = color.get("name")
						value = color.get("value")
						
						Tree.SubElement(SkinColors, "color", {"name": name, "value": value})
					
				else:
					theme.set("value", "inactive")

		if rootTheme.find("fonttheme") is not None:
			for theme in rootTheme.findall("fonttheme"):
				if theme.get("name") == config.plugins.MerlinSkinThemes.FontTheme.value:
					theme.set("value", "active")

					# fonts
					SkinFonts = rootSkin.find("fonts")

					# delete old fonts
					for font in SkinFonts.findall("font"):
						SkinFonts.remove(font)
					
					# Set new fonts
					ThemeFonts = theme.find("fonts")
					
					for font in ThemeFonts.findall("font"):
						filename = font.get("filename")
						name = font.get("name")
						scale = font.get("scale", "100")
						replacement = font.get("replacement", "0")
						
						Tree.SubElement(SkinFonts, "font", {"filename": filename, "name": name, "scale": scale, "replacement": replacement})
						

				else:
					theme.set("value", "inactive")

		if rootTheme.find("bordersettheme") is not None:
			for theme in rootTheme.findall("bordersettheme"):
				if theme.get("name") == config.plugins.MerlinSkinThemes.BorderSetTheme.value:
					theme.set("value", "active")

					# WindowStyle
					for ws in rootSkin.findall("windowstyle"):
						if ws.get("id") == "0":
							for bs in ws.findall("borderset"):
								if bs.get("name") == "bsWindow":
									for px in bs.findall("pixmap"):
										bs.remove(px)
										
									for tbs in theme.findall("borderset"):
										if tbs.get("name") == "bsWindow":
											for tpx in tbs.findall("pixmap"):
												bs.append(Tree.fromstring(Tree.tostring(tpx)))

								if bs.get("name") == "bsListboxEntry":
									for px in bs.findall("pixmap"):
										bs.remove(px)
						
									for tbs in theme.findall("borderset"):
										if tbs.get("name") == "bsListboxEntry":
											for tpx in tbs.findall("pixmap"):
												bs.append(Tree.fromstring(Tree.tostring(tpx)))
						else:
							print "[MST] id not found in windowstyle"
						
				else:
					theme.set("value", "inactive")
					
		if rootTheme.find("windowstylescrollbartheme") is not None:
			for theme in rootTheme.findall("windowstylescrollbartheme"):
				if theme.get("name") == config.plugins.MerlinSkinThemes.WindowStyleScrollbarTheme.value:
					theme.set("value", "active")

					# WindowStyleScrollbar
					for wssb in rootSkin.findall("windowstylescrollbar"):
						if wssb.get("id") == "4":
							for all in wssb.findall("*"):
								wssb.remove(all)
										
							for tall in theme.findall("*"):
								wssb.append(Tree.fromstring(Tree.tostring(tall)))

				else:
					theme.set("value", "inactive")
					
		if rootTheme.find("componenttheme") is not None:
			for theme in rootTheme.findall("componenttheme"):
				if theme.get("name") == config.plugins.MerlinSkinThemes.ComponentTheme.value:
					theme.set("value", "active")
					components = theme.find("components")
					
					# components
					SkinComponents = rootSkin.find("components")

					# delete old components
					#for component in SkinComponents.findall("component"):
					#	SkinComponents.remove(component)
					rootSkin.remove(SkinComponents)

					# Set new components
					rootSkin.append(Tree.fromstring(Tree.tostring(components)))
					
				else:
					theme.set("value", "inactive")

		if rootTheme.find("pngtheme") is not None and ImgCreate:
			for theme in rootTheme.findall("pngtheme"):
				if theme.get("name") == config.plugins.MerlinSkinThemes.PNGTheme.value:
					theme.set("value", "active")

					# png
					for tp in theme.findall("png"):
						png_name = tp.get("name")
						png_width = int(tp.get("width"))
						png_height = int(tp.get("height"))
						png_argb = tp.get("argb")
						#print "[MST] argb: %s" % str(png_argb)
						acolor = self.hex2argb(png_argb)
						#print "[MST] argb: %s" % str(acolor)
						
						if png_name is not None and png_width is not None and png_height is not None and png_argb is not None:
							imageCreater.createRectangle(png_width, png_height, (acolor[1], acolor[2], acolor[3], acolor[0]), resolveFilename(SCOPE_SKIN) + SkinName + "/" + png_name) 
				else:
					theme.set("value", "inactive")

		if rootTheme.find("screenthemes") is not None:
			themes = rootTheme.find("screenthemes")
			for screens in themes.findall("screens"):
				if screens.get("name") == "InfoBar":
					for infobar in screens.findall("screentheme"):
						if infobar.get("name") == config.plugins.MerlinSkinThemes.InfoBar.value:
							infobar.set("value", "active")
							ib = infobar.find("screen")

							# delete old InfoBar screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InfoBar":
									rootSkin.remove(SkinScreen)
							
							# Set new InfoBar screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							infobar.set("value", "inactive")

				if screens.get("name") == "Menu":
					for menu in screens.findall("screentheme"):
						if menu.get("name") == config.plugins.MerlinSkinThemes.Menu.value:
							menu.set("value", "active")
							mu = menu.find("screen")

							# delete old Menu screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "Menu":
									rootSkin.remove(SkinScreen)
							
							# Set new Menu screen
							rootSkin.append(Tree.fromstring(Tree.tostring(mu)))
								
						else:
							menu.set("value", "inactive")

				if screens.get("name") == "PluginBrowser":
					for pluginbrowser in screens.findall("screentheme"):
						if pluginbrowser.get("name") == config.plugins.MerlinSkinThemes.PluginBrowser.value:
							pluginbrowser.set("value", "active")
							pb = pluginbrowser.find("screen")

							# delete old Pluginbrowser screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "PluginBrowser":
									rootSkin.remove(SkinScreen)
							
							# Set new Pluginbrowser screen
							rootSkin.append(Tree.fromstring(Tree.tostring(pb)))
								
						else:
							pluginbrowser.set("value", "inactive")
				
				if screens.get("name") == "ChannelSelection":
					for channelselection in screens.findall("screentheme"):
						if channelselection.get("name") == config.plugins.MerlinSkinThemes.ChannelSelection.value:
							channelselection.set("value", "active")
							cs = channelselection.find("screen")

							# delete old ChannelSelection screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "ChannelSelection":
									rootSkin.remove(SkinScreen)
							
							# Set new ChannelSelection screen
							rootSkin.append(Tree.fromstring(Tree.tostring(cs)))
							
						else:
							channelselection.set("value", "inactive")
				
				if screens.get("name") == "MovieSelection":
					for movieselection in screens.findall("screentheme"):
						if movieselection.get("name") == config.plugins.MerlinSkinThemes.MovieSelection.value:
							movieselection.set("value", "active")
							ms = movieselection.find("screen")

							# delete old MovieSelection screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MovieSelection":
									rootSkin.remove(SkinScreen)
							
							# Set new MovieSelection screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ms)))
								
						else:
							movieselection.set("value", "inactive")
				
				if screens.get("name") == "MoviePlayer":
					for movieplayer in screens.findall("screentheme"):
						if movieplayer.get("name") == config.plugins.MerlinSkinThemes.MoviePlayer.value:
							movieplayer.set("value", "active")
							ms = movieplayer.find("screen")

							# delete old MoviePlayer screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MoviePlayer":
									rootSkin.remove(SkinScreen)
							
							# Set new MoviePlayer screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ms)))
								
						else:
							movieplayer.set("value", "inactive")
				
				if screens.get("name") == "SecondInfoBar":
					for secondinfobar in screens.findall("screentheme"):
						if secondinfobar.get("name") == config.plugins.MerlinSkinThemes.SecondInfoBar.value:
							secondinfobar.set("value", "active")
							sib = secondinfobar.find("screen")

							# delete old SecondInfoBar screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "SecondInfoBar":
									rootSkin.remove(SkinScreen)
							
							# Set new SecondInfoBar screen
							rootSkin.append(Tree.fromstring(Tree.tostring(sib)))
								
						else:
							secondinfobar.set("value", "inactive")
				
				if screens.get("name") == "GraphMultiEPG":
					for graphmultiepg in screens.findall("screentheme"):
						if graphmultiepg.get("name") == config.plugins.MerlinSkinThemes.GraphMultiEPG.value:
							graphmultiepg.set("value", "active")
							gmepg = graphmultiepg.find("screen")

							# delete old GraphMultiEPG screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "GraphMultiEPG":
									rootSkin.remove(SkinScreen)
							
							# Set new GraphMultiEPG screen
							rootSkin.append(Tree.fromstring(Tree.tostring(gmepg)))
								
						else:
							graphmultiepg.set("value", "inactive")
				
				if screens.get("name") == "EventView":
					for eventview in screens.findall("screentheme"):
						if eventview.get("name") == config.plugins.MerlinSkinThemes.EventView.value:
							eventview.set("value", "active")
							sib = eventview.find("screen")

							# delete old EventView screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "EventView":
									rootSkin.remove(SkinScreen)
							
							# Set new EventView screen
							rootSkin.append(Tree.fromstring(Tree.tostring(sib)))
								
						else:
							eventview.set("value", "inactive")
				
				if screens.get("name") == "EPGSelection":
					for epgselection in screens.findall("screentheme"):
						if epgselection.get("name") == config.plugins.MerlinSkinThemes.EPGSelection.value:
							epgselection.set("value", "active")
							sib = epgselection.find("screen")

							# delete old EPGSelection screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "EPGSelection":
									rootSkin.remove(SkinScreen)
							
							# Set new EPGSelection screen
							rootSkin.append(Tree.fromstring(Tree.tostring(sib)))
								
						else:
							epgselection.set("value", "inactive")
				
				if screens.get("name") == "MessageBox":
					for messagebox in screens.findall("screentheme"):
						if messagebox.get("name") == config.plugins.MerlinSkinThemes.MessageBox.value:
							messagebox.set("value", "active")
							mb = messagebox.find("screen")

							# delete old MessageBox screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MessageBox":
									rootSkin.remove(SkinScreen)
							
							# Set new MessageBox screen
							rootSkin.append(Tree.fromstring(Tree.tostring(mb)))
								
						else:
							messagebox.set("value", "inactive")
				
				if screens.get("name") == "InputBox":
					for inputbox in screens.findall("screentheme"):
						if inputbox.get("name") == config.plugins.MerlinSkinThemes.InputBox.value:
							inputbox.set("value", "active")
							ib = inputbox.find("screen")

							# delete old InputBox screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InputBox":
									rootSkin.remove(SkinScreen)
							
							# Set new InputBox screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							inputbox.set("value", "inactive")
				
				if screens.get("name") == "ChoiceBox":
					for choicebox in screens.findall("screentheme"):
						if choicebox.get("name") == config.plugins.MerlinSkinThemes.ChoiceBox.value:
							choicebox.set("value", "active")
							ib = choicebox.find("screen")

							# delete old ChoiceBox screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "ChoiceBox":
									rootSkin.remove(SkinScreen)
							
							# Set new ChoiceBox screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							choicebox.set("value", "inactive")
				
				if screens.get("name") == "Mute":
					for mute in screens.findall("screentheme"):
						if mute.get("name") == config.plugins.MerlinSkinThemes.Mute.value:
							mute.set("value", "active")
							ib = mute.find("screen")

							# delete old Mute screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "Mute":
									rootSkin.remove(SkinScreen)
							
							# Set new Mute screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mute.set("value", "inactive")
				
				if screens.get("name") == "Volume":
					for volume in screens.findall("screentheme"):
						if volume.get("name") == config.plugins.MerlinSkinThemes.Volume.value:
							volume.set("value", "active")
							ib = volume.find("screen")

							# delete old Volume screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "Volume":
									rootSkin.remove(SkinScreen)
							
							# Set new Volume screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							volume.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2Screen":
					for mmp2 in screens.findall("screentheme"):
						if mmp2.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen.value:
							mmp2.set("value", "active")
							ib = mmp2.find("screen")

							# delete old MerlinMusicPlayer2Screen screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2Screen":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2Screen screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2Screen_MIPSEL":
					for mmp2mipsel in screens.findall("screentheme"):
						if mmp2mipsel.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_MIPSEL.value:
							mmp2mipsel.set("value", "active")
							ib = mmp2mipsel.find("screen")

							# delete old MerlinMusicPlayer2Screen_MIPSEL screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2Screen_MIPSEL":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2Screen_MIPSEL screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2mipsel.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2Screen_ARM":
					for mmp2arm in screens.findall("screentheme"):
						if mmp2arm.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_ARM.value:
							mmp2arm.set("value", "active")
							ib = mmp2arm.find("screen")

							# delete old MerlinMusicPlayer2Screen_ARM screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2Screen_ARM":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2Screen_ARM screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2arm.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2Screen_AARCH64":
					for mmp2arch64 in screens.findall("screentheme"):
						if mmp2arch64.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2Screen_AARCH64.value:
							mmp2arch64.set("value", "active")
							ib = mmp2arch64.find("screen")

							# delete old MerlinMusicPlayer2Screen_AARCH64 screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2Screen_AARCH64":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2Screen_AARCH64 screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2arch64.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2ScreenSaver":
					for mmp2saver in screens.findall("screentheme"):
						if mmp2saver.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver.value:
							mmp2saver.set("value", "active")
							ib = mmp2saver.find("screen")

							# delete old MerlinMusicPlayer2ScreenSaver screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2ScreenSaver screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2saver.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2ScreenSaver_MIPSEL":
					for mmp2savermipsel in screens.findall("screentheme"):
						if mmp2savermipsel.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_MIPSEL.value:
							mmp2savermipsel.set("value", "active")
							ib = mmp2savermipsel.find("screen")

							# delete old MerlinMusicPlayer2ScreenSaver_MIPSEL screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver_MIPSEL":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2ScreenSaver_MIPSEL screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2savermipsel.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2ScreenSaver_ARM":
					for mmp2saverarm in screens.findall("screentheme"):
						if mmp2saverarm.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_ARM.value:
							mmp2saverarm.set("value", "active")
							ib = mmp2saverarm.find("screen")

							# delete old MerlinMusicPlayer2ScreenSaver_ARM screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver_ARM":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2ScreenSaver_ARM screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2saverarm.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2ScreenSaver_AARCH64":
					for mmp2saverarch64 in screens.findall("screentheme"):
						if mmp2saverarch64.get("name") == config.plugins.MerlinSkinThemes.MerlinMusicPlayer2ScreenSaver_AARCH64.value:
							mmp2saverarch64.set("value", "active")
							ib = mmp2saverarch64.find("screen")

							# delete old MerlinMusicPlayer2ScreenSaver_AARCH64 screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver_AARCH64":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2ScreenSaver_AARCH64 screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							mmp2saverarch64.set("value", "inactive")

		# LCD
		if rootTheme.find("lcdscreenthemes") is not None:
			themes = rootTheme.find("lcdscreenthemes")
			for screens in themes.findall("screens"):
				if screens.get("name") == "InfoBarSummary":
					for linfobar in screens.findall("lcdscreentheme"):
						if linfobar.get("name") == config.plugins.MerlinSkinThemes.LCDInfoBar.value:
							linfobar.set("value", "active")
							ib = linfobar.find("screen")

							# delete old InfoBarSummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InfoBarSummary" and SkinScreen.get("id") == "1":
									rootSkin.remove(SkinScreen)
							
							# Set new InfoBarSummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							linfobar.set("value", "inactive")

				if screens.get("name") == "EventView_summary":
					for leventview in screens.findall("lcdscreentheme"):
						if leventview.get("name") == config.plugins.MerlinSkinThemes.LCDEventView.value:
							leventview.set("value", "active")
							ib = leventview.find("screen")

							# delete old EventView_summary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "EventView_summary" and SkinScreen.get("id") == "1":
									rootSkin.remove(SkinScreen)
							
							# Set new EventView_summary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							leventview.set("value", "inactive")
							
				if screens.get("name") == "StandbySummary":
					for lstandby in screens.findall("lcdscreentheme"):
						if lstandby.get("name") == config.plugins.MerlinSkinThemes.LCDStandby.value:
							lstandby.set("value", "active")
							ib = lstandby.find("screen")

							# delete old StandbySummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "StandbySummary" and SkinScreen.get("id") == "1":
									rootSkin.remove(SkinScreen)
							
							# Set new StandbySummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							lstandby.set("value", "inactive")
							
				if screens.get("name") == "InfoBarMoviePlayerSummary":
					for lmovieplayer in screens.findall("lcdscreentheme"):
						if lmovieplayer.get("name") == config.plugins.MerlinSkinThemes.LCDMoviePlayer.value:
							lmovieplayer.set("value", "active")
							ib = lmovieplayer.find("screen")

							# delete old InfoBarMoviePlayerSummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InfoBarMoviePlayerSummary" and SkinScreen.get("id") == "1":
									rootSkin.remove(SkinScreen)
							
							# Set new InfoBarMoviePlayerSummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							lmovieplayer.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2LCDScreen":
					for lmmp2 in screens.findall("lcdscreentheme"):
						if lmmp2.get("name") == config.plugins.MerlinSkinThemes.LCDMMP2.value:
							lmmp2.set("value", "active")
							ib = lmmp2.find("screen")

							# delete old MerlinMusicPlayer2LCDScreen screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2LCDScreen" and SkinScreen.get("id") == "1":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2LCDScreen screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							lmmp2.set("value", "inactive")

		# OLED
		if rootTheme.find("oledscreenthemes") is not None:
			themes = rootTheme.find("oledscreenthemes")
			for screens in themes.findall("screens"):
				if screens.get("name") == "InfoBarSummary":
					for oinfobar in screens.findall("oledscreentheme"):
						if oinfobar.get("name") == config.plugins.MerlinSkinThemes.OLEDInfoBar.value:
							oinfobar.set("value", "active")
							ib = oinfobar.find("screen")

							# delete old InfoBarSummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InfoBarSummary" and SkinScreen.get("id") == "2":
									rootSkin.remove(SkinScreen)
							
							# Set new InfoBarSummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							oinfobar.set("value", "inactive")

				if screens.get("name") == "EventView_summary":
					for oeventview in screens.findall("oledscreentheme"):
						if oeventview.get("name") == config.plugins.MerlinSkinThemes.OLEDEventView.value:
							oeventview.set("value", "active")
							ib = oeventview.find("screen")

							# delete old EventView_summary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "EventView_summary" and SkinScreen.get("id") == "2":
									rootSkin.remove(SkinScreen)
							
							# Set new EventView_summary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							oeventview.set("value", "inactive")
							
				if screens.get("name") == "StandbySummary":
					for ostandby in screens.findall("oledscreentheme"):
						if ostandby.get("name") == config.plugins.MerlinSkinThemes.OLEDStandby.value:
							ostandby.set("value", "active")
							ib = ostandby.find("screen")

							# delete old StandbySummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "StandbySummary" and SkinScreen.get("id") == "2":
									rootSkin.remove(SkinScreen)
							
							# Set new StandbySummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							ostandby.set("value", "inactive")

				if screens.get("name") == "InfoBarMoviePlayerSummary":
					for omovieplayer in screens.findall("oledscreentheme"):
						if omovieplayer.get("name") == config.plugins.MerlinSkinThemes.OLEDMoviePlayer.value:
							omovieplayer.set("value", "active")
							ib = omovieplayer.find("screen")

							# delete old InfoBarMoviePlayerSummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InfoBarMoviePlayerSummary" and SkinScreen.get("id") == "2":
									rootSkin.remove(SkinScreen)
							
							# Set new InfoBarMoviePlayerSummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							omovieplayer.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2LCDScreen":
					for ommp2 in screens.findall("oledscreentheme"):
						if ommp2.get("name") == config.plugins.MerlinSkinThemes.OLEDMMP2.value:
							ommp2.set("value", "active")
							ib = ommp2.find("screen")

							# delete old MerlinMusicPlayer2LCDScreen screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2LCDScreen" and SkinScreen.get("id") == "2":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2LCDScreen screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							ommp2.set("value", "inactive")

		# external LCD
		if rootTheme.find("extlcdscreenthemes") is not None:
			themes = rootTheme.find("extlcdscreenthemes")
			for screens in themes.findall("screens"):
				if screens.get("name") == "InfoBarSummary":
					for extlinfobar in screens.findall("extlcdscreentheme"):
						if extlinfobar.get("name") == config.plugins.MerlinSkinThemes.ExtLCDInfoBar.value:
							extlinfobar.set("value", "active")
							ib = extlinfobar.find("screen")

							# delete old InfoBarSummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InfoBarSummary" and SkinScreen.get("id") == "3":
									rootSkin.remove(SkinScreen)
							
							# Set new InfoBarSummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							extlinfobar.set("value", "inactive")

				if screens.get("name") == "EventView_summary":
					for extleventview in screens.findall("extlcdscreentheme"):
						if extleventview.get("name") == config.plugins.MerlinSkinThemes.ExtLCDEventView.value:
							extleventview.set("value", "active")
							ib = extleventview.find("screen")

							# delete old EventView_summary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "EventView_summary" and SkinScreen.get("id") == "3":
									rootSkin.remove(SkinScreen)
							
							# Set new EventView_summary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							extleventview.set("value", "inactive")
							
				if screens.get("name") == "StandbySummary":
					for extlstandby in screens.findall("extlcdscreentheme"):
						if extlstandby.get("name") == config.plugins.MerlinSkinThemes.ExtLCDStandby.value:
							extlstandby.set("value", "active")
							ib = extlstandby.find("screen")

							# delete old StandbySummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "StandbySummary" and SkinScreen.get("id") == "3":
									rootSkin.remove(SkinScreen)
							
							# Set new StandbySummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							extlstandby.set("value", "inactive")

				if screens.get("name") == "InfoBarMoviePlayerSummary":
					for extlmovieplayer in screens.findall("extlcdscreentheme"):
						if extlmovieplayer.get("name") == config.plugins.MerlinSkinThemes.ExtLCDMoviePlayer.value:
							extlmovieplayer.set("value", "active")
							ib = extlmovieplayer.find("screen")

							# delete old InfoBarMoviePlayerSummary screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "InfoBarMoviePlayerSummary" and SkinScreen.get("id") == "3":
									rootSkin.remove(SkinScreen)
							
							# Set new InfoBarMoviePlayerSummary screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							extlmovieplayer.set("value", "inactive")

				if screens.get("name") == "MerlinMusicPlayer2LCDScreen":
					for extlmmp2 in screens.findall("extlcdscreentheme"):
						if extlmmp2.get("name") == config.plugins.MerlinSkinThemes.ExtLCDMMP2.value:
							extlmmp2.set("value", "active")
							ib = extlmmp2.find("screen")

							# delete old MerlinMusicPlayer2LCDScreen screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == "MerlinMusicPlayer2LCDScreen" and SkinScreen.get("id") == "3":
									rootSkin.remove(SkinScreen)
							
							# Set new MerlinMusicPlayer2LCDScreen screen
							rootSkin.append(Tree.fromstring(Tree.tostring(ib)))
								
						else:
							extlmmp2.set("value", "inactive")

		# corner Radius in skin.xml in allen eLabel ersetzen
		if config.plugins.MerlinSkinThemes.CornerRadius.value <> "":
			for elabel in rootSkin.findall('.//eLabel[@cornerRadius]'):
				if 'cornerRadius' in elabel.attrib:
					if rootTheme.find("cornerradius") is not None:
						crtheme = rootTheme.find("cornerradius")
						
						if elabel.get("cornerRadius") <> crtheme.get("exclude"):
							elabel.set("cornerRadius", config.plugins.MerlinSkinThemes.CornerRadius.value)
							
							for r in crtheme.findall("radius"):
								if r.get("name") == config.plugins.MerlinSkinThemes.CornerRadius.value:
									r.set("value", "active")
								else:
									r.set("value", "inactive")
			
		self.XMLindent(rootSkin, 0)
		curSkin.write(MerlinSkinThemes.selSkinFile)

		# SkinPathTheme
		xmlTree = Tree.parse(MerlinSkinThemes.selSkinFile)
		xmlRoot = xmlTree.getroot()
		xmlString = Tree.tostring(xmlRoot)
		
		if rootTheme.find("skinpaththemes") is not None:
			spt = rootTheme.find("skinpaththemes")
			for theme in spt.findall("theme"):
				if theme.get("name") == config.plugins.MerlinSkinThemes.SkinPathTheme.value:
					newPath = theme.get("path")
					theme.set("value", "active")
				else:
					theme.set("value", "inactive")
					
			for theme in spt.findall("theme"):
				xmlString = xmlString.replace(theme.get("path"), newPath)
		
			xmlSkin = open(MerlinSkinThemes.selSkinFile, "w")
			xmlSkin.write(xmlString)
			xmlSkin.close()
			
		curTree.write(MerlinSkinThemes.selThemeFile)
		
	def createThemes(self):
		if fileExists(MerlinSkinThemes.selThemeFile) == False:
			themes = Tree.Element("themes")


			# colors
			colortheme1 = Tree.SubElement(themes, "colortheme", {"name": "orginal", "value": "active"})
			colorsnode1 = Tree.SubElement(colortheme1, "colors")

			colortheme2 = Tree.SubElement(themes, "colortheme", {"name": "orginal - work", "value": "inactive"})
			colorsnode2 = Tree.SubElement(colortheme2, "colors")

			curTree = Tree.parse(MerlinSkinThemes.selSkinFile)
			colors = curTree.find("colors")

			for color in colors.findall("color"):
				name = color.get("name")
				value = color.get("value")
				
				Tree.SubElement(colorsnode1, "color", {"name": name, "value": value})
				Tree.SubElement(colorsnode2, "color", {"name": name, "value": value})


			# fonts
			fonttheme1 = Tree.SubElement(themes, "fonttheme", {"name": "orginal", "value": "active"})
			fontsnode1 = Tree.SubElement(fonttheme1, "fonts")

			fonttheme2 = Tree.SubElement(themes, "fonttheme", {"name": "orginal - work", "value": "inactive"})
			fontsnode2 = Tree.SubElement(fonttheme2, "fonts")

			fonts = curTree.find("fonts")

			for font in fonts.findall("font"):
				filename = font.get("filename")
				name = font.get("name")
				scale = font.get("scale", "100")
				replacement = font.get("replacement", "0")
				
				Tree.SubElement(fontsnode1, "font", {"filename": filename, "name": name, "scale": scale, "replacement": replacement})
				Tree.SubElement(fontsnode2, "font", {"filename": filename, "name": name, "scale": scale, "replacement": replacement})


			# bordersets
			bordersettheme1 = Tree.SubElement(themes, "bordersettheme", {"name": "orginal", "value": "active"})
			bordersettheme2 = Tree.SubElement(themes, "bordersettheme", {"name": "orginal - work", "value": "inactive"})

			curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
			rootSkin = curSkin.getroot()
			ws = rootSkin.find("windowstyle")
			for bs in ws.findall("borderset"):
				if bs.get("name") == "bsWindow":
					bordersettheme1.append(Tree.fromstring(Tree.tostring(bs)))
					bordersettheme2.append(Tree.fromstring(Tree.tostring(bs)))
			
				if bs.get("name") == "bsListboxEntry":
					bordersettheme1.append(Tree.fromstring(Tree.tostring(bs)))
					bordersettheme2.append(Tree.fromstring(Tree.tostring(bs)))

			
			# windowstylescrollbar
			wssbtheme1 = Tree.SubElement(themes, "windowstylescrollbartheme", {"name": "orginal", "value": "active"})
			wssbtheme2 = Tree.SubElement(themes, "windowstylescrollbartheme", {"name": "orginal - work", "value": "inactive"})
			
			curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
			rootSkin = curSkin.getroot()
			for wssb in rootSkin.findall("windowstylescrollbar"):
				if wssb.get("id") == "4":
					for sb in wssb.findall("*"):
						wssbtheme1.append(Tree.fromstring(Tree.tostring(sb)))
						wssbtheme2.append(Tree.fromstring(Tree.tostring(sb)))


			# pngs
			pngtheme1 = Tree.SubElement(themes, "pngtheme", {"name": "orginal", "value": "active"})
			pngcomment1 = Tree.Comment('Sample: name=path+png_name (root=skindir), argb=a:alpha r:red g:green b:blue')
			pngcomment11 = Tree.Comment('<png name="design/progress.png" width="814" height="5" argb="#ff55a0ff" />')
			pngtheme1.append(pngcomment1)
			pngtheme1.append(pngcomment11)

			pngtheme2 = Tree.SubElement(themes, "pngtheme", {"name": "work", "value": "inactive"})
			pngcomment2 = Tree.Comment('<png name="design/progress.png" width="814" height="5" argb="#ffffa055" />')
			pngtheme2.append(pngcomment2)
						
			
			# screenthemes
			screenthemes = Tree.SubElement(themes, "screenthemes")
			infobar = Tree.SubElement(screenthemes, "screens", {"name": "InfoBar"})
			menu = Tree.SubElement(screenthemes, "screens", {"name": "Menu"})
			pluginbrowser = Tree.SubElement(screenthemes, "screens", {"name": "PluginBrowser"})
			channelselection = Tree.SubElement(screenthemes, "screens", {"name": "ChannelSelection"})
			movieselection = Tree.SubElement(screenthemes, "screens", {"name": "MovieSelection"})
			movieplayer = Tree.SubElement(screenthemes, "screens", {"name": "MoviePlayer"})
			secondinfobar = Tree.SubElement(screenthemes, "screens", {"name": "SecondInfoBar"})
			graphmultiepg = Tree.SubElement(screenthemes, "screens", {"name": "GraphMultiEPG"})
			eventview = Tree.SubElement(screenthemes, "screens", {"name": "EventView"})
			epgselection = Tree.SubElement(screenthemes, "screens", {"name": "EPGSelection"})
			messagebox = Tree.SubElement(screenthemes, "screens", {"name": "MessageBox"})
			inputbox = Tree.SubElement(screenthemes, "screens", {"name": "InputBox"})
			choicebox = Tree.SubElement(screenthemes, "screens", {"name": "ChoiceBox"})
			mute = Tree.SubElement(screenthemes, "screens", {"name": "Mute"})
			volume = Tree.SubElement(screenthemes, "screens", {"name": "Volume"})
			mmp2screen = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2Screen"})
			mmp2screenmipsel = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2Screen_MIPSEL"})
			mmp2screenarm = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2Screen_ARM"})
			mmp2screenarch64 = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2Screen_AARCH64"})
			mmp2saverscreen = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2ScreenSaver"})
			mmp2saverscreenmipsel = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2ScreenSaver_MIPSEL"})
			mmp2saverscreenarm = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2ScreenSaver_ARM"})
			mmp2saverscreenarch64 = Tree.SubElement(screenthemes, "screens", {"name": "MerlinMusicPlayer2ScreenSaver_AARCH64"})

			extlcdscreenthemes = Tree.SubElement(themes, "extlcdscreenthemes")
			extlinfobar = Tree.SubElement(extlcdscreenthemes, "screens", {"name": "InfoBarSummary", "id": "3"})
			extleventview = Tree.SubElement(extlcdscreenthemes, "screens", {"name": "EventView_summary", "id": "3"})
			extlstandby = Tree.SubElement(extlcdscreenthemes, "screens", {"name": "StandbySummary", "id": "3"})
			extlmovieplayer = Tree.SubElement(extlcdscreenthemes, "screens", {"name": "InfoBarMoviePlayerSummary", "id": "3"})
			extlmmp2 = Tree.SubElement(extlcdscreenthemes, "screens", {"name": "MerlinMusicPlayer2Screen", "id": "3"})

			oledscreenthemes = Tree.SubElement(themes, "oledscreenthemes")
			oinfobar = Tree.SubElement(oledscreenthemes, "screens", {"name": "InfoBarSummary", "id": "2"})
			oeventview = Tree.SubElement(oledscreenthemes, "screens", {"name": "EventView_summary", "id": "2"})
			ostandby = Tree.SubElement(oledscreenthemes, "screens", {"name": "StandbySummary", "id": "2"})
			omovieplayer = Tree.SubElement(oledscreenthemes, "screens", {"name": "InfoBarMoviePlayerSummary", "id": "2"})
			ommp2 = Tree.SubElement(oledscreenthemes, "screens", {"name": "MerlinMusicPlayer2LCDScreen", "id": "2"})

			lcdscreenthemes = Tree.SubElement(themes, "lcdscreenthemes")
			linfobar = Tree.SubElement(lcdscreenthemes, "screens", {"name": "InfoBarSummary", "id": "1"})
			leventview = Tree.SubElement(lcdscreenthemes, "screens", {"name": "EventView_summary", "id": "1"})
			lstandby = Tree.SubElement(lcdscreenthemes, "screens", {"name": "StandbySummary", "id": "1"})
			lmovieplayer = Tree.SubElement(lcdscreenthemes, "screens", {"name": "InfoBarMoviePlayerSummary", "id": "1"})
			lmmp2 = Tree.SubElement(lcdscreenthemes, "screens", {"name": "MerlinMusicPlayer2LCDScreen", "id": "1"})

			infobar1 = Tree.SubElement(infobar, "screentheme", {"name": "orginal", "value": "active"})
			infobar2 = Tree.SubElement(infobar, "screentheme", {"name": "orginal - work", "value": "inactive"})

			menu1 = Tree.SubElement(menu, "screentheme", {"name": "orginal", "value": "active"})
			menu2 = Tree.SubElement(menu, "screentheme", {"name": "orginal - work", "value": "inactive"})

			pluginbrowser1 = Tree.SubElement(pluginbrowser, "screentheme", {"name": "orginal", "value": "active"})
			pluginbrowser2 = Tree.SubElement(pluginbrowser, "screentheme", {"name": "orginal - work", "value": "inactive"})

			channelselection1 = Tree.SubElement(channelselection, "screentheme", {"name": "orginal", "value": "active"})
			channelselection2 = Tree.SubElement(channelselection, "screentheme", {"name": "orginal - work", "value": "inactive"})

			movieselection1 = Tree.SubElement(movieselection, "screentheme", {"name": "orginal", "value": "active"})
			movieselection2 = Tree.SubElement(movieselection, "screentheme", {"name": "orginal - work", "value": "inactive"})

			movieplayer1 = Tree.SubElement(movieplayer, "screentheme", {"name": "orginal", "value": "active"})
			movieplayer2 = Tree.SubElement(movieplayer, "screentheme", {"name": "orginal - work", "value": "inactive"})

			secondinfobar1 = Tree.SubElement(secondinfobar, "screentheme", {"name": "orginal", "value": "active"})
			secondinfobar2 = Tree.SubElement(secondinfobar, "screentheme", {"name": "orginal - work", "value": "inactive"})

			graphmultiepg1 = Tree.SubElement(graphmultiepg, "screentheme", {"name": "orginal", "value": "active"})
			graphmultiepg2 = Tree.SubElement(graphmultiepg, "screentheme", {"name": "orginal - work", "value": "inactive"})

			eventview1 = Tree.SubElement(eventview, "screentheme", {"name": "orginal", "value": "active"})
			eventview2 = Tree.SubElement(eventview, "screentheme", {"name": "orginal - work", "value": "inactive"})

			epgselection1 = Tree.SubElement(epgselection, "screentheme", {"name": "orginal", "value": "active"})
			epgselection2 = Tree.SubElement(epgselection, "screentheme", {"name": "orginal - work", "value": "inactive"})

			messagebox1 = Tree.SubElement(messagebox, "screentheme", {"name": "orginal", "value": "active"})
			messagebox2 = Tree.SubElement(messagebox, "screentheme", {"name": "orginal - work", "value": "inactive"})

			inputbox1 = Tree.SubElement(inputbox, "screentheme", {"name": "orginal", "value": "active"})
			inputbox2 = Tree.SubElement(inputbox, "screentheme", {"name": "orginal - work", "value": "inactive"})

			choicebox1 = Tree.SubElement(choicebox, "screentheme", {"name": "orginal", "value": "active"})
			choicebox2 = Tree.SubElement(choicebox, "screentheme", {"name": "orginal - work", "value": "inactive"})

			mute1 = Tree.SubElement(mute, "screentheme", {"name": "orginal", "value": "active"})
			mute2 = Tree.SubElement(mute, "screentheme", {"name": "orginal - work", "value": "inactive"})

			volume1 = Tree.SubElement(volume, "screentheme", {"name": "orginal", "value": "active"})
			volume2 = Tree.SubElement(volume, "screentheme", {"name": "orginal - work", "value": "inactive"})

			mmp2screen1 = Tree.SubElement(mmp2screen, "screentheme", {"name": "orginal", "value": "active"})
			mmp2screen2 = Tree.SubElement(mmp2screen, "screentheme", {"name": "orginal - work", "value": "inactive"})

			mmp2screenmipsel1 = Tree.SubElement(mmp2screenmipsel, "screentheme", {"name": "orginal", "value": "active"})
			mmp2screenmipsel2 = Tree.SubElement(mmp2screenmipsel, "screentheme", {"name": "orginal - work", "value": "inactive"})

			mmp2screenarm1 = Tree.SubElement(mmp2screenarm, "screentheme", {"name": "orginal", "value": "active"})
			mmp2screenarm2 = Tree.SubElement(mmp2screenarm, "screentheme", {"name": "orginal - work", "value": "inactive"})

			mmp2saverscreen1 = Tree.SubElement(mmp2saverscreen, "screentheme", {"name": "orginal", "value": "active"})
			mmp2saverscreen2 = Tree.SubElement(mmp2saverscreen, "screentheme", {"name": "orginal - work", "value": "inactive"})

			mmp2saverscreenmipsel1 = Tree.SubElement(mmp2saverscreenmipsel, "screentheme", {"name": "orginal", "value": "active"})
			mmp2saverscreenmipsel2 = Tree.SubElement(mmp2saverscreenmipsel, "screentheme", {"name": "orginal - work", "value": "inactive"})

			mmp2saverscreenarm1 = Tree.SubElement(mmp2saverscreenarm, "screentheme", {"name": "orginal", "value": "active"})
			mmp2saverscreenarm2 = Tree.SubElement(mmp2saverscreenarm, "screentheme", {"name": "orginal - work", "value": "inactive"})

			# extlcd
			extlinfobar1 = Tree.SubElement(extlinfobar, "extlcdscreentheme", {"name": "orginal", "value": "active"})
			extlinfobar2 = Tree.SubElement(extlinfobar, "extlcdscreentheme", {"name": "orginal - work", "value": "inactive"})

			extleventview1 = Tree.SubElement(extleventview, "extlcdscreentheme", {"name": "orginal", "value": "active"})
			extleventview2 = Tree.SubElement(extleventview, "extlcdscreentheme", {"name": "orginal - work", "value": "inactive"})

			extlstandby1 = Tree.SubElement(extlstandby, "extlcdscreentheme", {"name": "orginal", "value": "active"})
			extlstandby2 = Tree.SubElement(extlstandby, "extlcdscreentheme", {"name": "orginal - work", "value": "inactive"})

			extlmovieplayer1 = Tree.SubElement(extlmovieplayer, "extlcdscreentheme", {"name": "orginal", "value": "active"})
			extlmovieplayer2 = Tree.SubElement(extlmovieplayer, "extlcdscreentheme", {"name": "orginal - work", "value": "inactive"})
			
			extlmmp21 = Tree.SubElement(extlmmp2, "extlcdscreentheme", {"name": "orginal", "value": "active"})
			extlmmp22 = Tree.SubElement(extlmmp2, "extlcdscreentheme", {"name": "orginal - work", "value": "inactive"})
			
			# oled
			oinfobar1 = Tree.SubElement(oinfobar, "oledscreentheme", {"name": "orginal", "value": "active"})
			oinfobar2 = Tree.SubElement(oinfobar, "oledscreentheme", {"name": "orginal - work", "value": "inactive"})

			oeventview1 = Tree.SubElement(oeventview, "oledscreentheme", {"name": "orginal", "value": "active"})
			oeventview2 = Tree.SubElement(oeventview, "oledscreentheme", {"name": "orginal - work", "value": "inactive"})

			ostandby1 = Tree.SubElement(ostandby, "oledscreentheme", {"name": "orginal", "value": "active"})
			ostandby2 = Tree.SubElement(ostandby, "oledscreentheme", {"name": "orginal - work", "value": "inactive"})

			omovieplayer1 = Tree.SubElement(omovieplayer, "oledscreentheme", {"name": "orginal", "value": "active"})
			omovieplayer2 = Tree.SubElement(omovieplayer, "oledscreentheme", {"name": "orginal - work", "value": "inactive"})
			
			ommp21 = Tree.SubElement(ommp2, "oledscreentheme", {"name": "orginal", "value": "active"})
			ommp22 = Tree.SubElement(ommp2, "oledscreentheme", {"name": "orginal - work", "value": "inactive"})
			
			# lcd
			linfobar1 = Tree.SubElement(linfobar, "lcdscreentheme", {"name": "orginal", "value": "active"})
			linfobar2 = Tree.SubElement(linfobar, "lcdscreentheme", {"name": "orginal - work", "value": "inactive"})

			leventview1 = Tree.SubElement(leventview, "lcdscreentheme", {"name": "orginal", "value": "active"})
			leventview2 = Tree.SubElement(leventview, "lcdscreentheme", {"name": "orginal - work", "value": "inactive"})

			lstandby1 = Tree.SubElement(lstandby, "lcdscreentheme", {"name": "orginal", "value": "active"})
			lstandby2 = Tree.SubElement(lstandby, "lcdscreentheme", {"name": "orginal - work", "value": "inactive"})
			
			lmovieplayer1 = Tree.SubElement(lmovieplayer, "lcdscreentheme", {"name": "orginal", "value": "active"})
			lmovieplayer2 = Tree.SubElement(lmovieplayer, "lcdscreentheme", {"name": "orginal - work", "value": "inactive"})
			
			lmmp21 = Tree.SubElement(lmmp2, "lcdscreentheme", {"name": "orginal", "value": "active"})
			lmmp22 = Tree.SubElement(lmmp2, "lcdscreentheme", {"name": "orginal - work", "value": "inactive"})
			
			curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
			rootSkin = curSkin.getroot()
			for SkinScreen in rootSkin.findall("screen"):
				if SkinScreen.get("name") == "InfoBar":
					infobar1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					infobar2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "Menu":
					menu1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					menu2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "PluginBrowser":
					pluginbrowser1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					pluginbrowser2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "ChannelSelection":
					channelselection1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					channelselection2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MovieSelection":
					movieselection1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					movieselection2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MoviePlayer":
					movieplayer1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					movieplayer2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					
				if SkinScreen.get("name") == "SecondInfoBar":
					secondinfobar1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					secondinfobar2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "GraphMultiEPG":
					graphmultiepg1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					graphmultiepg2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "EventView":
					eventview1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					eventview2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "EPGSelection":
					epgselection1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					epgselection2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MessageBox":
					messagebox1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					messagebox2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "InputBox":
					inputbox1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					inputbox2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "ChoiceBox":
					choicebox1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					choicebox2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "Mute":
					mute1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mute2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "Volume":
					volume1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					volume2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MerlinMusicPlayer2Screen":
					mmp2screen1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2screen2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MerlinMusicPlayer2Screen_MIPSEL":
					mmp2screenmipsel1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2screenmipsel2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MerlinMusicPlayer2Screen_ARM":
					mmp2screenarm1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2screenarm2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MerlinMusicPlayer2Screen_AARCH64":
					mmp2screenarm1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2screenarm2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver":
					mmp2saverscreen1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2saverscreen2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver_MIPSEL":
					mmp2saverscreenmipsel1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2saverscreenmipsel2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver_ARM":
					mmp2saverscreenarm1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2saverscreenarm2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "MerlinMusicPlayer2ScreenSaver_AARCH64":
					mmp2saverscreenarch641.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					mmp2saverscreenarch642.append(Tree.fromstring(Tree.tostring(SkinScreen)))
			
				# extlcd
				if SkinScreen.get("name") == "InfoBarSummary" and SkinScreen.get("id") == "3":
					extlinfobar1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					extlinfobar2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					
				if SkinScreen.get("name") == "EventView_summary" and SkinScreen.get("id") == "3":
					extleventview1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					extleventview2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "StandbySummary" and SkinScreen.get("id") == "3":
					extlstandby1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					extlstandby2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "InfoBarMoviePlayerSummary" and SkinScreen.get("id") == "3":
					extlmovieplayer1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					extlmovieplayer2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "MerlinMusicPlayer2LCDScreen" and SkinScreen.get("id") == "3":
					extlmmp21.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					extlmmp22.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				# oled
				if SkinScreen.get("name") == "InfoBarSummary" and SkinScreen.get("id") == "2":
					oinfobar1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					oinfobar2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					
				if SkinScreen.get("name") == "EventView_summary" and SkinScreen.get("id") == "2":
					oeventview1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					oeventview2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "StandbySummary" and SkinScreen.get("id") == "2":
					ostandby1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					ostandby2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "InfoBarMoviePlayerSummary" and SkinScreen.get("id") == "2":
					omovieplayer1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					omovieplayer2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "MerlinMusicPlayer2LCDScreen" and SkinScreen.get("id") == "2":
					ommp21.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					ommp22.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				# lcd
				if SkinScreen.get("name") == "InfoBarSummary" and SkinScreen.get("id") == "1":
					linfobar1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					linfobar2.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					
				if SkinScreen.get("name") == "EventView_summary" and SkinScreen.get("id") == "1":
					leventview1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					leventview2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "StandbySummary" and SkinScreen.get("id") == "1":
					lstandby1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					lstandby2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "InfoBarMoviePlayerSummary" and SkinScreen.get("id") == "1":
					lmovieplayer1.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					lmovieplayer2.append(Tree.fromstring(Tree.tostring(SkinScreen)))

				if SkinScreen.get("name") == "MerlinMusicPlayer2LCDScreen" and SkinScreen.get("id") == "1":
					lmmp21.append(Tree.fromstring(Tree.tostring(SkinScreen)))
					lmmp22.append(Tree.fromstring(Tree.tostring(SkinScreen)))

			# Sort
			self.XMLindent(themes, 0)
			
			# save xml
			themexml = open(MerlinSkinThemes.selThemeFile, "w")
			themexml.write(Tree.tostring(themes))
			themexml.close()
			
			self.updateSkinList()
	
	def loadPreview(self):
		pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/prev.png"

		if not fileExists(pngpath):
			pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

		self["Preview"].instance.setPixmapFromFile(pngpath)

	def MSTMenu(self):
		if fileExists(MerlinSkinThemes.selSkinFile):
			xml = Tree.parse(MerlinSkinThemes.selSkinFile)
			if xml.find("screen[@name='MerlinSkinThemes']"):
				MSTFixbox = self.session.openWithCallback(self.MSTScrFix,MessageBox,_("Delete screen to fix new MST version?"), MessageBox.TYPE_YESNO)
				MSTFixbox.setTitle(_("MST screen found"))
			else:
				self.session.open(MessageBox, _("No MST screen found in this skin.xml!"), MessageBox.TYPE_INFO)
		
	def Help(self):
		if self.curList == "SkinsList":
			HelpText = (
				"[OK]\nswitch to themes/designs config screen for selected skin\n\n" + 
				"[create themes] and [delete]\ntakes some time - please wait\n\n" +
				'[menu]\nremove <screen name="MerlinSkinThemes"...> from selected skin.'
				"This can fix a GS if skin is not sync to this version of MST."
			)

		elif self.curList == "ConfigList":
			HelpText = (
				"[OK]\nswitch to skin selection screen\n\n" + 
				"[apply themes] takes some time - please wait\n\n" + 
				"[delete design]\ndelete selected design\n\n" + 
				"[save as design]\nselected themes/screens stored in new design\n\n" +
				"choose Design: -none-\nto reset themes to active settings/themes"
			)
		
		self.session.open(MessageBox, HelpText, MessageBox.TYPE_INFO, title="MerlinSkinThemes - Help")

	def ImageInfo(self):
		InfoText = "Enigma: " + E2ver + " - "

		if Arch64:
			InfoText += "ARM64: " + _("Yes") + " - "

		if ArchArm:
			InfoText += "ARM: " + _("Yes") + " - "

		if ArchMipsel:
			InfoText += "MIPSEL: " + _("Yes") + " - "	
		
		if Merlin:
			InfoText += "Merlin: " + _("Yes") + " - "
		else:
			InfoText += "Merlin: " + _("No") + " - "

		if GP3:
			InfoText += "GP3: " + GP3ver + " - "
		else:
			InfoText += "GP3: " + _("No") + " - "

		if GP4:
			InfoText += "GP4: " + GP4ver
		else:
			InfoText += "GP4: " + _("No")
		
		self["ImageInfo"].setText(InfoText)
		
	def CopyrightInfo(self):
		InfoText = ""
		
		curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
		rootSkin = curSkin.getroot()
		if rootSkin.find("copyright") is not None:
			copyright = rootSkin.find("copyright")
			if copyright.find("orginal") is not None:
				org = copyright.find("orginal")

				oAuthor = org.get("author")
				if oAuthor is None:
					oAuthor = ""
				oVersion = org.get("version")
				if oVersion is None:
					oVersion = ""
				oName = org.get("name")
				if oName is None:
					oName = ""
				oSupport = org.get("supporturl")
				if oSupport is None:
					oSupport = ""
				oLicense = org.get("license")
				if oLicense is None:
					oLicense = ""
				
				OrgText = (
					"Skin " + oName + " by " + oAuthor + " - Version " + oVersion + " - " + oSupport + "\n\n" +
					"License:\n" + oLicense
				)
			
			else:
				OrgText = (
					"Skin ORGINAL - No info available"
				)
		
			if copyright.find("mod") is not None:
				mod = copyright.find("mod")

				mAuthor = mod.get("author")
				if mAuthor is None:
					mAuthor = ""
				mVersion = mod.get("version")
				if mVersion is None:
					mVersion = ""
				mName = mod.get("name")
				if mName is None:
					mName = ""
				mSupport = mod.get("supporturl")
				if mSupport is None:
					mSupport = ""
				
				ModText = (
					"Mod:\nSkin " + mName + " by " + mAuthor + " - Version " + mVersion + " - " + mSupport
				)
			
			else:
				ModText = (
					"Skin MOD - No info available"
				)
		
			InfoText = OrgText + "\n\n" + ModText

		else:
			InfoText = "No copyrightinfo available"
			
		#self.session.open(MessageBox, InfoText, MessageBox.TYPE_INFO, title="About Skin - " + MerlinSkinThemes.selSkinName)
		
		self["SkinCopyright"].setText(InfoText)
		
	def rgb2hex(self, r, g, b):
		return "#%02X%02X%02X" % (r,g,b)
		
	def hex2rgb(self, value):
		value = value.lstrip('#')
		lv = len(value)
		return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

	def argb2hex(self, a, r, g, b):
		return "#%02X%02X%02X%02X" % (a,r,g,b)
		
	def hex2argb(self, value):
		value = value.lstrip('#')
		lv = len(value)
		return tuple(int(value[i:i+lv/4], 16) for i in range(0, lv, lv/4))

	def Info(self):
		if config.plugins.MerlinSkinThemes.ShowPrevPNG.value == "1":
			config.plugins.MerlinSkinThemes.ShowPrevPNG.value = "0"
			self.session.open(MessageBox, "Show prev.png - " + _("Off"), MessageBox.TYPE_INFO, timeout=3)
			self["Preview"].hide()
		else:
			config.plugins.MerlinSkinThemes.ShowPrevPNG.value = "1"
			self.session.open(MessageBox, "Show prev.png - " + _("On"), MessageBox.TYPE_INFO, timeout=3)
			self.loadPreview()
			self["Preview"].show()
	
	def delSkinDir(self):
		print "[MST] Delete: %s" % resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/"
		shutil.rmtree(resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/")
		self.updateSkinList()
		
	def restartGUI(self, answer):
		if answer is True:
			#self.setTheme()
			self.session.open(TryQuitMainloop, 3)
		else:
			self.exit()

	def save(self):
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("For apply new skin settings.\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))

	def exit(self):
		print '[MST] closing'
		self["SkinsList"].onSelectionChanged.remove(self.changedSkinsList)
		self.close()
		
	def XMLindent(self, elem, level):
		i = "\n" + (level*"    ")
		#a = "\n%%-%ds" % level
		#i = a % '  '
		
		if len(elem):
			if not elem.text or not elem.text.strip():
				elem.text = i + "    "
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
			for elem in elem:
				self.XMLindent(elem, level+1)
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
		else:
			if level and (not elem.tail or not elem.tail.strip()):
				elem.tail = i
			
def main(session, **kwargs):
	session.open(MerlinSkinThemes)

def Plugins(path,**kwargs):
	list = [PluginDescriptor(name = "MerlinSkinThemes", description = "MerlinSkinThemes", where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main)]
	return list		

# =================================================================================================

class GetSkinsList(MenuList, MerlinSkinThemes):
	SKIN_COMPONENT_KEY = "MerlinSkinThemesList"
	SKIN_COMPONENT_DIR_WIDTH = "dirWidth"
	SKIN_COMPONENT_STATUS_WIDTH = "statusWidth"
	SKIN_COMPONENT_INFO_WIDTH = "infoWidth"

	def __init__(self, list, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setFont(1, gFont(tlf.face(tlf.SMALLER), tlf.size(tlf.SMALLER)))
		self.l.setItemHeight(componentSizes.itemHeight(self.SKIN_COMPONENT_KEY, 30))
		
	def buildList(self):
		list = []

		sizes = componentSizes[GetSkinsList.SKIN_COMPONENT_KEY]
		configEntryHeight = sizes.get(componentSizes.ITEM_HEIGHT, 30)
		dirWidth = sizes.get(GetSkinsList.SKIN_COMPONENT_DIR_WIDTH, 310)
		statusWidth = sizes.get(GetSkinsList.SKIN_COMPONENT_STATUS_WIDTH, 205)
		infoWidth = sizes.get(GetSkinsList.SKIN_COMPONENT_INFO_WIDTH, 205)
		
		dirs = os.listdir(resolveFilename(SCOPE_SKIN))
		for dir in dirs:
			if os.path.isdir(resolveFilename(SCOPE_SKIN) + dir) is True:
				curSkinFile = resolveFilename(SCOPE_SKIN) + dir + "/skin.xml"
				curThemeFile = resolveFilename(SCOPE_SKIN) + dir + "/themes.xml"
				
				info = ""
				status = ""

				skinxml = False;
				themexml = False;
				
				if fileExists(curSkinFile):
					skinxml = True;

				if fileExists(curThemeFile):
					themexml = True;
					
				if skinxml or themexml:
					if skinxml is False:
						info = "no skin.xml"

					if themexml is False:
						info = "no themes.xml"

					if dir == SkinName:
						status = "active skin"

					res = [
						dir,
						(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, dirWidth, configEntryHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, dir),
						(eListboxPythonMultiContent.TYPE_TEXT, 5 + dirWidth, 0, statusWidth, configEntryHeight, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, status),
						(eListboxPythonMultiContent.TYPE_TEXT, 5 + dirWidth + statusWidth, 0, infoWidth, configEntryHeight, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, info),
					]
					list.append(res)
				
		self.list = list.sort()
		self.l.setList(list)
		
# =================================================================================================
		
class MyConfigSelection(ConfigSelection):
	def getText(self):
		if self._descr is not None:
			return self._descr
		descr = self._descr = self.description[self.value]
		return descr
		
	def getMulti(self, selected):
		if self._descr is not None:
			descr = self._descr
		else:
			descr = self._descr = self.description[self.value]
		if descr:
			return ("text", descr)
		return ("text", descr)

