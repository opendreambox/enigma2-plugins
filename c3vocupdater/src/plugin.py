# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from enigma import cachestate, eDVBDB, eEPGCache, getDesktop
import requests
import json
import shutil
import re
import c3voc

sz_w = getDesktop(0).size().width()

class C3vocScreen (Screen):
	if sz_w == 1920:
		skin = """
		<screen position="center,center" size="840,180" title="c3voc Updater" >
		<widget font="Regular;30" halign="center" name="myText" position="10,10" size="820,70" valign="center" />
		<eLabel backgroundColor="grey" position="10,90" size="820,1" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="20,100" size="300,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="520,100" size="300,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="myRedBtn" position="20,100" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="300,70" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="myGreenBtn" position="520,100" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="300,70" transparent="1" valign="center" zPosition="1" />
		</screen>"""
	else:
		skin = """
		<screen position="center,center" size="520,130" title="c3voc Updater" >
		<widget name="myText" position="10,5" size="500,55" font="Regular;22" halign="center" valign="center"/>
		<eLabel position="10,65" size="500,1" backgroundColor="grey"/>
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,75" size="200,40"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="310,75" size="200,40"/>
		<widget name="myRedBtn" position="10,75" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="myGreenBtn" position="310,75" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		</screen>"""

	def __init__ (self, session):
		self.session = session
		Screen.__init__(self, session)

		self["myText"] = Label(_("Update the c3voc stream bouquet?"))
		self["myRedBtn"] = Label(_("Cancel"))
		self["myGreenBtn"] = Label(_("OK"))
		self["myActionsMap"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"ok": self.getinput,
				"green": self.getinput,
				"red": self.close,
				"cancel": self.close,
			}, -1)
		self._epg_cache = eEPGCache.getInstance()

	def _epg_cache_state_event(self, state):
		if state.state != cachestate.save_finished:
			return

		if c3voc.update_streams_v2("https://streaming.media.ccc.de/streams/v2.json"):
			text = _("c3voc stream bouquet updated")
			self._epg_cache.load()
		else:
			text = _("Nothing changed or no streams available. Please retry later!")

		self.session.open(MessageBox, text=text, type=MessageBox.TYPE_INFO, timeout=4)
		self.close()

	def getinput(self):
		self._conn = self._epg_cache.cacheState.connect(self._epg_cache_state_event)
		self._epg_cache.save()


def main(session, **kwargs):
	session.open(C3vocScreen)

def Plugins(**kwargs):
	return PluginDescriptor(name="C3vocUpdater", description="update the c3voc stream bouquet", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)