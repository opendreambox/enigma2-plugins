#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
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
#

from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.config import config
from enigma import getDesktop, eTimer, eConsoleAppContainer, eActionMap, eMusicPlayer
isAiO = True
try:
	from enigma import eSystemResourceLock
except:
	isAiO = False
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from urllib import quote
from twisted.web.client import downloadPage
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Input import Input
from Screens.InputBox import InputBox
from timer import TimerEntry
from Components.ProgressBar import ProgressBar
from Components.SystemInfo import SystemInfo
from twisted.web.client import getPage
import re
import os
import string
import xml.etree.cElementTree
from Tools.BoundFunction import boundFunction
from Tools.NumericalTextInput import NumericalTextInput

from InternetRadioFavoriteConfig import InternetRadioFavoriteConfig
from InternetRadioInformationScreen import InternetRadioInformationScreen
from InternetRadioOledDisplay import InternetRadioOledDisplay
from InternetRadioSetup import InternetRadioSetup
from InternetRadioCover import InternetRadioCover
from InternetRadioList import InternetRadioList
from InternetRadioWebFunctions import sendUrlCommand
from InternetRadioClasses import InternetRadioFilter, InternetRadioStation
from InternetRadioVisualization import InternetRadioVisualization
from InternetRadioPiPTVPlayer import InternetRadioPiPTVPlayer
from InternetRadioAdvancedSearch import InternetRadioAdvancedSearch
from json import loads as json_loads

containerStreamripper = None

class InternetRadioScreen(Screen, InternetRadioVisualization, InternetRadioPiPTVPlayer):

	FILTERLIST = 0
	STATIONLIST = 1
	FAVORITELIST = 2
	#SEARCHLIST = 3
	STREAMRIPPER_BIN = '/usr/bin/streamripper'
	
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		# helper for skinning ;)
#		count = 16
#		skincontent = ""
#		skincontent2 = ""
#		posx = 830
#		x = 0
#		while True:
#			skincontent += "<widget name=\"progress_%d\" zPosition=\"3\" position=\"%d,470\" size=\"25,200\" transparent=\"1\" orientation=\"orBottomToTop\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png\" />\n" % (x,posx)
#			skincontent2 += "<widget name=\"top_%d\" position=\"%d,465\" zPosition=\"6\" size=\"25,5\" transparent=\"1\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png\" />\n" % (x,posx)

