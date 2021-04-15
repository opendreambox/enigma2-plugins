# -*- coding: utf-8 -*-
#
#  AutomaticVolumeAdjustment E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Property GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, eServiceReference
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChannelSelection import SimpleChannelSelection
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config
from ServiceReference import ServiceReference
from AutomaticVolumeAdjustment import AutomaticVolumeAdjustment
from AutomaticVolumeAdjustmentConfig import AutomaticVolumeAdjustmentConfig
from skin import TemplatedListFonts, componentSizes

		
class AutomaticVolumeAdjustmentConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="AutomaticVolumeAdjustmentConfigScreen" position="center,center" size="820,400">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="config" position="10,60" size="800,240" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("Automatic Volume Adjustment - Config")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.blue,
			"cancel": self.keyCancel,
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText()
		self.configVA = AutomaticVolumeAdjustmentConfig()
		self.automaticVolumeAdjustmentInstance = AutomaticVolumeAdjustment.instance
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session)
		self.createSetup("config")
		
	def createSetup(self, widget):
		self.list = []
		self.config_enable = getConfigListEntry(_("Enable"), self.configVA.config.enable)
		self.list.append(self.config_enable)
		if self.configVA.config.enable.value:
			self.config_modus = getConfigListEntry(_("Modus"), self.configVA.config.modus)
			self.list.append(self.config_modus)
			if self.configVA.config.modus.value == "0":
				self.list.append(getConfigListEntry(_("Default volume adjustment value for AC3/DTS"), self.configVA.config.adustvalue))
				self.list.append(getConfigListEntry(_("Max. volume for mpeg audio"), self.configVA.config.mpeg_max_volume))
				self["key_blue"].text = _("Services")
			else:
				self["key_blue"].text = ""
			self.list.append(getConfigListEntry(_("Show volumebar when volume-value was changed"), self.configVA.config.show_volumebar))
		else:
			self.config_modus = None
		self[widget].list = self.list
		self[widget].l.setList(self.list)
	
	def newConfig(self):
		if self["config"].getCurrent() in (self.config_enable, self.config_modus):
			self.createSetup("config")

	def keyLeft(self):
			ConfigListScreen.keyLeft(self)
			self.newConfig()

	def keyRight(self):
			ConfigListScreen.keyRight(self)
			self.newConfig()
		
	def blue(self):
		if self.configVA.config.modus.value == "0":
			self.session.open(AutomaticVolumeAdjustmentEntriesListConfigScreen, self.configVA)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		self.configVA.save()
		if self.automaticVolumeAdjustmentInstance is not None:
			self.automaticVolumeAdjustmentInstance.initializeConfigValues(self.configVA, True) # submit config values
		self.close()

	def keyCancel(self):
		ConfigListScreen.cancelConfirm(self, True)
		

