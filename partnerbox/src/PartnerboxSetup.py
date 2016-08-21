#
#  Partnerbox E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from enigma import eListboxPythonMultiContent, eListbox, gFont, \
	RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.Button import Button
from Components.config import config
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigSubList, ConfigIP, ConfigInteger, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry, configfile
from skin import TemplatedListFonts, componentSizes

# for localized messages
from . import _

def initPartnerboxEntryConfig():
	config.plugins.Partnerbox.Entries.append(ConfigSubsection())
	i = len(config.plugins.Partnerbox.Entries) -1
	config.plugins.Partnerbox.Entries[i].name = ConfigText(default = "dreambox", visible_width = 50, fixed_size = False)
	config.plugins.Partnerbox.Entries[i].ip = ConfigIP(default = [192,168,0,98])
	config.plugins.Partnerbox.Entries[i].port = ConfigInteger(default=80, limits=(1, 65555))
	config.plugins.Partnerbox.Entries[i].enigma = ConfigSelection(default="0", choices = [("0", _("Enigma 2")),("1", _("Enigma 1"))])
	config.plugins.Partnerbox.Entries[i].password = ConfigText(default = "dreambox", visible_width = 50, fixed_size = False)
	config.plugins.Partnerbox.Entries[i].useinternal = ConfigSelection(default="1", choices = [("0", _("use external")),("1", _("use internal"))])
	config.plugins.Partnerbox.Entries[i].zaptoservicewhenstreaming = ConfigYesNo(default = True)
	return config.plugins.Partnerbox.Entries[i]

def initConfig():
	count = config.plugins.Partnerbox.entriescount.value
	if count != 0:
		i = 0
		while i < count:
			initPartnerboxEntryConfig()
			i += 1

class PartnerboxSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="720,420" title="Partnerbox Setup" >
			<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
			<ePixmap name="green" pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
			<ePixmap name="yellow" pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on"/>
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel	position="10,50" size="700,1" backgroundColor="grey"/>
			<widget name="config" position="10,60" size="700,330" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("Partnerbox Entries"))


		self.list = [ ]
		self.list.append(getConfigListEntry(_("Show 'RemoteTimer' in E-Menu"), config.plugins.Partnerbox.showremotetimerinextensionsmenu))
		self.list.append(getConfigListEntry(_("Show 'RemoteTV Player' in E-Menu"), config.plugins.Partnerbox.showremotetvinextensionsmenu))
		self.list.append(getConfigListEntry(_("Show 'Stream current Service' in E-Menu"), config.plugins.Partnerbox.showcurrentstreaminextensionsmenu))
		self.list.append(getConfigListEntry(_("Enable Partnerbox-Function in TimerEvent"), config.plugins.Partnerbox.enablepartnerboxintimerevent))
		self.list.append(getConfigListEntry(_("Enable Partnerbox-Function in EPGList"), config.plugins.Partnerbox.enablepartnerboxepglist))
		self.list.append(getConfigListEntry(_("Enable first Partnerbox-entry in Timeredit as default"), config.plugins.Partnerbox.enabledefaultpartnerboxintimeredit))
		ConfigListScreen.__init__(self, self.list, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"ok": self.keySave,
			"yellow": self.PartnerboxEntries,
		}, -2)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		configfile.save()
		self.close(self.session, True)

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(self.session, False)

	def PartnerboxEntries(self):
		self.session.open(PartnerboxEntriesListConfigScreen)


