# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from Tools.Downloader import downloadWithProgress
from twisted.web.client import getPage
from enigma import ePicLoad, eServiceReference, getDesktop
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
import os, re, random, string, six
from six.moves.urllib.parse import quote_plus

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigYesNo, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.PluginComponent import plugins
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from HTMLParser import HTMLParser

try:
	import htmlentitydefs
except ImportError as ie:
	from html import entities as htmlentitydefs
	unichr = chr

sz_w = getDesktop(0).size().width()

config.plugins.imdb = ConfigSubsection()
config.plugins.imdb.showinplugins = ConfigYesNo(default = True)
config.plugins.imdb.showepisodeinfo = ConfigYesNo(default = False)
config.plugins.imdb.origskin = ConfigYesNo(default = True)
config.plugins.imdb.ignore_tags = ConfigText(visible_width = 50, fixed_size = False)
config.plugins.imdb.language = ConfigSelection(default = None, choices = [(None, _("Default")),("en-us", _("English")),("fr-fr", _("French")),("de-de", _("German")),("it-it", _("Italian")),("es-es", _("Spanish"))])

imdb_headers = {}
agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'

def quoteEventName(eventName, safe="/()" + ''.join(map(chr, range(192, 255)))):
	try:
		text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
	except:
		text = eventName
	return quote_plus(text, safe="+")

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
	if sz_w == 1920:
		skin = """
		<screen name="IMDBv2" position="center,110" size="1800,930" title="IMDb - Internet Movie Database">
		<eLabel backgroundColor="grey" position="10,80" size="1780,1" />
    		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" size="300,70" />
    		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="310,5" size="300,70" />
    		<ePixmap pixmap="Default-FHD/skin_default/buttons/yellow.svg" position="610,5" size="300,70" />
    		<ePixmap pixmap="Default-FHD/skin_default/buttons/blue.svg" position="910,5" size="300,70" />
    		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="key_red" position="10,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="300,70" transparent="1" valign="center" zPosition="1" />
    		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="key_green" position="310,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="300,70" transparent="1" valign="center" zPosition="1" />
    		<widget backgroundColor="#a08500" font="Regular;30" halign="center" name="key_yellow" position="610,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="300,70" transparent="1" valign="center" zPosition="1" />
    		<widget backgroundColor="#18188b" font="Regular;30" halign="center" name="key_blue" position="910,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="300,70" transparent="1" valign="center" zPosition="1" />
    		<widget font="Regular;34" halign="right" position="1650,25" render="Label" size="120,40" source="global.CurrentTime">
    			<convert type="ClockToText">Default</convert>
    		</widget>
    		<widget font="Regular;34" halign="right" position="1240,25" render="Label" size="400,40" source="global.CurrentTime" >
    			<convert type="ClockToText">Date</convert>
    		</widget>
		<widget font="Regular;38" name="titlelabel" position="20,90" size="1780,45" foregroundColor="yellow"/>
		<widget enableWrapAround="1" name="menu" position="20,150" scrollbarMode="showOnDemand" size="1760,720" />
		<widget font="Regular;30" name="extralabel" position="20,150" size="1760,730" />
		<widget font="Regular;30" halign="left" name="ratinglabel" position="340,150" size="1000,40" foregroundColor="yellow"/>
		<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_empty.svg" position="20,150" size="300,31" />
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_filled.svg" position="20,150" size="300,31" transparent="1" />
		<widget name="poster" position="20,200" size="300,449" />
		<widget font="Regular;30" name="detailslabel" position="340,210" size="770,400" />
		<widget font="Regular;30" name="castlabel" position="1130,210" size="650,400" />
		<widget font="Regular;30" name="storylinelabel" position="20,660" size="1760,210" />
		<widget name="statusbar" halign="left" position="20,885" size="1600,35" font="Regular;30" foregroundColor="#b3b3b9" />
		</screen>"""
	else:
		skin = """
		<screen name="IMDBv2" position="center,80" size="1200,610" title="IMDb - Internet Movie Database">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40"/>
     		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40"/>
     		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40"/>
     		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40"/>
     		<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
        	<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
    		<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
    		<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
	    	<widget source="global.CurrentTime" render="Label" position="1120,12" size="60,25" font="Regular;22" halign="right">
	    		<convert type="ClockToText">Default</convert>
	    	</widget>
	    	<widget source="global.CurrentTime" render="Label" position="810,12" size="300,25" font="Regular;22" halign="right">
	    		<convert type="ClockToText">Format:%A %d. %B</convert>
	    	</widget>
	    	<eLabel position="10,50" size="1180,1" backgroundColor="grey"/>
		<widget name="titlelabel" position="20,55" size="1180,30" valign="center" font="Regular;24" foregroundColor="yellow"/>
		<widget name="menu" position="20,90" size="1160,480" zPosition="3" scrollbarMode="showOnDemand" enableWrapAround="1" />
		<widget name="extralabel" position="20,90" size="1160,490" font="Regular;20" />
		<widget name="ratinglabel" position="225,92" size="800,23" font="Regular;20" foregroundColor="yellow"/>
		<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_empty.svg" position="20,90" size="185,21"/>
		<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IMDb/starsbar_filled.svg" position="20,90" size="185,21" transparent="1" />
		<widget name="poster" position="20,120" size="185,278"/>
		<widget name="detailslabel" position="225,130" size="450,270" font="Regular;20" />
		<widget name="castlabel" position="695,130" size="485,280" font="Regular;20" />
		<widget name="storylinelabel" position="20,410" size="1160,170" font="Regular;20" />
		<widget name="statusbar" position="20,580" size="1150,25" halign="left" font="Regular;20" foregroundColor="#b3b3b9" />
		</screen>"""

	NBSP = unichr(htmlentitydefs.name2codepoint['nbsp']).encode("utf8")

	def __init__(self, session, eventName, callbackNeeded=False):
		Screen.__init__(self, session)
		if config.plugins.imdb.origskin.value:
			self.skinName = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
		else:
			self.skinName = "IMDBv2"

		for tag in config.plugins.imdb.ignore_tags.getValue().split(','):
			eventName = eventName.replace(tag,'')

		self.eventName = eventName

		self.callbackNeeded = callbackNeeded
		self.callbackData = ""
		self.callbackGenre = ""

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
		if self.callbackNeeded:
			self.close([self.callbackData, self.callbackGenre])
		else:
			self.close()

	def dictionary_init(self):
		self.generalinfomask = re.compile(
		'<h1.*?class="TitleHeader__TitleText.*?>(?P<title>.*?)</h1>*'
		'(?:.*?>(?P<g_episodes>Episodes)<span.*?>(?P<episodes>.*?)</span>)?'
		'(?:.*?class="OriginalTitle__OriginalTitleText.*?>(?P<g_originaltitle>.*?):\s.*?(?P<originaltitle>.*?)</div)?'
		'(?:.*?<label for="browse-episodes-season".*?>.*?(?P<seasons>\d+)\s(?P<g_seasons>seasons?)</label>)?'
		'(?:.*?<span.*?>(?P<g_director>Directors?)(?:</span>|</a>).*?<div.*?<ul.*?>(?P<director>.*?)</ul>)?'
		'(?:.*?<span.*?>(?P<g_creator>Creators?)(?:</span>|</a>).*?<div.*?<ul.*?>(?P<creator>.*?)</ul>)?'
		'(?:.*?<span.*?>(?P<g_writer>Writers?)(?:</span>|</a>).*?<div.*?<ul.*?>(?P<writer>.*?)</ul>)?'
		'(?:.*?<a.*?>(?P<g_premiere>Release date)</a>.*?<div.*?<ul.*?>(?P<premiere>.*?)</ul>)?'
		'(?:.*?<span.*?>(?P<g_country>Countr.*?of origin)</span>.*?<div.*?<ul.*?>(?P<country>.*?)</ul>)?'
		'(?:.*?<a.*?>(?P<g_alternativ>Also known as)</a>.*?<div.*?<ul.*?>(?P<alternativ>.*?)</ul>)?'
		'(?:.*?<span.*?>(?P<g_runtime>Runtime)</span>.*?<div.*?<ul.*?>(?P<runtime>.*?)</ul>)?', re.S)

		self.extrainfomask = re.compile(
		'(?:.*?<div.*?class="GenresAndPlot__TextContainerBreakpointXL.*?>(?P<outline>.+?)</div>)?'
		'(?:.*?<a.*?>(?P<g_tagline>Taglines?)(?:</span>|</a>).*?<div.*?<ul.*?<li.*?<span.*?>(?P<tagline>.*?)</span>)?'
		'(?:.*?<a.*?>(?P<g_cert>Certificate|Motion Picture Rating \(MPAA\))</a>.*?<div.*?<ul.*?<li.*?<span.*?>(?P<cert>.*?)</span>)?'
		'(?:.*?<a.*?>(?P<g_trivia>Trivia)</a><div.*?<div.*?<div.*?<div.*?>(?P<trivia>.+?)</div>)?'
		'(?:.*?<a.*?>(?P<g_goofs>Goofs)</a><div.*?<div.*?<div.*?<div.*?>(?P<goofs>.+?)</div>)?'
		'(?:.*?<a.*?>(?P<g_quotes>Quotes)</a><div.*?<div.*?<div.*?<div.*?>(?P<quotes>.+?)</div>)?'
		'(?:.*?<a.*?>(?P<g_crazycredits>Crazy credits)</a><div.*?<div.*?<div.*?<div.*?>(?P<crazycredits>.+?)</div>)?'
		'(?:.*?<a.*?>(?P<g_alternateversions>Alternate versions)</a><div.*?<div.*?<div.*?<div.*?>(?P<alternateversions>.+?)</div>)?'
		'(?:.*?<a.*?>(?P<g_connections>Bez\S*?ge zu anderen Titeln|Connections)</a><div.*?<div.*?<div.*?<div.*?>(?P<connections>.+?)</div>)?'
		'(?:.*?<a.*?>(?P<g_soundtracks>Soundtracks)</a><div.*?<div.*?<div.*?<div.*?>(?P<soundtracks>.+?)</div>)?'
		'(?:.*?<h3.*?>(?P<g_comments>User reviews)<span.*?UserReviewSummary__Summary.*?>(?P<commenttitle>.*?)</span></div.*?<div.*?<div.*?>(?P<comment>.+?)</div>.*?<div.*?UserReviewAuthor__AuthorContainer.*?>.*?<ul.*?<li.*?>(?P<commenter>.+?)</li>)?'
		'(?:.*?<span.*?>(?P<g_language>Languages?)</span>.*?<div.*?<ul.*?>(?P<language>.*?)</ul>)?'
		'(?:.*?<a.*?>(?P<g_locations>Filming locations?)</a>.*?<div.*?<ul.*?>(?P<locations>.*?)</ul>)?'
		'(?:.*?<a.*?>(?P<g_company>Production compan.*?)</a>.*?<div.*?<ul.*?>(?P<company>.*?)</ul>)?'
		'(?:.*?<span.*?>(?P<g_color>Color)</span>.*?<div.*?<ul.*?>(?P<color>.*?)</ul>)?'
		'(?:.*?<span.*?>(?P<g_sound>Sound mix)</span>.*?<div.*?<ul.*?>(?P<sound>.*?)</ul>)?'
		'(?:.*?<span.*?>(?P<g_aspect>Aspect ratio)</span>.*?<div.*?<ul.*?<li.*?<span.*?>(?P<aspect>.*?)</div>)?', re.S)

		self.awardsmask = re.compile('<li.*?data-testid="award_information".*?><a.*?>(?P<awards>.+?)</span></li>', re.S)
		self.keywordsmask = re.compile('data-testid="storyline-plot-keywords">(?P<keywords>.*?)</div>', re.S)
		self.boxofficemask = re.compile('<h3.*?>(?P<g_boxoffice>Box office)</h3.*?<div.*?list-item__label">Budget</span>.*?list-content-item">(?P<boxofficebudget>.*?)</span>.*?list-content-item">(?P<boxofficegrossuscanada>.*?)</span>.*?list-content-item">(?P<boxofficeopening>.*?)</span>.*?list-content-item">(?P<boxofficeopeningdate>.*?)</span>.*?list-content-item">(?P<boxofficegrossworld>.*?)</span>', re.S)
		self.genreblockmask = re.compile('<li.*?storyline-genres.*?><span.*?>(?P<g_genres>Genres?)</span>.*?<div.*?><ul.*?>(?P<genres>.*?)</ul>', re.S)
		self.ratingmask = re.compile('<span.*?AggregateRatingButton__RatingScore.*?>(?P<rating>.*?)</span>.*?<span.*?AggregateRatingButton__TotalRatingAmount.*?>(?P<ratingcount>.*?)</div', re.S)
		self.castmask = re.compile('<a.*?StyledComponents__ActorName.*?>(?P<actor>.*?)</a>.*?StyledComponents__CharacterNameWithoutAs.*?>(?P<character>.*?)</span>(?:.*?<span><span.*?>(?P<episodes>.*?)</span></span>)?', re.S)
		self.postermask = re.compile('<div.*?ipc-media--poster.*?<img.*?ipc-image.*?src="(http.*?)"', re.S)
		self.storylinemask = re.compile('<section.*?<div.*?<div.*?<hgroup.*?<h3.*?>(?P<g_storyline>Storyline)</h3>.*?<div.*?<div.*?<div.*?<div.*?>(?P<storyline>.+?)<span', re.S)

		self.htmltags = re.compile('<.*?>', re.S)
		self.allhtmltags = re.compile('<.*>', re.S)

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
			fetchurl = "https://www.imdb.com/title/" + link
			print("[IMDB] showDetails() downloading query " + fetchurl)
			getPage(fetchurl, agent=agent, headers=imdb_headers).addCallback(self.IMDBquery2).addErrback(self.http_failed)
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
			fetchurl = "https://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
			print("[IMDB] getIMDB() Downloading Query " + fetchurl)
			getPage(fetchurl, agent=agent, headers=imdb_headers).addCallback(self.IMDBquery).addErrback(self.http_failed)
		else:
			self["statusbar"].setText(_("Couldn't get Eventname"))

	def html2utf8(self, in_html):
		utf8 = ('charSet="utf-8"' in in_html or 'charset="utf-8"' in in_html or 'charSet=utf-8' in in_html or 'charset=utf-8' in in_html)
		start = in_html.find('<nav id="imdbHeader"')
		if start == -1:
			start = 0
		end = in_html.find('title-news-header')
		if end == -1:
			end = len(in_html)
		in_html = in_html[start:end]
		in_html = re.sub(r'(?s)<(script|style|svg).*?</\1>', '', in_html)
		entitydict = {}
		entities = re.finditer(r'&(?:([A-Za-z0-9]+)|#x([0-9A-Fa-f]+)|#([0-9]+));', in_html)
		for x in entities:
			key = x.group(0)
			if key not in entitydict:
				if x.group(1):
					if x.group(1) in htmlentitydefs.name2codepoint:
						entitydict[key] = htmlentitydefs.name2codepoint[x.group(1)]
				elif x.group(2):
					entitydict[key] = str(int(x.group(2), 16))
				else:
					entitydict[key] = x.group(3)
		if utf8:
			for key, codepoint in six.iteritems(entitydict):
				cp = six.unichr(int(codepoint))
				if six.PY2:
					cp = cp.encode('utf8')
				in_html = in_html.replace(key, cp)
			self.inhtml = in_html
		else:
			for key, codepoint in six.iteritems(entitydict):
				cp = six.unichr(int(codepoint))
				if six.PY2:
					cp = cp.encode('latin-1', 'ignore')
				in_html = in_html.replace(key, cp)
			if six.PY2:
				self.inhtml = in_html.decode('latin-1').encode('utf8')

	def IMDBquery(self, data):
		self["statusbar"].setText(_("IMDb Download completed"))
		self.html2utf8(data)
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		if self.generalinfos:
			self.IMDBparse()
		else:
			if not re.search('class="findHeader">No results found for', self.inhtml):
				pos = self.inhtml.find("<table class=\"findList\">")
				pos2 = self.inhtml.find("</table>",pos)
				findlist = self.inhtml[pos:pos2]
				searchresultmask = re.compile('<tr class=\"findResult (?:odd|even)\">.*?<td class=\"result_text\"> <a href=\"/title/(tt\d{7,8})/.*?\"\s?>(.*?)</td>', re.S)
				searchresults = searchresultmask.finditer(findlist)
				self.resultlist = [(self.htmltags.sub('', x.group(2)), x.group(1)) for x in searchresults]
				Len = len(self.resultlist)
				self["menu"].l.setList(self.resultlist)
				if Len == 1:
					self["key_green"].setText("")
					self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.resultlist[0][0],))
					self.eventName = self.resultlist[0][1]
					fetchurl = "https://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
					getPage(fetchurl, agent=agent, headers=imdb_headers).addCallback(self.IMDBquery).addErrback(self.http_failed)
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
					fetchurl = "https://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
					getPage(fetchurl, agent=agent, headers=imdb_headers).addCallback(self.IMDBquery).addErrback(self.http_failed)
				else:
					splitpos = self.eventName.find('-')
					if splitpos > 0:
						self.eventName = self.eventName[:splitpos-1].strip()
						self["statusbar"].setText(_("Re-Query IMDb: %s...") % (self.eventName))
						fetchurl = "https://www.imdb.com/find?ref_=nv_sr_fn&q=" + quoteEventName(self.eventName) + "&s=all"
						getPage(fetchurl, agent=agent, headers=imdb_headers).addCallback(self.IMDBquery).addErrback(self.http_failed)
					else:
						self["statusbar"].setText(_("IMDb query failed!"))

	def http_failed(self, error):
		text = _("IMDb Download failed")
		text += ": " + str(error)
		print("[IMDB] ",text)
		self["statusbar"].setText(text)

	def IMDBquery2(self, data):
		self["statusbar"].setText(_("IMDb Re-Download completed"))
		self.html2utf8(data)
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		self.IMDBparse()

	def IMDBparse(self):
		self.Page = 1
		Detailstext = _("No details found.")
		if self.generalinfos:
			self["key_yellow"].setText(_("Details"))
			self["statusbar"].setText(_("IMDb Details parsed"))
			Titletext = self.generalinfos.group("title").replace(self.NBSP, ' ').strip()
			if len(Titletext) > 57:
				Titletext = Titletext[0:54] + "..."
			self.title_setText(Titletext)

			Detailstext = ""
			addnewline = ""

			_("Genre:"), _("Genres:") # translate tags
			genreblock = self.genreblockmask.search(self.inhtml)
			if genreblock:
				genres = ', '.join(re.split('\|+', self.htmltags.sub('|', genreblock.group("genres"))))
				if genres:
					Detailstext += addnewline + _(genreblock.group('g_genres')+":") + " " + genres.strip(', ').strip(',')
					addnewline = "\n"

			_("Director:"), _("Directors:"), _("Creator:"), _("Creators:"), _("Writer:"), _("Writers:"), _('Episodes:'), _("Runtime:"), _("Release date:"), _("Country of origin:"), _("Countries of origin:"), _("Original title:"), _("Also known as:") # translate tags
			for category in ("director", "creator", "writer", "seasons", "episodes", "runtime", "premiere", "country", "originaltitle", "alternativ"):
				try:

					if self.generalinfos.group(category):
						if category == 'runtime':
							runtime = re.findall('(?:(\d+)h|)\s{0,1}(?:(\d+)min|)', self.htmltags.sub('', self.generalinfos.group(category)), re.S)
							if runtime:
								if runtime[0][0] and runtime[0][1]:
									runtime = str(60 * int(runtime[0][0]) + int(runtime[0][1]))
									txt = runtime + " min"
								elif runtime[0][0]:
									runtime = str(60 * int(runtime[0][0]))
									txt = runtime + " min"
								elif runtime[0][1]:
									txt = runtime[0][1] + " min"
							else:
								txt = ', '.join(re.split('\|+', self.htmltags.sub('|', self.generalinfos.group(category)).strip('|').replace("\n", ' ')))
						elif category == 'seasons':
							txt = ' '.join(self.htmltags.sub(' ', self.generalinfos.group(category)).replace("\n", ' ').replace('See all', '...').split())
						elif category in ('creator', 'writer'):
							txt = ', '.join(re.split('\|+', self.htmltags.sub('|', self.generalinfos.group(category).replace('</a><span class="ipc-metadata-list-item__list-content-item--subText">', ' ')).strip('|').replace("\n", ' ')))
						elif category in ("premiere", "country", "originaltitle", "alternativ"):
							txt = ', '.join(re.split('\|+', self.htmltags.sub('|', self.generalinfos.group(category).replace('\n', ' ')).strip('|')))
						else:
							txt = ', '.join(re.split('\|+', self.htmltags.sub('|', self.generalinfos.group(category)).strip('|').replace("\n", ' ')))
						Detailstext += addnewline + _(self.generalinfos.group('g_' + category)+":") + " " + txt
						if category == 'seasons':
							Detailstext = Detailstext.replace('seasons:', _('Seasons:'))
						addnewline = "\n"
				except IndexError:
					pass

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
						chartext = self.htmltags.sub(' ', x.group('character').replace('/ ...', '')).replace('\n', ' ').replace(self.NBSP, ' ')
						Casttext += _(" as ") + ' '.join(chartext.split()).replace('…', '')
						try:
							if config.plugins.imdb.showepisodeinfo.value and x.group('episodes'):
								Casttext += '\n(' + self.htmltags.sub('', re.sub(r"[0-9]+ eps", "", x.group('episodes').replace('episodes', _("episodes"))).replace(' • ', ', ')).strip() + ')'
						except IndexError:
							pass
				if Casttext:
					Casttext = _("Cast:") + " " + Casttext
				else:
					Casttext = _("No cast list found in the database.")
				self["castlabel"].setText(Casttext)

			storylineresult = self.storylinemask.search(self.inhtml)
			if storylineresult:
				_("Storyline:") # translate tag
				Storyline = ""
				if storylineresult.group("g_storyline"):
					Storyline = _(storylineresult.group('g_storyline')+":") + "\n"
					if not "Add content advisory" in storylineresult.group('storyline'):
						Storyline = Storyline + re.sub('\s{5,30}',', ', self.htmltags.sub('', storylineresult.group('storyline').replace('\n','').replace('<br>', '\n').replace('<br/>', '\n').replace('<br />','\n').replace('&nbsp;','').replace('&quot;','"').replace('<span class="','')).strip())

				if Storyline == _(storylineresult.group('g_storyline')+":") + "\n":
					self["storylinelabel"].hide()
				else:
					self["storylinelabel"].setText(Storyline)

			posterurl = self.postermask.search(self.inhtml)
			if posterurl and posterurl.group(1).find("jpg") > 0:
				posterurl = posterurl.group(1)
				self["statusbar"].setText(_("Downloading Movie Poster: %s...") % (posterurl))
				localfile = "/tmp/poster.jpg"
				print("[IMDB] downloading poster " + posterurl + " to " + localfile)
				download = downloadWithProgress(posterurl,localfile,headers=imdb_headers)
				download.start().addCallback(self.IMDBPoster).addErrback(self.http_failed)
			else:
				self.IMDBPoster("no poster")

			Extratext = ''

			extrainfos = self.extrainfomask.search(self.inhtml)

			if extrainfos:
				_("Tagline:"), _("Taglines:") # translate tags
				for category in ("outline", "tagline"):
					try:
						if extrainfos.group(category):
							sep = "\n" if category in ("outline") else " "
							if category == "outline":
								if "Add a plot" in extrainfos.group(category) or extrainfos.group(category) == "</span></p>":
									continue
								Extratext += "\n" + _("Plot outline:")
							else:
								Extratext += "\n" + _(extrainfos.group('g_' + category)+":")
							txt = ', '.join(re.split('\|+', self.htmltags.sub('|', extrainfos.group(category).replace("\n", ' ').replace("<br>", '\n').replace("<br/>", '\n').replace('<br />', '\n')).strip('|').replace(' |' + self.NBSP, '').replace(self.NBSP, ' ')))
							Extratext += sep + txt + "\n"
					except IndexError:
						pass

			keywordsresult = self.keywordsmask.search(self.inhtml)
			if keywordsresult:
				keywords = keywordsresult.group('keywords').replace(' ', '_')
				keywords = ', '.join(self.htmltags.sub(' ', keywords).split())
				keywords = re.sub(', \d+ more', '', keywords.replace('_', ' '))
				Extratext += "\n" + _("Keywords:") + " " + keywords + "\n"

			awardsresult = self.awardsmask.finditer(self.inhtml)
			if awardsresult:
				awardslist = [' '.join(x.group('awards').split()) for x in awardsresult]
				if awardslist:
					awards = self.allhtmltags.sub(', ', ''.join(awardslist).replace('<b>', '').replace('Awards</a>', '').strip()).strip(', ')
					Extratext += "\n" + _("Awards:") + " " + awards + "\n"

			boxofficeresult = self.boxofficemask.search(self.inhtml)
			if boxofficeresult:
				boxoffice = "Budget " + boxofficeresult.group('boxofficebudget') + "\n" + "Opening weekend US & Canada " + boxofficeresult.group('boxofficeopening') + " (" + boxofficeresult.group('boxofficeopeningdate') + ")" + "\n" + "Gross US & Canada " + boxofficeresult.group('boxofficegrossuscanada') + "\n" "Gross worldwide " + boxofficeresult.group('boxofficegrossworld')
				Extratext += "\n" + _("Box office:") + "\n" + boxoffice + "\n"

			if extrainfos:
				_("Certificate:"), _("Motion Picture Rating (MPAA):"), _("Language:"), _("Languages:"), _("Color:"), _("Aspect ratio:"), _("Sound mix:"), _("Filming location:"), _("Filming locations:"), _("Production company:"), _("Production companies:"), _("Trivia:"), _("Goofs:"), _("Quotes:"), _("Crazy credits:"), _("Alternate versions:"), _("Connections:"), _("Soundtracks:"), _("User reviews:") # translate tags
				for category in ("cert", "language", "color", "aspect", "sound", "locations", "company", "trivia", "goofs", "quotes", "crazycredits", "alternateversions", "connections", "soundtracks"):
					try:
						if extrainfos.group(category):
							sep = "\n" if category in ("trivia", "goofs", "quotes", "connections", "crazycredits", "alternateversions", "soundtracks") else " "
							Extratext += "\n" + _(extrainfos.group('g_' + category)+":")
							if category in ("trivia", "goofs", "quotes", "connections", "crazycredits", "alternateversions", "soundtracks"):
								txt = extrainfos.group(category).replace("<li>", '• ').replace("</li>", '\n').replace('Read all</a>', '').replace("</a>", '').replace("<br>", '\n').replace("<br/>", '\n').replace('<br />', '\n').replace("</p><p>", '\n')
								txt = self.htmltags.sub('', txt).strip('\n')
							elif category in ("aspect", "sound"):
								txt = extrainfos.group(category).replace(' : ', ':').replace('</a><span class="ipc-metadata-list-item__list-content-item--subText">', ' ').replace('</li>', ', ')
								txt = self.htmltags.sub('', txt).strip(', ').strip()
							else:
								txt = ', '.join(re.split('\|+', self.htmltags.sub('|', extrainfos.group(category).replace("\n", ' ').replace("<br>", '\n').replace("<br/>", '\n').replace('<br />', '\n')).strip('|').replace(' |' + self.NBSP, '').replace(self.NBSP, ' ')))
							Extratext += sep + txt + "\n"
					except IndexError:
						pass
				try:
					if extrainfos.group("g_comments"):
						Extratext += "\n" + _(extrainfos.group("g_comments")+":") + "\n" + self.htmltags.sub('', extrainfos.group("commenttitle")) + " [" + ' '.join(self.htmltags.sub('', extrainfos.group("commenter")).split()) + "]\n" + self.htmltags.sub('', extrainfos.group("comment").replace("<br>", '\n').replace("<br/>", '\n').replace("<br />", '\n')) + "\n"
				except IndexError:
					pass

			if Extratext:
				self["extralabel"].setText(Extratext.strip('\n'))
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
	skin = (
	"""<screen title="IMDB Plugin" position="0,0" size="132,64" id="1">
		<widget name="headline" font="Display;22" halign="center" position="1,3" size="130,22"/>
		<widget source="parent.titlelcd" render="Label" font="Display;16" halign="center" valign="center" position="1,28" size="130,34"/>
	</screen>""",
	"""<screen title="IMDB Plugin" position="0,0" size="96,64" id="2">
		<widget name="headline" font="Display;19" halign="center" position="0,2" size="96,20"/>
		<widget source="parent.titlelcd" render="Label" font="Display;15" halign="center" valign="center" position="0,28" size="96,34"/>
	</screen>""",
	"""<screen title="IMDB Plugin" position="0,0" size="400,240" id="3">
		<ePixmap position="0,0" size="400,240" pixmap="skin_default/display_bg.png" zPosition="-1"/>
		<widget name="headline" font="Display;60" halign="center" position="0,5" size="400,60" transparent="1"/>
		<eLabel backgroundColor="yellow" position="0,75" size="400,2" />
		<widget source="parent.titlelcd" render="Label" font="Display;45" halign="center" valign="center" position="0,85" size="400,135" transparent="1"/>
	</screen>""")

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
		self.list.append(getConfigListEntry(_("Use original IMDb skin:"), config.plugins.imdb.origskin))
		self.list.append(getConfigListEntry(_("Show episode and year information in cast list"), config.plugins.imdb.showepisodeinfo))
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