class AutomaticVolumeAdjustmentEntriesListConfigScreen(Screen):
	skin = """
		<screen position="center,120" size="820,520">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget source="name" render="Label" position="10,60" size="520,25" font="Regular;21" halign="left"/>
			<widget source="adjustvalue" render="Label" position="570,60" size="240,25" font="Regular;21" halign="right"/>
			<eLabel position="10,90" size="800,1" backgroundColor="grey" />
			<widget name="entrylist" position="10,100" size="800,390" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, configVA):
		Screen.__init__(self, session)
		self.title = _("Automatic Volume Adjustment - Service Config")
		self["name"] = StaticText(_("Servicename"))
		self["adjustvalue"] = StaticText(_("Adjustment value"))
		self["key_red"] = StaticText(_("Add"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Delete"))
		self["entrylist"] = AutomaticVolumeAdjustmentEntryList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyRed,
			 "green":	self.keyClose,
			 "yellow":	self.keyYellow,
			 "blue": 	self.keyDelete,
			 }, -1)
		self.automaticVolumeAdjustmentInstance = AutomaticVolumeAdjustment.instance
		self["entrylist"].setConfig(configVA)
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(-1, None)

	def keyRed(self):
		self.session.openWithCallback(self.updateList,AutomaticVolumeAdjustmentEntryConfigScreen,None, self["entrylist"].configVA)

	def keyOK(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		self.close(self["entrylist"].getCurrentIndex(), sel)

	def keyYellow(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList,AutomaticVolumeAdjustmentEntryConfigScreen,sel, self["entrylist"].configVA)

	def keyDelete(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Do you really want to delete this entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		self["entrylist"].configVA.remove(sel)
		if self.automaticVolumeAdjustmentInstance is not None:
			self.automaticVolumeAdjustmentInstance.initializeConfigValues(self["entrylist"].configVA, True) # submit config values
		self.updateList()

class AutomaticVolumeAdjustmentEntryList(MenuList):
	SKIN_COMPONENT_KEY = "AutomaticVolumeAdjustmentList"
	SKIN_COMPONENT_TEXT_WIDTH = "textWidth"
	SKIN_COMPONENT_TEXT_HEIGHT = "textHeight"
	
	def __init__(self, list, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.configVA = None

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(componentSizes.itemHeight(self.SKIN_COMPONENT_KEY, 30))

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()
		
	def setConfig(self, configVA):
		self.configVA = configVA
		
	def buildList(self):
		list = []
		
		sizes = componentSizes[AutomaticVolumeAdjustmentEntryList.SKIN_COMPONENT_KEY]
		textWidth = sizes.get(AutomaticVolumeAdjustmentEntryList.SKIN_COMPONENT_TEXT_WIDTH, 570)
		textHeight = sizes.get(AutomaticVolumeAdjustmentEntryList.SKIN_COMPONENT_TEXT_HEIGHT, 30)
				
		for c in self.configVA.config.Entries:
			c.name.value = ServiceReference(eServiceReference(c.servicereference.value)).getServiceName()
			res = [
				c,
				(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, textWidth-10, textHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, c.name.value),
				(eListboxPythonMultiContent.TYPE_TEXT, textWidth, 0,220, textHeight, 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, str(c.adjustvalue.value)),
			]
			list.append(res)
		self.list = list
		self.l.setList(list)
		self.moveToIndex(0)

class AutomaticVolumeAdjustmentEntryConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="AutomaticVolumeAdjustmentEntryConfigScreen" position="center,center" size="820,400">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="config" position="10,60" size="800,240" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, entry, configVA):	
		self.session = session
		Screen.__init__(self, session)
		self.title = _("Automatic Volume Adjustment - Entry Config")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"ok": self.keySelect,
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.configVA = configVA
		if entry is None:
			self.newmode = 1
			self.current = self.configVA.initEntryConfig()
			self.currentvalue = self.current.adjustvalue.value
		else:
			self.newmode = 0
			self.current = entry
			self.currentref = entry.servicereference.value
			self.currentvalue = entry.adjustvalue.value
		self.list = [ ]
		self.service = getConfigListEntry(_("Servicename"), self.current.name)
		self.list.append(self.service)
		self.adjustValue = getConfigListEntry(_("Adjustment value"), self.current.adjustvalue)
		self.list.append(self.adjustValue)
		ConfigListScreen.__init__(self, self.list, session)
		self.automaticVolumeAdjustmentInstance = AutomaticVolumeAdjustment.instance
		
	def keySelect(self):
		cur = self["config"].getCurrent()
		if cur == self.service:
			self.session.openWithCallback(self.channelSelected, SimpleChannelSelection, _("Channel Selection"))
			
	def channelSelected(self, ref = None):
		if ref:
			self.current.name.value = ServiceReference(ref).getServiceName()
			self.current.servicereference.value = ref.toString()
			self.current.save()

	def keySave(self):
		if self.current.servicereference.value:
			if self.newmode == 1:
				self.configVA.config.entriescount.value = self.configVA.config.entriescount.value + 1
				self.configVA.config.entriescount.save()
			for x in self["config"].list:
				x[1].save()
			self.configVA.save()
			if self.automaticVolumeAdjustmentInstance is not None:
				self.automaticVolumeAdjustmentInstance.initializeConfigValues(self.configVA, True) # submit config values
			self.close()
		else:
			self.session.open(MessageBox, _("You must select a valid service!"), type = MessageBox.TYPE_INFO)

	def keyCancel(self):
		if self.newmode == 1:
			self.configVA.config.Entries.remove(self.current)
			self.configVA.config.Entries.save()
		else:
			self.current.servicereference.value = self.currentref
			self.current.adjustvalue.value = self.currentvalue
			self.current.save()
		ConfigListScreen.cancelConfirm(self, True)
