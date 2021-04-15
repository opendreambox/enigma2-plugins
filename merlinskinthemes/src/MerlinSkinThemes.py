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

from __future__ import print_function

from Plugins.Plugin import PluginDescriptor

from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
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
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, getConfigListEntry, ConfigSelection, ConfigNumber, ConfigText, ConfigInteger, ConfigSubDict, ConfigBoolean, NoSave
from Components.ConfigList import ConfigListScreen

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, getEnigmaVersionString, getDesktop

from Tools.BoundFunction import boundFunction
from Tools.HardwareInfo import HardwareInfo
from Tools.Directories import resolveFilename, SCOPE_SKIN, SCOPE_PLUGINS, fileExists, createDir
from Tools import Notifications

from MerlinSkinThemesHelp import MerlinSkinThemesHelp

import xml.etree.cElementTree as Tree
import shutil
import os
# =========================================
PluginVersion = "v3.0.4"
Title = "MerlinSkinThemes - The Original "
Author = "by marthom"
# =========================================

SkinXML = config.skin.primary_skin.value
SkinFile = resolveFilename(SCOPE_SKIN) + SkinXML
SkinName = SkinXML[0:SkinXML.find("/")]
ThemeFile = resolveFilename(SCOPE_SKIN) + SkinName + "/themes.xml"
skin_user_xml = "/etc/enigma2/skin_user.xml"
enigmacontrol = "/var/lib/opkg/info/enigma2.control"
merlinChk = "/usr/share/enigma2/merlin_setup.xml"
PIL = "/usr/lib/python2.7/site-packages/PIL/Image.py"
CONFDIR = "/etc/enigma2/merlinskinthemes/"

# Merlin
Merlin = False
if fileExists(merlinChk):
	Merlin = True

# Arm/mipsel/aarch64
ArchArm = False
Arch64 = False
ArchMipsel = False

if HardwareInfo().get_device_name() in ('dm900', 'dm920'):
	ArchArm = True
	ArchString = "ARM"
elif HardwareInfo().get_device_name() == 'one':
	Arch64 = True
	ArchString = "AARCH64"
elif HardwareInfo().get_device_name() == 'two':
	Arch64 = True
	ArchString = "AARCH64"
else:
	ArchMipsel = True
	ArchString = "MIPSEL"
ModelString = HardwareInfo().get_device_name().upper()
IdString = "0" # no display
if HardwareInfo().get_device_name() in ('dm900', 'dm920', 'dm820','dm7080', 'two'):
	IdString = "%d" %(getDesktop(1).getStyleID())
displayDict = {"1": "lcdscreenthemes", "2": "oledscreenthemes", "3": "extlcdscreenthemes", "100": "lcdscreenthemes" }
displayTag = displayDict.get(IdString, None)

# List of preview pics
previewPicList = ["InfoBar", "Menu", "PluginBrowser", "ChannelSelection", "MovieSelection", "MoviePlayer", "SecondInfoBar", "GraphMultiEPG", "MessageBox", "InputBox", "ChoiceBox", "Mute", "Volume","MerlinMusicPlayer2Screen_%s" %(ArchString),"InfoBarSummary", "StandbySummary", "InfoBarMoviePlayerSummary", "MerlinMusicPlayer2LCDScreen"]

print("------------------------------------------------")
print(HardwareInfo().get_device_name())
print(PluginVersion)
print("------------------------------------------------")

# windowstyle id=0: GUI --> borderset can only be defined here
# windowstyle id=1: LCD
# windowstyle id=2: OLED
# windowstyle id=3: ???
# windowstyle id=4/5: scrollbar --> windowstylescrollbar (4 = vertical scrollbar; 5 = horizontral scrollbar)

# skin_user.xml
SkinUser = False
if fileExists(skin_user_xml):
	SkinUser = True
	
# Config
config.plugins.MerlinSkinThemes3 = ConfigSubsection()
config.plugins.MerlinSkinThemes3.rebuildSkinOnBoot = ConfigBoolean(default=True)
config.plugins.MerlinSkinThemes3.showInExtensions = ConfigBoolean(default=True)
config.plugins.MerlinSkinThemes3.showPreviewPicture = ConfigBoolean(default=True)
config.plugins.MerlinSkinThemes3.Skin = ConfigText(default=SkinName)
config.plugins.MerlinSkinThemes3.selSkin = ConfigText(default=SkinName)
config.plugins.MerlinSkinThemes3.designModified = ConfigBoolean(default=False)


def initConfigSubDict3():
	config.plugins.MerlinSkinThemes3.Designs = ConfigSubDict()
	config.plugins.MerlinSkinThemes3.DesignColors = ConfigSubDict()
	config.plugins.MerlinSkinThemes3.Themes = ConfigSubDict()
	config.plugins.MerlinSkinThemes3.Screens = ConfigSubDict()
	config.plugins.MerlinSkinThemes3.DisplayScreens = ConfigSubDict()
	config.plugins.MerlinSkinThemes3.CornerRadius = ConfigSubDict()
		
# list of display screens (a.k.a. summaries)
displayScreenList = ["InfoBarSummary", "EventView_summary", "StandbySummary", "InfoBarMoviePlayerSummary", "MerlinMusicPlayer2LCDScreen"]
# list of screens
screenList = ["InfoBar", "Menu", "PluginBrowser", "ChannelSelection", "MovieSelection", "MoviePlayer", "SecondInfoBar", "GraphMultiEPG", "EventView", "EPGSelection", "MessageBox", "InputBox", "ChoiceBox", "Mute", "Volume", "MerlinMusicPlayer2Screen_%s" %(ArchString), "MerlinMusicPlayer2ScreenSaver_%s" %(ArchString)]
# list of themes
themeList = ["ColorTheme", "SkinPathTheme", "FontTheme",  "BorderSetTheme", "WindowStyleScrollbarTheme", "ComponentTheme", "LayoutTheme", "GlobalsTheme", "PNGTheme" ]

# shared functions
# ImageCreator
import Image
import ImageDraw
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
	#i = a % ' 
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

