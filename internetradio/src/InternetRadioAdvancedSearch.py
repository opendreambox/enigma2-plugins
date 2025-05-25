from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigListScreen
from Components.MultiContent import MultiContentEntryText
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry, configfile, NoSave, ConfigText, ConfigSelection
from Tools.BoundFunction import boundFunction
from Tools.NumericalTextInput import NumericalTextInput
from InternetRadioWebFunctions import sendUrlCommand
from enigma import gFont
from json import loads as json_loads

class InternetRadioAdvancedSearch(Screen, ConfigListScreen):
	skin = """
		<screen name="InternetRadioAdvancedSearch" position="center,center" size="600,400" title="InternetRadio Advanced Search" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="300,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="445,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="10,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="150,0" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="10,50" size="580,400" scrollbarMode="showOnDemand" />
		</screen>""" 

	def __init__(self, session):
		Screen.__init__(self, session)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		
		self.stationname = NoSave(ConfigText(default="", fixed_size=False))
		if config.plugins.internetradio.savelastsearch.value:
			self.country = NoSave(ConfigSelection([_("None") if config.plugins.internetradio.lastcountry.value == "" else config.plugins.internetradio.lastcountry.value]))
			self.genre = NoSave(ConfigSelection([_("None") if config.plugins.internetradio.lastgenre.value == "" else config.plugins.internetradio.lastgenre.value]))
			self.language = NoSave(ConfigSelection([_("None") if config.plugins.internetradio.lastlanguage.value == "" else config.plugins.internetradio.lastlanguage.value]))
			self.codec = NoSave(ConfigSelection([_("None") if config.plugins.internetradio.lastcodec.value == "" else config.plugins.internetradio.lastcodec.value]))	
		else:
			self.country = NoSave(ConfigSelection([_("None")]))
			self.genre = NoSave(ConfigSelection([_("None")]))
			self.language = NoSave(ConfigSelection([_("None")]))
			self.codec = NoSave(ConfigSelection([_("None")]))
		
		self.list = [
			getConfigListEntry(_("Station name:"), self.stationname),
			getConfigListEntry(_("Country:"), self.country),
			getConfigListEntry(_("Genre:"), self.genre),
			getConfigListEntry(_("Language:"), self.language),
			getConfigListEntry(_("Codec:"), self.codec),
		]
		
		ConfigListScreen.__init__(self, self.list, session)
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green":	self.keyGo,
			"red":		self.cancel,
			"cancel":	self.cancel,
			"ok":		self.keySelect,
		}, -2)
		
	def keySelect(self):
		cur = self["config"].getCurrent()
		if cur and cur[0] != _("Station name:"):
			self.filterValue = ""
			if cur[0] == _("Country:"):
				self.filterValue = "countries"
			elif cur[0] == _("Genre:"):
				self.filterValue = "tags"
			elif cur[0] == _("Codec:"):
				self.filterValue = "codecs"
			elif cur[0] == _("Language:"):
				self.filterValue = "languages"
				
			sendUrlCommand("https://de1.api.radio-browser.info/json/%s?hidebroken=true" %(self.filterValue), None, 10).addCallback(self.callbackFilterList).addErrback(self.callbackFilterListError)
			
	def callbackFilterList(self, jsonstring):
		filters = json_loads(jsonstring)
		filterList = []
		for filter in filters:
			filterList.append((filter.get('name', '').encode('utf-8','ignore'),))
			
		self.session.openWithCallback(self.setSelection, InternetRadioSelection, filterList)
		
	def setSelection(self, selection):
		if selection:
			if self.filterValue == "countries":
				self.country.setCurrentText(selection)
				self["config"].invalidate(self.country)
			elif self.filterValue == "tags":
				self.genre.setCurrentText(selection)
				self["config"].invalidate(self.genre)
			elif self.filterValue == "codecs":
				self.codec.setCurrentText(selection)
				self["config"].invalidate(self.codec)
			elif self.filterValue == "languages": 
				self.language.setCurrentText(selection)
				self["config"].invalidate(self.language)
		else:
			if self.filterValue == "countries":
				self.country.setCurrentText(_("None"))
				self["config"].invalidate(self.country)
			elif self.filterValue == "tags":
				self.genre.setCurrentText(_("None"))
				self["config"].invalidate(self.genre)
			elif self.filterValue == "codecs":
				self.codec.setCurrentText(_("None"))
				self["config"].invalidate(self.codec)
			elif self.filterValue == "languages": 
				self.language.setCurrentText(_("None"))
				self["config"].invalidate(self.language)		
				
	def callbackFilterListError(self, error = None):
		if error is not None:
			try:
				self.session.open(MessageBox, text=error.getErrorMessage(), type=MessageBox.TYPE_ERROR, timeout=5)
			except: pass
			
	def cancel(self):
		self.close(None, [])
		
	def keyGo(self):
		if config.plugins.internetradio.savelastsearch.value:
			config.plugins.internetradio.lastcountry.value = self.country.value
			config.plugins.internetradio.lastlanguage.value = self.language.value
			config.plugins.internetradio.lastgenre.value = self.genre.value
			config.plugins.internetradio.lastcodec.value = self.codec.value
		self.close(None, [self.stationname.value, self.country.value, self.genre.value, self.codec.value, self.language.value])
		
class InternetRadioSelection(Screen):
	skin = """
		<screen name="InternetRadioSelection" position="center,center" size="800,700" title="InternetRadio Selection" >
			<widget source="list" render="Listbox" position="0,0" size="800,680" scrollbarMode="showOnDemand" zPosition="1">
				<convert type="TemplatedMultiContent">
					{"templates": {
						"default":(40, [
							MultiContentEntryText(pos=(5,5), size=(790,40), font=0, text=0),
						]),
					},
						"fonts": [gFont("Regular",27)],
					}
				</convert>
			</widget>
		</screen>"""
	
	def __init__(self, session, filterList):
		self.filterList = filterList
		Screen.__init__(self, session)
		
		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
		{
			"ok":		self.keyOk,
			"cancel":	self.keyExit,
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

		self["list"] = List(self.filterList)
		self.onShown.append(self.buildScreen)

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
		for i in range(len(self.filterList)):
			if self.filterList[i][0].upper().startswith(char):
				return i
		
	def buildScreen(self):
		self["list"].setList(self.filterList)
		self["list"].setBuildFunc(self.buildEntry)
		
	def buildEntry(self, name):
		return [name]
		
	def keyOk(self):
		cur = self["list"].getCurrent()
		self.close(cur[0])
		
	def keyExit(self):
		self.close(None)