#######################################################################
#
#    EasyMedia for Dreambox-Enigma2
#    Coded by Vali (c)2010-2011
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Property GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#######################################################################

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBarGenerics import InfoBarPlugins
from Screens.InfoBar import InfoBar
from Screens.ChoiceBox import ChoiceBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.PluginComponent import plugins
from Components.PluginList import *
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection
from Tools.Directories import fileExists, pathExists, resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from Tools.HardwareInfo import HardwareInfo
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont, getDesktop
import pickle
from os import system as os_system
from os import listdir as os_listdir



EMbaseInfoBarPlugins__init__ = None
EMStartOnlyOneTime = False
EMsession = None
InfoBar_instance = None



config.plugins.easyMedia  = ConfigSubsection()
config.plugins.easyMedia.music = ConfigSelection(default="mediaplayer", choices = [("no", _("Disabled")), ("mediaplayer", _("MediaPlayer")), ("merlinmp", _("MerlinMusicPlayer"))])
config.plugins.easyMedia.files = ConfigSelection(default="dreamexplorer", choices = [("no", _("Disabled")), ("filebrowser", _("Filebrowser")), ("dreamexplorer", _("DreamExplorer")), ("tuxcom", _("TuxCom"))])
config.plugins.easyMedia.videodb = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.bookmarks = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.pictures = ConfigSelection(default="yes", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.mytube = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.vlc = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.dvd = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.weather = ConfigSelection(default="yes", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.iradio = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.idream = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.zdfmedia = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.radio = ConfigSelection(default="yes", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.myvideo = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])
config.plugins.easyMedia.timers = ConfigSelection(default="no", choices = [("no", _("Disabled")), ("yes", _("Enabled"))])



def Plugins(**kwargs):
	return [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = EasyMediaAutostart),
			PluginDescriptor(name="EasyMedia", description=_("Not easy way to start EasyMedia"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=notEasy),]



def EasyMediaAutostart(reason, **kwargs):
	global EMbaseInfoBarPlugins__init__
	if "session" in kwargs:
		global EMsession
		EMsession = kwargs["session"]
		if EMbaseInfoBarPlugins__init__ is None:
			EMbaseInfoBarPlugins__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.__init__ = InfoBarPlugins__init__
		InfoBarPlugins.pvr = pvr



def InfoBarPlugins__init__(self):
	global EMStartOnlyOneTime
	if not EMStartOnlyOneTime: 
		EMStartOnlyOneTime = True
		global InfoBar_instance
		InfoBar_instance = self
		self["EasyMediaActions"] = ActionMap(["EasyMediaActions"],
			{"video_but": self.pvr}, -1)
	else:
		InfoBarPlugins.__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.pvr = None
	EMbaseInfoBarPlugins__init__(self)



def pvr(self):
	self.session.openWithCallback(MPcallbackFunc, EasyMedia)



def notEasy(session, **kwargs):
	session.openWithCallback(MPcallbackFunc, EasyMedia)



def MPanelEntryComponent(key, text, cell):
	sz_w = getDesktop(0).size().width()
	if sz_w > 1400:
		ih=90
		wx=200
		wy=20
		psx=135
		psy=85
	else:
		ih=60
		wx=150
		wy=17
		psx=100
		psy=50

	res = [ text ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, wx, wy, 300, ih, 0, RT_HALIGN_LEFT, text[0]))
	if cell<5:
		bpng = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/key-' + str(cell) + ".png")
		if bpng is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 5, 5, psy, bpng))
	png = LoadPixmap(EasyMedia.EMiconspath + key + '.png')
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, 5, psx, psy, png))
	else:
		png = LoadPixmap(EasyMedia.EMiconspath + 'default.png')
		if png is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, 5, psx, psy, png))
	return res



class MPanelList(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=True):
		sz_w = getDesktop(0).size().width()
		if sz_w > 1400:
			fs=32
			ih=90
		else:
			fs=20
			ih=60 

		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", fs))
		self.l.setItemHeight(ih)
		self.selection = selection
	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)



def BookmarksCallback(choice):
	choice = choice and choice[1]
	if choice:
		config.movielist.last_videodir.value = choice
		config.movielist.last_videodir.save()
		if InfoBar_instance:
			InfoBar_instance.showMovies()



def TvRadioCallback(choice):
	choice = choice and choice[1]
	if choice == "TM":
		if InfoBar_instance:
			InfoBar_instance.showTv()
	elif choice == "RM":
		if InfoBar_instance:
			InfoBar_instance.showRadio()



