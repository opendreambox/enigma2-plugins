# -*- coding: utf-8 -*-
#
# Wetter Infos von
# www.unwetterzentrale.de und www.uwz.at
#
# Author: barabas
# Fix for Austria by Koepi

import xml.sax.saxutils as util

from Plugins.Plugin import PluginDescriptor
from twisted.web.client import getPage
from twisted.internet import reactor
from Screens.Screen import Screen
from Screens.Console import Console
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from enigma import eTimer, ePicLoad
from re import sub, search, findall
from os import unlink

###############################################################################

class PictureView(Screen):
	skin = """
		<screen position="center,center" size="700,700" flags="wfNoBorder" title="UWZ" >
			<ePixmap position="50,680" size="36,20" pixmap="skin_default/buttons/key_.png" zPosition="2" alphatest="on" />
			<eLabel text="Ok" position="44,680" size="50,20" font="Regular; 16" shadowColor="#000000" shadowOffset="-2,-2" halign="center" transparent="1" valign="center" zPosition="4" />
			<ePixmap position="614,680" size="36,20" pixmap="skin_default/buttons/key_.png" zPosition="2" alphatest="on" />
			<eLabel text="Info" position="608,680" size="50,20" font="Regular; 14" shadowColor="#000000" shadowOffset="-2,-2" halign="center" transparent="1" valign="center" zPosition="4" />
			<widget name="picture" position="center,center" zPosition="2" size="600,600" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.picfile = "/tmp/uwz.png"

		self["picture"] = Pixmap()

		self["actions"] = ActionMap(["OkCancelActions","MovieSelectionActions"],
		{
			"cancel": self.exit,
			"ok": self.exit,
			"showEventInfo": self.HelpView,
		}, -1)

		self.picload = ePicLoad()
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((550, 550, sc[0], sc[1], 0, 0, '#ff000000'))
		self.picload_conn = self.picload.PictureData.connect(self.gotPic)
		self.onLayoutFinish.append(self.getPic)

	def getPic(self):
		self.picload.startDecode(self.picfile)

	def gotPic(self, picInfo = None):
		ptr = self.picload.getData()
		if ptr:
			self["picture"].instance.setPixmap(ptr)

	def HelpView(self):
		self.session.openWithCallback(self.getPic, HelpPictureView)

	def exit(self):
		self.close()

class HelpPictureView(Screen):
	skin = """
		<screen position="center,center" size="700,320" title="Warnstufen" >
			<eLabel position="0,0" zPosition="1" size="700,320" backgroundColor="black" />
			<ePixmap position="80,270" zPosition="2" size="45,45" pixmap="skin_default/vkey_left.png" alphatest="on" />
			<ePixmap position="328,270" zPosition="2" size="45,45" pixmap="skin_default/vkey_esc.png" alphatest="on" />
			<ePixmap position="575,270" zPosition="2" size="45,45" pixmap="skin_default/vkey_right.png" alphatest="on" />
			<widget name="picture" position="5,20" zPosition="2" size="690,225" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["picture"] = Pixmap()

		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"cancel": self.exit,
			"ok": self.exit,
			"left": self.prevPic,
			"right": self.nextPic
		}, -1)

		self.list = (
			pluginpath + "/W_gruen.gif",
			pluginpath + "/W_gelb.gif",
			pluginpath + "/W_orange.gif",
			pluginpath + "/W_rot.gif",
			pluginpath + "/W_violett.gif"
		)
		self.index = 0

		self.picload = ePicLoad()
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((690, 225, sc[0], sc[1], 0, 0, '#ff000000'))
		self.picload_conn = self.picload.PictureData.connect(self.gotPic)

		self.onShown.append(self.getPic)

	def getPic(self):
		self.picload.startDecode(self.list[self.index])

	def gotPic(self, picInfo = None):
		ptr = self.picload.getData()
		if ptr:
			self["picture"].instance.setPixmap(ptr)

	def nextPic(self):
		self.index += 1
		if self.index > 4:
			self.index = 0
		self.getPic()

	def prevPic(self):
		self.index -= 1
		if self.index < 0:
			self.index = 4
		self.getPic()

	def exit(self):
		self.close()