def setThemes(themeFile=None, skinFile=None, configDictFile=None, retFunc=None):
	print("[MST] - start applying changes to themes.xml")
	
	configDict = {}
	# read config data
	f = open(configDictFile, 'r')
					
	for line in f:
		configData = line.split(":::")
		if len(configData)==2:
			configDict[configData[0]] = configData[1].strip("\n")
	f.close()
	
	# first, we update themes.xml by setting the selected option to active and all others to inactive
	with open(themeFile, 'rb') as theme:
		curTheme = Tree.parse(theme)
	rootTheme = curTheme.getroot()
	themeVersion = rootTheme.get('version')
	if themeVersion is not None:
		if themeVersion not in ("1.0"):
			return False

	themeDict = {}
	
	print("[MST] - updating designs")
	if rootTheme.find("designs") is not None:
		ds = rootTheme.find("designs")
		designNameList = [ x.get('name') for x in ds.findall("design") ]
		currentValue = configDict.get("design", None)
		currentDscValue = configDict.get("designColor", None)
		if not currentValue in designNameList:
			activeDesignList = [ x.get('name') for x in ds.findall("design") if x.get('value') == 'active' ]
			if len(activeDesignList):
				print("[MST] - Design stored in config does no longer exist in skin. Using active design")
				currentValue = activeDesignList[0]
		activeDesignName = None
		for design in ds.findall("design"):
			if design.get('name') == currentValue:
				design.set("value", "active")
				activeDesignName = design.get('name')
			
				if design.find("designColors") is not None:
					# don't update designColors if value is -none-
					if currentDscValue != "-none-":
						dsc = design.find("designColors")
						designColorNameList = [ x.get('name') for x in dsc.findall('designColor') ]
						if not currentDscValue in designColorNameList:
							activeDesignColorList = [ x.get('name') for x in dsc.findall('designColor')  if x.get('value') == 'active' ]
							if len(activeDesignColorList):
								print("[MST] - Design color stored in config does no longer exist in skin. Using active design color")
								currentDscValue = activeDesignColorList[0]
						for designColor in dsc.findall("designColor"):
							if designColor.get('name') == currentDscValue:
								designColor.set("value", "active")
							else:
								designColor.set("value", "inactive")
			else:
				if currentValue is None:
					if design.get('value') == 'active':
						activeDesignName = design.get('name')
						print("[MST] - current design is None - use active design from themes ", activeDesignName)
				else:
					design.set("value", "inactive")
					
	print("[MST] - updating themes")
	for theme in [
		("colortheme", "colors", "color"),
		("fonttheme", "fonts", "font"), 
		("layouttheme", "layouts", "layout", "*"),
		("globalstheme", "globals", "value"),
		("bordersettheme","borderset", "pixmap"),
		("windowstylescrollbartheme", "*", ""),
		("componenttheme", "components", "component", "*"),
		("skinpaththemes", "theme", ""),
		("pngtheme", "png", ""),
		]:
		for currenttheme in rootTheme.findall(theme[0]):
			currentValue = configDict.get("%s" %(theme[0]), None)
			
			# skinpaththemes has name on child level!
			if theme[0] == "skinpaththemes":
				currentValue = configDict.get("%s" %(theme[0][:-1]), None)
				oldSkinPath = None
				newPath = None
				newSkinPath = None
				for child in currenttheme.findall(theme[1]):
					if child.get('value') == 'active':
						oldSkinPath = child.get('path')
						child.set("value", "inactive")
					if child.get("name") == currentValue:
						child.set("value", "active")
						newSkinPath = child.get('path')
						themeDict[theme[0]] = newSkinPath
					else:
						child.set("value", "inactive")
				if newSkinPath is not None and oldSkinPath is not None:
					print("[MST] - replacing %s by %s in screens" %(oldSkinPath, newSkinPath))
					for attr in ('pixmap', 'pointer', 'picServiceEventProgressbar'):
						for pathElement in rootTheme.findall('.//screens/*/screen/*[@%s]' %(attr)):
							currentPath = pathElement.get('%s' %(attr))
							if currentPath is not None:
								newPath = currentPath.replace(oldSkinPath, newSkinPath)
								pathElement.set("%s"%(attr), newPath)
					for pathElement in rootTheme.findall('.//bordersettheme/borderset/pixmap[@filename]'):
						currentPath = pathElement.get('filename')
						if currentPath is not None:
							newPath = currentPath.replace(oldSkinPath, newSkinPath)
							pathElement.set("filename", newPath)

			else:
				# name matches - set to active and store values
				if currenttheme.get("name") == currentValue:
					currenttheme.set("value", "active")
					themeElement = None
					if theme[0] in ["bordersettheme", "globalstheme", "windowstylescrollbartheme", "fonttheme", "colortheme", "componenttheme", "layouttheme" ]:
						subList = []
						for child in currenttheme.findall(theme[1]):
							tempList = []
							if theme[2] == "":
								if theme[1] == "*":
									subDict = {}
									tempDict = child.attrib
									tempDict['tag'] = child.tag
									tempList.append(child.attrib)
									subDict[child.get('name')] = tempList
									subList.append(subDict)
									themeDict[theme[0]] = subList
							
							else:
								for grandchild in child.findall(theme[2]):
									# Value by ref! If grandchild.attrib is directly assigned to attribsDict, grandchild.attrib is modified by assigning l4List to attribsDict
									attribsDict = dict(grandchild.attrib)
									
									if len(theme)==4:
										if theme[3] == "*":
											l4List = []
											for greatgrandchild in grandchild.findall(theme[3]):
												l4Dict = {}
												l4ValueDict = {}
											
												l5List = []
												
												for greatgreatgrandchild in greatgrandchild.findall('*'):
													l5Dict = {}
													l5ValueDict = {}
													l5ValueDict['attrib'] = greatgreatgrandchild.attrib
													l5ValueDict['text'] = greatgreatgrandchild.text
													l5Dict[greatgreatgrandchild.tag] = l5ValueDict
											
													l5List.append( l5Dict )
												
												if len(l5List):
													l4ValueDict['l5'] = l5List
												

												l4ValueDict['attrib'] = greatgrandchild.attrib
												l4ValueDict['text'] = greatgrandchild.text
												l4Dict[greatgrandchild.tag] = l4ValueDict
											
												l4List.append( l4Dict )
											if len(l4List):
												attribsDict['l4'] = l4List

									tempList.append(attribsDict)				

								if child.get("name") is not None:
									subDict = {}
									print("[MST] - theme[1] has name - use it to build subDict")
									subDict[child.get("name")] = tempList
									subList.append(subDict)
									themeDict[theme[0]] = subList
								else:
									print("[MST] - theme[1] has no name - use theme[0]")
									themeDict[theme[0]] = tempList
							if theme[2] == "" and theme[1] != "*":
								print("[MST] - theme[2] is empty - use theme[0]", tempList)
								themeDict[theme[0]] = tempList
							
					# pictures can be generated - no need to store values in dict
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
									imageCreator.createRectangle(png_width, png_height, (acolor[1], acolor[2], acolor[3], acolor2[0]),(acolor2[1], acolor2[2], acolor2[3], acolor2[0]), skinFile[:-8] + png_name, gradienttype) 
								else:
									imageCreator.createRectangle(png_width, png_height, (acolor[1], acolor[2], acolor[3], acolor[0]), None, skinFile[:-8] + png_name)

					# add all elements from themes.xml to skin.xml
					if themeElement is not None:
						if theme[2] != "":
							tempList = []
							for childElement in themeElement.findall(theme[2]):
								attributeDict = {}
								if theme[0] in ["colortheme", "fonttheme" ]:
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
									
									tempList.append(attributeDict)

							if len(tempList):
								themeDict[theme[2]] = tempList

				# name does not match - set it to inactive	
				else:
					currenttheme.set("value", "inactive")
	
	print("[MST] - updating screens and displayscreens")
	screenDict = {}
	screenThemeData = [("screenthemes", "screens", "screentheme", "screen")]
	if displayTag is not None:
		screenThemeData.append((displayTag, "screens", displayTag[:-1], "screen"))
	for theme in screenThemeData:
		for currenttheme in rootTheme.findall(theme[0]):
			for currentscreen in currenttheme.findall(theme[1]):
				screenname = currentscreen.get('name')
				currentValue = configDict.get("%s" %(screenname))
				for screentheme in currentscreen.findall(theme[2]):
					
					if screentheme.get('name') == currentValue:
						screentheme.set("value", "active")
						newscreen = screentheme.find(theme[3])
						screenDict[screenname]=Tree.tostring(newscreen)
					else:
						screentheme.set("value", "inactive")
	
	radiusFound = False	

	radiusValue = configDict.get('CornerRadius')
	if radiusValue is None:
		radiusValue = configDict.get('cornerradius')
	radiusFound = True

	excludedCornerRadiusValue = None		

	print("[MST] - updating cornerradius")
	if themeVersion is None:
		for cRadius in rootTheme.findall("cornerradius"):
			excludedCornerRadiusValue = cRadius.get('exclude')
			for radius in cRadius.findall("radius"):
				if radius.get("name") == radiusValue:
					radius.set("value", "active")
				else:
					radius.set("value", "inactive")
	elif themeVersion == "1.0":
		designNode = rootTheme.find("designs")
		if activeDesignName is not None:
			activeDesign = designNode.find("design[@name='%s']" %(activeDesignName))
			if activeDesign is not None:
				cRadius = activeDesign.find("cornerRadius")
				if cRadius is not None:
					excludedCornerRadiusValue = cRadius.get('exclude')
					for radius in cRadius.findall("radius"):
						if radius.get("name") == radiusValue:
							radius.set("value", "active")
						else:
							radius.set("value", "inactive")
		else:
			print("[MST] - cannot update CornerRadius as design does not longer exist")

	# write changes to themes.xml
	with open(themeFile, 'wb') as theme:
		curTheme.write(theme)
	print("[MST] - themes.xml updated")
	
	# now, we update skin.xml
	with open(skinFile, 'rb') as skin:
		curSkin = Tree.parse(skin)
	rootSkin = curSkin.getroot()

	print("[MST] - start applying changes to skin.xml")
	# let's brand the skin as edited by MST
	if rootSkin.find("merlinskinthemes") is None:
		mst = Tree.Element("merlinskinthemes", {"text":"Edited with MerlinSkinThemes3"})
		rootSkin.insert(0, mst)
								
	tagDict = {
		"colortheme": ["colors", "color"],
		"fonttheme":  ["fonts", "font"],
		"layouttheme": ["layouts", "layout"],
		"globalstheme": ["globals", "value"],
		"bordersettheme": ["borderset", "pixmap"],
		"windowstylescrollbartheme": ["windowstylescrollbar", "*"],
		"componenttheme": ["components", "component"],
		"skinpaththemes": ["theme"],
		}

	print("[MST] - applying screens")
	for screen in rootSkin.findall('screen'):
		screenname = screen.get('name')
			
		screenId = screen.get('id')
		if screenId is not None and screenId != IdString:
			continue

		screenData = screenDict.get(screenname)
		if screenData is not None:
			
			# delete old screen
			rootSkin.remove(screen)
			
			# insert new screen
			rootSkin.append(Tree.fromstring(screenData))

	print("[MST] - applying themes")
	# themes must be applied post screens as skinpaththemes update paths in screens
	# iterate over the dict and update skin.xml	
	for key, value in themeDict.iteritems():	
		print("key is", key)	
		tagList = tagDict.get(key)
		node = tagList[0]
		elementIndex = 1
		
		# for skinpaththemes we have to update the path in all elements with a path attribute
		if key == "skinpaththemes" and oldSkinPath is not None:
			for attr in ['pixmap', 'pointer', 'picServiceEventProgressbar']:
				for pathelement in rootSkin.findall('.//*[@%s]' %(attr)):
					currentPath = pathelement.get('%s' %(attr))
					if currentPath is not None:
						newPath = currentPath.replace(oldSkinPath, value)
						pathelement.set("%s"%(attr), newPath)
			
			if themeDict.get('windowstylescrollbartheme') is None:
				for idValue in ('4', '5'):
					for pathelement in rootSkin.findall('.//windowstylescrollbar[@id="%s"]/pixmap[@filename]' %(idValue)):
						currentPath = pathelement.get('filename')
						if currentPath is not None:
							newPath = currentPath.replace(oldSkinPath, value)
							pathelement.set("filename", newPath)
				
			for pathelement in rootSkin.findall('.//windowstyle[@id="0"]/borderset/pixmap[@filename]'):
				currentPath = pathelement.get('filename')
				if currentPath is not None:
					newPath = currentPath.replace(oldSkinPath, value)
					pathelement.set("filename", newPath)
			continue
		
		if key == "bordersettheme":
			node = "windowstyle"
			elementIndex = 0

		elementList = rootSkin.findall(node)
		if not len(elementList):
			continue
		# single element lists are: colors, globals, fonts
		# multi element lists are: windowstyle (but only 1 is relevant)
		for element in elementList:
			if element.tag == "windowstyle" and element.get('id') != "0":
				continue
			if element.tag == "windowstylescrollbar" and element.get('id') not in ("4", "5"):
				print("[MST] - windowstylescrollbar with id != 4/5")
				continue
			# list with all matching elements in skin.xml
			elementList = element.findall(tagList[elementIndex])

			# remove existing elements in skin.xml
			for elementListItem in elementList:
				if elementIndex == 1:
					element.remove(elementListItem)
				else:
					subElementList = elementListItem.findall(tagList[elementIndex+1])
					for subElementListItem in subElementList:
						elementListItem.remove(subElementListItem)
		
		# key: bordersettheme; value: list of dict
		# key: fonttheme; value: list of dict
		for item in value:
			hasSub = False
			# key: bsWindow; value: list of dict
			# key: scale; value: 100
			
			for subkey, subvalue in item.iteritems():
				# l4 will be handled later
				if subkey == "l4":
					continue
				if isinstance(subvalue, list):
					# key: pos; value: bpTopLeft
					for subitem in subvalue:
						hasSub = True
						# this is safe as there's exactly one matching windowstyle element in skin.xml
						tempElement = rootSkin.find("./%s[@id='0']/%s[@name='%s']" %(node, tagList[0], subkey))
						if tempElement is not None:
							Tree.SubElement(tempElement, tagList[elementIndex+1], subitem)
						else:
							# this is safe as there's exactly one matching windowstylescrollbar element in skin.xml
							tempElement = rootSkin.find("./%s[@id='4']" %(node))
							if tempElement is not None:
								tag = subitem.get('tag')
								if subitem.get('tag') is not None:
									del subitem['tag']
									Tree.SubElement(tempElement, tag, subitem)
							
							tempElement = rootSkin.find("./%s[@id='5']" %(node))
							if tempElement is not None:
								tag = subitem.get('tag')
								if subitem.get('tag') is not None:
									del subitem['tag']
									Tree.SubElement(tempElement, tag, subitem)


			# add element again with data from dict
			if not hasSub:
				# check if we have an additional level
				if item.get('l4') is not None:
					l4List = item.get('l4')
					# attribute l4 must be deleted otherwise it's added to the element - crashes guaranteed
					del item['l4']
					newElem = Tree.SubElement(element, tagList[elementIndex], item)
					for l4Item in l4List:
						for itemKey, itemValue in l4Item.iteritems():
							newL4Elem = Tree.SubElement(newElem, itemKey, itemValue.get('attrib', {}))
							newL4Elem.text = itemValue.get('text', '')
							# widgets can have an additional level with the converter information
							for l5Item in itemValue.get('l5', []):
								for l5ItemKey, l5ItemValue in l5Item.iteritems():
									Tree.SubElement(newL4Elem, l5ItemKey, l5ItemValue.get('attrib', {})).text = l5ItemValue.get('text', '')
				else:
					Tree.SubElement(element, tagList[elementIndex], item)	

	print("[MST] - applying cornerradius")
	# replace value of cornerRadius attribute in all eLabel elements in skin.xml
	for elabel in rootSkin.findall('.//eLabel[@cornerRadius]'):
		# current cornerRadius is not matching excluded value from theme		
		if elabel.get("cornerRadius") != excludedCornerRadiusValue:
			if radiusValue is not None:
				elabel.set("cornerRadius", radiusValue)

	# elementtree does not support pretty print - so we do it
	XMLindent(rootSkin,0)
	#newXml = addIndent(rootSkin, 0)
	# write updates to skin.xml
	curSkin.write(skinFile)
	print("[MST] - skin.xml updated")
	
	if retFunc is not None:
		retFunc