#			posx += 25
#			x += 1
#			if x == count:
#				break

		skin = """
			<screen name="InternetRadio" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget transparent="1" name="video" position="0,0" size="1280,720" zPosition="1"/>
				<eLabel backgroundColor="#00000000" position="0,0" size="1280,720" zPosition="1"/>
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" scale="stretch" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="350,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="500,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="50,77" zPosition="1" size="1180,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				
				
				
				<widget source="list" render="Listbox" position="50,110" zPosition="2" size="1180,340" scrollbarMode="showOnDemand" transparent="0" backgroundColor="#00000000">
					<convert type="TemplatedMultiContent">
						{"templates": {
							"default":(30, [
								MultiContentEntryText(pos=(0,0), size=(1180,28), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=0),
							]),
							"favorite": (65,
							[
								MultiContentEntryText(pos=(0,0), size=(1180,28), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=0),
								MultiContentEntryText(pos=(10,28), size=(1180,26), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=1),
							]),
						},
							"fonts": [gFont("Regular",22),gFont("Regular",18)],
						}
					</convert>				
				</widget>
				
				<widget name="statustext" position="50,470" zPosition="2" size="1240,18" font="Regular;16" transparent="0"  backgroundColor="#00000000"/>
				<widget name="cover" zPosition="2" position="50,490" size="51,55" />
				<eLabel name="stationCap" position="50,550" size="85,20" text="Station:" font="Regular;18" transparent="1"  zPosition="1" backgroundColor="#00000000"/>
				<widget name="station" position="125,550" zPosition="2" size="825,20" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<eLabel name="titleCap" position="50,575" size="65,20" text="Title:" font="Regular;18" transparent="1"  zPosition="1" backgroundColor="#00000000"/>
				<widget name="title" position="105,575" zPosition="2" size="720,40" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="console" position="50,620" zPosition="1" size="900,50" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="830,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="855,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="880,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="905,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="930,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="955,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="980,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="1005,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="1030,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="1055,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="1080,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="1105,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="1130,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="1155,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="1180,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="1205,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="830,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="855,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="880,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="905,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="930,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="955,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="980,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="1005,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="1030,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="1055,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="1080,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="1105,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="1130,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="1155,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="1180,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="1205,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""
	else: # assume 1080 skin here...
		skin = """
			<screen name="InternetRadio" position="0,0" size="1920,1080" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget transparent="1" name="video" position="0,0" size="1280,720" zPosition="1"/>
				<eLabel backgroundColor="#00000000" position="0,0" size="1280,720" zPosition="1"/>
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" scale="stretch" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" scale="stretch" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;24" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;24" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="350,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;24" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="500,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;24" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="50,77" zPosition="1" size="1180,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				
			
				
				<widget source="list" render="Listbox" position="50,110" zPosition="2" size="1820,510" scrollbarMode="showOnDemand" transparent="0" backgroundColor="#00000000">
					<convert type="TemplatedMultiContent">
						{"templates": {
							"default":(40, [
								MultiContentEntryText(pos=(0,0), size=(1820,36), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=0),
							]),
							"favorite": (86,
							[
								MultiContentEntryText(pos=(0,0), size=(1820,36), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=0),
								MultiContentEntryText(pos=(10,36), size=(1820,30), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=1),
							]),
						},
							"fonts": [gFont("Regular",32),gFont("Regular",28)],
						}
					</convert>
				</widget>
				
				<widget name="statustext" position="50,705" zPosition="2" size="1240,30" font="Regular;24" transparent="0"  backgroundColor="#00000000"/>
				<widget name="cover" zPosition="2" position="50,735" size="51,55" />
				<eLabel name="stationCap" position="50,825" size="100,32" text="Station:" font="Regular;28" transparent="1"  zPosition="1" backgroundColor="#00000000"/>
				<widget name="station" position="140,825" zPosition="2" size="1725,32" font="Regular;28" transparent="1"  backgroundColor="#00000000"/>
				<eLabel name="titleCap" position="50,864" size="80,32" text="Title:" font="Regular;28" transparent="1"  zPosition="1" backgroundColor="#00000000"/>
				<widget name="title" position="120,864" zPosition="2" size="1705,32" font="Regular;28" transparent="1"  backgroundColor="#00000000"/>
				<widget name="console" position="50,930" zPosition="1" size="1800,50" font="Regular;28" transparent="1"  backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="1245,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="1270,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="1295,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="1320,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="1345,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="1370,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="1395,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="1420,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="1445,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="1470,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="1495,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="1520,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="1545,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="1570,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="1595,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="1620,705" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="1245,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="1270,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="1295,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="1320,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="1345,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="1370,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="1395,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="1420,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="1445,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="1470,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="1495,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="1520,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="1545,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="1570,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="1595,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="1620,698" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""
	
	def __init__(self, session, url = None, radioStation = None):
		self.session = session
		Screen.__init__(self, session)
		InternetRadioVisualization.__init__(self)
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		InternetRadioPiPTVPlayer.__init__(self,session, self.currentService, self.setPiPPlayerEnabled)
		self.skinName = "InternetRadio"
		self.session.nav.stopService()
		self["cover"] = InternetRadioCover(self.coverLoaded)
		self["key_red"] = StaticText(_("Record"))
		self["key_green"] = StaticText(_("Filters"))
		self["key_yellow"] = StaticText(_("Search"))
		self["key_blue"] = StaticText(_("Stations"))

		self.mode = self.FAVORITELIST
		self["list"] = InternetRadioList()
		self["statustext"] = Label()
		self["actions"] = ActionMap(["WizardActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.ok_pressed,
			"back": self.close,
			"input_date_time": self.menu_pressed,
			"red": self.red_pressed,
			"green": self.green_pressed,
			"yellow": self.yellow_pressed,
			"blue": self.blue_pressed,
			"info" : self.info_pressed,
			
		}, -1)
		
		self["NumberActions"] = NumberActionMap(["NumberActions","InputAsciiActions"],
		{
			"gotAsciiCode": self.keyAsciiCode,
			"0": self.keyNumberGlobal,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		})
		
		self.numericalTextInput = NumericalTextInput()
		self.numericalTextInput.setUseableChars(u'1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ#')

		self.stationList = []
		self.stationListIndex = 0

		self.filterList = []
		self.filterListIndex = 0

		self.favoriteList = []
		self.favoriteListIndex = 0

		self.stationListFiltered = []
		
		self.offsetValue = 0
	
		self.favoriteConfig = InternetRadioFavoriteConfig()
		
		self["title"] = Label()
		self["station"] = Label()
		self["headertext"] = Label()
		self["console"] = Label()

		self.stationHeaderText = ""
		self.searchInternetRadioString = ""

		self.currentPlayingStation = None 

		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.startRun)
		self.onExecBegin.append(self.onBeginExec)

		self.musicPlayer = eMusicPlayer(self.BANDS)
		#self.musicPlayer.timeout.connect(self.musicPlayerCallBack)
		self.musicPlayer_conn = self.musicPlayer.callback.connect(self.musicPlayerCallBack)

		self.try_url = ""
		self.url_tried = 0
		
		self.currentCoverArtSearchRequest = ""

		self.stationSearchURL = "https://de1.api.radio-browser.info/json/stations/search"
		self.baseUrl = "https://de1.api.radio-browser.info/json/"
		
		self.currentFilter = ""

		self.visuCleanerTimer = eTimer()
		self.visuCleanerTimer_conn = self.visuCleanerTimer.timeout.connect(self.visuCleanerTimerCallback)

		self.clearStatusTextTimer = eTimer()
		self.clearStatusTextTimer_conn = self.clearStatusTextTimer.timeout.connect(self.clearStatusTextTimerCallback)

		self.fullScreenAutoActivationTimer = eTimer()
		self.fullScreenAutoActivationTimer_conn = self.fullScreenAutoActivationTimer.timeout.connect(self.fullScreenAutoActivationTimerCallback)
		
		self.visible = True
		
		self.fullScreen = session.instantiateDialog(InternetRadioFullScreen, zPosition=1000)
		self.autoActivationKeyPressedActionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.autoActivationKeyPressed)

		global containerStreamripper
		global dataAvail_conn
		global appClosed_conn
		if containerStreamripper is None:
			containerStreamripper = eConsoleAppContainer()

		dataAvail_conn = containerStreamripper.dataAvail.connect(self.streamripperDataAvail)
		appClosed_conn = containerStreamripper.appClosed.connect(self.streamripperClosed)

		if url is not None and radioStation is not None:
			self.playRadioStation(url, radioStation)
		elif containerStreamripper.running():
			self["key_red"].setText(_("Stop record"))
			# just to hear to recording music when starting the plugin...
			self.currentPlayingStation = InternetRadioStation(name = _("Recording stream station"))
			self.playServiceStream("http://localhost:9191")
		self.session.nav.SleepTimer.on_state_change.append(self.sleepTimerEntryOnStateChange)
		
		self._lock = None
		self.messageShown = False
		self.onShown.append(self.__run)	
		
	def __run(self):
		if isAiO:
			self._lock = eSystemResourceLock(eSystemResourceLock.ResrouceLockAudio)
		else:
			if not self.messageShown:
				self.messageShown = True
				self.session.open(MessageBox, _("This plugin does not work on Dream One/Two unless AiO image is used."), MessageBox.TYPE_INFO, timeout=0)

	def keyAsciiCode(self):
		unichar = unichr(getPrevAsciiCode())
		charstr = unichar.encode('utf-8')
		if len(charstr) == 1:
			index = self.getFirstMatchingEntry(charstr[0])
			if index is not None:
				self["list"].setIndex(index)
				
	def keyNumberGlobal(self, number):
		unichar = self.numericalTextInput.getKey(number)
		charstr = unichar.encode('utf-8')
		if len(charstr) == 1:
			index = self.getFirstMatchingEntry(charstr[0])
			if index is not None:
				self["list"].setIndex(index)
				
	def getFirstMatchingEntry(self, char):
		if self.mode == self.STATIONLIST:
			for i in range(len(self.stationList)):
				if self.stationList[i].name.upper().startswith(char):
					return i
		elif self.mode == self.FILTERLIST:
			for i in range(len(self.filterList)):
				if self.filterList[i].name.upper().startswith(char):
					return i
	
	def sleepTimerEntryOnStateChange(self, timer):
		if timer.state == TimerEntry.StateEnded:
			self.closePlayer()

	def onBeginExec(self):
		if config.plugins.internetradio.visualization.value in ("2", "3"):
			self.summaries.setLabelVisibility(True)			

	def visualizationConfigOnChange(self, configElement = None):
		if config.plugins.internetradio.visualization.value in ("0", "1"):
			self.musicPlayer.setBands(self.BANDS)
			self.summaries.setLabelVisibility(False)
		elif config.plugins.internetradio.visualization.value == "2":
			self.musicPlayer.setBands(self.BANDS)
			self.summaries.setLabelVisibility(True)
		elif config.plugins.internetradio.visualization.value == "3":
			if config.plugins.internetradio.fullscreenlayout.value != "0":
				self.musicPlayer.setBands(0)
			self.summaries.setLabelVisibility(True)
		if config.plugins.internetradio.visualization.value in ("1", "3"):
			self.hideControls()

	def fullscreenlayoutConfigOnChange(self, configElement = None):
		if config.plugins.internetradio.visualization.value == "3" and config.plugins.internetradio.fullscreenlayout.value != "0":
			self.musicPlayer.setBands(0)
		else:
			self.musicPlayer.setBands(self.BANDS)

	def fullscreenautoactivationConfigOnChange(self, configElement = None):
		if config.plugins.internetradio.fullscreenautoactivation.value == "-1":
			self.fullScreenAutoActivationTimer.stop()
		else:
			self.fullScreenAutoActivationTimer.start(int(config.plugins.internetradio.fullscreenautoactivation.value)*1000)

	def autoActivationKeyPressed(self, key = None, flag = None):
		self.fullScreenAutoActivationTimer.stop()
		if  self.shown == True and self.visible == True and config.plugins.internetradio.fullscreenautoactivation.value != "-1":
			self.fullScreenAutoActivationTimer.start(int(config.plugins.internetradio.fullscreenautoactivation.value)*1000)
		return 0

	def fullScreenAutoActivationTimerCallback(self):
		self.fullScreenAutoActivationTimer.stop()
		self.showFullScreen()

	def startRun(self):
		self.setPiPTVPlayerEnabled(False)
		config.plugins.internetradio.visualization.addNotifier(self.visualizationConfigOnChange, initial_call = True)
		config.plugins.internetradio.fullscreenautoactivation.addNotifier(self.fullscreenautoactivationConfigOnChange, initial_call = True)
		config.plugins.internetradio.fullscreenlayout.addNotifier(self.fullscreenlayoutConfigOnChange, initial_call = False)
		self.setPBtoNull()
		self.setProperties()
		self.getFavoriteList()
		self.visuCleanerTimer.start(1000)
		if self.currentPlayingStation is None and config.plugins.internetradio.startupname.value != "" and config.plugins.internetradio.startuptext.value != "":
			self["list"].moveToFavorite(config.plugins.internetradio.startupname.value, config.plugins.internetradio.startuptext.value)
			url = config.plugins.internetradio.startuptext.value
			self.currentPlayingStation = InternetRadioStation(name = config.plugins.internetradio.startupname.value, url = url)
			self.url_tried = 0
			self.try_url = url
			if url.endswith(".pls") or url.endswith(".m3u") or url.endswith(".asx"):
				self.setStatusText(_("Getting streaming data from %s") % url)
				sendUrlCommand(url, None,10).addCallback(self.callbackPlayList).addErrback(self.callbackStationListError)
			else:
				self.playServiceStream(url)

	def info_pressed(self):
		meta = self.musicPlayer.getMetaInfos()
		self.session.open(InternetRadioInformationScreen, meta)

	def showFullScreen(self):
		if self.fullScreen.isVisible() == False:
			self.visible = False
			self.fullScreen.setVisibility(True)
			if config.plugins.internetradio.fullscreenlayout.value in ("0","1"):
				self.fullScreen.setStation(self["station"].getText())
				self.fullScreen.setText(self["title"].getText())
				if config.plugins.internetradio.googlecover.value:
					if self["cover"].getPicloaded():
						self.fullScreen.updateCover()
					else:
						self.fullScreen.setVisibilityCover(False)
			else:
				self.fullScreen.setStation("")
				self.fullScreen.setText("")
				self.fullScreen.setVisibilityCover(False)
			self.fullScreenKeyPressedActionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.fullScreenKeyPressed)
			
	def fullScreenKeyPressed(self, key = None, flag = None):
		if self.fullScreen.isVisible():
			self.visible = True
			self.fullScreen.setVisibility(False)
			self.fullScreenKeyPressedActionSlot = None
			self.autoActivationKeyPressed()
			return 1
		else:
			return 0

	def visuCleanerTimerCallback(self):
		self.visuCleanerTimer.stop()
		if self.needCleanup() == True:
			code = 0
			v = (-80,) * self.BANDS
			self.musicPlayerCallBack(code,v,True)

	def musicPlayerCallBack(self, code = None, v = None, cleanup = False):
		if self.visuCleanerTimer.isActive():
			self.visuCleanerTimer.stop()
		if code == 0 and len(v) > 0:
			if config.plugins.internetradio.visualization.value in ("0","1"):
				self.summaries.setValues(v)
			if self.fullScreen.isVisible() and config.plugins.internetradio.fullscreenlayout.value == "0":
				self.fullScreen.setValues(v)
			if self.visible and config.plugins.internetradio.visualization.value in ("0","2"):
				self.setValues(v)
		elif code == 1:
			cleanup = True
			if (len(v[0]) !=0):
				if len(v[1]) != 0:
					sTitle = "%s - %s" % (v[0],v[1])
				else:
					sTitle = v[0]
				if config.plugins.internetradio.googlecover.value and self.currentCoverArtSearchRequest != sTitle:
					self.currentCoverArtSearchRequest = sTitle
					url = "http://itunes.apple.com/search?term=%s&limit=1&media=music" %quote(sTitle)
					getPage(url, timeout=4).addCallback(self.GoogleImageCallback).addErrback(self.Error)
			else:
				sTitle = "n/a"
				self.hideCover()
			self["title"].setText(sTitle)
			
			self.summaries.setText(sTitle)
			if self.fullScreen.isVisible() and config.plugins.internetradio.fullscreenlayout.value in ("0", "1"):
				self.fullScreen.setText(sTitle)
		elif code == -2:
			cleanup = True
			if v[0] in (5, 6): # text/uri-list - this can't be decoded.
				self.url_tried += 1
				if self.url_tried == 1:
					self.setStatusText(_("Getting streaming data from\n%s") % self.try_url)
					sendUrlCommand(self.try_url, None,10).addCallback(self.callbackPlayList).addErrback(self.callbackStationListError)
				else:
					self.setStatusText("Error: %s" % v[1], 15000)
					self.currentPlayingStation = None
			else:
				self.setStatusText("Error: %s" % v[1], 15000)
				self.currentPlayingStation = None
		elif code == -5:
			cleanup = True
			if v[0] == 0:
				text = "trying to start %s..." % v[1]
			elif v[0] == 1:
				text = "playing %s..." % v[1]
			elif v[0] == 2:
				text = "%s stopped playing..." % v[1]
			else:
				text = ""
			self.setStatusText(text)
		else:
			if v and len(v) > 2:
				self.setStatusText("Error: %s" % v[1], 15000)
			cleanup = True

		if cleanup == True:
			self.visuCleanerTimer.start(100)

	def streamripperClosed(self, retval):
		if retval == 0:
			self["console"].setText("")
		self["key_red"].setText(_("Record"))

	def streamripperDataAvail(self, data):
		sData = data.replace('\n','')
		self["console"].setText(sData)

	def InputBoxStartRecordingCallback(self, returnValue = None):
		if returnValue:
			recordingLength =  int(returnValue) * 60
			if not os.path.exists(config.plugins.internetradio.dirname.value):
				os.mkdir(config.plugins.internetradio.dirname.value)
			args = []
			args.append(self.currentPlayingStation.url)
			args.append('-d')
			args.append(config.plugins.internetradio.dirname.value)
			args.append('-r')
			args.append('9191')
			if recordingLength != 0:
				args.append('-l')
				args.append("%d" % int(recordingLength))
			if config.plugins.internetradio.riptosinglefile.value:
				args.append('-a')
				args.append('-A')
			if not config.plugins.internetradio.createdirforeachstream.value:
				args.append('-s')
			if config.plugins.internetradio.addsequenceoutputfile.value:
				args.append('-q')
			cmd = [self.STREAMRIPPER_BIN, self.STREAMRIPPER_BIN] + args
			containerStreamripper.execute(*cmd)
			self["key_red"].setText(_("Stop record"))
			
	def deleteRecordingConfirmed(self,val):
		if val:
			containerStreamripper.sendCtrlC()

	def red_pressed(self):
		if containerStreamripper.running():
			self.session.openWithCallback(self.deleteRecordingConfirmed, MessageBox, _("Do you really want to stop the recording?"))
		else:
			if self.currentPlayingStation and len(self.currentPlayingStation.url) != 0:
				self.session.openWithCallback(self.InputBoxStartRecordingCallback, InputBox, windowTitle = _("Recording length"),  title=_("Enter in minutes (0 means unlimited)"), text="0", type=Input.NUMBER)
			else:
				self.session.open(MessageBox, _("Only running streamings can be recorded!"), type = MessageBox.TYPE_INFO,timeout = 20 )

	def green_pressed(self):
		self.offsetValue = 0
		self.session.openWithCallback(self.getValuesForFilter, ChoiceBox, _("Please select filter type..."), list = [(_("Country"), "countries"), (_("Language"), "languages"), (_("Genre"), "tags"), (_("Codec"), "codecs")])
	
	def getValuesForFilter(self, selection):
		if selection:
			self["key_blue"].setText(_("Favorites"))
			self.offsetValue = 0
			self.currentFilter = selection[1]
			sendUrlCommand("%s%s?hidebroken=true" %(self.baseUrl, selection[1]), None, 10).addCallback(self.callbackFilterList).addErrback(self.callbackFilterListError)

	def yellow_pressed(self):
		self["key_blue"].setText(_("Favorites"))
		self.search()
		"""
		if self.mode != self.STATIONLIST or (self.mode == self.STATIONLIST and self.currentFilter != ""):
			self.currentFilter = ""
			self.stationListIndex = 0
			self.getStationList(_("All"))
		"""
				
	def blue_pressed(self):
		if self.mode != self.FAVORITELIST:
			self.getFavoriteList(self.favoriteListIndex)
			self["key_blue"].setText(_("Stations"))
		elif self.mode != self.STATIONLIST or (self.mode == self.STATIONLIST and self.currentFilter != ""):
			self.currentFilter = ""
			self.stationListIndex = 0
			self["key_blue"].setText(_("Favorites"))
			self.getStationList(_("All"))

	def getFavoriteList(self, favoriteListIndex = 0):
		self.mode = self.FAVORITELIST
		self["headertext"].setText(_("Favorite list"))
		self["list"].setListMode(self.mode)
		favoriteList = self.favoriteConfig.getFavoriteList()
		self["list"].setList(favoriteList)
		if len(favoriteList):
			self["list"].moveToIndex(favoriteListIndex)

	def callbackFilterList(self, jsonstring):
		filters = json_loads(jsonstring)
		
		allText = ""
		if self.currentFilter == "countries":
			allText = _("All countries")
		elif self.currentFilter == "languages":
			allText = _("All languages")
		elif self.currentFilter == "codecs":
			allText = _("All codecs")
		elif self.currentFilter == "tags":
			allText = _("All genres")
		self.filterList = [InternetRadioFilter(name = allText)]
		
		for filter in filters:
			self.filterList.append(InternetRadioFilter(name = filter.get('name', '').encode('utf-8','ignore')))
		
		self.filterListFiltered = self.getTupleList(self.filterList)
		self.mode = self.FILTERLIST
		self["list"].setListMode(self.mode)
		self["list"].setList(self.filterListFiltered)

	def callbackFilterListError(self, error = None):
		if error is not None:
			try:
				self.setStatusText(_("%s...") % str(error.getErrorMessage()), 15000)
			except: pass

	def ok_pressed(self):
		if self.visible:
			sel = None
			try:
				sel = self["list"].getCurrentSelection()
			except:return
			if sel is None:
				return
			else:
				if self.mode == self.FILTERLIST:
					self.stationListIndex = 0
					self.filterListIndex = self["list"].getCurrentIndex()
					self.getStationList(sel.name)
					
				elif self.mode in (self.STATIONLIST, self.FAVORITELIST):
					if self.mode == self.STATIONLIST and sel.name == _("Load next %s stations" %(config.plugins.internetradio.pagingsize.value)):
						self.offsetValue += int(config.plugins.internetradio.pagingsize.value)
						self.stationListIndex = self.offsetValue
						self.getStationList(sel.id)
					else:
						goOn = True
						currentPlayingStation = None
						if self.mode == self.STATIONLIST:
							url = sel.url.rstrip().strip().lower()
							currentPlayingStation = sel
							currentPlayingStation.url = ""
							self.stationListIndex = self["list"].getCurrentIndex()
						else:
							self.favoriteListIndex = self["list"].getCurrentIndex()
							if sel.configItem.type.value == 0:
								url = sel.configItem.text.value
								currentPlayingStation = InternetRadioStation(name = sel.configItem.name.value, tags = sel.configItem.tags.value, country = sel.configItem.country.value, homepage = sel.configItem.homepage.value)
							else:
								goOn = False
								if sel.configItem.type.value > 0:
									self.stationListIndex = 0
									self.filterList = []
									if sel.configItem.type.value == 1:
										f = _("Genres")
										self.currentFilter = "tags"
									elif sel.configItem.type.value == 2:
										f = _("Countries")
										self.currentFilter = "countries"
									elif sel.configItem.type.value == 3:
										f = _("Languages")
										self.currentFilter = "languages"
									elif sel.configItem.type.value == 4:
										f = _("Codecs")
										self.currentFilter = "codecs"
									self.mode = self.FILTERLIST
									self.getStationList(sel.configItem.name.value)
						if goOn == True:
							self.playRadioStation(url, currentPlayingStation)
				# shouldn't be needed anymore
				"""
				elif self.mode == self.SEARCHLIST and self.searchInternetRadioString != "":
					self.searchInternetRadio(self.searchInternetRadioString)
				"""

	def playRadioStation(self, url, radioStation):
		self.stopPlaying()
		self.currentPlayingStation = radioStation
		self.url_tried = 0
		self.try_url = url
		if url.endswith(".pls") or url.endswith(".m3u") or url.endswith(".asx"):
			self.setStatusText(_("Getting streaming data from %s") % url)
			sendUrlCommand(url, None,10).addCallback(self.callbackPlayList).addErrback(self.callbackStationListError)
		else:
			self.playServiceStream(url)
			
	def stopPlaying(self):
		self.musicPlayer.play("")
		self.currentPlayingStation = None 
		self["title"].setText("")
		self["station"].setText("")
		self.summaries.setText("")
		self["cover"].hide()
		self.visuCleanerTimer.start(100)

	def callbackPlayList(self, result):
		found = False
		parts = string.split(result.lower(),"\n")
		if parts[0].startswith("http://"):
					url = parts[0]
					found = True
					self.playServiceStream(url.rstrip().strip())
		elif parts[0].find("[playlist]") != -1:
			for lines in parts:
				if lines.find("file1=") != -1:
					line = string.split(lines,"file1=")
					found = True
					self.playServiceStream(line[-1].rstrip().strip())
					break
		elif parts[0].find("#extm3u") != -1:
			for lines in parts:
				if lines.startswith("http://"):
					found = True
					self.playServiceStream(lines.rstrip().strip())
					break

		elif parts[0].lower().find("asx version") != -1:
			stationList = []
			try:
				root = xml.etree.cElementTree.fromstring(result.lower())
			except: 
				root = None
			if root:
				for childs in root.findall("entry"):
					for childs2 in childs.findall("ref"):
						url = childs2.get("href")
						if len(url):
							found = True
							self.playServiceStream(url.rstrip().strip())
							break
					if found:
						break
		if not found:
			self.currentPlayingStation = None
			self.setStatusText(_("No streaming data found..."), 15000)

	def getStationList(self,filter_string):
		self.stationHeaderText = _("InternetRadio station list for filter: %s") % filter_string
		self["headertext"].setText(self.stationHeaderText)
		self.setStatusText(_("Getting %s") %  self.stationHeaderText)

		self.stationListIndex = self.offsetValue
		searchAttribute = ""
		if self.currentFilter == "countries":
			searchAttribute = "country"
		elif self.currentFilter == "languages":
			searchAttribute = "language"
		elif self.currentFilter == "codecs":
			searchAttribute = "codec"
			
		if searchAttribute == "":
			url = "%s?hidebroken=true&limit=%s&offset=%d&bitrateMin=%d" %(self.stationSearchURL, config.plugins.internetradio.pagingsize.value, self.offsetValue, config.plugins.internetradio.bitratemin.value,)
		else:
			filter_string_quote = quote(filter_string)
			url = "%s?%s=%s&hidebroken=true&limit=%s&offset=%d&bitrateMin=%d" %(self.stationSearchURL, searchAttribute, filter_string_quote, config.plugins.internetradio.pagingsize.value, self.offsetValue, config.plugins.internetradio.bitratemin.value)
		sendUrlCommand(url, None,10).addCallback(boundFunction(self.callbackStationList,filter_string)).addErrback(self.callbackStationListError)

	def callbackStationList(self, filter_string, jsonstring):
		self.stationList = self.fillStationList(jsonstring, filter_string)
		self.stationListFiltered = self.getTupleList(self.stationList)
		if filter_string == "":
			self.currentFilter = ""
		self.setStationList()
		
	def setStationList(self):
		self.setStatusText("")
		self.mode = self.STATIONLIST
		self["headertext"].setText(self.stationHeaderText)
		self["list"].setListMode(self.mode)
		self["list"].setList(self.stationListFiltered)
		if len(self.stationList):
			self["list"].moveToIndex(self.stationListIndex)
		
	def getTupleList(self, list):
		return [ (x,) for x in list]

	def fillStationList(self,jsonstring, filter_string=""):
		if self.offsetValue == 0:	
			stationList = []
		else:
			stationList = self.stationList[:-1]
	
		stations = json_loads(jsonstring)
		
		for station in stations:
			stationList.append(InternetRadioStation(name= station.get('name', '').encode('utf-8','ignore'), tags = station.get('tags', '').encode('utf-8','ignore'), country= station.get('country', '').encode('utf-8','ignore'), url = station.get('url', '').encode('utf-8','ignore'), language = station.get('language', '').encode('utf-8','ignore'), id = station.get('id', '').encode('utf-8','ignore'), homepage = station.get('homepage', '').encode('utf-8','ignore')))
		
		if len(stationList)%int(config.plugins.internetradio.pagingsize.value) == 0 and len(stationList):
			stationList.append(InternetRadioStation(name= _("Load next %s stations" %(config.plugins.internetradio.pagingsize.value)), id=filter_string ))

		return stationList
		
	def menu_pressed(self):
		self.fullScreenAutoActivationTimer.stop()
		options = [(_("Config"), self.config),] #(_("Search"), self.search),]
		if self.mode == self.FAVORITELIST and self.getSelectedItem() is not None:
			options.extend(((_("rename current selected favorite"), self.renameFavorite),))
			options.extend(((_("remove current selected favorite"), self.removeFavorite),))
			if config.plugins.internetradio.startupname.value != "":
				options.extend(((_("do not play a service on startup"), boundFunction(self.startUpStation,False)),))
			if self.getSelectedItem().configItem.type.value == 0:
				options.extend(((_("play current selected favorite on startup"), boundFunction(self.startUpStation,True)),))
		elif self.mode == self.FILTERLIST and self.getSelectedItem() is not None:
			options.extend(((_("Add current selected genre to favorite"), self.addFilterToFavorite),))
		elif self.mode == self.STATIONLIST and self.getSelectedItem() is not None:
			options.extend(((_("Add current selected station to favorite"), self.addStationToFavorite),))
		if self.currentPlayingStation and len(self.currentPlayingStation.url) != 0:
			options.extend(((_("Add current playing stream to favorite"), self.addCurrentStreamToFavorite),))
		options.extend(((_("Fullscreen"), self.showFullScreen),))
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			options.extend(((_("Show TV"), boundFunction(self.setPiPPlayerEnabled,True)),))
		self.session.openWithCallback(self.menuCallback, ChoiceBox,list = options)

	def menuCallback(self, ret):
		ret and ret[1]()

	def setPiPPlayerEnabled(self, value):
		if value:
			self["actions"].setEnabled(False)
			self.fullScreenAutoActivationTimer.stop()
			self.hide()
			self.visible = False
			self.setPiPTVPlayerEnabled(True)
		else:
			self.currentService = self.currService
			self["actions"].setEnabled(True)
			self.show()
			self.visible = True
			self.autoActivationKeyPressed()			

	def startUpStation(self, add):
		if add == True:
			sel = self.getSelectedItem()
			if sel and sel.configItem.type.value == 0:
				config.plugins.internetradio.startupname.value = sel.configItem.name.value
				config.plugins.internetradio.startuptext.value = sel.configItem.text.value
		else:
			config.plugins.internetradio.startupname.value = ""
			config.plugins.internetradio.startuptext.value = ""
		config.plugins.internetradio.save()

	def addFilterToFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			if self.currentFilter == "countries":
				favoritetype = 2
			elif self.currentFilter == "tags":
				favoritetype = 1
			elif self.currentFilter == "languages":
				favoritetype = 3
			elif self.currentFilter == "codecs":
				favoritetype = 4
			self.favoriteConfig.addFavorite(name = sel.name, text = sel.name, favoritetype = favoritetype, tags = "", country = "", homepage = "")			

	def addStationToFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			self.favoriteConfig.addFavorite(name = sel.name, text = sel.url, favoritetype = 0, tags = sel.genre, country = sel.country, homepage = sel.homepage)			
		
	def addCurrentStreamToFavorite(self):
		self.favoriteConfig.addFavorite(name = self.currentPlayingStation.name, text = self.currentPlayingStation.url, favoritetype = 0, tags =self.currentPlayingStation.tags, country = self.currentPlayingStation.country, homepage = self.currentPlayingStation.homepage)

	def renameFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			self.session.openWithCallback(boundFunction(self.renameFavoriteFinished, sel.configItem), VirtualKeyBoard, title = _("Enter new name for favorite item"), text = sel.configItem.name.value)

	def renameFavoriteFinished(self, configItem, text = None):
		if text:
			self.favoriteConfig.renameFavorite(configItem, text)
			self.favoriteListIndex = self["list"].getCurrentIndex()
			self.getFavoriteList(self.favoriteListIndex)

	def removeFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			self.favoriteConfig.removeFavorite(sel.configItem)
			self.favoriteListIndex = self["list"].getCurrentIndex()
			if self.favoriteListIndex >= 1:
				self.favoriteListIndex -= 1
			self.getFavoriteList(self.favoriteListIndex)

	def search(self):
		if config.plugins.internetradio.advancedsearch.value:
			self.session.openWithCallback(self.searchInternetRadio, InternetRadioAdvancedSearch)
		else:
			self.session.openWithCallback(self.searchInternetRadio, VirtualKeyBoard, title = _("Enter text to search for"))

	def searchInternetRadio(self, searchstring = None, searchstringList=[]):
		if searchstring:
			self.stationHeaderText =  _("InternetRadio station list for search-criteria: %s") % searchstring
			self["headertext"].setText(self.stationHeaderText)
			self.setStatusText(_("Searching InternetRadio for %s...") % searchstring)
			#self.mode = self.SEARCHLIST
			self.searchInternetRadioString = searchstring.lower()
			self.stationListIndex = 0
			self.offsetValue = 0
			self.stationListIndex = 0
			sendUrlCommand("%s?name=%s&bitrateMin=%d" %(self.stationSearchURL, quote(self.searchInternetRadioString), config.plugins.internetradio.bitratemin.value ), None,10).addCallback(boundFunction(self.callbackStationList,"")).addErrback(self.callbackStationListError)
		else:
			if len(searchstringList):
				self.stationHeaderText =  _("InternetRadio station list for search-criteria: %s") % (searchstringList[0])
				self["headertext"].setText(self.stationHeaderText)
				self.setStatusText(_("Searching InternetRadio..."))
				#self.mode = self.SEARCHLIST
				searchAttributeString = ""
				if searchstringList[0] != "":
					searchAttributeString += "&name=%s" %(quote(searchstringList[0].lower()))
				if searchstringList[1] != _("None"):
					searchAttributeString += "&country=%s" %(quote(searchstringList[1]))
				if searchstringList[2] != _("None"):
					searchAttributeString += "&tagList=%s" %(quote(searchstringList[2].lower()))
				if searchstringList[3] != _("None"):
					searchAttributeString += "&codec=%s" %(quote(searchstringList[3].lower()))
				if searchstringList[4] != _("None"):
					searchAttributeString += "&language=%s" %(quote(searchstringList[4].lower()))
				self.stationListIndex = 0
				self.offsetValue = 0
				self.stationListIndex = 0
				sendUrlCommand("%s?hidebroken=true&bitrateMin=%d%s" %(self.stationSearchURL, config.plugins.internetradio.bitratemin.value, searchAttributeString), None,10).addCallback(boundFunction(self.callbackStationList,"")).addErrback(self.callbackStationListError)				

	def config(self):
		self.session.open(InternetRadioSetup)

	def callbackStationListError(self, error = None):
		if error is not None:
			try:
				self.setStatusText(_("%s ...") % str(error.getErrorMessage()), 15000)
			except: pass

	def Error(self, error = None):
		if error is not None:
			try:
				self.setStatusText(str(error.getErrorMessage()), 15000)
			except: pass
	
	def __onClose(self):
		global dataAvail_conn
		global appClosed_conn
		self.session.deleteDialog(self.fullScreen)
		self.fullScreen = None
		self.autoActivationKeyPressedActionSlot = None
		self.session.nav.SleepTimer.on_state_change.remove(self.sleepTimerEntryOnStateChange)
		self.session.nav.playService(self.currentService)
		dataAvail_conn = None
		appClosed_conn = None
		
		self._lock = None
		
		# fallback to earlier enigma versions FIXME Delete that when commiting
		try:
			config.plugins.internetradio.visualization.removeNotifier(self.visualizationConfigOnChange)
			config.plugins.internetradio.fullscreenautoactivation.removeNotifier(self.fullscreenautoactivationConfigOnChange)
			config.plugins.internetradio.fullscreenlayout.removeNotifier(self.fullscreenlayoutConfigOnChange)
		
		except:
			config.plugins.internetradio.visualization.notifiers.remove(self.visualizationConfigOnChange)
			config.plugins.internetradio.fullscreenautoactivation.notifiers.remove(self.fullscreenautoactivationConfigOnChange)
			config.plugins.internetradio.fullscreenlayout.notifiers.remove(self.fullscreenlayoutConfigOnChange)

	def GoogleImageCallback(self, result):
		self.hideCover()
		url = ""
		try:
			data = json_loads(result)
			url = data['results'][0]['artworkUrl100'].encode('utf-8').replace('100x100', '450x450').replace('https', 'http')
		except:
			pass
		if url:
			print "[InternetRadio] downloading cover from %s " % url
			downloadPage(url, "/tmp/.cover").addCallback(self.coverDownloadFinished).addErrback(self.coverDownloadFailed)
		else:
			print 'iTunes-images not found...'
			
	def coverDownloadFailed(self,result):
		print "[InternetRadio] cover download failed: %s " % result
		self.hideCover()
		
	def hideCover(self):
		self["cover"].hide()
		self["cover"].setPicloaded(False)
		if self.fullScreen.isVisible() and config.plugins.internetradio.fullscreenlayout.value in ("0","1"):
			self.fullScreen.setVisibilityCover(False)

	def coverDownloadFinished(self,result):
		print "[InternetRadio] cover download finished"
		self["cover"].updateIcon("/tmp/.cover")

	def coverLoaded(self):
		self["cover"].show()
		if self.fullScreen.isVisible() and config.plugins.internetradio.fullscreenlayout.value in ("0","1"):
			self.fullScreen.updateCover()
		
	def playServiceStream(self, url):
		self.currentCoverArtSearchRequest = ""
		self.musicPlayer.play(url)
		if self.currentPlayingStation:
			self.currentPlayingStation.url = url
			self["station"].setText(self.currentPlayingStation.name)
		self["title"].setText(_("Title: n/a"))

	def createSummary(self):
		return InternetRadioOledDisplay

	def getSelectedItem(self):
		sel = None
		try:
			sel = self["list"].getCurrentSelection()
		except:return None
		return sel
		
	def closePlayer(self):
		self.fullScreenKeyPressed()
		self.close()

	def setStatusText(self, text, cleartimertime = 3000):
		self.clearStatusTextTimer.stop()
		self["statustext"].setText(text)
		self.clearStatusTextTimer.start(cleartimertime)

	def clearStatusTextTimerCallback(self):
		self.clearStatusTextTimer.stop()
		self["statustext"].setText("")

	# used from webinterface
	def updateFullscreenStationName(self, stationname):
		if self.fullScreen.isVisible():
			self.fullScreen.setStation(stationname)

	# used from webinterface
	def getCurrentPlayingStation(self):
		if self.currentPlayingStation and self.currentPlayingStation.url != "":
			return (True, "%s - %s" % (self["station"].getText(), self["title"].getText()))
		else:
			return (False, _("nothing playing..."))
		
	# used from webinterface
	def getStreamingInfos(self):
		return self.musicPlayer.getMetaInfos()

	# used from webinterface
	def updateFavoriteList(self):
		if self.mode == self.FAVORITELIST:
			index = self["list"].getCurrentIndex()
			self.favoriteConfig.loadFavoriteConfig() # reload favorites
			favoriteList = self.favoriteConfig.getFavoriteList()
			self["list"].setList(favoriteList)
			if len(favoriteList):
				self["list"].moveToIndex(index)
		
