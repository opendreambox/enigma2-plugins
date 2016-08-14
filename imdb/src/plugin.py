# -*- coding: UTF-8 -*-
from . import _

from Plugins.Plugin import PluginDescriptor
from Tools.Downloader import downloadWithProgress
from enigma import ePicLoad, eServiceReference
from Screens.Screen import Screen
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.AVSwitch import AVSwitch
from Components.MenuList import MenuList
from Components.ProgressBar import ProgressBar
from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
import os, re
try:
	from urllib import quote_plus
except ImportError as ie:
	from urllib.parse import quote_plus

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigYesNo, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.PluginComponent import plugins
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from HTMLParser import HTMLParser

def transHTML(text):
	h = HTMLParser()
	return h.unescape(text)

config.plugins.imdb = ConfigSubsection()
config.plugins.imdb.showinplugins = ConfigYesNo(default = True)
config.plugins.imdb.ignore_tags = ConfigText(visible_width = 50, fixed_size = False)
config.plugins.imdb.language = ConfigSelection(default = None, choices = [(None, _("Default")),("en-us", _("English")),("fr-fr", _("French")),("de-de", _("German")),("it-it", _("Italian")),("es-es", _("Spanish"))])

imdb_headers = {}

def quoteEventName(eventName):
	eventName = eventName.replace(' ','+')
	return quote_plus(eventName, safe='+')

class IMDBChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = "SimpleChannelSelection"

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.channelSelected
			}
		)

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.openWithCallback(
				self.epgClosed,
				IMDBEPGSelection,
				ref,
				openPlugin = False
			)

	def epgClosed(self, ret = None):
		if ret:
			self.close(ret)

class IMDBEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin = True):
		EPGSelection.__init__(self, session, ref)
		self.skinName = "EPGSelection"
		self["key_green"].setText(_("Lookup"))
		self.openPlugin = openPlugin

	def infoKeyPressed(self):
		self.timerAdd()

	def timerAdd(self):
		cur = self["list"].getCurrent()
		evt = cur[0]
		sref = cur[1]
		if not evt:
			return

		if self.openPlugin:
			self.session.open(
				IMDB,
				evt.getEventName()
			)
		else:
			self.close(evt.getEventName())

	def onSelectionChanged(self):
		pass