class UnwetterMain(Screen):
	skin = """
		<screen position="center,80" size="800,600" title="Unwetterzentrale" >
			<widget name="hmenu" position="5,0"     size="260,540" scrollbarMode="showOnDemand" zPosition="1" />
			<widget name="thumbnail" position="270,50" size="500,500" zPosition="2" />
			<widget name="thumbland" position="700,0"   size="90,40" zPosition="2" />
			<widget name="statuslabel" position="5,520"   size="530,20" font="Regular;16" halign="left" zPosition="2" />
			<ePixmap position="750,570" size="36,20" pixmap="skin_default/buttons/key_.png" zPosition="2" alphatest="on" />
			<eLabel text="Menu" position="744,570" size="50,20" font="Regular; 12" shadowColor="#000000" shadowOffset="-2,-2" halign="center" transparent="1" valign="center" zPosition="4" />
			<ePixmap position="50,570" size="36,20" pixmap="skin_default/buttons/key_.png" zPosition="2" alphatest="on" />
			<eLabel text="Ok" position="44,570" size="50,20" font="Regular; 16" shadowColor="#000000" shadowOffset="-2,-2" halign="center" transparent="1" valign="center" zPosition="4" />

		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["statuslabel"] = Label()
		self["thumbland"] = Pixmap()
		self["thumbnail"] = Pixmap()
		self["hmenu"] = MenuList([])
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "MovieSelectionActions"],
		{
			"ok":	self.ok,
			"up": self.up,
			"right": self.rightDown,
			"left": self.leftUp,
			"down": self.down,
			"cancel": self.exit,
			"contextMenu": self.switchDeA,
		}, -1)

		self.loadinginprogress = False
		self.picfile = "/tmp/uwz.png"
		self.picweatherfile = pluginpath + "/wetterreport.jpg"
		self.reportfile = "/tmp/uwz.report"

		sc = AVSwitch().getFramebufferScale()
		self.picload_thumb_land = ePicLoad()
		self.picload_thumbs_land_conn = self.picload_thumb_land.PictureData.connect(self.gotThumbLand)
		self.picload_thumb_land.setPara((90, 40, sc[0], sc[1], 0, 0, '#ff000000'))
		
		self.picload_thumb = ePicLoad()
		self.picload_thumbs_conn = self.picload_thumb.PictureData.connect(self.gotThumb)
		self.picload_thumb.setPara((90, 40, sc[0], sc[1], 0, 0, '#ff000000'))

#		self.onLayoutFinish.append(self.go)

		self.ThumbTimer = eTimer()
		self.ThumbTimer_conn = self.ThumbTimer.timeout.connect(self.showThumb)

		self.switchDeA(load=True)

	def hauptmenu(self,output):
		self.loadinginprogress = False
		trans = { '&szlig;' : 'ß' , '&auml;' : 'ä' , '&ouml;' : 'ö' , '&uuml;' : 'ü' , '&Auml;' : 'Ä', '&Ouml;' : 'Ö' , '&Uuml;' : 'Ü'}
		output= util.unescape(output,trans)

		if self.land == "de":
			startpos = output.find('<div id="navigation">')
			endpos = output.find('<li><a class="section-link" title="Unwetterwarnungen Europa"', startpos)
			bereich = output[startpos:endpos]
			a = findall(r'href=(?P<text>.*?)</a>',bereich)
			for x in a:
				x = x.replace('">',"#").replace('"',"").split('#')
				if not len(x) > 1:
					break
				if x[0] == "index.html":
					continue
				name = x[1]
				link = self.baseurl + x[0]
				self.menueintrag.append(name)
				self.link.append(link)
		else:
			self.menueintrag.append("Lagebericht")
			self.link.append(self.weatherreporturl)
			startpos = output.find('</ul><ul><ul id="level_3">')
			endpos = output.find('</ul></ul>', startpos)
			bereich = output[startpos:endpos]
			a = findall(r'href=(?P<text>.*?)</a>',bereich)
			for x in a:
				x = x.replace('">',"#").replace('"',"").split('#')
				if not len(x) > 1:
					break
				if x[0] == "index.html":
					continue
				name = x[1]
				link = self.baseurl + x[0]
				self.menueintrag.append(name)
				self.link.append(link)

		self["statuslabel"].setText("")
		self["hmenu"].l.setList(self.menueintrag)
		self["hmenu"].instance.moveSelectionTo(0)
		self.showThumbLand()

	def ok(self):
		self.go()
		c = self["hmenu"].getCurrent()
		if c is not None:
			x = self.menueintrag.index(c)
			if x != 0:
				self.session.open(PictureView)
			else:
				self.downloadWeatherReport()

	def go(self):
		c = self["hmenu"].getCurrent()
		if c is not None:
			x = self.menueintrag.index(c)
			# Wetterlagebericht ist Index 0
			if x != 0:
				url = self.link[x]
				self["statuslabel"].setText("Loading Data")
				self.downloadPicUrl(url)
			self.ThumbTimer.start(1500, True)

	def up(self):
		self["hmenu"].up()
		self.go()

	def down(self):
		self["hmenu"].down()
		self.go()

	def leftUp(self):
		self["hmenu"].pageUp()
		self.go()

	def rightDown(self):
		self["hmenu"].pageDown()
		self.go()

	def showThumbLand(self):
		picture = ""
		if self.land == "de":
			picture = pluginpath + "/uwz.png"
		else:
			picture = pluginpath + "/uwzat.png"
		self.picload_thumb_land.startDecode(picture)

	def gotThumbLand(self, picInfo = None):
		ptr = self.picload_thumb_land.getData()
		if ptr:
			self["thumbland"].instance.setPixmap(ptr)

	def showThumb(self):
		picture = ""
		if self.land == "de":
			width = 142
			height = 150
		else:
			width = 142
			height = 135
		c = self["hmenu"].getCurrent()
		if c is not None:
			x = self.menueintrag.index(c)
			if x != 0:
				picture = self.picfile
			else:
				picture = self.picweatherfile
				height = 150
			self.picload_thumb.startDecode(picture)

	def gotThumb(self, picInfo = None):
		ptr = self.picload_thumb.getData()
		if ptr:
			self["statuslabel"].setText("")
			self["thumbnail"].show()
			self["thumbnail"].instance.setPixmap(ptr)
		else:
			self["thumbnail"].hide()

	def getPicUrl(self,output):
		self.loadinginprogress = False
		if self.land == "de":
			startpos = output.find('<!-- Anfang msg_Box Content -->')
			endpos = output.find('<!-- Ende msg_Box Content -->', startpos)
			bereich = output[startpos:endpos]
			picurl = search(r'<img src="(?P<text>.*?)" width=',bereich)
			picurl = self.baseurl + picurl.group(1)
		else:
			startpos = output.find('style="background-color: rgb(255,0,255)')
			endpos = output.find('<div id="oben"><img src="../images/map/oesterreich_index_small.png"', startpos)
			bereich = output[startpos:endpos]
			picurl = search(r'<img src="(?P<text>.*?)" width=',bereich)
			picurl = self.baseurl + picurl.group(1)
		self.downloadPic(picurl)

	def getPic(self,output):
		self.loadinginprogress = False
		f = open(self.picfile, "wb")
		f.write(output)
		f.close()

	def getWeatherReport(self,output):
		self.loadinginprogress = False
		trans = { '&szlig;' : 'ß' , '&auml;' : 'ä' , '&ouml;' : 'ö' , '&uuml;' : 'ü' , '&Auml;' : 'Ä', '&Ouml;' : 'Ö' , '&Uuml;' : 'Ü'}
		output= util.unescape(output,trans)
		if self.land == "de":
			startpos = output.find('<!-- Anfang msg_Box Content -->')
			endpos = output.find('<!-- Ende msg_Box Content -->')
			bereich = output[startpos:endpos]
			bereich = bereich.replace('<strong>', '\n')
		else:
			startpos = output.find('<div class="content"')
			endpos = output.find('</div>', startpos)
			bereich = output[startpos:endpos]

		bereich = sub('<br\s*/?>',"\n",bereich)
		bereich = sub('<[^>]*>',"",bereich)
		bereich = sub('Fronten- und Isobarenkarte.*',"",bereich)
		bereich = bereich.strip()
		bereich = sub("\n[\s\n]+", "\n\n", bereich)

		f = open(self.reportfile, "w")
		f.write("%s" % bereich)
		f.close()
		self.session.open(Console,"Warnlagebericht",["cat %s" % self.reportfile])

	def downloadError(self,output):
		self.loadinginprogress = False
		self["statuslabel"].setText("Fehler beim Download")

	def downloadMenu(self):
		self.loadinginprogress = True
		getPage(self.menuurl).addCallback(self.hauptmenu).addErrback(self.downloadError)

	def downloadPicUrl(self,url):
		self.loadinginprogress = True
		getPage(url).addCallback(self.getPicUrl).addErrback(self.downloadError)

	def downloadPic(self,picurl):
		headers = {}
		self.loadinginprogress = True
#		self["statuslabel"].setText("Lade Bild: %s" % picurl)
		if self.land == "a":
			c = self["hmenu"].getCurrent()
			x = self.menueintrag.index(c)
			headers["Referer"] = self.link[x]
		getPage(picurl, headers=headers).addCallback(self.getPic).addErrback(self.downloadError)

	def downloadWeatherReport(self):
		self.loadinginprogress = True
#		self["statuslabel"].setText("Lade Report: %s" % self.weatherreporturl)
		getPage(self.weatherreporturl).addCallback(self.getWeatherReport).addErrback(self.downloadError)

	def switchDeA(self, load=False):
		if load:
			try:
				f = open(pluginpath + "/last.cfg","r")
				self.land = f.read()
				f.close
			except:
				self.land = "a"

		self.menueintrag = []
		self.link = []

		if self.land == "de":
			self.land = "a"
			self.baseurl = "http://unwetter.wetteralarm.at/"
			self.menuurl = self.baseurl + "index.html"
			self.weatherreporturl = self.baseurl + "lagebericht.html"
		else:
			self.land = "de"
			self.baseurl = "http://www.unwetterzentrale.de/uwz/"
			self.menuurl = self.baseurl + "index.html"
			self.weatherreporturl = self.baseurl + "lagebericht.html"

		if not load:
			f = open(pluginpath + "/last.cfg","w")
			f.write(self.land)
			f.close

		self.downloadMenu()
		self.ThumbTimer.start(1500, True)

	def exit(self):
		if self.loadinginprogress:
			reactor.callLater(1,self.exit)
		else:
			try:
				unlink(self.picfile)
				unlink(self.reportfile)
			except OSError:
				pass
			self.close()

#############################

def main(session, **kwargs):
	session.open(UnwetterMain)

def Plugins(path,**kwargs):
	global pluginpath
	pluginpath = path
	return PluginDescriptor(
		name="Unwetterzentrale",
		description="www.unwetterzentrale.de und www.uwz.at",
		icon="uwz.png",
		where = PluginDescriptor.WHERE_PLUGINMENU,
		fnc=main)