class PartnerboxEntriesListConfigScreen(Screen):
	skin = """
		<screen position="center,center" size="820,420" title="%s" >
			<widget name="name" position="10,60" size="250,25" font="Regular;20" halign="left"/>
			<widget name="ip" position="275,60" size="190,25" font="Regular;20" halign="left"/>
			<widget name="port" position="460,60" size="120,25" font="Regular;20" halign="left"/>
			<widget name="type" position="580,60" size="160,25" font="Regular;20" halign="left"/>

			<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
			<ePixmap name="yellow" pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on"/>
			<ePixmap name="blue" pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on"/>
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
			<widget name="entrylist" position="10,90" size="800,300" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		</screen>""" % _("Partnerbox: List of Entries")

	def __init__(self, session, what = None):
		Screen.__init__(self, session)
		self.session = session
		self["name"] = Button(_("Name"))
		self["ip"] = Button(_("IP"))
		self["port"] = Button(_("Port"))
		self["type"] = Button(_("Enigma Type"))
		self["key_red"] = Button(_("Add"))
		self["key_yellow"] = Button(_("Edit"))
		self["key_blue"] = Button(_("Delete"))
		self["entrylist"] = PartnerboxEntryList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyRed,
			 "yellow":	self.keyYellow,
			 "blue": 	self.keyDelete,
			 }, -1)
		self.what = what
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(self.session, self.what, None)

	def keyRed(self):
		self.session.openWithCallback(self.updateList,PartnerboxEntryConfigScreen,None)

	def keyOK(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		self.close(self.session, self.what, sel)

	def keyYellow(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList,PartnerboxEntryConfigScreen,sel)

	def keyDelete(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Partnerbox Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.Partnerbox.entriescount.value = config.plugins.Partnerbox.entriescount.value - 1
		config.plugins.Partnerbox.entriescount.save()
		config.plugins.Partnerbox.Entries.remove(sel)
		config.plugins.Partnerbox.Entries.save()
		config.plugins.Partnerbox.save()
		configfile.save()
		self.updateList()

class PartnerboxEntryList(MenuList):
	SKIN_COMPONENT_KEY = "PartnerboxList"
	SKIN_COMPONENT_NAME_WIDTH = "nameWidth"
	SKIN_COMPONENT_IP_WIDTH = "ipWidth"
	SKIN_COMPONENT_PORT_WIDTH = "portWidth"
	SKIN_COMPONENT_ENIGMA_WIDTH = "enigmaWidth"
	
	def __init__(self, list, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.SMALL), tlf.size(tlf.SMALL)))
	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(componentSizes.itemHeight(self.SKIN_COMPONENT_KEY, 30))

	def buildList(self):
		self.list=[]
		
		sizes = componentSizes[PartnerboxEntryList.SKIN_COMPONENT_KEY]
		configEntryHeight = sizes.get(componentSizes.ITEM_HEIGHT, 30)
		nameWidth = sizes.get(PartnerboxEntryList.SKIN_COMPONENT_NAME_WIDTH, 250)
		ipWidth = sizes.get(PartnerboxEntryList.SKIN_COMPONENT_IP_WIDTH, 185)
		portWidth = sizes.get(PartnerboxEntryList.SKIN_COMPONENT_PORT_WIDTH, 120)
		enigmaWidth = sizes.get(PartnerboxEntryList.SKIN_COMPONENT_ENIGMA_WIDTH, 160)
				
		for c in config.plugins.Partnerbox.Entries:
			res = [c]
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, nameWidth, configEntryHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.name.value)))
			ip = "%d.%d.%d.%d" % tuple(c.ip.value)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 10+nameWidth, 0, ipWidth, configEntryHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(ip)))
			port = "%d"%(c.port.value)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 15+nameWidth+ipWidth, 0, portWidth, configEntryHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(port)))
			if int(c.enigma.value) == 0:
				e_type = "Enigma2"
			else:
				e_type = "Enigma1"
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 15+nameWidth+ipWidth+portWidth, 0, enigmaWidth, configEntryHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(e_type)))
			self.list.append(res)
		self.l.setList(self.list)
		self.moveToIndex(0)

class PartnerboxEntryConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="PartnerboxEntryConfigScreen" position="center,center" size="820,420" title="%s">
			<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
			<ePixmap name="green" pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
			<ePixmap name="blue" pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on"/>
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
			<widget name="config" position="10,60" size="800,330" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		</screen>""" % _("Partnerbox: Edit Entry")

	def __init__(self, session, entry):
		self.session = session
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Delete"))

		if entry is None:
			self.newmode = 1
			self.current = initPartnerboxEntryConfig()
		else:
			self.newmode = 0
			self.current = entry

		cfglist = [
			getConfigListEntry(_("Name"), self.current.name),
			getConfigListEntry(_("IP"), self.current.ip),
			getConfigListEntry(_("Port"), self.current.port),
			getConfigListEntry(_("Enigma Type"), self.current.enigma),
			getConfigListEntry(_("Password"), self.current.password),
			getConfigListEntry(_("Servicelists/EPG"), self.current.useinternal),
			getConfigListEntry(_("Zap to service when streaming"), self.current.zaptoservicewhenstreaming)
		]

		ConfigListScreen.__init__(self, cfglist, session)

	def keySave(self):
		if self.newmode == 1:
			config.plugins.Partnerbox.entriescount.value = config.plugins.Partnerbox.entriescount.value + 1
			config.plugins.Partnerbox.entriescount.save()
		ConfigListScreen.keySave(self)
		config.plugins.Partnerbox.save()
		configfile.save()
		self.close()

	def keyCancel(self):
		if self.newmode == 1:
			config.plugins.Partnerbox.Entries.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)

	def keyDelete(self):
		if self.newmode == 1:
			self.keyCancel()
		else:		
			self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Partnerbox Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		config.plugins.Partnerbox.entriescount.value = config.plugins.Partnerbox.entriescount.value - 1
		config.plugins.Partnerbox.entriescount.save()
		config.plugins.Partnerbox.Entries.remove(self.current)
		config.plugins.Partnerbox.Entries.save()
		config.plugins.Partnerbox.save()
		configfile.save()
		self.close()