class IMDB(Screen):
	skin = """
		<screen name="IMDBv2" position="center,120" size="920,520" title="IMDb - Internet Movie Database">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="225,40" alphatest="on" />
			<widget name="titlelabel" position="10,55" size="900,50" valign="center" font="Regular;24" />
			<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_empty.png" position="600,55" zPosition="0" size="210,21" transparent="1" alphatest="on" />
			<widget name="stars" position="600,55" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_filled.png" transparent="1" />
			<widget name="ratinglabel" position="490,83" size="410,23" font="Regular;19" halign="center" foregroundColor="#f0b400" />
			<widget name="menu" position="10,110" size="900,360" zPosition="3" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<widget name="extralabel" position="10,110" size="900,360" font="Regular;24" />
			<widget name="detailslabel" position="115,110" size="795,140" font="Regular;20" />
			<widget name="poster" position="10,110" size="96,140" alphatest="on" />
			<widget name="castlabel" position="10,260" size="445,230" font="Regular;20" />
			<widget name="storylinelabel" position="465,260" size="445,230" font="Regular;20" />
			<widget name="statusbar" position="10,497" size="900,22" font="Regular;17" foregroundColor="#b3b3b9" />
		</screen>"""
	def __init__(self, session, eventName, callbackNeeded=False):
		Screen.__init__(self, session)
		self.skinName = "IMDBv2"

		for tag in config.plugins.imdb.ignore_tags.getValue().split(','):
			eventName = eventName.replace(tag,'')

		self.eventName = eventName

		self.callbackNeeded = callbackNeeded
		self.callbackData = ""
		self.callbackGenre = ""

		self.fetchurl = None

		self.dictionary_init()

		self["poster"] = Pixmap()
		self.picload = ePicLoad()
		self.picload_conn = self.picload.PictureData.connect(self.paintPosterPixmapCB)

		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1

		self.setTitle(_("IMDb - Internet Movie Database"))
		self["titlelabel"] = Label("")
		self["titlelcd"] = StaticText("")
		self["detailslabel"] = ScrollLabel("")
		self["castlabel"] = ScrollLabel("")
		self["storylinelabel"] = ScrollLabel("")
		self["extralabel"] = ScrollLabel("")
		self["statusbar"] = Label("")
		self["ratinglabel"] = Label("")
		self.resultlist = []
		self["menu"] = MenuList(self.resultlist)
		self["menu"].hide()

		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		# 0 = multiple query selection menu page
		# 1 = movie info page
		# 2 = extra infos page
		self.Page = 0

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MovieSelectionActions", "DirectionActions"],
		{
			"ok": self.showDetails,
			"cancel": self.exit,
			"down": self.pageDown,
			"up": self.pageUp,
			"right": self.keyRight,
			"left": self.keyLeft,
			"red": self.exit,
			"green": self.showMenu,
			"yellow": self.showDetails,
			"blue": self.showExtras,
			"contextMenu": self.contextMenuPressed,
			"showEventInfo": self.showDetails
		}, -1)

		self.getIMDB()

	def title_setText(self, txt):
		StaticText.setText(self["titlelcd"], txt)
		self["titlelabel"].setText(txt)

	def exit(self):
		if fileExists("/tmp/poster.jpg"):
			os.remove("/tmp/poster.jpg")
		if fileExists("/tmp/imdbquery.html"):
			os.remove("/tmp/imdbquery.html")
		if fileExists("/tmp/imdbquery2.html"):
			os.remove("/tmp/imdbquery2.html")
		if self.callbackNeeded:
			self.close([self.callbackData, self.callbackGenre])
		else:
			self.close()

	def dictionary_init(self):
		self.generalinfomask = re.compile(
		'<h1 itemprop="name" class=".*?>(?P<title>.*?)<.*?/h1>*'
		'(?:.*?<div class="originalTitle">(?P<originaltitle>.*?)\s*\((?P<g_originaltitle>original title))*'
		'(?:.*?<h4 class="inline">\s*(?P<g_director>Directors?):\s*</h4>.*?<a.*?>(?P<director>.*?)(?:\d+ more|</div>))*'
		'(?:.*?<h4 class="inline">\s*(?P<g_creator>Creators?):\s*</h4>.*?<a.*?>(?P<creator>.*?)(?:\d+ more|</div>))*'
		'(?:.*?<h4 class="inline">\s*(?P<g_writer>Writers?):\s*</h4>.*?<a.*?>(?P<writer>.*?)(?:\d+ more|</div>))*'
		'(?:.*?<h4 class="float-left">(?P<g_seasons>Seasons?)\s*</h4>.*?<a.*?>(?P<seasons>(?:\d+|unknown)?)</a>)*'
		'(?:.*?<h4 class="inline">\s*(?P<g_country>Country):\s*</h4>.*?<a.*?>(?P<country>.*?)</a>)*'
		'(?:.*?<h4 class="inline">\s*(?P<g_premiere>Release Date).*?</h4>\s+(?P<premiere>.*?)\D+\s+<span)*'
		'(?:.*?<h4 class="inline">(?P<g_runtime>Runtime):</h4>\s*(?P<runtime>.*?)</div>)*'
		, re.S)

		self.extrainfomask = re.compile(
		'(?:.*?<h4 class="inline">(?P<g_keywords>Plot Keywords):</h4>(?P<keywords>.*?)(?:See All|</div>))*'
		'(?:.*?<h4 class="inline">(?P<g_tagline>Taglines):</h4>\s*(?P<tagline>.*?)<)*'
		'(?:.*?<h4 class="inline">(?P<g_cert>Certificate):.*?>(?P<cert>\d{1,2})<.*?(?:certification))*'
		'(?:.*?<h4>(?P<g_mpaa>Motion Picture Rating).*?</h4>*(?P<mpaa>.*?)</span.*?(?:certification))*'
		'(?:.*?<h4 class="inline">(?P<g_language>Language):</h4>\s*(?P<language>.*?)</div>)*'
		'(?:.*?<h4 class="inline">(?P<g_locations>Filming Locations):</h4>.*?<a.*?>(?P<locations>.*?)</a>)*'
		'(?:.*?<h4 class="inline">(?P<g_company>Production Co):</h4>\s*(?P<company>.*?)(?:See more|</div>))*'
		'(?:.*?<h4 class="inline">(?P<g_sound>Sound Mix):</h4>\s*(?P<sound>.*?)</div>)*'
		'(?:.*?<h4 class="inline">(?P<g_color>Color):</h4>\s*(?P<color>.*?)</div>)*'
		'(?:.*?<h4 class="inline">(?P<g_aspect>Aspect Ratio):</h4>\s*(?P<aspect>.*?)(?:See more</a>|</div>))*'
		'(?:.*?<h4>(?P<g_trivia>Trivia)</h4>\s*(?P<trivia>.*?)(?:See more|<span))*'
		'(?:.*?<h4>(?P<g_goofs>Goofs)</h4>\s*(?P<goofs>.*?)(?:See more|<span))*'
		'(?:.*?<h4>(?P<g_quotes>Quotes)</h4>.*?class="character">(?P<quotes>.*?)(?:See more))*'
		'(?:.*?<h4>(?P<g_crazy>Crazy Credits)</h4>\s*(?P<crazy>.*?)(?:See more))*'
		'(?:.*?<h4>(?P<g_connections>Connections)</h4>\s*(?P<connections>.*?)(?:See more|<span))*'
		'(?:.*?<h2>(?P<g_comments>User Reviews)</h2>.*?href="/user/ur\d+/\?ref_=tt_urv".{0,1}>(?:<span itemprop="author">)(?P<commenter>.*?)</span>.*?<p\sitemprop="reviewBody">(?P<comment>.*?)</p>)*'
		, re.S)

		self.genreblockmask = re.compile('href="/genre/.*?\?ref_=tt_stry_gnr.*?\n.*?\s(?P<genre>.*?)</a>', re.S)
		self.ratingmask = re.compile('<span itemprop="ratingValue">(?P<rating>.*?)</.*?itemprop="ratingCount">(?P<ratingcount>.*?)</', re.S)
		self.castmask = re.compile('itemprop="actor".*?class="itemprop"\sitemprop="name">(?P<actor>.*?)</span>.*?class="character">(?P<character>.*?)(?:</a>|</div>|\()', re.S)
		self.postermask = re.compile('<div class="poster">.*?<img .*?src=\"(http.*?)\"', re.S)
		self.storylinemask = re.compile('(?:.*?<h2>(?P<g_storyline>Storyline)</h2>.*?(?P<storyline>.*?)(?:see-more inline|</p>|Written))*', re.S)

		self.htmltags = re.compile('<.*?>')

	def resetLabels(self):
		self["detailslabel"].setText("")
		self["ratinglabel"].setText("")
		self["castlabel"].setText("")
		self["storylinelabel"].setText("")
		self.title_setText("")
		self["extralabel"].setText("")
		self.ratingstars = -1

	def pageUp(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveUp)
		if self.Page == 1:
			self["castlabel"].pageUp()
			self["detailslabel"].pageUp()
			self["storylinelabel"].pageUp()
		if self.Page == 2:
			self["extralabel"].pageUp()

	def pageDown(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveDown)
		if self.Page == 1:
			self["castlabel"].pageDown()
			self["detailslabel"].pageDown()
			self["storylinelabel"].pageDown()
		if self.Page == 2:
			self["extralabel"].pageDown()

	def keyLeft(self):
		if self.Page == 0:
			self["menu"].pageUp()
		if self.Page == 1:
			self["castlabel"].pageUp()
			self["detailslabel"].pageUp()
			self["storylinelabel"].pageUp()
		if self.Page == 2:
			self["extralabel"].pageUp()

	def keyRight(self):
		if self.Page == 0:
			self["menu"].pageDown()
		if self.Page == 1:
			self["castlabel"].pageDown()
			self["detailslabel"].pageDown()
			self["storylinelabel"].pageDown()
		if self.Page == 2:
			self["extralabel"].pageDown()

	def showMenu(self):
		if ( self.Page is 1 or self.Page is 2 ) and self.resultlist:
			self["menu"].show()
			self["stars"].hide()
			self["starsbg"].hide()
			self["ratinglabel"].hide()
			self["castlabel"].hide()
			self["storylinelabel"].hide()
			self["poster"].hide()
			self["extralabel"].hide()
			self["detailslabel"].hide()
			self.title_setText(_("Please select the matching entry"))
			self["key_blue"].setText("")
			self["key_green"].setText(_("Title Menu"))
			self["key_yellow"].setText(_("Details"))
			self.Page = 0

	def showDetails(self):
		self["ratinglabel"].show()
		self["castlabel"].show()
		self["detailslabel"].show()
		self["storylinelabel"].show()

		if self.resultlist and self.Page == 0:
			link = self["menu"].getCurrent()[1]
			title = self["menu"].getCurrent()[0]
			self["statusbar"].setText(_("Re-Query IMDb: %s...") % (title))
			localfile = "/tmp/imdbquery2.html"
			fetchurl = "http://www.imdb.com/title/" + link
			print("[IMDB] showDetails() downloading query " + fetchurl + " to " + localfile)
			download = downloadWithProgress(fetchurl,localfile,headers=imdb_headers)
			download.start().addCallback(self.IMDBquery2).addErrback(self.http_failed)
			self.fetchurl = fetchurl
			self["menu"].hide()
			self.resetLabels()
			self.Page = 1

		if self.Page == 2:
			self["extralabel"].hide()
			self["poster"].show()
			if self.ratingstars > 0:
				self["starsbg"].show()
				self["stars"].show()
				self["stars"].setValue(self.ratingstars)

			self.Page = 1

	def showExtras(self):
		if self.Page == 1:
			self["extralabel"].show()
			self["detailslabel"].hide()
			self["castlabel"].hide()
			self["storylinelabel"].hide()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self["ratinglabel"].hide()
			self.Page = 2

	def contextMenuPressed(self):
		list = [
			(_("Enter search"), self.openVirtualKeyBoard),
			(_("Select from EPG"), self.openChannelSelection),
			(_("Setup"), self.setup),
		]

		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/YTTrailer/plugin.py")):
			list.extend((
				(_("Play Trailer"), self.openYttrailer),
				(_("Search Trailer"), self.searchYttrailer),
			))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title=_("IMDb Menu"),
			list = list,
		)

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def openYttrailer(self):
		try:
			from Plugins.Extensions.YTTrailer.plugin import YTTrailer, baseEPGSelection__init__
		except ImportError as ie:
			pass
		if baseEPGSelection__init__ is None:
			return

		ytTrailer = YTTrailer(self.session)
		ytTrailer.showTrailer(self.eventName)

	def searchYttrailer(self):
		try:
			from Plugins.Extensions.YTTrailer.plugin import YTTrailerList, baseEPGSelection__init__
		except ImportError as ie:
			pass
		if baseEPGSelection__init__ is None:
			return

		self.session.open(YTTrailerList, self.eventName)

	def openVirtualKeyBoard(self):
		self.session.openWithCallback(
			self.gotSearchString,
			VirtualKeyBoard,
			title = _("Enter text to search for"),
			text = self.eventName
		)

	def openChannelSelection(self):
		self.session.openWithCallback(
			self.gotSearchString,
			IMDBChannelSelection
		)

	def gotSearchString(self, ret = None):
		if ret:
			self.eventName = ret
			self.Page = 0
			self.resultlist = []
			self["menu"].hide()
			self["ratinglabel"].show()
			self["castlabel"].show()
			self["storylinelabel"].show()
			self["detailslabel"].show()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self.getIMDB(search=True)

	def getIMDB(self, search=False):
		global imdb_headers
		if config.plugins.imdb.language.value:
			imdb_headers = {'Accept-Language': config.plugins.imdb.language.value}
		else:
			imdb_headers = {}
		self.resetLabels()
		if not self.eventName:
			s = self.session.nav.getCurrentService()
			info = s and s.info()
			event = info and info.getEvent(0) # 0 = now, 1 = next
			if event:
				self.eventName = event.getEventName()
			else:
				self.eventName = self.session.nav.getCurrentlyPlayingServiceReference().toString()
				self.eventName = self.eventName.split('/')
				self.eventName = self.eventName[-1]
				self.eventName = self.eventName.replace('.',' ')
				self.eventName = self.eventName.split('-')
				self.eventName = self.eventName[0]
				if self.eventName.endswith(' '):
					self.eventName = self.eventName[:-1]

		if self.eventName:
			self["statusbar"].setText(_("Query IMDb: %s") % (self.eventName))
			localfile = "/tmp/imdbquery.html"
			fetchurl = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
			print("[IMDB] getIMDB() Downloading Query " + fetchurl + " to " + localfile)
			download = downloadWithProgress(fetchurl,localfile,headers=imdb_headers)
			download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)

		else:
			self["statusbar"].setText(_("Couldn't get Eventname"))

	def cleanhtml(self, in_html):
		in_html = (re.subn(r'<(script).*?</\1>(?s)', '', in_html)[0])
		in_html = (re.subn(r'<(style).*?</\1>(?s)', '', in_html)[0])
		return in_html

	def IMDBquery(self,string):
		self["statusbar"].setText(_("IMDb Download completed"))

		self.inhtml = open("/tmp/imdbquery.html", "r").read()
		self.inhtml = self.cleanhtml(self.inhtml)

		self.generalinfos = self.generalinfomask.search(self.inhtml)

		if self.generalinfos:
			self.IMDBparse()
		else:
			if not re.search('class="findHeader">No results found for', self.inhtml):
				pos = self.inhtml.find("<table class=\"findList\">")
				pos2 = self.inhtml.find("</table>",pos)
				findlist = self.inhtml[pos:pos2]
				searchresultmask = re.compile('<tr class=\"findResult (?:odd|even)\">.*?<td class=\"result_text\"> <a href=\"/title/(tt\d{7,7})/.*?\"\s?>(.*?)</a>.*?</td>', re.S)
				searchresults = searchresultmask.finditer(findlist)
				self.resultlist = [(self.htmltags.sub('',x.group(2)), x.group(1)) for x in searchresults]
				Len = len(self.resultlist)
				self["menu"].l.setList(self.resultlist)
				if Len == 1:
					self["key_green"].setText("")
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.resultlist[0][0],))
					self.eventName = self.resultlist[0][1]
					localfile = "/tmp/imdbquery.html"
					fetchurl = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
					download = downloadWithProgress(fetchurl,localfile,headers=imdb_headers)
					download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)
				elif Len > 1:
					self.Page = 1
					self.showMenu()
				else:
					self["statusbar"].setText(_("No IMDb match.") + ' ' + self.eventName)
			else:
				splitpos = self.eventName.find('(')
				if splitpos > 0:
					self.eventName = self.eventName[:splitpos-1]
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.eventName))
					localfile = "/tmp/imdbquery.html"
					fetchurl = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
					download = downloadWithProgress(fetchurl,localfile,headers=imdb_headers)
					download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)
				else:
					splitpos = self.eventName.find('-')
					if splitpos > 0:
						self.eventName = self.eventName[:splitpos-1].strip()
						self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.eventName))
						localfile = "/tmp/imdbquery.html"
						fetchurl = "http://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
						download = downloadWithProgress(fetchurl,localfile,headers=imdb_headers)
						download.start().addCallback(self.IMDBquery).addErrback(self.http_failed)
					else:
						self["statusbar"].setText(_("IMDb query failed!"))

	def http_failed(self, failure_instance=None, error_message=""):
		text = _("IMDb Download failed")
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			text += ": " + error_message
		print("[IMDB] ",text)
		self["statusbar"].setText(text)

	def IMDBquery2(self,string):
		self["statusbar"].setText(_("IMDb Re-Download completed"))
		self.inhtml = open("/tmp/imdbquery2.html", "r").read()
		self.inhtml = self.cleanhtml(self.inhtml)
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		self.IMDBparse()

	def IMDBparse(self):
		self.Page = 1
		Detailstext = _("No details found.")
		if self.generalinfos:
			self["key_yellow"].setText(_("Details"))
			self["statusbar"].setText(_("IMDb Details parsed"))
			Titeltext = self.generalinfos.group("title").replace('&nbsp;',' ').strip()
			if len(Titeltext) > 57:
				Titeltext = Titeltext[0:54] + "..."
			self.title_setText(Titeltext)

			Detailstext = ""
			stripmask = re.compile('\s{2,}', re.S)

			for category in ("originaltitle", "premiere", "country", "runtime", "seasons"):
				if self.generalinfos.group(category):
					Detailstext += self.generalinfos.group('g_'+category).title() + ": " + stripmask.sub(' ', self.htmltags.sub('', self.generalinfos.group(category).replace('\n',' ').replace('<br>', '\n').replace('<br />','\n'))).replace(' | ',', ').strip() + "\n"

			genreblock = self.genreblockmask.findall(self.inhtml)
			if genreblock:
				s = ''
				if len(genreblock) > 1: s = 's'
				Detailstext += "Genre%s: " % s
				for x in genreblock:
					genres = self.htmltags.sub('', x)
					Detailstext += genres + ", "
				if Detailstext[-2:] == ", ":
					Detailstext = Detailstext[:-2]
				Detailstext += "\n"

			for category in ("director", "creator", "writer"):
				if self.generalinfos.group(category):
					striplink1 = re.compile('<a href="/name/nm\d+\?ref_=tt_ov_.."itemprop=\'url\'>', re.S)
					striplink2 = re.compile('(<a href="fullcredits\?ref_=tt_ov_..#.*?">)', re.S)
					Detailstext += self.generalinfos.group('g_'+category) + ": " + striplink2.sub('', striplink1.sub('', stripmask.sub(' ', self.htmltags.sub('', self.generalinfos.group(category)).replace('\n','').replace('|','')))) + "\n"

			rating = self.ratingmask.search(self.inhtml)
			Ratingtext = _("no user rating yet")
			if rating:
				ratingval = rating.group("rating")
				if ratingval != '<span id="voteuser"></span>':
					count = ''
					if rating.group("ratingcount"): count = ' (' + rating.group("ratingcount").replace(',','.') + ' ' + _("votes") +')'
					Ratingtext = _("User Rating") + ": " + ratingval + "/10" + count
					self.ratingstars = int(10*round(float(ratingval.replace(',','.')),1))
					self["stars"].show()
					self["stars"].setValue(self.ratingstars)
					self["starsbg"].show()
			self["ratinglabel"].setText(str(Ratingtext))

			castresult = self.castmask.finditer(self.inhtml)
			if castresult:
				Casttext = ""
				for x in castresult:
					Casttext += "\n" + self.htmltags.sub('', x.group('actor'))
					if x.group('character'):
						Casttext += " as " + stripmask.sub(' ', self.htmltags.sub('', x.group('character').replace('/ ...','').replace('\n','').replace('&nbsp;',''))).strip()
				if Casttext:
					Casttext = "Cast: " + Casttext
				else:
					Casttext = _("No cast list found in the database.")
				self["castlabel"].setText(str(Casttext))

			storylineresult = self.storylinemask.search(self.inhtml)
			if storylineresult:
				Storyline = ""
				if storylineresult.group("g_storyline"):
					Storyline = storylineresult.group('g_storyline') + ":\n" + re.sub('\s{5,30}',', ', self.htmltags.sub('', storylineresult.group('storyline').replace('\n','').replace('<br>', '\n').replace('<br />','\n').replace('&nbsp;','').replace('&quot;','"').replace('<span class="','')).strip())

				if Storyline == storylineresult.group('g_storyline') + ":\n":
					self["storylinelabel"].hide()
				else:
					self["storylinelabel"].setText(str(Storyline))

			posterurl = self.postermask.search(self.inhtml)
			if posterurl and posterurl.group(1).find("jpg") > 0:
				posterurl = posterurl.group(1)
				self["statusbar"].setText(_("Downloading Movie Poster: %s...") % (posterurl))
				localfile = "/tmp/poster.jpg"
				print("[IMDB] downloading poster " + posterurl + " to " + localfile)
				download = downloadWithProgress(posterurl,localfile,headers=imdb_headers)
				download.start().addCallback(self.IMDBPoster).addErrback(self.http_failed)
			else:
				self.IMDBPoster("kein Poster")

			extrainfos = self.extrainfomask.search(self.inhtml)
			if extrainfos:
				Extratext = ""
				for category in ("tagline","keywords","cert","mpaa","language","color","aspect","company","sound","locations","trivia","goofs","quotes","crazy","connections"):
					if extrainfos.group('g_'+category):
						Extratext += extrainfos.group('g_'+category) + ":\n" + re.sub('\s{5,30}',', ', self.htmltags.sub('', extrainfos.group(category).replace('\n','').replace('<br>', '\n').replace('<br />','\n').replace('&view=simple&sort=alpha&ref_=tt_stry_pl" >',' ').replace('&nbsp;','').replace('&quot;','"').replace('|','').replace(' : ',':').replace(',        ',' / ')).strip()) + "\n\n"
				if extrainfos.group("g_comments"):
					stripmask = re.compile('\s{2,}', re.S)
					Extratext += extrainfos.group("g_comments") + " [" + stripmask.sub(' ', self.htmltags.sub('', extrainfos.group("commenter"))) + "]:\n" + transHTML(self.htmltags.sub('',extrainfos.group("comment").replace("\n",' '))).strip()

				self["extralabel"].setText(str(Extratext))
				self["extralabel"].hide()
				self["key_blue"].setText(_("Extra Info"))
			else:
				self["key_blue"].setText("")

		self["detailslabel"].setText(str(Detailstext))

	def IMDBPoster(self,string):
		self["statusbar"].setText(_("IMDb Details parsed"))
		if not string:
			filename = "/tmp/poster.jpg"
		else:
			filename = resolveFilename(SCOPE_PLUGINS, "Extensions/IMDb/no_poster.png")
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
		self.picload.startDecode(filename)

	def paintPosterPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self["poster"].instance.setPixmap(ptr)
			self["poster"].show()

	def setup(self):
		self.session.open(IMDbSetup)

	def createSummary(self):
		return IMDbLCDScreenV2

