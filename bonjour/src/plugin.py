# -*- coding: utf-8 -*-

from __future__ import print_function
from enigma import eListboxPythonMultiContent, gFont

from Plugins.Plugin import PluginDescriptor
from Bonjour import bonjour

from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.ActionMap import ActionMap
from skin import TemplatedListFonts, componentSizes

class BonjourScreen(Screen):	
	skin = """
	<screen position="center,120" size="820,520" title="Bonjour" >
		<widget name="menuList" position="10,5" size="800,510" scrollbarMode="showOnDemand" />
	</screen>"""

	SKIN_COMPONENT_KEY = "BonjourList"
	SKIN_COMPONENT_FILE_WIDTH = "fileWidth"
	SKIN_COMPONENT_NAME_WIDTH = "nameWidth"
	SKIN_COMPONENT_TYPE_WIDTH = "typeWidth"
	SKIN_COMPONENT_PROT_WIDTH = "protWidth"
	SKIN_COMPONENT_PORT_WIDTH = "portWidth"
	SKIN_COMPONENT_TEXT_WIDTH = "textWidth"
	SKIN_COMPONENT_TEXT_HEIGHT = "textHeight"
	SKIN_COMPONENT_ITEM_MARGIN = "itemMargin"

	def __init__(self, session, services, files):
		Screen.__init__(self, session)
		self.session = session
		self.services = services
		self.files = files
		
		self["menuList"] = MenuList([], content=eListboxPythonMultiContent)
		self["menuList"].l.setItemHeight(componentSizes.itemHeight(self.SKIN_COMPONENT_KEY, 85))
		tlf = TemplatedListFonts()
		self["menuList"].l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		self["menuList"].l.setFont(1, gFont(tlf.face(tlf.SMALL), tlf.size(tlf.SMALL)))
		
		self["actions"] = ActionMap(["OkCancelActions"],
			{
			 "ok": self._ok,
			 "cancel": self._exit,
			 }, -1)
		
		self.onLayoutFinish.append(self.buildMenu)
		self.onLayoutFinish.append(self.layoutFinished)
								
	def layoutFinished(self):
		print("LAYOUT FINISHED!!")
		self.setTitle(_("Bonjour: Overview"))
										
	def _ok(self):
		print("OK OK OK OK")
		pass
	
	def _exit(self):
		self.close()
		
	def buildMenu(self):
		list = []
		for key in sorted(self.files):
			if self.files[key] != None:
				list.append( self.__buildMenuEntry(self.services[self.files[key]]) )
		
		self["menuList"].l.setList(list)
		self["menuList"].setList(list)
		
	def __buildMenuEntry(self, service):
		print("[Bonjour.__buildMenuEntry] service=%s" %service)
		
		file = "%s" %(service['file'])
		name = "Name: %s" %(service['name'])
		type = "Type: %s" %(service['type'].split('.')[0].replace('_',''))
		prot = "Protocol: %s" %(service['type'].split('.')[1].replace('_',''))
		port = "Port: %s" %(service['port'])
		text = "Text: %s" %(service['text'])
		
		sizes = componentSizes[BonjourScreen.SKIN_COMPONENT_KEY]
		fileWidth = sizes.get(BonjourScreen.SKIN_COMPONENT_FILE_WIDTH, 235)
		nameWidth = sizes.get(BonjourScreen.SKIN_COMPONENT_NAME_WIDTH, 435)
		typeWidth = sizes.get(BonjourScreen.SKIN_COMPONENT_TYPE_WIDTH, 215)
		protWidth = sizes.get(BonjourScreen.SKIN_COMPONENT_PROT_WIDTH, 150)
		portWidth = sizes.get(BonjourScreen.SKIN_COMPONENT_PORT_WIDTH, 150)
		textWidth = sizes.get(BonjourScreen.SKIN_COMPONENT_TEXT_WIDTH, 800)
		textHeight = sizes.get(BonjourScreen.SKIN_COMPONENT_TEXT_HEIGHT, 28)
		itemMargin = sizes.get(BonjourScreen.SKIN_COMPONENT_ITEM_MARGIN, 5)

		return [
			service,
			MultiContentEntryText(pos=(itemMargin, 2), size=(fileWidth, textHeight), font=0, text=file),
			MultiContentEntryText(pos=(itemMargin+fileWidth, 2), size=(nameWidth, textHeight), font=0, text=name),
			MultiContentEntryText(pos=(itemMargin, textHeight+itemMargin), size=(typeWidth, textHeight), font=1, text=type),
			MultiContentEntryText(pos=(itemMargin+typeWidth, textHeight), size=(protWidth, textHeight), font=1, text=prot),
			MultiContentEntryText(pos=(itemMargin+typeWidth+protWidth, textHeight), size=(portWidth, textHeight), font=1, text=port),
			MultiContentEntryText(pos=(itemMargin, textHeight*2), size=(textWidth, textHeight), font=1, text=text)
		]
		
def opencontrol(session):
	bonjour.reloadConfig()
	session.open(BonjourScreen, bonjour.services, bonjour.files)
	print("[Bonjour.opencontrol] %s" %(bonjour.files))
	#TODO GUI-Stuff

	
def Plugins(**kwargs):
	return [ PluginDescriptor(
							name=_("Bonjour"), description=_("Control Bonjour (avahi-daemon)"),
							where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=opencontrol)
			]
