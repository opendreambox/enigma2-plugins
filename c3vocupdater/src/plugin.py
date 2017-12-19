# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from enigma import eDVBDB
import requests
import json
import shutil

class C3vocScreen (Screen):

	skin = """
		<screen position="130,150" size="460,150" title="c3voc Updater" >
			<widget name="myText" position="10,50" size="400,40" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;22"/>
			<widget name="myGreenBtn" position="10,110" size="110,40" backgroundColor="green" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
			<widget name="myRedBtn" position="130,110" size="110,40" backgroundColor="red" valign="center" halign="center" zPosition="2" foregroundColor="white" font="Regular;20"/>
		</screen>"""

	def  __init__ (self, session, args = 0 ):
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
			page = req.get("https://streaming.media.ccc.de/streams/v2.json", headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'})
			data = json.loads(page.content)

			with open("/tmp/c3voc", "a") as myfile:
				myfile.write("#NAME c3voc (TV)\n")
				myfile.close()

			for conference in data:
				conference_name = conference["conference"]
				rooms = self.get_rooms_for_group(conference["groups"], "Lecture Rooms")
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

        def get_rooms_for_group(self, groups, group_title):
		for group in groups:
			if group["group"] != group_title:
				continue
			return group["rooms"]

        def get_hls_url(self, streams, slug):
		for stream in streams:
			if stream["slug"] != slug:
				continue
			return stream["urls"]["hls"]["url"]

def main(session, **kwargs):
	session.open(C3vocScreen)

def Plugins(**kwargs):
	return PluginDescriptor(name="C3vocUpdater", description="update the c3voc stream bouquet", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)