class IMDbLCDScreenV2(Screen):
	skin = """
	<screen position="0,0" size="132,64" title="IMDB Plugin">
		<widget name="headline" position="4,0" size="128,22" font="Regular;20"/>
		<widget source="parent.titlelcd" render="Label" position="6,26" size="120,34" font="Regular;14"/>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent)
		self["headline"] = Label(_("IMDb Plugin"))

class IMDbSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"

		self.setup_title = _("IMDb Setup")
		self.onChangedEntry = []

		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["description"] = Label("")

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createSetup()
		self.changedEntry()
		self.onLayoutFinish.append(self.layoutFinished)

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("IMDb query language"), config.plugins.imdb.language))
		self.list.append(getConfigListEntry(_("Show in plugin browser"), config.plugins.imdb.showinplugins))
		self.list.append(getConfigListEntry(_("Words / phrases to ignore (comma separated)"), config.plugins.imdb.ignore_tags))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))

	def changedEntry(self):
		self.item = self["config"].getCurrent()
		for x in self.onChangedEntry:
			x()
		try:
			if isinstance(self["config"].getCurrent()[1], ConfigYesNo) or isinstance(self["config"].getCurrent()[1], ConfigSelection):
				self.createSetup()
		except:
			pass

	def getCurrentEntry(self):
		return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

	def getCurrentValue(self):
		return self["config"].getCurrent() and str(self["config"].getCurrent()[1].getText()) or ""

	def getCurrentDescription(self):
		return self["config"].getCurrent() and len(self["config"].getCurrent()) > 2 and self["config"].getCurrent()[2] or ""

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def keySave(self):
		self.saveAll()
		global imdb_headers
		if config.plugins.imdb.language.value:
			imdb_headers = {'Accept-Language': config.plugins.imdb.language.value}
		else:
			imdb_headers = {}
		if not config.plugins.imdb.showinplugins.value:
			for plugin in plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU):
				if plugin.name == _("IMDb Details"):
					plugins.removePlugin(plugin)

		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()

def eventinfo(session, eventName="", **kwargs):
	if not eventName:
		s = session.nav.getCurrentService()
		if s:
			info = s.info()
			event = info.getEvent(0) # 0 = now, 1 = next
			eventName = event and event.getEventName() or ''
	session.open(IMDB, eventName)

def main(session, eventName="", **kwargs):
	session.open(IMDB, eventName)

pluginlist = PluginDescriptor(name=_("IMDb Details"), description=_("Query details from the Internet Movie Database"), icon="imdb.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, needsRestart=False)

def Plugins(**kwargs):
	l = [PluginDescriptor(name=_("IMDb Details") + "...",
			description=_("Query details from the Internet Movie Database"),
			where=PluginDescriptor.WHERE_EVENTINFO,
			fnc=eventinfo,
			needsRestart=False,
			),
		]

	if config.plugins.imdb.showinplugins.value:
		l.append(pluginlist)

	return l