class ConfigEasyMedia(ConfigListScreen, Screen):
	skin = """
		<screen name="ConfigEasyMedia" position="center,center" size="600,410" title="EasyMedia settings...">
			<widget name="config" position="5,5" scrollbarMode="showOnDemand" size="590,380"/>
			<eLabel font="Regular;20" foregroundColor="#00ff4A3C" halign="center" position="20,388" size="140,26" text="Cancel"/>
			<eLabel font="Regular;20" foregroundColor="#0056C856" halign="center" position="165,388" size="140,26" text="Save"/>
			<eLabel font="Regular;20" foregroundColor="#00f3ca09" halign="center" position="310,388" size="140,26" text="Plugins"/>
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("EasyMedia settings..."))
		self.session = session
		list = []
		list.append(getConfigListEntry(_("Video database:"), config.plugins.easyMedia.videodb))
		list.append(getConfigListEntry(_("Music player:"), config.plugins.easyMedia.music))
		list.append(getConfigListEntry(_("Files browser:"), config.plugins.easyMedia.files))
		list.append(getConfigListEntry(_("Show bookmarks:"), config.plugins.easyMedia.bookmarks))
		list.append(getConfigListEntry(_("Timer:"), config.plugins.easyMedia.timers))
		list.append(getConfigListEntry(_("PicturePlayer:"), config.plugins.easyMedia.pictures))
		list.append(getConfigListEntry(_("Show tv/radio switch:"), config.plugins.easyMedia.radio))
		list.append(getConfigListEntry(_("YouTube player:"), config.plugins.easyMedia.mytube))
		list.append(getConfigListEntry(_("VLC player:"), config.plugins.easyMedia.vlc))
		list.append(getConfigListEntry(_("DVD player:"), config.plugins.easyMedia.dvd))
		list.append(getConfigListEntry(_("Weather plugin:"), config.plugins.easyMedia.weather))
		list.append(getConfigListEntry(_("InternetRadio player:"), config.plugins.easyMedia.iradio))
		list.append(getConfigListEntry(_("Show Merlin-iDream:"), config.plugins.easyMedia.idream))
		list.append(getConfigListEntry(_("ZDFmediathek player:"), config.plugins.easyMedia.zdfmedia))
		list.append(getConfigListEntry(_("MyVideo player:"), config.plugins.easyMedia.myvideo))
		ConfigListScreen.__init__(self, list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {"green": self.save, "red": self.exit, "cancel": self.exit, "yellow": self.plug}, -1)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def plug(self):
		self.session.open(AddPlug)



class AddPlug(Screen):
	skin = """
		<screen name="AddPlug" position="center,center" size="440,420" title="EasyMedia...">
		<widget source="pluginlist" render="Listbox" position="10,10" size="420,400" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
			{"templates":
				{"default": (50,[
						MultiContentEntryText(pos = (120, 5), size = (320, 25), font = 0, text = 1), # index 1 is the plugin.name
						MultiContentEntryText(pos = (120, 26), size = (320, 17), font = 1, text = 2), # index 2 is the plugin.description
						MultiContentEntryPixmapAlphaTest(pos = (10, 5), size = (100, 40), png = 3), # index 3 is the icon
						
					]),
				},
				"fonts": [gFont("Regular", 20), gFont("Regular", 14)],
				"itemHeight": 50
			}
			</convert>
		</widget>
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Add/remove plugin"))
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.session = session
		self.list = []
		self["pluginlist"] = PluginList(self.list)
		#self.updateList()
		self.pluginlist = []
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.save,
			"back": self.close
		}, -1)
		self.onExecBegin.append(self.checkWarnings)
		self.onShown.append(self.updateList)

	def checkWarnings(self):
		if len(plugins.warnings):
			text = _("Some plugins are not available:\n")
			for (pluginname, error) in plugins.warnings:
				text += _("%s (%s)\n") % (pluginname, error)
			plugins.resetWarnings()
			self.session.open(MessageBox, text = text, type = MessageBox.TYPE_WARNING)

	def updateList(self):
		self.pluginlist = plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU)
		self.list = [PluginEntryComponent(plugin) for plugin in self.pluginlist]
		self["pluginlist"].setList(self.list)

	def save(self):
		plugin = self["pluginlist"].getCurrent()[0]
		print plugin
		plugin.icon = None
		if not fileExists("/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/" + plugin.name + ".plug"):
			try:
				outf = open(("/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/" + plugin.name + ".plug"), 'wb')
				pickle.dump(plugin, outf)
				outf.close()
				self.session.open(MessageBox, text = (plugin.name + _(" added to EasyMedia")), type = MessageBox.TYPE_INFO)
			except: self.session.open(MessageBox, text = "Write Error!", type = MessageBox.TYPE_WARNING)
		else:
			order = 'rm -f \"' + '/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/' + plugin.name + '.plug' + '\"'
			try:
				os_system(order)
				self.session.open(MessageBox, text = (plugin.name + _(" removed from EasyMedia")), type = MessageBox.TYPE_INFO)
			except: self.session.open(MessageBox, text = "Write Error!", type = MessageBox.TYPE_WARNING)



