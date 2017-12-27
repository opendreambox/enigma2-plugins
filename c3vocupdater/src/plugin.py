# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from enigma import eDVBDB, getDesktop
import requests
import json
import shutil

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

	def getinput(self):
		try:
			req = requests.session()
			page = req.get("http://streaming.media.ccc.de/streams/v2.json", headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'})
			data = json.loads(page.content)

			with open("/tmp/c3voc", "a") as myfile:
				myfile.write("#NAME c3voc (TV)\n")
				myfile.close()

			for conference in data:
				conference_name = conference["conference"]
				for group in conference["groups"]:
					rooms = group["rooms"]
					if not rooms:
						continue

					for room in rooms:
						schedule_name = room["schedulename"]
						url = self.get_hls_url(room["streams"], "hd-native")
						with open("/tmp/c3voc", "a") as myfile:
							myfile.write("#SERVICE 4097:0:1:0:0:0:0:0:0:0:%s\n#DESCRIPTION %s, %s\n" % (url.replace(":", "%3a"), conference_name, schedule_name))
							myfile.close()

			if 'c3voc' not in open('/etc/enigma2/bouquets.tv').read():
				with open("/etc/enigma2/bouquets.tv", "a") as myfile:
					myfile.write("#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.c3voc__tv_.tv\" ORDER BY bouquet")
					myfile.close()

			shutil.move("/tmp/c3voc","/etc/enigma2/userbouquet.c3voc__tv_.tv")
			eDVBDB.getInstance().reloadBouquets()
			self.session.open(MessageBox, text = _("c3voc stream bouquet updated"), type = MessageBox.TYPE_INFO, timeout=4)
		except:
			pass

		self.close()

        def get_hls_url(self, streams, slug):
		for stream in streams:
			if stream["slug"] != slug:
				continue
			return stream["urls"]["hls"]["url"]

def main(session, **kwargs):
	session.open(C3vocScreen)

def Plugins(**kwargs):
	return PluginDescriptor(name="C3vocUpdater", description="update the c3voc stream bouquet", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)