class MerlinSkinThemes(Screen, HelpableScreen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="1920,1080" title="%s" backgroundColor="#00303030" >
			<widget name="DescLabel" position="10,10" size="1900,40" font="Regular;26" zPosition="2" valign="center" halign="center" />

			<widget name="ListLabel" position="10,60" size="945,40" font="Regular;26" zPosition="2" valign="center" halign="center" />
	
			<widget name="SkinsList" position="10,110" size="945,840" scrollbarMode="showOnDemand" zPosition="4" />
			<widget name="config" position="10,110" size="945,840" scrollbarMode="showOnDemand" zPosition="4" separation="450" /> 
			
			<widget name="descriptionText" position="10,970" size="945,50" font="Regular;26" halign="center" />
			
			<widget name="ImageInfo" position="965,60" size="945,40" font="Regular;23" zPosition="2" halign="left" />
			<widget name="SkinCopyright" position="965,100" size="945,220" font="Regular;23" zPosition="2" halign="left" />
			<widget name="Preview" position="965,320" size="945,700" alphatest="blend" scale="1" />

			<widget name="key_red" position="10,1030" size="220,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<widget name="key_green" position="245,1030" size="220,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<widget name="key_yellow" position="480,1030" size="220,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />
			<widget name="key_blue" position="715,1030" size="220,40" valign="center" halign="center" zPosition="3" transparent="1" font="Regular;24" />

			<ePixmap name="red" position="10,1030" zPosition="1" size="225,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="blend" scale="stretch" />
			<ePixmap name="green" position="245,1030" zPosition="1" size="225,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="blend" scale="stretch"/>
			<ePixmap name="yellow" position="480,1030" zPosition="1" size="225,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="blend" scale="stretch" />
			<ePixmap name="blue" position="715,1030" zPosition="1" size="225,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="blend" scale="stretch" />
		</screen>"""% ("MerlinSkinThemes")

	ThemeName = ""
	selSkinName = ""
	selThemeFile = ""
	
	def __init__(self, session):
		print("[MST] " + PluginVersion + " running...")
		self.session = session
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		self.configInitDone = False
		self.clist = []
		ConfigListScreen.__init__(self, self.clist)
		
		self.setTitle(Title + " " + PluginVersion + " - " + Author)

		self["DescLabel"] = Label(Title + " " + PluginVersion + " " + Author)
		self["SkinCopyright"] = Label()
		self["Preview"] = Pixmap()
		self["ImageInfo"] = Label()
		self["ListLabel"] = Label()
		self["descriptionText"] = Label()
		
		self.curList = "SkinsList"

		self.setListLabelText()
				
		self["key_red"] = Button(_("exit"))
		self["key_green"] = Button(_("switch to skin"))
		self["key_yellow"] = Button(_("save as design"))
		self["key_blue"] = Button(_("More..."))
		
		self.helpDict = {
			"ColorTheme": 		_("ColorTheme: A ColorTheme defines the set of colors. This allows to give a skin a completely different appearance."),
			"FontTheme":		_("FontTheme: A FontTheme defines the font used in the skin."),
			"BorderSetTheme":	_("BorderSetTheme: A BorderSetTheme defines graphics used for windows and listboxes."),
			"SkinPathTheme": 	_("SkinPathTheme: A SkinPathTheme define the path value in all elements of the skin. This allows to change graphics used."),
			"ComponentTheme":	_("ComponentTheme: A ComponentTheme defines the look and feel of components used in e.g. Movielist or Channel Selection."),
			"CornerRadius":		_("CornerRadius: A CornerRadius defines the look and feel of corners."),
			"LayoutTheme":		_("LayoutTheme: A LayoutTheme defines layouts that are reused in the skin and guarantee e.g. a consistent look and feel of buttons."),
			"GlobalsTheme":		_("GlobalsTheme: A GlobalsTheme defines values for variables that are reused in the skin and guarantee e.g. a consistent position of elements."),
			"PNGTheme":			_("PNGTheme: A PNGTheme defines the values that are used to generate graphics that are used e.g. for progress bars.")
		
		}
		
		self.skinsList = []
		self["SkinsList"] = GetSkinsList([])

		self.onSelectionChanged = [ ]
		
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red":     self.buttonRed,
			"green":   self.buttonGreen,
			"yellow":  self.buttonYellow,
			"blue":	   self.openContextMenu,
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

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
		{
			"menu":		(self.openContextMenu, _("Open context menu")),
		}, -1)
		
		self["ChannelSelectEPGActions"] = HelpableActionMap(self, "ChannelSelectEPGActions",
		{
			"showEPGList":	(self.showEntryInfo, _("Show info what setting does")),
		}, -1)
		
		self.updateSkinList()
		
		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		self.onLayoutFinish.append(self.startRun)

	def showEntryInfo(self):
		if self.curList == "config":
			self.session.open(MessageBox,self.helpDict.get(self["config"].getCurrent()[0], _("No help available")) , MessageBox.TYPE_INFO, windowTitle=_("Setting Info"), timeout=0)

	def setListLabelText(self):
		if self.curList == "config":
			typeText = _("Skin Configuration")
		else:
			typeText = _("Skins")
		if not SkinUser:
			self["ListLabel"].setText( typeText )
		else:
			self["ListLabel"].setText("%s - %s" %(typeText, _("ATTENTION: skin_user.xml found")))

	def openContextMenu(self):
		self.session.openWithCallback(self.openSelection, ChoiceBox, title=_("Please select..."), list=[(_("Settings"), "settings"), (_("Help"), "help"),(_("Delete MerlinSkinThemes screen from selected skin"), "deleteMST") ])

	def openSelection(self, selection):
		if selection:
			if selection[1] == "settings":
				self.session.openWithCallback(self.setPreviewPic, MerlinSkinThemesConfig)
			elif selection[1] == "help":
				self.session.open(MerlinSkinThemesHelp, self.curList)
			elif selection[1] == "deleteMST":
				self.check4MSTScreen()

	def setDescriptionText(self):
		if isinstance(self["config"].getCurrent()[1].value, bool):
			textValue = _("Yes") if True else _("No")
		else:
			textValue = self["config"].getCurrent()[1].value
		self["descriptionText"].setText(textValue)

	def startRun(self):
		self["SkinsList"].onSelectionChanged.append(self.changedSkinsList)
		self["config"].onSelectionChanged.append(self.setDescriptionText)
		self["config"].onSelectionChanged.append(self.setPreviewPic)

		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
		
		self["config"].hide()
		
		self["SkinsList"].moveToIndex(self["SkinsList"].selectedIndex)

		self.ImageInfo()
		if fileExists(MerlinSkinThemes.selSkinFile):
			self.CopyrightInfo()
			
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
			self.restartYesNo()
		elif self.curList == "config":
			askBox = self.session.openWithCallback(self.askYN,MessageBox,_("[apply themes] needs time to build new settings\nDo you want to do this now?"), MessageBox.TYPE_YESNO)
			askBox.setTitle(_("Apply themes now?"))

	def askYN(self, answer):
		if answer is True:
			# only update settings when skin is currently active skin
			if config.plugins.MerlinSkinThemes3.selSkin.value == SkinName:
				config.plugins.MerlinSkinThemes3.designModified.save()
				configfile.save()

			self.updateConfigFile()
			
	def updateConfigFile(self):
		if not fileExists(CONFDIR):
			createDir("/etc/enigma2/merlinskinthemes")
		
		configDictFile = CONFDIR + config.plugins.MerlinSkinThemes3.selSkin.value + ".cfg"
		f = open(configDictFile, 'w')

		skinKeys = [ x[0].lower() for x in self.clist2 if len(x)==2 ]
		for configKey in config.plugins.MerlinSkinThemes3.dict():
			mst3Dict = config.plugins.MerlinSkinThemes3.__getattr__(configKey)
			if not isinstance(mst3Dict, dict):
				continue
			for mst3DictKey, mst3DictValue in mst3Dict.items():
				if mst3DictKey.lower() in skinKeys or mst3DictKey == "designColor":
					f.write("%s:::%s\n" %(mst3DictKey, mst3DictValue.value))
				elif mst3DictKey.lower() == "cornerradius":
					print("[MST] - CornerRadius not used. Set to 0 to reset.")
					f.write("%s:::%s\n" %(mst3DictKey, "0"))
				else:
					print("[MST] %s not in list. Don't save.", mst3DictKey)
		f.close()

		if SkinName == MerlinSkinThemes.selSkinName:
			retFunc = MerlinSkinThemes.restartYesNo(self)
		else:
			retFunc = MerlinSkinThemes.showConfirmationMessage(self)		
			
		setThemes(MerlinSkinThemes.selThemeFile, MerlinSkinThemes.selSkinFile, configDictFile, retFunc)

	def restartYesNo(self):
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("GUI needs a restart to apply a new skin\nDo you want to Restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))
			
	def showConfirmationMessage(self):
		self.session.open(MessageBox, _("Changes to skin " + MerlinSkinThemes.selSkinName + " ready!"), MessageBox.TYPE_INFO)		

	def check4MSTScreen(self):
		if fileExists(MerlinSkinThemes.selSkinFile):
			xml = Tree.parse(MerlinSkinThemes.selSkinFile)
			if xml.find("screen[@name='MerlinSkinThemes']"):
				MSTFixbox = self.session.openWithCallback(self.deleteMSTScreen,MessageBox,_("Delete MerlinSkinThemes screen from selected skin?"), MessageBox.TYPE_YESNO)
				MSTFixbox.setTitle(_("MerlinSkinThemes screen found"))
			else:
				self.session.open(MessageBox, _("No MerlinSkinThemes screen found in selected skin!"), MessageBox.TYPE_INFO)

	def deleteMSTScreen(self, answer):
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
				
		elif self.curList == "config":
			if self["config"].getCurrent()[0] == "Design":
				# delete design
				self.deleteDesign(config.plugins.MerlinSkinThemes3.Designs["design"].value)
			
			else:
				# save as design
				if not config.plugins.MerlinSkinThemes3.designModified.value:
					self.session.open(MessageBox, _("No changes to save"), MessageBox.TYPE_INFO, timeout=5)
				else:
					self.session.openWithCallback(self.setDesignColorName, InputBox, title=_("Please enter a name for design"))
				
	def setDesignColorName(self, designname):
		if designname is not None:
			self.session.openWithCallback(boundFunction(self.saveDesign, designname), InputBox, title=_("Please enter a name for design color"))
	
	# write a new design into <designs>	# designcolorname hand over implementation
	def saveDesign(self, designname=None, designcolorname=None):
		if designname is not None and designcolorname is not None:
		
			designname = designname.strip()
			
			curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
			xmlroot = curTree.getroot()
			themeVersion = xmlroot.get('version')
			
			if xmlroot.find("designs") is None:
				xmldesigns = Tree.SubElement(xmlroot, "designs")
			else:
				xmldesigns = xmlroot.find("designs")
				
			if xmldesigns.find("design[@name='%s']" %(designname)) is not None:
				self.session.open(MessageBox, _("Design already exists. Please choose a different name"), MessageBox.TYPE_ERROR, timeout=5)
			else:
				xmldesign = Tree.SubElement(xmldesigns, "design", {"name": designname, "value": "inactive"})
				xmldesigncolors = Tree.SubElement(xmldesign, "designColors")
				xmldesigncolor = Tree.SubElement(xmldesigncolors, "designColor", {"name": designcolorname, "value": "active" })

				for theme in themeList:
					tag = theme.lower()
					if theme == "SkinPathTheme":
						tag = "%ss" %(tag)
					if theme.lower() in config.plugins.MerlinSkinThemes3.Themes.keys():
						if theme in ['BorderSetTheme', 'ColorTheme', 'PNGTheme']:
							Tree.SubElement(xmldesigncolor, theme, {"name": config.plugins.MerlinSkinThemes3.Themes[theme.lower()].value})
						else:
							Tree.SubElement(xmldesign, theme, {"name": config.plugins.MerlinSkinThemes3.Themes[theme.lower()].value})
					else:
						if theme in ['BorderSetTheme', 'ColorTheme', 'PNGTheme']:
							Tree.SubElement(xmldesigncolor, theme, {"name": "original" })
						else:
							Tree.SubElement(xmldesign, theme, {"name": "original" })

				# Screens
				for screen in screenList:
					if screen in config.plugins.MerlinSkinThemes3.Screens.keys():
						Tree.SubElement(xmldesign, screen, {"name": config.plugins.MerlinSkinThemes3.Screens[screen].value})
					else:
						Tree.SubElement(xmldesign, screen, {"name": "original" })
				
				# LCD Screens
				if displayTag is not None:
					for screen in displayScreenList:
						if screen in config.plugins.MerlinSkinThemes3.DisplayScreens.keys():
							Tree.SubElement(xmldesign, screen, {"name": config.plugins.MerlinSkinThemes3.DisplayScreens[screen].value})
						else:
							Tree.SubElement(xmldesign, screen, {"name": "original" })
			
				# cornerRadius
				if themeVersion is None:
					if "CornerRadius" in config.plugins.MerlinSkinThemes3.CornerRadius.keys():
						Tree.SubElement(xmldesign, "CornerRadius", {"name": config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"].value})
					else:
						Tree.SubElement(xmldesign, "CornerRadius", {"name": "14" })
				else:
					cr = Tree.SubElement(xmldesign, "cornerRadius", {})
					if "CornerRadius" in config.plugins.MerlinSkinThemes3.CornerRadius.keys():
						Tree.SubElement(cr, "radius", {"name": config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"].value, "value": "active" })
					else:
						Tree.SubElement(cr, "radius", {"name": "14", "value": "active" })
			
			XMLindent(xmlroot, 0)
			
			curTree.write(MerlinSkinThemes.selThemeFile)
			
			config.plugins.MerlinSkinThemes3.Designs["design"].choices.choices.append(designname)
			config.plugins.MerlinSkinThemes3.Designs["design"].value = designname
			
			if not "designColor" in config.plugins.MerlinSkinThemes3.DesignColors.keys():		
				config.plugins.MerlinSkinThemes3.DesignColors["designColor"] = NoSave(MyConfigSelection(default=designcolorname, choices = [designcolorname]))
				self.clist2.insert(6, getConfigListEntry("Design Color", config.plugins.MerlinSkinThemes3.DesignColors["designColor"]))
			else:
				config.plugins.MerlinSkinThemes3.DesignColors["designColor"].choices.choices.append(designcolorname)
				config.plugins.MerlinSkinThemes3.DesignColors["designColor"].value = designcolorname
			
			self["config"].invalidate(("Design", config.plugins.MerlinSkinThemes3.Designs["design"]))
			self["config"].invalidate(("Design Color", config.plugins.MerlinSkinThemes3.DesignColors["designColor"]))
			self["Preview"].hide()
			self.readOptions(True)
			
	# delete the selected design from themes.xml				
	def deleteDesign(self, designName):
		if designName == "-none-":
			self.session.open(MessageBox,_("Design not deleted. Please select a design to be deleted."), MessageBox.TYPE_ERROR)
		else:
			curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
			xmlroot = curTree.getroot()
			designs = xmlroot.find("designs")
			design = xmlroot.find(".//designs/design[@name='%s']" %(designName))
			if design is not None:
				designs.remove(design)
				curTree.write(MerlinSkinThemes.selThemeFile)
		
				# it's sufficient to read designs only
				self.readDesign("active")

	# read all options available for themes - this is independent of a design
	def readOptions(self, saveAsDesign=False):
		print("[MST] - readOptions")

		self.configDict = {}
		print(config.plugins.MerlinSkinThemes3.Skin.value )
		if fileExists(CONFDIR + config.plugins.MerlinSkinThemes3.Skin.value + ".cfg"):
			print("[MST] - config found for active skin")
			# read config data
			f = open(CONFDIR + config.plugins.MerlinSkinThemes3.Skin.value + ".cfg", 'r')
				
			for line in f:
				configData = line.split(":::")
				if len(configData)==2:
					self.configDict[configData[0]] = configData[1].strip("\n")
			f.close()	
			
		if not self.configInitDone:
			self.configInitDone = True
			initConfigSubDict3()
		
		xmltree = Tree.parse(MerlinSkinThemes.selThemeFile)
		
		xmlroot = xmltree.getroot()
		
		self.themeVersion = xmlroot.get('version')
		
		self.continueProcessing = True
		if self.themeVersion is not None:
			if self.themeVersion not in ("1.0"):
				self.continueProcessing = False
				self.ok(False)

		if self.continueProcessing:
			self.themeDict = {}
		
			# <xyztheme></xyztheme>
			for themeType in themeList:
				themes = []
				tag = themeType.lower()
				if themeType == "SkinPathTheme":
					tag = "%ss" %(tag)
				
				for themeOption in xmlroot.findall(tag):
					# active skinpaththeme is on child level
					if tag == "skinpaththemes":
						for childOption in themeOption.findall('theme'):
							themes.append((childOption.get("name"), childOption.get("value") == "active" ))
					else:
						themes.append((themeOption.get("name"),themeOption.get("value") == "active"))
				self.themeDict[themeType] = themes
			
			# <screenthemes><screens><screentheme><screen></screen></screentheme></screens></screenthemes>
			scrt = xmlroot.find("screenthemes")
			if scrt is not None:
				for screen in screenList:
					themes = []			
					scr = scrt.find('screens[@name="%s"]' %(screen))
					if scr is not None:
						for screenOption in scr.findall("screentheme"):
							themes.append((screenOption.get("name"),screenOption.get("value") == "active"))
					self.themeDict[screen] = themes

			# <lcdscreenthemes><screens><lcdscreentheme><screen></screen></lcdscreentheme></screens></lcdscreenthemes>
			if displayTag is not None:
				lscrt = xmlroot.find(displayTag)
				if lscrt is not None:
					for screen in displayScreenList:
						themes = []			
						lscr = lscrt.find('screens[@name="%s"]' %(screen))
						if lscr is not None:
							for screenOption in lscr.findall(displayTag[:-1]):
								if screenOption.find('screen[@id="%s"]' %(IdString)) is not None:
									themes.append((screenOption.get("name"),screenOption.get("value") == "active"))
						self.themeDict[screen] = themes

			if self.themeVersion is None:
				# <cornerradius><radius></radius></cornerradius>
				themeType = "CornerRadius"
				themes = []
				cr = xmlroot.find("cornerradius")
				if cr is not None:
					for radius in cr.findall("radius"):
						themes.append((radius.get("name"), radius.get("value") == "active"))
					self.themeDict[themeType] = themes

			if not saveAsDesign:	
				self.readDesign("init")
			else:
				self.readDesign("save")

	def readDesign(self, mode="init", what=None):
		# modes
		# init = set values as stored in .cfg
		# read = set values based on selected design / design color
		# active = if no .cfg found read active as defined by skinner
		# save = read design just saved
		print("[MST] - readDesign")
		self.clist2 = []
		
		if not bool(self.configDict) and mode== "init":
			mode = "active"
		
		print("[MST]- configDict", self.configDict)		
		
		print("[MST] - mode is ", mode)
		if what is not None:
			print("[MST] - what is ", what)
		
		selSkinList = []
		selSkinList.append(MerlinSkinThemes.selSkinName)
		config.plugins.MerlinSkinThemes3.selSkin = NoSave(MyConfigSelection(default=MerlinSkinThemes.selSkinName, choices = selSkinList))
		self.clist2.append(getConfigListEntry(" " + u'\u00b7' + " SKIN", ))
		self.clist2.append(getConfigListEntry("Skin", config.plugins.MerlinSkinThemes3.selSkin))
		self.clist2.append(getConfigListEntry(" ", ))
		self.clist2.append(getConfigListEntry(" " + u'\u00b7' + " DESIGNS", ))
		
		curTree = Tree.parse(MerlinSkinThemes.selThemeFile)
		xmlroot = curTree.getroot()
		
		designs = xmlroot.find("designs")
		
		designList = ["-none-"]
		designColorList = ["-none-"]
		defaultDesign = "-none-"
		defaultDesignColor = "-none-"
		
		if designs is not None:
			for design in designs.findall("design"):
				designName = design.get("name")
				state = design.get("value")
			
				designList.append(designName)
			
				# read the design
				if (mode == "init" and designName == self.configDict.get('design')) or (mode == "init" and self.configDict.get('design') is None and state == "active") or (mode == "active" and state == "active") or ((mode == "read" or mode == "save") and designName == config.plugins.MerlinSkinThemes3.Designs["design"].value):
					defaultDesign = designName
					hasDesignColors = False
					designColors = design.find("designColors")
					if designColors is not None:
						for designColor in designColors:
							designColorName = designColor.get("name")
							if designColorName is not None:
								designColorList.append(designColorName)
								isSelectedDsc = False
								if (mode == "active" and designColor.get('value') == "active") or (designColor.get('value') == "active" and what == "ds") or ((mode == "save" or what == "dsc") and config.plugins.MerlinSkinThemes3.DesignColors["designColor"].value == designColorName) or (mode == "init" and (designColorName == self.configDict.get('designColor') or self.configDict.get('designColor', '-none-') == '-none-')):
									defaultDesignColor = designColor.get('name')
									if mode == "init":
										defaultDesignColor = self.configDict.get('designColor', "-none-")
										if defaultDesignColor == "-none-" and designColor.get('value') == "inactive":
											print("[MST] - ignore inactive design color when stored value is -none-")
											continue
									if designColor.get('value') == "active" or what == "dsc":
										isSelectedDsc = True
								else:
									continue
								
								hasDesignColors = True
								for dsctheme in ('BorderSetTheme', 'ColorTheme', 'PNGTheme'):
									defaultValue = None
									dsct = designColor.find(dsctheme)
									if dsct is not None:
										dsctname = dsct.get('name')
										if dsctname is not None:
											optionList = [ x[0] for x in self.themeDict.get(dsctheme, [])]
											if isSelectedDsc:
												defaultValue = dsctname
												if defaultDesignColor == "-none-":
													confValue = self.configDict.get(dsctheme.lower())
													if confValue in optionList:
														defaultValue = confValue
										
											if not defaultValue in optionList:
												themeDefaultList = [ x[0] for x in self.themeDict.get(dsctheme, []) if x[1]]
												if len(themeDefaultList):
													defaultValue = themeDefaultList[0]
												else:
													if len(optionList):
														defaultValue = optionList[0]
													else:
														defaultValue = None
									if defaultValue is not None and self.themeDict.get(dsctheme) is not None:
										if len(self.themeDict.get(dsctheme)):
											if not dsctheme.lower() in config.plugins.MerlinSkinThemes3.Themes.keys():
												config.plugins.MerlinSkinThemes3.Themes[dsctheme.lower()] = NoSave(MyConfigSelection(default=defaultValue, choices = optionList ))
											else:
												config.plugins.MerlinSkinThemes3.Themes[dsctheme.lower()].setChoices(optionList, defaultValue)
												config.plugins.MerlinSkinThemes3.Themes[dsctheme.lower()].value = defaultValue
							
					if not "designColor" in config.plugins.MerlinSkinThemes3.DesignColors.keys():
						config.plugins.MerlinSkinThemes3.DesignColors["designColor"] = NoSave(MyConfigSelection(default=defaultDesignColor, choices = designColorList))
						config.plugins.MerlinSkinThemes3.DesignColors["designColor"].value = defaultDesignColor
					else: 
						config.plugins.MerlinSkinThemes3.DesignColors["designColor"].setChoices(designColorList, defaultDesignColor)
						config.plugins.MerlinSkinThemes3.DesignColors["designColor"].value = defaultDesignColor
					self.clist2.append(getConfigListEntry("Design Color", config.plugins.MerlinSkinThemes3.DesignColors["designColor"]))
				
					# name of theme is read and displayed in the section THEMES, active one is set as default
					self.clist2.append(getConfigListEntry(" ", ))
					self.clist2.append(getConfigListEntry(" " + u'\u00b7' + " THEMES", ))

					# for each theme in the design set the value to the selected design
					for element in themeList:
						# ignore BorderSetTheme, ColorTheme and PNGTheme as it's defined in designColor
						if hasDesignColors and element in ['BorderSetTheme', 'ColorTheme', 'PNGTheme']:
							print("[MST] - ignoring %s as designColor is used" %(element))
							self.clist2.append(getConfigListEntry(element, config.plugins.MerlinSkinThemes3.Themes[element.lower()]))
							continue

						tmp = design.find(element)
						defaultValue = None
						if tmp is not None:
							if tmp.get("name") is not None:
								defaultValue = tmp.get('name')
								optionList = [ x[0] for x in self.themeDict.get(element, [])]
								if mode == "init":
									confValue = self.configDict.get(element.lower())
									if confValue in optionList:
										defaultValue = confValue
								if not defaultValue in optionList:
									themeDefaultList = [ x[0] for x in self.themeDict.get(element, []) if x[1]]
									if len(themeDefaultList):
										defaultValue = themeDefaultList[0]
									else:
										if len(optionList):
											defaultValue = optionList[0]
										else:
											defaultValue = None
								
								print("[MST] - Default %s: %s" %(element, defaultValue))
							else:
								print("[MST] - %s has no name" %(element))
						else:
							print("[MST] - %s not found" %(element))
						if defaultValue is not None and self.themeDict.get(element) is not None:
							if len(self.themeDict.get(element)):
								if not element.lower() in config.plugins.MerlinSkinThemes3.Themes.keys():
									config.plugins.MerlinSkinThemes3.Themes[element.lower()] = NoSave(MyConfigSelection(default=defaultValue, choices = [ x[0] for x in self.themeDict.get(element)]))
									if not config.plugins.MerlinSkinThemes3.designModified.value:
										config.plugins.MerlinSkinThemes3.Themes[element.lower()].value = defaultValue
								else:
									config.plugins.MerlinSkinThemes3.Themes[element.lower()].setChoices([ x[0] for x in self.themeDict.get(element)], defaultValue)
									config.plugins.MerlinSkinThemes3.Themes[element.lower()].value = defaultValue
								self.clist2.append(getConfigListEntry(element, config.plugins.MerlinSkinThemes3.Themes[element.lower()]))

					self.clist2.append(getConfigListEntry(" ", ))
					self.clist2.append(getConfigListEntry(" " + u'\u00b7' + " SCREENS", ))

					if self.themeVersion is None:
						for screenname in screenList:
							defaultValue = None
							optionList = [ x[0] for x in self.themeDict.get(screenname, [])]
							themeDefaultList = [ x[0] for x in self.themeDict.get(screenname, []) if x[1]]
							if len(themeDefaultList):
								defaultValue = themeDefaultList[0]
								
							if len(optionList):
								if not screenname in config.plugins.MerlinSkinThemes3.Screens.keys():
									config.plugins.MerlinSkinThemes3.Screens[screenname] = NoSave(MyConfigSelection(default=defaultValue, choices = optionList))
									if not config.plugins.MerlinSkinThemes3.designModified.value:
										config.plugins.MerlinSkinThemes3.Screens[screenname].value = defaultValue
								else:
									config.plugins.MerlinSkinThemes3.Screens[screenname].setChoices(optionList, defaultValue)
									config.plugins.MerlinSkinThemes3.Screens[screenname].value = defaultValue
								self.clist2.append(getConfigListEntry(screenname, config.plugins.MerlinSkinThemes3.Screens[screenname]))
									
						
					else:
						# for each screen in the design set the value to the selected design
						for screenname in screenList:
							tmp = design.find(screenname)
							defaultValue = None
							if tmp is not None:
								if tmp.get("name") is not None:
									defaultValue = tmp.get('name')
									optionList = [ x[0] for x in self.themeDict.get(screenname, [])]
									if mode == "init":
										confValue = self.configDict.get(screenname)
										if confValue in optionList:
											defaultValue = confValue
									if not defaultValue in optionList:
										themeDefaultList = [ x[0] for x in self.themeDict.get(screenname, []) if x[1]]
										if len(themeDefaultList):
											defaultValue = themeDefaultList[0]
										else:
											if len(optionList):
												defaultValue = optionList[0]
											else:
												defaultValue = None
									print("[MST] - Default %s: %s" %(screenname, defaultValue))
								else:
									print("[MST] - %s has no name" %(screenname))
							else:
								print("[MST] - %s not found" %(screenname))
					
							if defaultValue is not None and self.themeDict.get(screenname) is not None:
								if len(self.themeDict.get(screenname)):
									if not screenname in config.plugins.MerlinSkinThemes3.Screens.keys():
										config.plugins.MerlinSkinThemes3.Screens[screenname] = NoSave(MyConfigSelection(default=defaultValue, choices = optionList))
										if not config.plugins.MerlinSkinThemes3.designModified.value:
											config.plugins.MerlinSkinThemes3.Screens[screenname].value = defaultValue
									else:
										config.plugins.MerlinSkinThemes3.Screens[screenname].setChoices(optionList, defaultValue)
										config.plugins.MerlinSkinThemes3.Screens[screenname].value = defaultValue
									self.clist2.append(getConfigListEntry(screenname, config.plugins.MerlinSkinThemes3.Screens[screenname]))

					if displayTag is not None:
						self.clist2.append(getConfigListEntry(" ", ))
						self.clist2.append(getConfigListEntry(" " + u'\u00b7' + " DISPLAY SCREENS ID=%s (%s) %dx%d" %(IdString, ModelString, getDesktop(1).size().width(), getDesktop(1).size().height()), ))
						
						if self.themeVersion is None:
							for lcdscreenname in displayScreenList:
								defaultValue = None
								optionList = [ x[0] for x in self.themeDict.get(lcdscreenname, [])]
								themeDefaultList = [ x[0] for x in self.themeDict.get(lcdscreenname, []) if x[1]]
								if len(themeDefaultList):
									defaultValue = themeDefaultList[0]
									
								if len(optionList):
									if not lcdscreenname in config.plugins.MerlinSkinThemes3.DisplayScreens.keys():
										config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname] = NoSave(MyConfigSelection(default=defaultValue, choices = optionList))
										if not config.plugins.MerlinSkinThemes3.designModified.value:
											config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname].value = defaultValue
									else:
										config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname].setChoices(optionList, defaultValue)
										config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname].value = defaultValue
									self.clist2.append(getConfigListEntry(lcdscreenname, config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname]))									
						else:
							# for each LCD screen in the design set the value to the selected design
							for lcdscreenname in displayScreenList:
								# check for id-specific default
								tmp = design.find("%s[@id='%s']" %(lcdscreenname, IdString))
								defaultValue = None
								if tmp is not None:
									if tmp.get("name") is not None:
										defaultValue = tmp.get('name')
										optionList = [ x[0] for x in self.themeDict.get(lcdscreenname, [])]
										if mode == "init":
											confValue = self.configDict.get(lcdscreenname)
											if confValue in optionList:
												defaultValue = confValue
										if not defaultValue in optionList:
											themeDefaultList = [ x[0] for x in self.themeDict.get(lcdscreenname, []) if x[1]]
											if len(themeDefaultList):
												defaultValue = themeDefaultList[0]
											else:
												if len(optionList):
													defaultValue = optionList[0]
												else:
													defaultValue = None
										print("[MST] - Default %s (ID: %s): %s" %(lcdscreenname, IdString, defaultValue))
									else:
										print("[MST] - %s (ID: %s) has no name" %(lcdscreenname, IdString))
								else:
									# check for generic default
									tmp = design.find(lcdscreenname)
									if tmp is not None:
										if tmp.get("name") is not None:
											defaultValue = tmp.get('name')
											optionList = [ x[0] for x in self.themeDict.get(lcdscreenname, [])]
											if mode == "init":
												confValue = self.configDict.get(lcdscreenname)
												if confValue in optionList:
													defaultValue = confValue
											if not defaultValue in optionList:
												themeDefaultList = [ x[0] for x in self.themeDict.get(lcdscreenname, []) if x[1]]
												if len(themeDefaultList):
													defaultValue = themeDefaultList[0]
												else:
													if len(optionList):
														defaultValue = optionList[0]
													else:
														defaultValue = None
											print("[MST] - Default %s: %s" %(lcdscreenname, defaultValue))
										else:
											print("[MST] - %s has no name" %(lcdscreenname))
									else:							
										print("[MST] - %s not found" %(lcdscreenname))
	
								if defaultValue is not None and self.themeDict.get(lcdscreenname) is not None:
									if len(self.themeDict.get(lcdscreenname)):
										if not lcdscreenname in config.plugins.MerlinSkinThemes3.DisplayScreens.keys():
											config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname] = NoSave(MyConfigSelection(default=defaultValue, choices = optionList))
											if not config.plugins.MerlinSkinThemes3.designModified.value:
												config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname].value = defaultValue
										else:
											config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname].setChoices(optionList, defaultValue)
											config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname].value = defaultValue
										self.clist2.append(getConfigListEntry(lcdscreenname, config.plugins.MerlinSkinThemes3.DisplayScreens[lcdscreenname]))
				
					defaultRadius = "0"
					# for each corner radius in the design set the value to the selected design
					if self.themeVersion is None:
						tmp = design.find("CornerRadius")
						defaultValue = None
						if tmp is not None:
							if tmp.get("name") is not None:
								defaultValue = tmp.get('name')
								optionList = [ x[0] for x in self.themeDict.get("CornerRadius", [])]
								if mode == "init":
									confValue = self.configDict.get('CornerRadius')
									if confValue is None:
										confValue = self.configDict.get('cornerradius')
									if confValue in optionList:
										defaultValue = confValue
								if not defaultValue in optionList:
									themeDefaultList = [ x[0] for x in self.themeDict.get("CornerRadius", []) if x[1]]
									if len(themeDefaultList):
										defaultValue = themeDefaultList[0]
									else:
										if len(optionList):
											defaultValue = optionList[0]
										else:
											defaultValue = None
								print("[MST] - Default %s: %s" %("CornerRadius", defaultValue))
							else:
								print("[MST] - %s has no name" %("CornerRadius"))
						else:
							print("[MST] - CornerRadius not found")
							
						if defaultValue is not None and self.themeDict.get("CornerRadius") is not None:
							if len(self.themeDict.get("CornerRadius", [])):
								if not "CornerRadius" in config.plugins.MerlinSkinThemes3.CornerRadius.keys():
									config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"] = NoSave(MyConfigSelection(default=defaultValue, choices = optionList))
									if not config.plugins.MerlinSkinThemes3.designModified.value:
										config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"].value = defaultValue
								else:
									config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"].setChoices(optionList, defaultValue)
									config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"].value = defaultValue
				
								self.clist2.append(getConfigListEntry(" ", ))
								self.clist2.append(getConfigListEntry(" " + u'\u00b7' + " CORNERRADIUS", ))
								self.clist2.append(getConfigListEntry("CornerRadius", config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"]))
					else:
						cornerRadius = design.find("cornerRadius")
						defaultValue = None
						if cornerRadius is not None:
							optionList = []
							for radius in cornerRadius:
								radiusValue = radius.get('name')
								state = radius.get('value')
								if radiusValue is not None:
									optionList.append(radiusValue)
									if state == 'active':
										defaultValue = radiusValue
						
							if mode == "init":
								confValue = self.configDict.get('CornerRadius')
								if confValue is None:
									confValue = self.configDict.get('cornerradius')		
									if confValue in optionList:
										defaultValue = confValue
									if not defaultValue in optionList:
										themeDefaultList = [ x[0] for x in self.themeDict.get("CornerRadius", []) if x[1]]
										if len(themeDefaultList):
											defaultValue = themeDefaultList[0]
										else:
											if len(optionList):
												defaultValue = optionList[0]
											else:
												defaultValue = None
							print("[MST] - Default CornerRadius: %s" %(defaultValue))
						else:
							print("[MST] - CornerRadius has no name")						
									
						if defaultValue is not None:		
							if not "CornerRadius" in config.plugins.MerlinSkinThemes3.CornerRadius.keys():
								config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"] = NoSave(MyConfigSelection(default=defaultValue, choices = optionList))
							else: 
								config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"].setChoices(optionList, defaultValue)
								config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"].value = defaultValue
							self.clist2.append(getConfigListEntry(" ", ))
							self.clist2.append(getConfigListEntry(" " + u'\u00b7' + " CORNERRADIUS", ))
							self.clist2.append(getConfigListEntry("CornerRadius", config.plugins.MerlinSkinThemes3.CornerRadius["CornerRadius"]))				
	
			
		if len(designList):
			if not "design" in config.plugins.MerlinSkinThemes3.Designs.keys():
				config.plugins.MerlinSkinThemes3.Designs["design"] = NoSave(MyConfigSelection(default=defaultDesign, choices = designList))
				config.plugins.MerlinSkinThemes3.Designs["design"].value = defaultDesign
			else:
				config.plugins.MerlinSkinThemes3.Designs["design"].setChoices(designList, defaultDesign)
				config.plugins.MerlinSkinThemes3.Designs["design"].value = defaultDesign
		self.clist2.insert(4, getConfigListEntry("Design", config.plugins.MerlinSkinThemes3.Designs["design"]))

		if mode == "save":
			config.plugins.MerlinSkinThemes3.designModified.value = False
		self.clist2.insert(5, getConfigListEntry(_("Design modified"), config.plugins.MerlinSkinThemes3.designModified))
						
		# refresh Screen
		self["config"].setList(self.clist2)		
		
	def ok(self, retVal=None):
	
		if retVal == False:
			self.curList = "config"
			self.session.open(MessageBox, _("Theme version %s is not supported. Please check for updated version of MerlinSkinThemes." %(self.themeVersion)), MessageBox.TYPE_ERROR, timeout=5)
		
		if self.curList == "SkinsList":
			if self["SkinsList"].getCurrent()[3][7] == "":
				self.curList = "config"
				
				self.setListLabelText()

				if fileExists(MerlinSkinThemes.selSkinFile):
					self.CopyrightInfo()
				
				config.plugins.MerlinSkinThemes3.Skin.value = self["SkinsList"].getCurrent()[1][7]
				self.readOptions()
				
				if self.continueProcessing:
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
			else:
				self.CopyrightInfo()
				self.session.open(MessageBox,_("No themes.xml or skin.xml found.\nPlease select a valid skin including themes.xml"), MessageBox.TYPE_ERROR, title=_("Error"))
				
		else:
			self.curList = "SkinsList"
			
			self.setListLabelText()
 			
			self["SkinCopyright"].setText("")
			
			self["key_green"].setText(_("switch to skin"))
			self["key_green"].hide()
			self["key_yellow"].setText("")
			self["key_yellow"].hide()
			self["descriptionText"].setText("")

			self.updateSkinList()
		
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
			if self["config"].getCurrentIndex() > 1:
				ConfigListScreen.keyLeft(self)
			
				self.executeConfigEntryActions()
	
	def right(self):
		if self.curList == "SkinsList":
			self[self.curList].pageDown()
		else:
			if self["config"].getCurrentIndex() > 1:
				ConfigListScreen.keyRight(self)
			
				self.executeConfigEntryActions()
			
	def executeConfigEntryActions(self):
		if self[self.curList].getCurrent()[0] in previewPicList:
			folderName = self["config"].getCurrent()[0]			
			if self[self.curList].getCurrent()[0] in displayScreenList:
				folderName = "%s%s" %(self["config"].getCurrent()[0], IdString)
			pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + folderName + "/" + self["config"].getCurrent()[1].value + ".png"
			self.setPreviewPic(pngpath)
			self.adjustDesignSettings()
		elif self["config"].getCurrent()[0] == "Design":
			if config.plugins.MerlinSkinThemes3.Designs["design"].value == "-none-":
				self["Preview"].hide()
			else:
				self.setPreviewPic(None)
			config.plugins.MerlinSkinThemes3.designModified.value = False
			self.readDesign("read", "ds")
		elif self["config"].getCurrent()[0] == "Design Color":
			config.plugins.MerlinSkinThemes3.designModified.value = False
			self.readDesign("read", "dsc")
		else:
			if self["config"].getCurrent()[0] != "Design modified":
				self.adjustDesignSettings()
	
	def setPreviewPic(self, pngpath=None):
		if pngpath is None:
			if self.curList == "config" and self["config"].getCurrent()[0] in previewPicList:
				folderName = self["config"].getCurrent()[0]			
				if self[self.curList].getCurrent()[0] in displayScreenList:
					folderName = "%s%s" %(self["config"].getCurrent()[0], IdString)
				pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + folderName + "/" + self["config"].getCurrent()[1].value + ".png"
			else:
				if self.curList == "SkinsList":
					pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/prev.png"
				else:
					pngpath = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/preview/" + config.plugins.MerlinSkinThemes3.Designs["design"].value + ".png"
		
		if not fileExists(pngpath):
			pngpath = resolveFilename(SCOPE_PLUGINS) + "Extensions/MerlinSkinThemes/noprev.png"

		if pngpath is not None:
			if config.plugins.MerlinSkinThemes3.showPreviewPicture.value:
				self["Preview"].instance.setPixmapFromFile(pngpath)
				self["Preview"].show()
			else:
				self["Preview"].hide()
		else:
			self["Preview"].hide()
				
	def adjustDesignSettings(self):
		if config.plugins.MerlinSkinThemes3.Designs["design"].value != "-none-" or config.plugins.MerlinSkinThemes3.DesignColors["designColor"].value != "-none-":
			config.plugins.MerlinSkinThemes3.designModified.value = True
			self["config"].invalidate((_("Design modified"), config.plugins.MerlinSkinThemes3.designModified))
			self["config"].invalidate(("Design", config.plugins.MerlinSkinThemes3.Designs["design"]))
			config.plugins.MerlinSkinThemes3.DesignColors["designColor"].value = "-none-"
			self["config"].invalidate(("Design Color", config.plugins.MerlinSkinThemes3.DesignColors["designColor"]))
	
	def changedSkinsList(self):
		self["SkinCopyright"].setText("")
		
		MerlinSkinThemes.selSkinName = self["SkinsList"].getCurrent()[1][7]
		
		MerlinSkinThemes.selSkinFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/skin.xml"
		MerlinSkinThemes.selThemeFile = resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/themes.xml"
			
		if config.plugins.MerlinSkinThemes3.showPreviewPicture.value:
			self.setPreviewPic()
		else:
			self["Preview"].hide()
		
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

	# read skins			
	def updateSkinList(self):
		self["SkinsList"].buildList()

	# create a themes.xml for the skin
	def createThemes(self):
		if not fileExists(MerlinSkinThemes.selThemeFile):
		
			# first let's parse the selected skin
			skinTree = Tree.parse(MerlinSkinThemes.selSkinFile)
			
			newTheme = Tree.Element("themes", {"version": "1.0"})
			newThemeTree = Tree.ElementTree(newTheme)
			
			# theme.xml : skin.xml
			topNodeLinkDict = {
				"colortheme": "colors",
				"fonttheme": "fonts",
				"pngtheme": "",
				"globalstheme": "globals",
				"componenttheme":"components",
				"layouttheme": "layouts",
				"bordersettheme":"windowstyle",
				"windowstylescrollbartheme":"windowstylescrollbar",
				"skinpaththeme": "",
				}
				
			exampleDict = {
				"colortheme":					{ "name": "samplecolor", "value": "#00339933" },
				"fonttheme":					{ "name": "sample", "filename": "/usr/share/enigma2/fonts/samplefont.ttf" },
				"globalstheme":					{ "name": "sample", "value":"120,50" },
				"componenttheme":				{ "type": "sample", "xOffset":"50", "yOffset": "2" },
				"layouttheme":					{ "name": "sample" },
				"bordersettheme":				{ "filename": "folder/sample.png", "pos": "bpTop" },
				"windowstylescrollbartheme":	{ "name": "ScrollbarWidth", "value":"10" },
				"pngtheme":						{ "argb": "#ff664004", "argb2": "#ffcf8106", "gtype": "round", "height": "8", "name": "img/sample.png", "width": "995" },
				"skinpaththemes":				{ "name": "sample1", "path": "skinname/folder1/", "value" : "active" },
			}
			
			for node in [("colortheme", "colors", "color"), ("fonttheme", "fonts", "font"),("pngtheme", "png"), ("skinpaththemes", "theme"), ("globalstheme", "globals", "value"), ("bordersettheme", "borderset"), ("windowstylescrollbartheme", "*"), ("componenttheme", "components", "component"), ("layouttheme", "layouts", "layout")]:

				# create the top nodes for the theme - always origina and original - work
				if node[0] == "windowstylescrollbartheme":
					newNode4Org = Tree.SubElement(newTheme, node[0], {"name": "original", "value": "active", "id": "4"})
					newNode4Work = Tree.SubElement(newTheme, node[0], {"name": "original - work", "value": "inactive", "id": "4"})					
					newNode5Org = Tree.SubElement(newTheme, node[0], {"name": "original", "value": "active", "id": "5"})
					newNode5Work = Tree.SubElement(newTheme, node[0], {"name": "original - work", "value": "inactive", "id": "5"})
				elif node[0] == "skinpaththemes":
					newNodeOrg = Tree.SubElement(newTheme, node[0])
					newNodeOrg.append(Tree.Comment("Example only"))
					childNodeOrg = Tree.SubElement(newNodeOrg, node[1], exampleDict.get(node[0], {} ))					
					childNodeWork = Tree.SubElement(newNodeOrg, node[1], { "name":"sample2", "path":"skinpath/folder2/", "value":"inactive"} )
				else:
					newNodeOrg = Tree.SubElement(newTheme, node[0], {"name": "original", "value": "active"})
					newNodeWork = Tree.SubElement(newTheme, node[0], {"name": "original - work", "value": "inactive"})
					
					if node[0] in ( "pngtheme"):
						newNodeOrg.append(Tree.Comment("Example only"))
						childNodeOrg = Tree.SubElement(newNodeOrg, node[1], exampleDict.get(node[0], {} ))
						newNodeWork.append(Tree.Comment("Example only"))
						childNodeWork = Tree.SubElement(newNodeWork, node[1], exampleDict.get(node[0], {} ))
					else:
						childNodeOrg = Tree.SubElement(newNodeOrg, node[1])
						childNodeWork = Tree.SubElement(newNodeWork, node[1])
						
				skinElement = topNodeLinkDict.get(node[0], "")
				
				# read definition in skin
				if skinElement == "windowstyle":
					skinElementList = skinTree.findall(".//%s[@id='0']/%s" %(skinElement, node[1]))
					if skinElementList:
						for element in skinElementList:
							newChildOrg = Tree.SubElement(childNodeOrg, element.tag, element.attrib)
							newChildWork = Tree.SubElement(childNodeWork, element.tag, element.attrib)
							for subelement in element.findall("*"):
								Tree.SubElement(newChildOrg, subelement.tag, subelement.attrib)
								Tree.SubElement(newChildWork, subelement.tag, subelement.attrib)
					else:
						childNodeOrg.append(Tree.Comment("Example only"))
						newChildOrg = Tree.SubElement(childNodeOrg, "borderset", {"name":"bsWindow"})
						childNodeWork.append(Tree.Comment("Example only"))
						newChildWork = Tree.SubElement(childNodeWork, "borderset", {"name":"bsWindow"})	
						Tree.SubElement(newChildOrg, "pixmap", exampleDict.get(node[0], {}) )
						Tree.SubElement(newChildWork, "pixmap", exampleDict.get(node[0], {}) )
											
				elif skinElement == "windowstylescrollbar":
					skinElementList = skinTree.findall(".//%s[@id='4']/%s" %(skinElement, node[1])) 
					if skinElementList:
						for element in skinElementList:
							Tree.SubElement(newNode4Org, element.tag, element.attrib)
							Tree.SubElement(newNode4Work, element.tag, element.attrib)
					else:
						newNode4Org.append(Tree.Comment("Example only"))
						Tree.SubElement(newNode4Org, "value", exampleDict.get(node[0], {}) )
						newNode4Work.append(Tree.Comment("Example only"))
						Tree.SubElement(newNode4Work, "value", exampleDict.get(node[0], {}) )
					skinElementList = skinTree.findall(".//%s[@id='5']/%s" %(skinElement, node[1]))
					if skinElementList:
						for element in skinElementList:
							Tree.SubElement(newNode5Org, element.tag, element.attrib)
							Tree.SubElement(newNode5Work, element.tag, element.attrib)
					else:
						newNode5Org.append(Tree.Comment("Example only"))
						Tree.SubElement(newNode5Org, "value", exampleDict.get(node[0], {}) )
						newNode5Work.append(Tree.Comment("Example only"))
						Tree.SubElement(newNode5Work, "value", exampleDict.get(node[0], {}) )
				elif skinElement in ('components', 'layouts'):
					skinElementList = skinTree.findall(".//%s/%s" %(skinElement, node[2]))
					if skinElementList:
						for element in skinElementList:
							childNodeOrg.append(Tree.fromstring(Tree.tostring(element)))								
							childNodeWork.append(Tree.fromstring(Tree.tostring(element)))
					else:
						childNodeOrg.append(Tree.Comment("Example only"))
						Tree.SubElement(childNodeOrg, node[2], exampleDict.get(node[0], {}) )
						childNodeWork.append(Tree.Comment("Example only"))
						Tree.SubElement(childNodeWork, node[2], exampleDict.get(node[0], {}) )
				else:
					if skinElement == "":
						skinElementList = []
					else:
						skinElementList = skinTree.findall(".//%s/%s" %(skinElement, node[2]))
					if skinElementList:
						for element in skinElementList:
							Tree.SubElement(childNodeOrg, element.tag, element.attrib)						
							Tree.SubElement(childNodeWork, element.tag, element.attrib)
					else:
						if skinElement == "":
							pass
						else:							
							childNodeOrg.append(Tree.Comment("Example only"))
							Tree.SubElement(childNodeOrg, node[2], exampleDict.get(node[0], {}) )
							childNodeWork.append(Tree.Comment("Example only"))
							Tree.SubElement(childNodeWork, node[2], exampleDict.get(node[0], {}) )
			
			# screenthemes
			screenthemes = Tree.SubElement(newTheme, "screenthemes")
			for screenname in screenList:
				screennode = Tree.SubElement(screenthemes, "screens", {"name": screenname })
				newNodeOrg = Tree.SubElement(screennode, "screentheme", {"name": "original", "value": "active"})
				newNodeWork = Tree.SubElement(screennode, "screentheme", {"name": "original - work", "value": "inactive"})
				
				skinElementList = skinTree.findall("screen[@name='%s']" %(screenname))
				for element in skinElementList:
					newNodeOrg.append(Tree.fromstring(Tree.tostring(element)))
					newNodeWork.append(Tree.fromstring(Tree.tostring(element)))

			# displayscreenthemes
			if displayTag is not None:
				displayscreenthemes = Tree.SubElement(newTheme, displayTag)
				for displayscreenname in displayScreenList: 
					displayscreennode = Tree.SubElement(displayscreenthemes, "screens", {"name": displayscreenname, "id": IdString})
					newNodeOrg = Tree.SubElement(displayscreennode, displayTag[:-1], {"name": "original", "value": "active"})
					newNodeWork = Tree.SubElement(displayscreennode, displayTag[:-1], {"name": "original - work", "value": "inactive"})
					skinElementList = skinTree.findall("screen[@name='%s'][@id='%s']" %(displayscreenname, IdString))
					for element in skinElementList:
						newNodeOrg.append(Tree.fromstring(Tree.tostring(element)))
						newNodeWork.append(Tree.fromstring(Tree.tostring(element)))				

			designs = Tree.SubElement(newTheme, "designs")
			design1 = Tree.SubElement(designs, "design", {"name": "Design 1", "value": "active"})
			design2 = Tree.SubElement(designs, "design", {"name": "Design 2", "value": "inactive"})
			designcolors1 = Tree.SubElement(design1, "designColors")
			designcolor11 = Tree.SubElement(designcolors1, "designColor", {"name": "Design Color 1", "value": "active"})
			designcolor12 = Tree.SubElement(designcolors1, "designColor", {"name": "Design Color 2", "value": "inactive"})
			designcolors2 = Tree.SubElement(design2, "designColors")
			designcolor21 = Tree.SubElement(designcolors2, "designColor", {"name": "Design Color 1", "value": "active"})
			designcolor22 = Tree.SubElement(designcolors2, "designColor", {"name": "Design Color 2", "value": "inactive"})
			Tree.SubElement(designcolor11, "BorderSetTheme", {"name": "original"})
			Tree.SubElement(designcolor12, "BorderSetTheme", {"name": "original - work"})
			Tree.SubElement(designcolor11, "ColorTheme", {"name": "original"})
			Tree.SubElement(designcolor12, "ColorTheme", {"name": "original - work"})
			Tree.SubElement(designcolor11, "PNGTheme", {"name": "original"})
			Tree.SubElement(designcolor12, "PNGTheme", {"name": "original - work"})
			Tree.SubElement(designcolor21, "BorderSetTheme", {"name": "original"})
			Tree.SubElement(designcolor22, "BorderSetTheme", {"name": "original - work"})
			Tree.SubElement(designcolor21, "ColorTheme", {"name": "original"})
			Tree.SubElement(designcolor22, "ColorTheme", {"name": "original - work"})
			Tree.SubElement(designcolor21, "PNGTheme", {"name": "original"})
			Tree.SubElement(designcolor22, "PNGTheme", {"name": "original - work"})
			Tree.SubElement(design1, "LayoutTheme", {"name": "original"})
			Tree.SubElement(design2, "LayoutTheme", {"name": "original - work"})
			Tree.SubElement(design1, "GlobalsTheme", {"name": "original"})
			Tree.SubElement(design2, "GlobalsTheme", {"name": "original - work"})
			Tree.SubElement(design1, "FontTheme", {"name": "original"})
			Tree.SubElement(design2, "FontTheme", {"name": "original - work"})
			Tree.SubElement(design1, "SkinPathTheme", {"name": "sample1"})
			Tree.SubElement(design2, "SkinPathTheme", {"name": "sample2"})
			Tree.SubElement(design1, "GlobalsTheme", {"name": "original"})
			Tree.SubElement(design2, "GlobalsTheme", {"name": "original - work"})
			Tree.SubElement(design1, "WindowStyleScrollbarTheme", {"name": "original"})
			Tree.SubElement(design2, "WindowStyleScrollbarTheme", {"name": "original - work"})
			Tree.SubElement(design1, "ComponentTheme", {"name": "original"})
			Tree.SubElement(design2, "ComponentTheme", {"name": "original - work"})
			Tree.SubElement(design1, "InfoBar", {"name": "original"})
			Tree.SubElement(design1, "SecondInfoBar", {"name": "original"})
			Tree.SubElement(design1, "PluginBrowser", {"name": "original"})
			Tree.SubElement(design1, "Menu", {"name": "original"})
			Tree.SubElement(design1, "GraphMultiEPG", {"name": "original"})
			Tree.SubElement(design1, "EventView", {"name": "original"})
			Tree.SubElement(design1, "EPGSelection", {"name": "original"})
			Tree.SubElement(design1, "MessageBox", {"name": "original"})
			Tree.SubElement(design1, "InputBox", {"name": "original"})
			Tree.SubElement(design1, "ChoiceBox", {"name": "original"})
			Tree.SubElement(design1, "ChannelSelection", {"name": "original"})
			Tree.SubElement(design1, "MovieSelection", {"name": "original"})			
			Tree.SubElement(design1, "MoviePlayer", {"name": "original"})
			Tree.SubElement(design1, "Mute", {"name": "original"})
			Tree.SubElement(design1, "Volume", {"name": "original"})
			Tree.SubElement(design1, "MerlinMusicPlayer2Screen_%s" %(ArchString), {"name": "original"})
			Tree.SubElement(design1, "MerlinMusicPlayer2ScreenSaver_%s" %(ArchString), {"name": "original"})
			Tree.SubElement(design1, "InfoBarSummary", {"name": "original"})
			Tree.SubElement(design1, "StandbySummary", {"name": "original"})
			Tree.SubElement(design1, "InfoBarMoviePlayerSummary", {"name": "original"})
			Tree.SubElement(design1, "MerlinMusicPlayer2LCDScreen", {"name": "original"})
			Tree.SubElement(design1, "EventView_summary", {"name": "original"})
			Tree.SubElement(design2, "InfoBar", {"name": "original"})
			Tree.SubElement(design2, "SecondInfoBar", {"name": "original"})
			Tree.SubElement(design2, "PluginBrowser", {"name": "original"})
			Tree.SubElement(design2, "Menu", {"name": "original"})
			Tree.SubElement(design2, "GraphMultiEPG", {"name": "original"})
			Tree.SubElement(design2, "EventView", {"name": "original"})
			Tree.SubElement(design2, "EPGSelection", {"name": "original"})
			Tree.SubElement(design2, "MessageBox", {"name": "original"})
			Tree.SubElement(design2, "InputBox", {"name": "original"})
			Tree.SubElement(design2, "ChoiceBox", {"name": "original"})
			Tree.SubElement(design2, "ChannelSelection", {"name": "original"})
			Tree.SubElement(design2, "MovieSelection", {"name": "original"})			
			Tree.SubElement(design2, "MoviePlayer", {"name": "original"})
			Tree.SubElement(design2, "Mute", {"name": "original"})
			Tree.SubElement(design2, "Volume", {"name": "original"})
			Tree.SubElement(design2, "MerlinMusicPlayer2Screen_%s" %(ArchString), {"name": "original"})
			Tree.SubElement(design2, "MerlinMusicPlayer2ScreenSaver_%s" %(ArchString), {"name": "original"})
			Tree.SubElement(design2, "InfoBarSummary", {"name": "original"})
			Tree.SubElement(design2, "StandbySummary", {"name": "original"})
			Tree.SubElement(design2, "InfoBarMoviePlayerSummary", {"name": "original"})
			Tree.SubElement(design2, "MerlinMusicPlayer2LCDScreen", {"name": "original"})
			Tree.SubElement(design2, "EventView_summary", {"name": "original"})
			cr1 = Tree.SubElement(design1, "cornerRadius")
			cr2 = Tree.SubElement(design2, "cornerRadius")
			Tree.SubElement(cr1, "radius", {"name": "0", "value": "active"})
			Tree.SubElement(cr1, "radius", {"name": "20", "value": "inactive"})
			Tree.SubElement(cr1, "radius", {"name": "30", "value": "inactive"})			
			Tree.SubElement(cr2, "radius", {"name": "0", "value": "active"})
			Tree.SubElement(cr2, "radius", {"name": "20", "value": "inactive"})
			Tree.SubElement(cr2, "radius", {"name": "30", "value": "inactive"})	
			
			XMLindent(newTheme,0)
			
			newThemeTree.write(MerlinSkinThemes.selThemeFile)
			
			self.updateSkinList()
	
	def ImageInfo(self):
		if Arch64:
			archText = "ARM64"
		elif ArchArm:
			archText = "ARM"
		elif ArchMipsel:
			archText = "MIPSEL"
		
		merlinText = _("No")
		if Merlin:
			merlinText = _("Yes")
			
		infoText = "Enigma2: %s - Arch: %s - Merlin: %s" %(getEnigmaVersionString(), archText, merlinText)
		
		self["ImageInfo"].setText(infoText)
		
	def CopyrightInfo(self):
		InfoText = ""
		
		curSkin = Tree.parse(MerlinSkinThemes.selSkinFile)
		rootSkin = curSkin.getroot()
		copyright = rootSkin.find("copyright")
		if copyright is not None:
			if copyright.find("original") is not None:
				org = copyright.find("original")
				oAuthor = org.get('author', "")
				oVersion = org.get("version", "")
				oName = org.get("name", "")
				oSupport = org.get("supporturl", "")
				oLicense = org.get("license", "")
				
				OrgText = _("Skin: %s by %s - Version: %s\nSupport: %s\n\nLicense: %s" %(oName, oAuthor, oVersion, oSupport, oLicense))			
			else:
				OrgText = _("Skin ORIGINAL - No info available")
		
			if copyright.find("mod") is not None:
				mod = copyright.find("mod")
				mAuthor = mod.get("author", "")
				mVersion = mod.get("version", "")
				mName = mod.get("name", "")
				mSupport = mod.get("supporturl", "")
				
				ModText = _("Mod:\nSkin: %s by %s - Version: %s\nSupport: %s" %(mName, mAuthor, mVersion, mSupport))
			else:
				ModText = _("Skin MOD - No info available")
		
			InfoText = OrgText + "\n\n" + ModText
		else:
			InfoText = _("No copyright info available")
			
		self["SkinCopyright"].setText(InfoText)
	
	def delSkinDir(self):
		print("[MST] Delete: %s" % resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/")
		shutil.rmtree(resolveFilename(SCOPE_SKIN) + MerlinSkinThemes.selSkinName + "/")
		self.updateSkinList()
		
	def restartGUI(self, answer):
		if answer is True:
			self["SkinsList"].onSelectionChanged.remove(self.changedSkinsList)
			self.session.open(TryQuitMainloop, 3)
		else:
			self.exit(False)

	def save(self):
		restartbox = self.session.openWithCallback(self.restartGUI,MessageBox,_("Do you want to Restart the GUI now to apply new skin settings?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))

	def exit(self, cancel=True):
		print('[MST] closing')
		self["SkinsList"].onSelectionChanged.remove(self.changedSkinsList)
		if cancel:
			# exit means settings must not be stored
			config.plugins.MerlinSkinThemes3.Skin.cancel()
			config.plugins.MerlinSkinThemes3.selSkin.cancel()
			config.plugins.MerlinSkinThemes3.designModified.cancel()
			if "Designs" in config.plugins.MerlinSkinThemes3.dict():
				for key in config.plugins.MerlinSkinThemes3.Designs:
					config.plugins.MerlinSkinThemes3.Designs[key].cancel()
			if "DesignColor" in config.plugins.MerlinSkinThemes3.dict():
				for key in config.plugins.MerlinSkinThemes3.DesignColors:
					config.plugins.MerlinSkinThemes3.DesignColors[key].cancel()
			if "Themes" in config.plugins.MerlinSkinThemes3.dict():
				for key in config.plugins.MerlinSkinThemes3.Themes:
					config.plugins.MerlinSkinThemes3.Themes[key].cancel()
			if "Screens" in config.plugins.MerlinSkinThemes3.dict():
				for key in config.plugins.MerlinSkinThemes3.Screens:
					config.plugins.MerlinSkinThemes3.Screens[key].cancel()
			if "DisplayScreens" in config.plugins.MerlinSkinThemes3.dict():
				for key in config.plugins.MerlinSkinThemes3.DisplayScreens:
					config.plugins.MerlinSkinThemes3.DisplayScreens[key].cancel()
			if "CornerRadius" in config.plugins.MerlinSkinThemes3.dict():
				for key in config.plugins.MerlinSkinThemes3.CornerRadius:
					config.plugins.MerlinSkinThemes3.CornerRadius[key].cancel()
		self.close()
		
def main(session, **kwargs):
	session.open(MerlinSkinThemes)

def Plugins(path,**kwargs):
	list = [PluginDescriptor(name = "MerlinSkinThemes", description = "MerlinSkinThemes", where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main)]
	return list		

class MerlinSkinThemesConfig(Screen, HelpableScreen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="600,200" title="MerlinSkinThemes - Settings" backgroundColor="#00303030" >
			<widget name="config" position="10,10" size="580,130" scrollbarMode="showOnDemand" zPosition="1" /> 
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
		
		self.setTitle(_("MerlinSkinThemes - Settings"))

		self.list = []
		self.list.append(getConfigListEntry(_("Show preview picture"), config.plugins.MerlinSkinThemes3.showPreviewPicture))
		self.list.append(getConfigListEntry(_("Rebuild skin on boot"), config.plugins.MerlinSkinThemes3.rebuildSkinOnBoot))
		self.list.append(getConfigListEntry(_("Show plugin in extensions menu"), config.plugins.MerlinSkinThemes3.showInExtensions))
		
		ConfigListScreen.__init__(self, self.list)
		
		self["config"].setList(self.list)
	
	def saveSettings(self):
		config.plugins.MerlinSkinThemes3.rebuildSkinOnBoot.save()
		config.plugins.MerlinSkinThemes3.showInExtensions.save()
		config.plugins.MerlinSkinThemes3.showPreviewPicture.save()
		configfile.save()
		self.close()
		
	def closePlugin(self):
		config.plugins.MerlinSkinThemes3.rebuildSkinOnBoot.cancel()
		config.plugins.MerlinSkinThemes3.showInExtensions.cancel()
		config.plugins.MerlinSkinThemes3.showPreviewPicture.cancel()
		configfile.save()
		self.close()

# =================================================================================================

class GetSkinsList(MenuList, MerlinSkinThemes):
	SKIN_COMPONENT_KEY = "MerlinSkinThemesList"
	SKIN_COMPONENT_DIR_WIDTH = "dirWidth"
	SKIN_COMPONENT_STATUS_WIDTH = "statusWidth"
	SKIN_COMPONENT_INFO_WIDTH = "infoWidth"
	SKIN_COMPONENT_SKINENTRY_HEIGHT = "skinEntryHeight"

	def __init__(self, list, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setFont(1, gFont(tlf.face(tlf.SMALLER), tlf.size(tlf.SMALLER)))
		self.l.setItemHeight(componentSizes.itemHeight(GetSkinsList.SKIN_COMPONENT_SKINENTRY_HEIGHT, 40))
		self.selectedIndex = 0
		
	def buildList(self):
		list = []
		self.selectedIndex = 0

		sizes = componentSizes[GetSkinsList.SKIN_COMPONENT_KEY]
		configEntryHeight = sizes.get(componentSizes.ITEM_HEIGHT, 40)
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