class EasyMediaSummary(Screen):
	if "800se" in HardwareInfo().get_device_name():
		skin = """
			<screen position="0,0" size="96,64" id="2">
				<eLabel text="EasyMedia:" foregroundColor="#fcc000" position="0,0" size="96,24" font="Regular;16"/>
				<widget name="text1" position="0,24" size="96,40" font="Regular;18"/>
			</screen>"""
	else:
		skin = """
			<screen position="0,0" size="132,64">
				<eLabel text="EasyMedia:" position="0,0" size="132,24" font="Regular;14"/>
				<widget name="text1" position="0,24" size="132,40" font="Regular;16"/>
			</screen>"""
	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["text1"] = Label()
		self.onLayoutFinish.append(self.layoutEnd)

	def layoutEnd(self):
		self["text1"].setText(_("Movies"))

	def setText(self, text, line):
		self["text1"].setText(text)



class EasyMedia(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w > 1800:
		skin = """
		<screen flags="wfNoBorder" position="0,0" size="550,1080" title="Easy Media">
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg2.png" position="0,0" size="750,576"/>
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg2.png" position="0,576" size="750,503"/>
			<widget name="list" position="60,30" size="450,1080" scrollbarMode="showNever" transparent="1" zPosition="2"/>
		</screen>"""
	elif sz_w > 1100:
		skin = """
		<screen flags="wfNoBorder" position="0,0" size="450,720" title="Easy Media">
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg.png" position="0,0" size="450,576"/>
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg.png" position="0,576" size="450,145"/>
			<widget name="list" position="60,30" size="350,660" scrollbarMode="showNever" transparent="1" zPosition="2"/>
		</screen>"""
	elif sz_w > 1000:
		skin = """
		<screen flags="wfNoBorder" position="-20,0" size="450,576" title="Easy Media">
			#<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg.png" position="0,0" size="450,576"/>
			<widget name="list" position="70,48" size="320,480" scrollbarMode="showNever" transparent="1" zPosition="2"/>
		</screen>"""
	else:
		skin = """
		<screen position="center,center" size="320,440" title="Easy Media">
			<widget name="list" position="10,10" size="300,420" scrollbarMode="showOnDemand" />
		</screen>"""
	if pathExists('/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/icons/'):
		EMiconspath = '/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/icons/'
	else:
		EMiconspath = '/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/'
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.list = []
		self.__keys = []
		MPaskList = []
		self["key_pvr"] = StaticText(" ")
		self["key_yellow"] = StaticText(" ")
		self["key_green"] = StaticText(" ")
		self["key_red"] = StaticText(" ")
		self["key_blue"] = StaticText(" ")
		if True:
			self.__keys.append("movies")
			MPaskList.append((_("Movies"), "PLAYMOVIES"))
		if config.plugins.easyMedia.bookmarks.value != "no":
			self.__keys.append("bookmarks")
			MPaskList.append((_("Bookmarks"), "BOOKMARKS"))
		if config.plugins.easyMedia.timers.value != "no":
			self.__keys.append("timers")
			MPaskList.append((_("Timer"), "TIMERS"))
		if config.plugins.easyMedia.videodb.value != "no":
			self.__keys.append("videodb")
			MPaskList.append((_("VideoDB"), "VIDEODB"))
		if config.plugins.easyMedia.pictures.value != "no":
			self.__keys.append("pictures")
			MPaskList.append((_("Pictures"), "PICTURES"))
		if config.plugins.easyMedia.music.value != "no":
			self.__keys.append("music")
			MPaskList.append((_("Music"), "MUSIC"))
		if config.plugins.easyMedia.radio.value != "no":
			self.__keys.append("radio")
			if config.usage.e1like_radio_mode.value:
				MPaskList.append((_("Tv/Radio"), "RADIO"))
			else:
				MPaskList.append((_("Radio"), "RADIO"))
		if config.plugins.easyMedia.dvd.value != "no":
			self.__keys.append("dvd")
			MPaskList.append((_("DVD Player"), "DVD"))
		if config.plugins.easyMedia.weather.value != "no":
			self.__keys.append("weather")
			MPaskList.append((_("Weather"), "WEATHER"))
		if config.plugins.easyMedia.files.value != "no":
			self.__keys.append("files")
			MPaskList.append((_("Files"), "FILES"))
		if config.plugins.easyMedia.iradio.value != "no":
			self.__keys.append("internetradio")
			MPaskList.append((_("InternetRadio"), "INTERNETRADIO"))
		if config.plugins.easyMedia.idream.value != "no":
			self.__keys.append("idream")
			MPaskList.append((_("iDream"), "IDREAM"))
		if config.plugins.easyMedia.mytube.value != "no":
			self.__keys.append("mytube")
			MPaskList.append((_("MyTube Player"), "MYTUBE"))
		if config.plugins.easyMedia.vlc.value != "no":
			self.__keys.append("vlc")
			MPaskList.append((_("VLC Player"), "VLC"))
		if config.plugins.easyMedia.zdfmedia.value != "no":
			self.__keys.append("zdf")
			MPaskList.append((_("ZDFmediathek"), "ZDF"))
		if config.plugins.easyMedia.myvideo.value != "no":
			self.__keys.append("myvideo")
			MPaskList.append((_("MyVideo"), "MYVIDEO"))
		plist = os_listdir("/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia")
		plist = [x[:-5] for x in plist if x.endswith('.plug')]
		plist.sort()
		for onePlug in plist:
			try:
				inpf = open(("/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/" + onePlug + ".plug"), 'rb')
				binPlug = pickle.load(inpf)
				inpf.close()	
				self.__keys.append(binPlug.name)
				MPaskList.append((binPlug.name, ("++++" + binPlug.name)))
			except: pass
		pos = 0
		for x in MPaskList:
			strpos = str(self.__keys[pos])
			self.list.append(MPanelEntryComponent(key = strpos, text = x, cell = pos))
			if pos==0: self["key_pvr"].setText(MPaskList[0][0])
			elif pos==1: self["key_red"].setText(MPaskList[1][0])
			elif pos==2: self["key_green"].setText(MPaskList[2][0])
			elif pos==3: self["key_yellow"].setText(MPaskList[3][0])
			elif pos==4: self["key_blue"].setText(MPaskList[4][0])
			pos += 1
		self["list"] = MPanelList(list = self.list, selection = 0)
		self["list"].onSelectionChanged.append(self.updateOLED)
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "InfobarActions", "ColorActions"],
		{
			"ok": self.go,
			"back": self.cancel,
			"menu": self.emContextMenu,
			"showMovies": lambda: self.go2(MPaskList,0),
			"green": lambda: self.go2(MPaskList,2),
			"red": lambda: self.go2(MPaskList,1),
			"blue": lambda: self.go2(MPaskList,4),
			"yellow": lambda: self.go2(MPaskList,3)
		}, -1)

	def cancel(self):
		self.close(None)

	def go(self):
		cursel = self["list"].l.getCurrentSelection()
		if cursel:
			self.goEntry(cursel[0])
		else:
			self.cancel()

	def go2(self, was, wohin):
		if wohin == 0:
			self.close(was[wohin])
		elif wohin == 1:
			if len(was)>1: 
				self.close(was[wohin])
		elif wohin == 2:
			if len(was)>2: 
				self.close(was[wohin])
		elif wohin == 3:
			if len(was)>3: 
				self.close(was[wohin])
		elif wohin == 4:
			if len(was)>4: 
				self.close(was[wohin])

	def goEntry(self, entry):
		if len(entry) > 2 and isinstance(entry[1], str) and entry[1] == "CALLFUNC":
			arg = self["list"].l.getCurrentSelection()[0]
			entry[2](arg)
		else:
			self.close(entry)

	def emContextMenu(self):
		self.session.open(ConfigEasyMedia)

	def createSummary(self):
		return EasyMediaSummary

	def updateOLED(self):
		text = str(self["list"].l.getCurrentSelection()[0][0])
		self.summaries.setText(text, 1)



