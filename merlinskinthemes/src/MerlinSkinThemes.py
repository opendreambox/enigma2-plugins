#######################################################################
#
#  MerlinSkinThemes for Dreambox/Enigma2/Dreambox OS
#  Coded by marthom (c)2012 - 2019
#
#  Support: board.dreambox.tools
#  E-Mail: marthom@dreambox-tools.info
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
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

from skin import TemplatedListFonts, componentSizes

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigNumber, ConfigText, ConfigInteger, ConfigSubDict, ConfigBoolean
from Components.ConfigList import ConfigListScreen

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, getEnigmaVersionString

from Tools.HardwareInfo import HardwareInfo
from Tools.Directories import resolveFilename, SCOPE_SKIN, SCOPE_PLUGINS, fileExists, createDir

import xml.etree.cElementTree as Tree

import shutil
import os
from six.moves import range

# =========================================
PluginVersion = "v2.8.1"
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
CONFDIR = "/etc/enigma2/merlinskinthemes/"

# Liste der Vorschaubilder
myList = ["InfoBar", "Menu", "PluginBrowser", "ChannelSelection", "MovieSelection", "MoviePlayer", "SecondInfoBar", "GraphMultiEPG", "MessageBox", "InputBox", "ChoiceBox", "Mute", "Volume", "MerlinMusicPlayer2", "ExtLCDInfoBar", "ExtLCDEventView", "ExtLCDStandby", "ExtLCDMoviePlayer", "ExtLCDMMP2", "OLEDInfoBar", "OLEDEventView", "OLEDStandby", "OLEDMoviePlayer", "OLEDMMP2", "LCDInfoBar", "LCDEventView", "LCDStandby", "LCDMoviePlayer", "LCDMMP2"]

# Enigma2Version
E2ver = _("not available")
if open("/proc/stb/info/model","rb").read() == "dm7080":
	if fileExists(enigmacontrol):
		file = open(enigmacontrol, 'r')
		while True:
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
	while True:
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
	while True:
		line = file.readline()
		if not line:break
		data += line
	file.close()
	
	data = data.split("'")
	GP4ver = data[1]

# Arm/mipsel/aarch64
ArchArm = False
Arch64 = False
ArchMipsel = False
if HardwareInfo().get_device_name() in ('dm900', 'dm920'):
	ArchArm = True
	ArchString = "ARM"
	IdString = "3"
	DisplayXY = "400x240"
elif HardwareInfo().get_device_name() == 'one':
	Arch64 = True
	ArchString = "AARCH64"
	IdString = "0" #no display
	DisplayXY = "0x0"
elif HardwareInfo().get_device_name() == 'two':
	Arch64 = True
	ArchString = "AARCH64"
	IdString = "100"
	DisplayXY = "240x86"
else:
	if HardwareInfo().get_device_name() == 'dm820':
		IdString = "2"
		DisplayXY = "96x64"
	elif HardwareInfo().get_device_name() == 'dm7080':
		IdString = "1"
		DisplayXY = "132x64"
	elif HardwareInfo().get_device_name() in ('dm520', 'dm525'):
		IdString = "0"
		DisplayXY = "0x0"
	ArchMipsel = True
	ArchString = "MIPSEL"
ModelString = HardwareInfo().get_device_name().upper()
displayDict = {"1": "lcdscreenthemes", "2": "oldescreenthemes", "3": "extlcdscreenthemes", "100": "lcdscreenthemes" }
displayTag = displayDict.get(IdString, None)

print "------------------------------------------------"
print HardwareInfo().get_device_name()
print PluginVersion
print "------------------------------------------------"

# skin_user.xml
SkinUser = False
if fileExists(skin_user_xml):
	SkinUser = True
	
# Config
config.plugins.MerlinSkinThemes = ConfigSubsection()
config.plugins.MerlinSkinThemes.rebuildSkinOnBoot = ConfigBoolean(default=True)
config.plugins.MerlinSkinThemes.Skin = ConfigText(default=SkinName)
config.plugins.MerlinSkinThemes.selSkin = ConfigText(default=SkinName)
config.plugins.MerlinSkinThemes.ShowPrevPNG = ConfigText(default="1")
config.plugins.MerlinSkinThemes.CornerRadius = ConfigText(default="")

def initConfigSubDict(sectionName=None):
	if sectionName == "Design":
		config.plugins.MerlinSkinThemes.Designs = ConfigSubDict()
	elif sectionName == "Themes":
		config.plugins.MerlinSkinThemes.Themes = ConfigSubDict()
	elif sectionName == "Screens":
		config.plugins.MerlinSkinThemes.Screens = ConfigSubDict()
	elif sectionName == "DisplayScreens":
		config.plugins.MerlinSkinThemes.DisplayScreens = ConfigSubDict()
		
# list of display screens (a.k.a. summaries)
displayScreenList = ["InfoBarSummary", "EventView_summary", "StandbySummary", "InfoBarMoviePlayerSummary", "MerlinMusicPlayer2LCDScreen"]
# list of screens
screenList = ["InfoBar", "Menu", "PluginBrowser", "ChannelSelection", "MovieSelection", "MoviePlayer", "SecondInfoBar", "GraphMultiEPG", "EventView", "EPGSelection", "MessageBox", "InputBox", "ChoiceBox", "Mute", "Volume", "MerlinMusicPlayer2Screen", "MerlinMusicPlayer2Screen_%s" %(ArchString), "MerlinMusicPlayer2ScreenSaver", "MerlinMusicPlayer2ScreenSaver_%s" %(ArchString)]
# list of themes
themeList = ["ColorTheme", "SkinPathTheme", "FontTheme",  "BorderSetTheme", "WindowStyleScrollbarTheme", "ComponentTheme", "LayoutTheme", "GlobalsTheme", "PNGTheme" ]

# shared functions
# ImageCreator
import Image,ImageDraw
import math