class InternetRadioFullScreen(Screen, InternetRadioVisualization):

	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:

		skin = """
			<screen name="InternetRadioFullScreen" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget name="station" position="50,120" zPosition="1" size="1180,20" font="Regular;18" transparent="1"  halign="center" foregroundColor="#356835" backgroundColor="#00000000"/>
				<widget name="title" position="50,550" zPosition="1" size="1180,80" font="Regular;22" transparent="1"  halign="center" foregroundColor="#4e9a4e" backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="440,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="465,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="490,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="515,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="540,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="565,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="590,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="615,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="640,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="665,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="690,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="715,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="740,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="765,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="790,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="815,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="440,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="465,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="490,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="515,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="540,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="565,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="590,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="615,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="640,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="665,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="690,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="715,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="740,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="765,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="790,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="815,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""

	elif sz_w == 1024:
		skin = """
			<screen name="InternetRadioFullScreen" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget name="station" position="50,120" zPosition="1" size="924,20" font="Regular;18" transparent="1"  halign="center" foregroundColor="#356835" backgroundColor="#00000000"/>
				<widget name="title" position="50,400" zPosition="1" size="924,80" font="Regular;22" transparent="1"  halign="center" foregroundColor="#4e9a4e" backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="312,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="337,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="362,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="387,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="412,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="437,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="462,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="487,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="512,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="537,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="562,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="587,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="612,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="637,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="662,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="687,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="312,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="337,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="362,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="387,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="412,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="437,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="462,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="487,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="512,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="537,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="562,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="587,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="612,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="637,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="662,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="687,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""



			
	else:
		skin = """
			<screen name="InternetRadioFullScreen" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget name="station" position="50,120" zPosition="1" size="620,20" font="Regular;18" transparent="1"  halign="center" foregroundColor="#356835" backgroundColor="#00000000"/>
				<widget name="title" position="50,400" zPosition="1" size="620,80" font="Regular;22" transparent="1"  halign="center" foregroundColor="#4e9a4e" backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="170,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="195,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="220,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="245,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="270,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="295,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="320,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="345,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="370,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="395,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="420,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="445,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="470,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="495,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="520,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="545,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="170,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="195,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="220,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="245,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="270,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="295,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="320,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="345,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="370,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="395,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="420,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="445,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="470,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="495,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="520,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="545,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""


	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		InternetRadioVisualization.__init__(self)
		self["title"] =  Label("")
		self["station"] = Label("")
		self["cover"] = InternetRadioCover(self.coverLoaded)
		self.onLayoutFinish.append(self.startRun)
		self.visible = False

	def startRun(self):
		self.setProperties()
		self.hideControls()

	def setText(self, title):
		self["title"].setText(title)

	def setStation(self, station):
		self["station"].setText(station)


	def setVisibility(self, visible):
		if visible:
			if config.plugins.internetradio.fullscreenlayout.value != "0":
				self.hideControls()
			self.show()
		else:
			self.hide()
		self.visible = visible

	def isVisible(self):
		return self.visible

	def setVisibilityCover(self, visible):
		if visible and config.plugins.internetradio.googlecover.value:
			self["cover"].show()
		else:
			self["cover"].hide()
			
	def updateCover(self):
		self["cover"].updateIcon("/tmp/.cover")
		
	def coverLoaded(self):
		self.setVisibilityCover(True)