def MPcallbackFunc(answer):
	if EMsession is None:
		return
	answer = answer and answer[1]
	if answer == "PLAYMOVIES":
		if InfoBar_instance:
			InfoBar_instance.showMovies()
	elif answer == "RADIO":
		if config.usage.e1like_radio_mode.value:
			askBM = []
			askBM.append((_("TV-mode"), "TM"))
			askBM.append((_("Radio-mode"), "RM"))
			askBM.append((_("Nothing"), "NO"))
			EMsession.openWithCallback(TvRadioCallback, ChoiceBox, title="EasyMedia...", list = askBM)
		else:
			if InfoBar_instance:
				InfoBar_instance.showRadio()
	elif answer == "BOOKMARKS":
		tmpBookmarks = config.movielist.videodirs
		myBookmarks = tmpBookmarks and tmpBookmarks.value[:] or []
		if len(myBookmarks)>0:
			askBM = []
			for s in myBookmarks:
				askBM.append((s, s))
			EMsession.openWithCallback(BookmarksCallback, ChoiceBox, title=_("Select bookmark..."), list = askBM)
	elif answer == "PICTURES":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/PicturePlayer/plugin.pyo"):
			from Plugins.Extensions.PicturePlayer.plugin import picshow
			EMsession.open(picshow)
		else:
			EMsession.open(MessageBox, text = _('Picture-player is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "MUSIC":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyo") and (config.plugins.easyMedia.music.value == "merlinmp"):
			from Plugins.Extensions.MerlinMusicPlayer.plugin import MerlinMusicPlayerFileList
			servicelist = None
			EMsession.open(MerlinMusicPlayerFileList, servicelist)
		elif fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer/plugin.pyo") and (config.plugins.easyMedia.music.value == "mediaplayer"):
			from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer
			EMsession.open(MediaPlayer)
		else:
			EMsession.open(MessageBox, text = _('No Music-Player installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "FILES":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Tuxcom/plugin.pyo") and (config.plugins.easyMedia.files.value == "tuxcom"):
			from Plugins.Extensions.Tuxcom.plugin import TuxComStarter
			EMsession.open(TuxComStarter)
		elif fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/plugin.pyo") and (config.plugins.easyMedia.files.value == "dreamexplorer"):
			from Plugins.Extensions.DreamExplorer.plugin import DreamExplorerII
			EMsession.open(DreamExplorerII)
		elif fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Filebrowser/plugin.pyo") and (config.plugins.easyMedia.files.value == "filebrowser"):
			from Plugins.Extensions.Filebrowser.plugin import FilebrowserScreen
			EMsession.open(FilebrowserScreen)
		else:
			EMsession.open(MessageBox, text = _('No File-Manager installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "WEATHER":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/WeatherPlugin/plugin.pyo"):
			from Plugins.Extensions.WeatherPlugin.plugin import MSNWeatherPlugin
			EMsession.open(MSNWeatherPlugin)
		else:
			EMsession.open(MessageBox, text = _('Weather Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "DVD":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyo"):
			from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
			EMsession.open(DVDPlayer)
		else:
			EMsession.open(MessageBox, text = _('DVDPlayer Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "MYTUBE":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MyTube/plugin.pyo"):
			from Plugins.Extensions.MyTube.plugin import *
			MyTubeMain(EMsession)
		else:
			EMsession.open(MessageBox, text = _('MyTube Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "INTERNETRADIO":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/plugin.pyo"):
			from Plugins.Extensions.InternetRadio.InternetRadioScreen import InternetRadioScreen
			EMsession.open(InternetRadioScreen)
		else:
			EMsession.open(MessageBox, text = _('SHOUTcast Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "ZDF":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/ZDFMediathek/plugin.pyo"):
			from Plugins.Extensions.ZDFMediathek.plugin import ZDFMediathek
			EMsession.open(ZDFMediathek)
		else:
			EMsession.open(MessageBox, text = _('ZDFmediathek Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "VLC":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/VlcPlayer/plugin.pyo"):
			from Plugins.Extensions.VlcPlayer.plugin import *
			main(EMsession)
		else:
			EMsession.open(MessageBox, text = _('VLC Player is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "IDREAM":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyo"):
			from Plugins.Extensions.MerlinMusicPlayer.plugin import iDreamMerlin
			servicelist = None
			EMsession.open(iDreamMerlin, servicelist)
		else:
			EMsession.open(MessageBox, text = _('Merlin iDream is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "MYVIDEO":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MyVideoPlayer/plugin.pyo"):
			from Plugins.Extensions.MyVideoPlayer.plugin import Vidtype
			EMsession.open(Vidtype)
		else:
			EMsession.open(MessageBox, text = _('MyVideo Player is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "VIDEODB":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/VideoDB/plugin.pyo"):
			from Plugins.Extensions.VideoDB.plugin import main as vdbmain
			vdbmain(EMsession)
		else:
			EMsession.open(MessageBox, text = _('VideoDB is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "TIMERS":
		from Screens.TimerEdit import TimerEditList
		EMsession.open(TimerEditList)
	elif answer is not None and "++++" in answer:
		plugToRun = answer[4:]
		try:
			inpf = open(("/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/" + plugToRun + ".plug"), 'rb')
			runPlug = pickle.load(inpf)
			inpf.close()	
			runPlug(session = EMsession)
		except: EMsession.open(MessageBox, text = (plugToRun + " not found!"), type = MessageBox.TYPE_WARNING)