class ImageCreator:
	def __init__(self):
		pass

	def createRectangle(self, width=200, height=50, fromColor=None, toColor=None, filename=None, mode="no",):
		
		if mode == "no":
			image = Image.new(mode='RGBA', size=(width, height), color=fromColor)
			image.save(filename)
		else:
			gradient = Image.new(mode='RGBA',size=(width,height),color=0)
			draw = ImageDraw.Draw(gradient)
			
			if mode == "horizontal":
				steps=width
			elif mode == "vertical":
				steps=height
			elif mode == "diametral":
				steps=width*2
			elif mode == "rectangular":
				fromColorList = list(fromColor)
				toColorList = list(toColor)
				for y in range(height):
					for x in range(width):
						#Find the distance to the closest edge
						distanceToEdge = min(abs(x - width), x, abs(y - height), y)

						#Make it on a scale from 0 to 1
						distanceToEdge = float(distanceToEdge) / (width/2)

						#Calculate a, r, g, and b values
						a = fromColorList[3] * distanceToEdge + toColorList[3] * (1 - distanceToEdge)
						r = fromColorList[0] * distanceToEdge + toColorList[0] * (1 - distanceToEdge)
						g = fromColorList[1] * distanceToEdge + toColorList[1] * (1 - distanceToEdge)
						b = fromColorList[2] * distanceToEdge + toColorList[2] * (1 - distanceToEdge)
						
						gradient.putpixel((x, y), (int(r), int(g), int(b)))
			elif mode == "round":
				fromColorList = list(fromColor)
				toColorList = list(toColor)
				for y in range(height):
					for x in range(width):
						#Find the distance to the center
						distanceToCenter = math.sqrt((x - width/2) ** 2 +(y - height/2) ** 2)

						#Make it on a scale from 0 to 1
						distanceToCenter = float(distanceToCenter) / (math.sqrt(2) * width/2)

						#Calculate a, r, g, and b values
						a = fromColorList[3] * distanceToCenter + toColorList[3] * (1 - distanceToCenter)
						r = fromColorList[0] * distanceToCenter + toColorList[0] * (1 - distanceToCenter)
						g = fromColorList[1] * distanceToCenter + toColorList[1] * (1 - distanceToCenter)
						b = fromColorList[2] * distanceToCenter + toColorList[2] * (1 - distanceToCenter)
						
						gradient.putpixel((x, y), (int(r), int(g), int(b), int(a)))			
						
			if mode != "rectangular" and mode != "round":
						
				for i, color in enumerate(self.interpolate(fromColor, toColor, steps)):
					if mode == "horizontal":
						draw.line([(i, 0), (i, height)], tuple(color), width=1)
					elif mode == "vertical":
						draw.line([(0, i), (width, i)], tuple(color), width=1)
					elif mode == "diametral":
						draw.line([(i, 0), (0, i)], tuple(color), width=1)

			gradient.save(filename)
		
	def interpolate(self, fromColor, toColor, interval):
		# (r/g/b/a(to) - r/g/b/a(from)) / (imagewidth * 2) -> build list. result will be int() [x, y, z, a]
		delta_co =[(t - f) / interval for f , t in zip(fromColor, toColor)]
		for i in range(interval):
			# for each pixel from 0 to imagewidth * 2: r/g/b/a(from) + r/g/b/a(delta) * i
			yield [int(round(f + delta * i)) for f, delta in zip(fromColor, delta_co)]
		
imageCreator = ImageCreator()

def hex2argb(value):
	value = value.lstrip('#')
	lv = len(value)
	return tuple(int(value[i:i+lv/4], 16) for i in range(0, lv, lv/4))
	
def XMLindent(elem, level):
	i = "\n" + (level*"    ")
	#a = "\n%%-%ds" % level
	#i = a % '  '
		
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "    "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			XMLindent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

import datetime

def setThemes(themeFile=None, skinFile=None, configDict=None, mode="apply"):
	# set all "inactive", set new theme "active"
	curTheme = Tree.parse(themeFile)
	rootTheme = curTheme.getroot()

	curSkin = Tree.parse(skinFile)
	rootSkin = curSkin.getroot()

	if mode == "apply":
		if not fileExists(CONFDIR):
			createDir("/etc/enigma2/merlinskinthemes")
		f = open(CONFDIR + config.plugins.MerlinSkinThemes.selSkin.value + ".cfg", 'w')
			
	if rootSkin.find("merlinskinthemes") is None:
		mst = Tree.Element("merlinskinthemes", {"text":"Edited with MerlinSkinThemes"})
		rootSkin.insert(0, mst)

	for theme in [("colortheme", "colors", "color"), ("fonttheme", "fonts", "font"), ("layouttheme", "layouts", "layout"), ("globalstheme", "globals", ""), ("bordersettheme", "", "borderset"), ("windowstylescrollbartheme", "", ""), ("componenttheme", "components", ""),("pngtheme", "", "")]:
		#find colortheme in themes.xml
		if rootTheme.find(theme[0]) is not None:
			# loop themes in selected theme
			for currenttheme in rootTheme.findall(theme[0]):
				attributeDict = {}
				# find selected theme
				if configDict is None:
					currentValue = config.plugins.MerlinSkinThemes.Themes[theme[0]].value
				else:
					currentValue = configDict.get("%s" %(theme[0]), None)
				if currenttheme.get("name") == currentValue:
					# set theme active
					currenttheme.set("value", "active")
					if mode == "apply":
						f.write("%s:::%s\n" %(theme[0], currentValue))
					# find all in skin.xml
					if (theme[1] != "" and theme[2] != ""):
						skinElement = rootSkin.find(theme[1])
						# delete all in skin.xml
						if theme[1] != "layouts" and theme[1] != "components":
							for element in skinElement.findall(theme[2]):
								skinElement.remove(element)
					if theme[1] != "":				
						# find all in themes.xml
						themeElement = currenttheme.find(theme[1])
					# add all elements from themes.xml to skin.xml
					if themeElement is not None:
						if theme[1] in ["layouts","components","globals"]:
							skinElement = rootSkin.find(theme[1])
							rootSkin.remove(skinElement)
							rootSkin.append(Tree.fromstring(Tree.tostring(themeElement)))
						elif theme[2] != "":
							for childElement in themeElement.findall(theme[2]):
								if theme[0] in ["colortheme", "fonttheme"]:
									name = childElement.get("name", None)
									if name is not None:
										attributeDict["name"] = name
									value = childElement.get("value", None)
									if value is not None:
										attributeDict["value"] = value
									filename = childElement.get("filename", None)
									if filename is not None:
										attributeDict["filename"] = filename
									scale = childElement.get("scale", None)
									if scale is None and childElement == "font":
										scale = "100"
									if scale is not None:
										attributeDict["scale"] = scale
									replacement = childElement.get("replacement", None)
									if replacement is None and childElement == "font":
										replacement = "0"
									if replacement is not None:
										attributeDict["replacement"] = replacement
						
									Tree.SubElement(skinElement, theme[2], attributeDict)
					if theme[0] == "bordersettheme":
						ws = rootSkin.find("windowstyle")
						if ws.get("id") == "0":
							for bs in ws.findall(theme[2]):
								if bs.get("name") == "bsWindow":
									for px in bs.findall("pixmap"):
										bs.remove(px)
											
									for tbs in currenttheme.findall(theme[2]):
										if tbs.get("name") == "bsWindow":
											for tpx in tbs.findall("pixmap"):
												bs.append(Tree.fromstring(Tree.tostring(tpx)))
								if bs.get("name") == "bsListboxEntry":
									for px in bs.findall("pixmap"):
										bs.remove(px)
					
									for tbs in currenttheme.findall(theme[2]):
										if tbs.get("name") == "bsListboxEntry":
											for tpx in tbs.findall("pixmap"):
												bs.append(Tree.fromstring(Tree.tostring(tpx)))
					if theme[0] == "windowstylescrollbartheme":
						for wssb in rootSkin.findall("windowstylescrollbar"):
							if wssb.get("id") == "4":
								for all in wssb.findall("*"):
									wssb.remove(all)
							
								for tall in currenttheme.findall("*"):
									wssb.append(Tree.fromstring(Tree.tostring(tall)))	
					if theme[0] == "pngtheme":
						for tp in currenttheme.findall("png"):
							png_name = tp.get("name")
							png_width = int(tp.get("width"))
							png_height = int(tp.get("height"))
							png_argb = tp.get("argb")
							acolor = hex2argb(png_argb)
							png_argb2 = tp.get("argb2", None)
							if png_argb2 is not None:
								acolor2 = hex2argb(png_argb2)
							else:
								acolor2 = None
							gradienttype = tp.get("gtype", None)

							if png_name is not None and png_width is not None and png_height is not None and png_argb is not None:						
								if acolor2 is not None and gradienttype is not None:
									imageCreator.createRectangle(png_width, png_height, (acolor[1], acolor[2], acolor[3], acolor2[0]),(acolor2[1], acolor2[2], acolor2[3], acolor2[0]), resolveFilename(SCOPE_SKIN) + SkinName + "/" + png_name, gradienttype) 
								else:
									imageCreator.createRectangle(png_width, png_height, (acolor[1], acolor[2], acolor[3], acolor[0]), None, resolveFilename(SCOPE_SKIN) + SkinName + "/" + png_name) 
													
				# if name does not match set it to inactive	
				else:
					currenttheme.set("value", "inactive")

	if rootTheme.find("screenthemes") is not None:
		themes = rootTheme.find("screenthemes")
		for screens in themes.findall("screens"):
			for screenname in screenList:
				if screens.get("name") == screenname:
					for screen in screens.findall("screentheme"):
						if configDict is None:
							currentValue = config.plugins.MerlinSkinThemes.Screens[screenname].value
						else:
							currentValue = configDict.get("%s" %(screenname),None)
						if screen.get("name") == currentValue:
							screen.set("value", "active")
							if mode == "apply":
								f.write("%s:::%s\n" %(screenname, currentValue))
							newscreen = screen.find("screen")

							# delete old screen
							for SkinScreen in rootSkin.findall("screen"):
								if SkinScreen.get("name") == screenname:
									rootSkin.remove(SkinScreen)
							
							# Set new screen
							rootSkin.append(Tree.fromstring(Tree.tostring(newscreen)))
									
						else:
							screen.set("value", "inactive")

	# LCD / OLED / External LCD
	if displayTag is not None:
		if rootTheme.find(displayTag) is not None:
			themes = rootTheme.find(displayTag)
			for screens in themes.findall("screens"):
				for displayscreenname in displayScreenList:
					if screens.get("name") == displayscreenname:
						for screen in screens.findall(displayTag[:-1]):
							if configDict is None:
								currentValue = config.plugins.MerlinSkinThemes.DisplayScreens[displayscreenname].value
							else:
								currentValue = configDict.get("%s" %(displayscreenname), None)
							if screen.get("name") == currentValue:
								screen.set("value", "active")
								if mode == "apply":
									f.write("%s:::%s\n" %(displayscreenname, currentValue))
								newscreen = screen.find("screen")

								# delete old screen
								for SkinScreen in rootSkin.findall("screen"):
									if SkinScreen.get("name") == displayscreenname and SkinScreen.get("id") == IdString:
										rootSkin.remove(SkinScreen)
							
								# Set new screen
								rootSkin.append(Tree.fromstring(Tree.tostring(newscreen)))							
							else:
								screen.set("value", "inactive")

	# corner Radius in skin.xml in allen eLabel ersetzen
	if config.plugins.MerlinSkinThemes.CornerRadius.value <> "":
		for elabel in rootSkin.findall('.//eLabel[@cornerRadius]'):
			if 'cornerRadius' in elabel.attrib:
				if rootTheme.find("cornerradius") is not None:
					crtheme = rootTheme.find("cornerradius")
					
					if configDict is None:
						radiusValue = config.plugins.MerlinSkinThemes.CornerRadius.value
					else:
						radiusValue = configDict.get("cornerradius", None)
					
					if elabel.get("cornerRadius") <> crtheme.get("exclude"):
						if radiusValue is not None:
							elabel.set("cornerRadius", config.plugins.MerlinSkinThemes.CornerRadius.value)
								
							for r in crtheme.findall("radius"):
								if r.get("name") == config.plugins.MerlinSkinThemes.CornerRadius.value:
									r.set("value", "active")
								else:
									r.set("value", "inactive")
		
		if mode == "apply":						
			f.write("%s:::%s\n" %("cornerradius", config.plugins.MerlinSkinThemes.CornerRadius.value))

	XMLindent(rootSkin, 0)
	curSkin.write(skinFile)

	# SkinPathTheme
	xmlTree = Tree.parse(skinFile)
	xmlRoot = xmlTree.getroot()
	xmlString = Tree.tostring(xmlRoot)

	if rootTheme.find("skinpaththemes") is not None:
		spt = rootTheme.find("skinpaththemes")
		for theme in spt.findall("theme"):
			if configDict is None:
				currentValue = config.plugins.MerlinSkinThemes.Themes["skinpaththeme"].value
			else:
				currentValue = configDict.get("skinpaththemes", None)
			if theme.get("name") == currentValue:
				newPath = theme.get("path")
				theme.set("value", "active")
				if mode == "apply":
					f.write("skinpaththemes:::%s\n" %(currentValue))
			else:
				theme.set("value", "inactive")
					
		for theme in spt.findall("theme"):
			xmlString = xmlString.replace(theme.get("path"), newPath)
		
		xmlSkin = open(skinFile, "w")
		xmlSkin.write(xmlString)
		xmlSkin.close()

	curTheme.write(themeFile)
	
	if mode == "apply":
		f.close()	

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
		</screen>"""% ("MerlinSkinThemes")

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
		self["key_blue"] = Button(_("open config"))
		
		self.skinsList = []
		self["SkinsList"] = GetSkinsList([])

		self.onSelectionChanged = [ ]
		
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red":     self.buttonRed,
			"green":   self.buttonGreen,
			"yellow":  self.buttonYellow,
			"blue":    self.openConfig,
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
			"ok":		(self.ok, ""),
			"cancel":	(self.exit, _("Close plugin")),
		}, -1)

		self["TeleTextActions"] = HelpableActionMap(self, "TeleTextActions",
		{
			"help":		(self.Help, ""),
			"info":		(self.Info, ""),
		}, -1)

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
		{
			"menu":		(self.MSTMenu, ""),
		}, -1)
		
		self.updateSkinList()
		
		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		self.onLayoutFinish.append(self.startRun)

	def openConfig(self):
		self.session.open(MerlinSkinThemesConfig)

	def startRun(self):
		self["SkinsList"].onSelectionChanged.append(self.changedSkinsList)

		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		self["config"].hide()
		
		self["SkinsList"].moveToIndex(self["SkinsList"].selectedIndex)

		self.ImageInfo()
		if fileExists(MerlinSkinThemes.selSkinFile):
			self.CopyrightInfo()

	# parse themes.xml
	def readThemes(self):
		self.clist = []

		try:
			xml = Tree.parse(MerlinSkinThemes.selThemeFile)

			selSkinList = []
			selSkinList.append(MerlinSkinThemes.selSkinName)
			config.plugins.MerlinSkinThemes.selSkin = MyConfigSelection(default=MerlinSkinThemes.selSkinName, choices = selSkinList)
			self.clist.append(getConfigListEntry(" ", ))
			self.clist.append(getConfigListEntry("Skin", config.plugins.MerlinSkinThemes.selSkin))
			
			#####################
			#	-- Designs --	#
			#####################
			#	<designs>
			#		<design>
			#			<xyzTheme />
			#		</design>
			#	</designs>
			# this reads all <design> and its themes that are defined in <designs>
			# name of <design> is read and displayed in the section DESIGNS, active one is set as default
			self.clist.append(getConfigListEntry(" ", ))
			self.clist.append(getConfigListEntry(" " + u'\u00b7' + " DESIGNS", ))

			initDesignsDone = False	
			if xml.find("designs") is not None:
				ds = xml.find("designs")
				for element in ["design"]:
					elementList = []
					elementList.append("-none-")
					defaultValue = "-none-"
					for design in ds.findall(element):
						elementList.append(design.get("name"))

				if len(elementList) > 0:
					if not initDesignsDone:
						initConfigSubDict("Design")
						initDesignsDone = True
					config.plugins.MerlinSkinThemes.Designs[element] = MyConfigSelection(default=defaultValue, choices = elementList)
					self.clist.append(getConfigListEntry("Design", config.plugins.MerlinSkinThemes.Designs[element]))
			else:
				if not initDesignsDone:
					initConfigSubDict("Design")
					initDesignsDone = True
					config.plugins.MerlinSkinThemes.Designs["design"] = MyConfigSelection(default="-none-", choices = ["-none-"])
					self.clist.append(getConfigListEntry("Design", config.plugins.MerlinSkinThemes.Designs["design"]))				

			################
			# -- Themes -- #
			################
			# name of theme is read and displayed in the section THEMES, active one is set as default
			self.clist.append(getConfigListEntry(" ", ))
			self.clist.append(getConfigListEntry(" " + u'\u00b7' + " THEMES", ))
			
			themesInitDone = False
			for element in themeList:
				elementList = []
				defaultValue = None
				tag = element.lower()
				if tag == "skinpaththeme":
					tag = tag + "s"
				if xml.find(tag) is not None:
					if tag != "skinpaththemes":
						for theme in xml.findall(tag):
							elementList.append(theme.get("name"))
							if theme.get("value") == "active":
								defaultValue = theme.get("name")
					else:
						themes = xml.find(tag)
						for theme in themes.findall("theme"):
							elementList.append(theme.get("name"))
							if theme.get("value") == "active":
								defaultValue = theme.get("name")
				
				if len(elementList) > 0:
					if not themesInitDone:
						initConfigSubDict("Themes")
						themesInitDone = True
					config.plugins.MerlinSkinThemes.Themes[element.lower()] = MyConfigSelection(default=defaultValue, choices = elementList)
					self.clist.append(getConfigListEntry(element, config.plugins.MerlinSkinThemes.Themes[element.lower()]))
			
			#################
			# -- SCREENS -- #
			#################
			#	<screenthemes>
			#		<!-- multiple screens possible -->
			#		<screens name="screenname">
			#			<!-- multiple screentheme possible -->
			#			<screentheme>
			#				<screen>...</screen>
			#			</screentheme>
			#		</screens>
			#	</screenthemes>
			self.clist.append(getConfigListEntry(" ", ))
			self.clist.append(getConfigListEntry(" " + u'\u00b7' + " SCREENS", ))

			if xml.find("screenthemes") is not None:
				st = xml.find("screenthemes")
				initScreenDone = False
				for screens in st.findall("screens"):
					for screenname in screenList:
						elementList = []
						defaultValue = None
						if screens.get("name") == screenname:
							for themes in screens.findall("screentheme"):
								elementList.append(themes.get("name"))
								if themes.get("value") == "active":
									defaultValue = themes.get("name")
							if len(elementList)>0:
								if not initScreenDone:
									initConfigSubDict("Screens")
									initScreenDone = True
								config.plugins.MerlinSkinThemes.Screens[screenname] = MyConfigSelection(default=defaultValue, choices = elementList)
								self.clist.append(getConfigListEntry(screenname, config.plugins.MerlinSkinThemes.Screens[screenname]))

			#########################
			# -- Display Screens -- #
			#########################
			#	<lcdscreenthemes> / <oledscreenthemes> / <extlcdscreenthemes>
			#		<!-- multiple screens possible -->
			#		<screens name="screenname">
			#			<!-- multiple lcdscreentheme possible -->
			#			<lcdscreentheme> / <oledscreentheme> / <extlcdscreentheme>
			#				<screen>...</screen>
			#			</lcdscreentheme> / </oledscreentheme> / </extlcdscreentheme>
			#		</screens>
			#	</lcdscreenthemes> / <oledscreenthemes> / </extlcdscreenthemes>
			
			if displayTag is not None:
				if xml.find(displayTag) is not None:
					self.clist.append(getConfigListEntry(" ", ))
					self.clist.append(getConfigListEntry(" " + u'\u00b7' + " DISPLAY SCREENS ID=%s (%s) %s" %(IdString, ModelString, DisplayXY ), ))		
		
					initDisplayScreenDone = False
					for element in displayScreenList:
						elementList = []
						defaultValue = None
						st = xml.find(displayTag)
						if st.find("screens[@name='%s']" %(element)) is not None:
							lst = st.find("screens[@name='%s']" %(element))
							for th in lst.findall(displayTag[:-1]):
								for screen in th.findall("screen"):
									if screen.get("name") == element and screen.get("id") == IdString:
										elementList.append(th.get("name"))
										if th.get("value") == "active":
											defaultValue = th.get("name")
										
							if len(elementList) > 0:
								if not initDisplayScreenDone:
									initConfigSubDict("DisplayScreens")
									initDisplayScreenDone = True
								config.plugins.MerlinSkinThemes.DisplayScreens[element] = MyConfigSelection(default=defaultValue, choices = elementList)
								self.clist.append(getConfigListEntry(element, config.plugins.MerlinSkinThemes.DisplayScreens[element]))
			
			######################	
			# -- cornerRadius -- #
			######################
			#	<cornerradius>
			#		<radius />
			#	</cornerradius>
			if xml.find("cornerradius") is not None:
				self.clist.append(getConfigListEntry(" ", ))
				self.clist.append(getConfigListEntry(" " + u'\u00b7' + " CORNERRADIUS", ))

				elementList = []
				defaultValue = None
				cr = xml.find("cornerradius")
				for cradius in cr.findall("radius"):
					elementList.append(cradius.get("name"))
					if cradius.get("value") == "active":
						defaultValue = cradius.get("name")

				if len(elementList) > 0:
					config.plugins.MerlinSkinThemes.CornerRadius = MyConfigSelection(default=defaultValue, choices = elementList)
					self.clist.append(getConfigListEntry("CornerRadius", config.plugins.MerlinSkinThemes.CornerRadius))
						
		except Exception as error:
			print "Error", error
			print "[MST] themes.xml in " + MerlinSkinThemes.selSkinName + " corrupt!"
			self.clist.append(getConfigListEntry(" ", ))
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
			setThemes(MerlinSkinThemes.selThemeFile, MerlinSkinThemes.selSkinFile, None)
			for x in self["config"].list:
				if len(x) > 1:
					x[1].save()
			configfile.save()
			if SkinName == MerlinSkinThemes.selSkinName:
				restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply a new skin\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
				restartbox.setTitle(_("Restart GUI now?"))
			
			else:
				self.session.open(MessageBox, _("Changes to skin " + MerlinSkinThemes.selSkinName + " ready!"), MessageBox.TYPE_INFO)

	def MSTScrFix(self, answer):
		if answer is True:
			curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
			rootSkin = curSkin.getroot()
			mstscreen = rootSkin.find("screen[@name='MerlinSkinThemes']")
			rootSkin.remove(mstscreen)

			XMLindent(rootSkin, 0)
			curSkin.write(MerlinSkinThemes.selSkinFile)
			
			self.updateSkinList()

			self.session.open(MessageBox, '<screen name="MerlinSkinThemes"...> was removed from selected skin.', MessageBox.TYPE_INFO)
			
	def buttonRed(self):
		self.exit()
		
	def buttonYellow(self):
		if self.curList == "SkinsList":
			if self["SkinsList"].getCurrent()[3][7] == _("no themes.xml"):
				self.createThemes()

			if self["SkinsList"].getCurrent()[3][7] == _("no skin.xml"):
				self.delSkinDir()
				
		elif self.curList == "ConfigList":
			if self["config"].getCurrent()[0] == "Design":
				# delete design
				self.deleteDesign()
			
			else:
				# save as design
				self.session.openWithCallback(self.saveDesign, InputBox, title=_("Please enter designname!"))
	
	# write a new design into <designs>	
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
				
			# write design
			xmldesign = Tree.SubElement(xmldesigns, "design", {"name": designname, "value": "active"})
			
			for element in themeList:
				# remark: for now don't handle it here. Needs alignment
				if element == "SkinPathTheme":
					continue
				# check if theme exists
				if element.lower() in config.plugins.MerlinSkinThemes.Themes.keys():
					if xmlroot.find("%s[@name='" %(element.lower()) + config.plugins.MerlinSkinThemes.Themes[element.lower()].value + "']" ) is not None:
						if xmldesign.find(element) is not None:
							td = xmldesign.find(element)
							td.set("name", config.plugins.MerlinSkinThemes.Themes[element.lower()].value)
						else:
							Tree.SubElement(xmldesign, element, {"name": config.plugins.MerlinSkinThemes.Themes[element.lower()].value })

			# SkinPathThemes
			# todo: same check required like for themes? is it really possible to define it in Designs?
			if xmlroot.find("skinpaththemes") is not None:
				t = xmlroot.find("skinpaththemes")
				
				if t.find("theme[@name='" + config.plugins.MerlinSkinThemes.Themes["skinpaththemes"].value + "']") is not None:
					if xmldesign.find("SkinPathTheme") is not None:
						td = xmldesign.find("SkinPathTheme")
						td.set("name", config.plugins.MerlinSkinThemes.Themes["skinpaththemes"].value)
					else:
						Tree.SubElement(xmldesign, "SkinPathTheme", {"name": config.plugins.MerlinSkinThemes.Themes["skinpaththemes"].value})
					
			# Screens
			if xmlroot.find("screenthemes") is not None:
				t = xmlroot.find("screenthemes")
				
				for element in screenList:
					if t.find("screens[@name='%s']" %(element)) is not None:
						ts = t.find("screens[@name='%s']" %(element))
						if ts.find("screentheme[@name='" + config.plugins.MerlinSkinThemes.Screens[element].value + "']") is not None:
							Tree.SubElement(xmldesign, element, {"name": config.plugins.MerlinSkinThemes.Screens[element].value})
				
			# LCD Screens
			if displayTag is not None:
				if xmlroot.find(displayTag) is not None:
					t = xmlroot.find(displayTag) 
				
					for element in displayScreenList:
						if t.find("screens[@name='%s']" %(element)) is not None:
							ts = t.find("screens[@name='%s']" %(element))
							if ts.find("%s[@name='" %(displayTag[:-1]) + config.plugins.MerlinSkinThemes.DisplayScreens[element].value + "']") is not None:
								# todo: LCDInfoBar vs. InfoBarSummary!!!! wie geht das?
								Tree.SubElement(xmldesign, element, {"name": config.plugins.MerlinSkinThemes.DisplayScreens[element].value})
			
			# cornerRadius
			if xmlroot.find("cornerradius") is not None:
				if xmldesign.find("CornerRadius") is not None:
					td = xmldesign.find("CornerRadius")
					td.set("name", config.plugins.MerlinSkinThemes.CornerRadius.value)
				else:
					Tree.SubElement(xmldesign, "CornerRadius", {"name": config.plugins.MerlinSkinThemes.CornerRadius.value})
						
			XMLindent(xmlroot, 0)
			
			curTree.write(MerlinSkinThemes.selThemeFile)
				
			self.readThemes()
				
	def deleteDesign(self):
		if config.plugins.MerlinSkinThemes.Designs["design"].value == "-none-":
			self.session.open(MessageBox,_("nothing to delete"), MessageBox.TYPE_ERROR)
		else:
			curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
			xmlroot = curTree.getroot()
			designs = xmlroot.find("designs")
			for design in designs.findall("design"):
				if design.get("name") == config.plugins.MerlinSkinThemes.Designs["design"].value:
					designs.remove(design)
			
					XMLindent(xmlroot, 0)

					curTree.write(MerlinSkinThemes.selThemeFile)
		
					self.readThemes()
	
	# update screen when a different design is selected in section DESIGNS
	def setDesign(self):
		curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
		xmlroot = curTree.getroot()
		designs = xmlroot.find("designs")
		for design in designs.findall("design"):
			# design matches the currently selected design in section DESIGN
			if design.get("name") == config.plugins.MerlinSkinThemes.Designs["design"].value:
				# for each theme in the design set the value to the selected design
				for element in themeList:
					tmp = design.find(element)
					if tmp is not None:
						try:
							if tmp.get("name", None) is not None:
								config.plugins.MerlinSkinThemes.Themes[element.lower()].value = tmp.get("name")
						except:
							print "[MST] %s not found" %(element)

				# for each screen in the design set the value to the selected design
				for screenname in screenList:
					elementList = []
					defaultValue = None
					tmp = design.find(screenname)
					if tmp is not None:
						try:
							if tmp.get("name", None) is not None:
								config.plugins.MerlinSkinThemes.Screens[screenname].value = tmp.get("name")
						except:
							print "[MST] %s not found" %(screenname)

				#todo: maybe merge all displays into one config
				# for each LCD screen in the design set the value to the selected design
				for lcdscreen in displayScreenList:
					if design.find(lcdscreen) is not None:
						tmp = design.find(lcdscreen)
						if tmp is not None:
							try:
								if tmp.get("name", None) is not None:
									config.plugins.MerlinSkinThemes.DisplayScreens[lcdscreen].value = tmp.get("name")
							except:
								print "[MST] %s not found"
			
				# for each corner radius in the design set the value to the selected design
				if design.find("CornerRadius") is not None:
					tmp = design.find("CornerRadius")
					if tmp is not None:
						try:
							if tmp.get("name", None) is not None:
								config.plugins.MerlinSkinThemes.CornerRadius.value = tmp.get("name")
						except:
							print "[MST] CornerRadius not found"					
		
				# refresh Screen
				self["config"].setList(self.clist)
						
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
			self["key_yellow"].setText("")
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
				if config.plugins.MerlinSkinThemes.Designs["design"].value == "-none-":
					self.readThemes()
				else:
					# PreviewPNG anzeigen
					pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + config.plugins.MerlinSkinThemes.Designs["design"].value + ".png"

					if not fileExists(pngpath):
						pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

					self["Preview"].instance.setPixmapFromFile(pngpath)
					self["Preview"].show()
					
					self.setDesign()
			else:
				if config.plugins.MerlinSkinThemes.Designs["design"].value != "-none-":
					config.plugins.MerlinSkinThemes.Designs["design"].value = "-none-"
					self["config"].invalidate(("Design", config.plugins.MerlinSkinThemes.Designs["design"]))
	
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
				if config.plugins.MerlinSkinThemes.Designs["design"].value == "-none-":
					self.readThemes()
				else:
					# PreviewPNG anzeigen
					pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + config.plugins.MerlinSkinThemes.Designs["design"].value + ".png"

					if not fileExists(pngpath):
						pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

					self["Preview"].instance.setPixmapFromFile(pngpath)
					self["Preview"].show()

					self.setDesign()
			else:
				if config.plugins.MerlinSkinThemes.Designs["design"].value != "-none-":
					config.plugins.MerlinSkinThemes.Designs["design"].value = "-none-"
					self["config"].invalidate(("Design", config.plugins.MerlinSkinThemes.Designs["design"]))
	
	def changedSkinsList(self):
		self["SkinCopyright"].setText("")
		
		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		#if fileExists(MerlinSkinThemes.selSkinFile):
		#	self.CopyrightInfo()
			
		if config.plugins.MerlinSkinThemes.ShowPrevPNG.value == "1":
			self.loadPreview()
		
		if self["SkinsList"].getCurrent()[2][7] == _("active skin"):
			self["key_green"].hide()
		else:
			self["key_green"].show()

		if self["SkinsList"].getCurrent()[3][7] == _("no skin.xml"):
			self["key_green"].hide()

			self["key_yellow"].show()
			self["key_yellow"].setText(_("delete"))
			
		elif self["SkinsList"].getCurrent()[3][7] == _("no themes.xml"):
			self["key_green"].show()
			
			self["key_yellow"].show()
			self["key_yellow"].setText(_("create themes"))
			
		else:
			self["key_yellow"].show()

			self["key_yellow"].hide()
			#self.readThemes()
			
	def updateSkinList(self):
		self["SkinsList"].buildList()

	def createThemes(self):
		if fileExists(MerlinSkinThemes.selThemeFile) == False:
			themes = Tree.Element("themes")
			
			curTree = Tree.parse(MerlinSkinThemes.selSkinFile)
			
			for theme in [("colortheme", "colors", "color"), ("fonttheme", "fonts", "font"), ("layouttheme", "layouts", "layout"), ("globalstheme", "globals", ""), ("bordersettheme", "", "borderset"), ("windowstylescrollbartheme", "", ""), ("pngtheme", "", "")]:
				parentnode1 = Tree.SubElement(themes, theme[0], {"name": "orginal", "value": "active"})
				if theme[0] == "globalstheme":
					childnode1 = Tree.SubElement(parentnode1, theme[1], {"name": "sample", "value": "120,50"})
				elif theme[1] != "":
					childnode1 = Tree.SubElement(parentnode1, theme[1])
				parentnode2 = Tree.SubElement(themes, theme[0], {"name": "orginal - work", "value": "inactive"})
				if theme[0] == "globalstheme":
					childnode2 = Tree.SubElement(parentnode2, theme[1], {"name": "sample", "value": "120,50"})
				elif theme[1] != "":				
					childnode2 = Tree.SubElement(parentnode2, theme[1])

				parentnodeSkin = curTree.find(theme[1])				
				if theme[0] in ["colortheme", "fonttheme"]:
					attributeDict = {}
					for element in parentnodeSkin.findall(theme[2]):
						name = element.get("name", None)
						if name is not None:
							attributeDict["name"] = name
						value = element.get("value", None)
						if value is not None:
							attributeDict["value"] = value
						filename = element.get("filename", None)
						if filename is not None:
							attributeDict["filename"] = filename
						scale = element.get("scale", None)
						if scale is None and element == "font":
							scale = "100"
						if scale is not None:
							attributeDict["scale"] = scale
						replacement = element.get("replacement", None)
						if replacement is None and element == "font":
							replacement = "0"
						if replacement is not None:
							attributeDict["replacement"] = replacement
					
						Tree.SubElement(childnode1, theme[2], attributeDict)
						Tree.SubElement(childnode2, theme[2], attributeDict)
				# todo: check if it can be integrated in if
				elif theme[0] == "bordersettheme":
					ws = curTree.find("windowstyle")
					for bs in ws.findall(theme[2]):
						if bs.get("name") == "bsWindow":
							parentnode1.append(Tree.fromstring(Tree.tostring(bs)))
							parentnode2.append(Tree.fromstring(Tree.tostring(bs)))
			
						if bs.get("name") == "bsListboxEntry":
							parentnode1.append(Tree.fromstring(Tree.tostring(bs)))
							parentnode2.append(Tree.fromstring(Tree.tostring(bs)))	
				elif theme[0] == "windowstylescrollbartheme":
					for wssb in curTree.findall("windowstylescrollbar"):
						if wssb.get("id") == "4":
							for sb in wssb.findall("*"):
								parentnode1.append(Tree.fromstring(Tree.tostring(sb)))
								parentnode2.append(Tree.fromstring(Tree.tostring(sb)))
				elif theme[0] == "layouttheme":
					Tree.SubElement(childnode1, theme[2], {"name": "sample"}).append(Tree.Comment('Sample: <widget source="Title" render="Label" position="200,77" size="400,40" halign="left" valign="center" font="Regular; 30" foregroundColor="title" backgroundColor="bg2" transparent="1" zPosition="1" />'))
					Tree.SubElement(childnode2, theme[2], {"name": "sample"})
				elif theme[0] == "pngtheme":
					parentnode1.append(Tree.Comment('Sample: name=path+png_name (root=skindir), argb=a:alpha r:red g:green b:blue'))
					parentnode1.append(Tree.Comment('<png name="design/progress.png" width="814" height="5" argb="#ff55a0ff" />'))
					parentnode2.append(Tree.Comment('<png name="design/progress.png" width="814" height="5" argb="#ffffa055" argb2="#ff000000" gtype="vertical"/>'))
			
			# screenthemes
			screenthemes = Tree.SubElement(themes, "screenthemes")
			for screenname in screenList:
				screennode = Tree.SubElement(screenthemes, "screens", {"name": screenname })
				childnode1 = Tree.SubElement(screennode, "screentheme", {"name": "orginal", "value": "active"})
				childnode2 = Tree.SubElement(screennode, "screentheme", {"name": "orginal - work", "value": "inactive"})
				
				skinScreen = curTree.find("screen[@name='%s']" %(screenname))
				if skinScreen is not None:
					childnode1.append(Tree.fromstring(Tree.tostring(skinScreen)))
					childnode2.append(Tree.fromstring(Tree.tostring(skinScreen)))
			
			# displayscreenthemes
			if displayTag is not None:
				displayscreenthemes = Tree.SubElement(themes, displayTag)
				for displayscreenname in displayScreenList: 
					displayscreennode = Tree.SubElement(displayscreenthemes, "screens", {"name": displayscreenname, "id": IdString})
					childnode1 = Tree.SubElement(displayscreennode, displayTag[:-1], {"name": "orginal", "value": "active"})
					childnode2 = Tree.SubElement(displayscreennode, displayTag[:-1], {"name": "orginal - work", "value": "inactive"})
					skinScreen = curTree.find("screen[@name='%s'][@id='%s']" %(displayscreenname, IdString))
					if skinScreen is not None:
						childnode1.append(Tree.fromstring(Tree.tostring(skinScreen)))
						childnode2.append(Tree.fromstring(Tree.tostring(skinScreen)))				

			# Sort
			XMLindent(themes, 0)
			
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
				_("[OK]\nswitch to themes/designs config screen for selected skin\n\n" + 
				"[create themes] and [delete]\ntakes some time - please wait\n\n" +
				'[menu]\nremove <screen name="MerlinSkinThemes"...> from selected skin.'
				"This can fix a greenscreen if skin is not up to date for MST.")
			)

		elif self.curList == "ConfigList":
			HelpText = (
				_("[OK]\nswitch to skin selection screen\n\n" + 
				"[apply themes] takes some time - please wait\n\n" + 
				"[delete design]\ndelete selected design\n\n" + 
				"[save as design]\nselected themes/screens stored in new design\n\n" +
				"choose Design: -none-\nto reset themes to active settings/themes")
			)
		
		self.session.open(MessageBox, HelpText, MessageBox.TYPE_INFO, title=_("MerlinSkinThemes - Help"))

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
					_("Skin ORGINAL - No info available")
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
					_("Skin MOD - No info available")
				)
		
			InfoText = OrgText + "\n\n" + ModText

		else:
			InfoText = _("No copyright info available")
			
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
		
	def Info(self):
		if config.plugins.MerlinSkinThemes.ShowPrevPNG.value == "1":
			config.plugins.MerlinSkinThemes.ShowPrevPNG.value = "0"
			self.session.open(MessageBox, _("Show prev.png - ") + _("Off"), MessageBox.TYPE_INFO, timeout=3)
			self["Preview"].hide()
		else:
			config.plugins.MerlinSkinThemes.ShowPrevPNG.value = "1"
			self.session.open(MessageBox, _("Show prev.png - ") + _("On"), MessageBox.TYPE_INFO, timeout=3)
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
			self.exit(False)

	def save(self):
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("Do you want to Restart the GUI now to apply new skin settings?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))

	def exit(self, cancel=True):
		print '[MST] closing'
		self["SkinsList"].onSelectionChanged.remove(self.changedSkinsList)
		if cancel:
			# exit means settings must not be stored
			config.plugins.MerlinSkinThemes.Skin.cancel()
			config.plugins.MerlinSkinThemes.selSkin.cancel()
			config.plugins.MerlinSkinThemes.ShowPrevPNG.cancel()
			config.plugins.MerlinSkinThemes.CornerRadius.cancel()
			if "Designs" in config.plugins.MerlinSkinThemes.dict():
				for key in config.plugins.MerlinSkinThemes.Designs:
					config.plugins.MerlinSkinThemes.Designs[key].cancel()
			if "Themes" in config.plugins.MerlinSkinThemes.dict():
				for key in config.plugins.MerlinSkinThemes.Themes:
					config.plugins.MerlinSkinThemes.Themes[key].cancel()
			if "Screens" in config.plugins.MerlinSkinThemes.dict():
				for key in config.plugins.MerlinSkinThemes.Screens:
					config.plugins.MerlinSkinThemes.Screens[key].cancel()
			if "DisplayScreens" in config.plugins.MerlinSkinThemes.dict():
				for key in config.plugins.MerlinSkinThemes.DisplayScreens:
					config.plugins.MerlinSkinThemes.DisplayScreens[key].cancel()
		self.close()
		
def main(session, **kwargs):
	session.open(MerlinSkinThemes)

def Plugins(path,**kwargs):
	list = [PluginDescriptor(name = "MerlinSkinThemes", description = "MerlinSkinThemes", where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main)]
	return list		

class MerlinSkinThemesConfig(Screen, HelpableScreen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="600,200" title="Merlin Skin Themes - Config" backgroundColor="#00808080" >
			<widget name="config" position="10,10" size="580,100" scrollbarMode="showOnDemand" zPosition="1" /> 
			<widget name="key_red" position="10,150" size="200,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<widget name="key_green" position="390,150" size="200,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<ePixmap name="red" position="10,150" zPosition="1" size="200,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="blend" />
			<ePixmap name="green" position="390,150" zPosition="1" size="200,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="blend" />
		</screen>"""
		
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Save"))

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red":     (self.closePlugin, _("Close plugin")),
			"green":   (self.saveSettings,_("Save settings")),
		}, -1)
		
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"ok":		(self.saveSettings, _("Save settings")),
			"cancel":	(self.closePlugin, _("Close plugin")),
		}, -1)

		self.list = []
		self.list.append(getConfigListEntry(_("Rebuild skin on boot"), config.plugins.MerlinSkinThemes.rebuildSkinOnBoot))
		
		ConfigListScreen.__init__(self, self.list)
		
		self["config"].setList(self.list)
	
	def saveSettings(self):
		config.plugins.MerlinSkinThemes.rebuildSkinOnBoot.save()
		configfile.save()
		self.close()
		
	def closePlugin(self):
		config.plugins.MerlinSkinThemes.rebuildSkinOnBoot.cancel()
		configfile.save()
		self.close()

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
		self.selectedIndex = 0
		
	def buildList(self):
		list = []
		self.selectedIndex = 0

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
						info = _("no skin.xml")

					if themexml is False:
						info = _("no themes.xml")

					if dir == SkinName:
						status = _("active skin")

					res = [
						dir,
						(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, dirWidth, configEntryHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, dir),
						(eListboxPythonMultiContent.TYPE_TEXT, 5 + dirWidth, 0, statusWidth, configEntryHeight, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, status),
						(eListboxPythonMultiContent.TYPE_TEXT, 5 + dirWidth + statusWidth, 0, infoWidth, configEntryHeight, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, info),
					]
					list.append(res)

					
		self.list = list.sort()
		for x in range(len(list)):
			if list[x][2][7] == _("active skin"):
				self.selectedIndex = x

			
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
