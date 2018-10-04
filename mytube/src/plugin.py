from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Task import Task, Job, job_manager
from Components.config import config, ConfigSelection, ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry
#, ConfigIP, ConfigNumber, ConfigLocations
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_HDD, SCOPE_CURRENT_PLUGIN
from Tools.Downloader import downloadWithProgress
from Tools.Log import Log

from Plugins.Plugin import PluginDescriptor

from MyTubePlayer import MyTubePlayer
from MyTubeSearch import ConfigTextWithGoogleSuggestions, MyTubeTasksScreen, MyTubeHistoryScreen
from MyTubeService import validate_cert, get_rnd, myTubeService
from MyTubeSettings import MyTubeSettingsScreen

from Plugins.SystemPlugins.TubeLib.youtube.Search import Search

from __init__ import decrypt_block

from enigma import eTPM, eTimer, ePoint, ePicLoad, eServiceReference
from os import path as os_path, remove as os_remove
from twisted.web import client

etpm = eTPM()
rootkey = ['\x9f', '|', '\xe4', 'G', '\xc9', '\xb4', '\xf4', '#', '&', '\xce', '\xb3', '\xfe', '\xda', '\xc9', 'U', '`', '\xd8', '\x8c', 's', 'o', '\x90', '\x9b', '\\', 'b', '\xc0', '\x89', '\xd1', '\x8c', '\x9e', 'J', 'T', '\xc5', 'X', '\xa1', '\xb8', '\x13', '5', 'E', '\x02', '\xc9', '\xb2', '\xe6', 't', '\x89', '\xde', '\xcd', '\x9d', '\x11', '\xdd', '\xc7', '\xf4', '\xe4', '\xe4', '\xbc', '\xdb', '\x9c', '\xea', '}', '\xad', '\xda', 't', 'r', '\x9b', '\xdc', '\xbc', '\x18', '3', '\xe7', '\xaf', '|', '\xae', '\x0c', '\xe3', '\xb5', '\x84', '\x8d', '\r', '\x8d', '\x9d', '2', '\xd0', '\xce', '\xd5', 'q', '\t', '\x84', 'c', '\xa8', ')', '\x99', '\xdc', '<', '"', 'x', '\xe8', '\x87', '\x8f', '\x02', ';', 'S', 'm', '\xd5', '\xf0', '\xa3', '_', '\xb7', 'T', '\t', '\xde', '\xa7', '\xf1', '\xc9', '\xae', '\x8a', '\xd7', '\xd2', '\xcf', '\xb2', '.', '\x13', '\xfb', '\xac', 'j', '\xdf', '\xb1', '\x1d', ':', '?']

config.plugins.mytube = ConfigSubsection()
config.plugins.mytube.search = ConfigSubsection()


config.plugins.mytube.search.searchTerm = ConfigTextWithGoogleSuggestions("", False)
config.plugins.mytube.search.orderBy = ConfigSelection(
				[
				 ("relevance", _("Relevance")),
				 ("viewCount", _("View Count")),
				 ("date", _("Published")),
				 ("rating", _("Rating"))
				], "relevance")
config.plugins.mytube.search.time = ConfigSelection(
				[
				 ("all_time", _("All Time")),
				 ("this_month", _("This Month")),
				 ("this_week", _("This Week")),
				 ("today", _("Today"))
				], "all_time")
config.plugins.mytube.search.safeSearch = ConfigSelection(
				[
				 (Search.SAFE_SEARCH_NONE, _("No")),
				 (Search.SAFE_SEARCH_MODERATE, _("Moderately")),
				 (Search.SAFE_SEARCH_STRICT, _("Strictly")),
				], Search.SAFE_SEARCH_NONE)
config.plugins.mytube.search.categories = ConfigSelection(
				[
				 (None, _("All")),
				 ("Film", _("Film & Animation")),
				 ("Autos", _("Autos & Vehicles")),
				 ("Music", _("Music")),
				 ("Animals", _("Pets & Animals")),
				 ("Sports", _("Sports")),
				 ("Travel", _("Travel & Events")),
				 ("Shortmov", _("Short Movies")),
				 ("Games", _("Gaming")),
				 ("Comedy", _("Comedy")),
				 ("People", _("People & Blogs")),
				 ("News", _("News & Politics")),
				 ("Entertainment", _("Entertainment")),
				 ("Education", _("Education")),
				 ("Howto", _("Howto & Style")),
				 ("Nonprofit", _("Nonprofits & Activism")),
				 ("Tech", _("Science & Technology"))
				], None)
config.plugins.mytube.search.lr = ConfigSelection(
				[
				 ("au", _("Australia")),
				 ("br", _("Brazil")),
				 ("ca", _("Canada")),
				 ("cz", _("Czech Republic")),
				 ("fr", _("France")),
				 ("de", _("Germany")),
				 ("gb", _("Great Britain")),
				 ("au", _("Australia")),
				 ("nl", _("Holland")),
				 ("hk", _("Hong Kong")),
				 ("in", _("India")),
				 ("ie", _("Ireland")),
				 ("il", _("Israel")),
				 ("it", _("Italy")),
				 ("jp", _("Japan")),
				 ("mx", _("Mexico")),
				 ("nz", _("New Zealand")),
				 ("pl", _("Poland")),
				 ("ru", _("Russia")),
				 ("kr", _("South Korea")),
				 ("es", _("Spain")),
				 ("se", _("Sweden")),
				 ("tw", _("Taiwan")),
				 ("us", _("United States"))
				], "de")

config.plugins.mytube.general = ConfigSubsection()
config.plugins.mytube.general.showHelpOnOpen = ConfigYesNo(default = True)
config.plugins.mytube.general.loadFeedOnOpen = ConfigYesNo(default = True)
config.plugins.mytube.general.startFeed = ConfigSelection(
				[
				 ("top_rated", _("Top rated")),
				], "top_rated")
config.plugins.mytube.general.on_movie_stop = ConfigSelection(default = "ask", choices = [
	("ask", _("Ask user")), ("quit", _("Return to movie list")), ("playnext", _("Play next video")), ("playagain", _("Play video again")) ])

config.plugins.mytube.general.on_exit = ConfigSelection(default = "ask", choices = [
	("ask", _("Ask user")), ("quit", _("Return to movie list"))])

default = resolveFilename(SCOPE_HDD)
tmp = config.movielist.videodirs.value
if default not in tmp:
	tmp.append(default)
config.plugins.mytube.general.videodir = ConfigSelection(default = default, choices = tmp)
config.plugins.mytube.general.history = ConfigText(default="")
config.plugins.mytube.general.clearHistoryOnClose = ConfigYesNo(default = False)
config.plugins.mytube.general.AutoLoadFeeds = ConfigYesNo(default = True)
config.plugins.mytube.general.resetPlayService = ConfigYesNo(default = False)
config.plugins.mytube.general.authenticate = ConfigYesNo(default=False)

class downloadJob(Job):
	def __init__(self, url, file, title):
		Job.__init__(self, title)
		downloadTask(self, url, file)

class downloadTask(Task):
	def __init__(self, job, url, file):
		Task.__init__(self, job, ("download task"))
		self.end = 100
		self.url = url
		self.local = file

	def prepare(self):
		self.error = None

	def run(self, callback):
		self.callback = callback
		self.download = downloadWithProgress(self.url,self.local)
		self.download.addProgress(self.http_progress)
		self.download.start().addCallback(self.http_finished).addErrback(self.http_failed)

	def http_progress(self, recvbytes, totalbytes):
		#print "[http_progress] recvbytes=%d, totalbytes=%d" % (recvbytes, totalbytes)
		self.progress = int(self.end*recvbytes/float(totalbytes))

	def http_finished(self, string=""):
		print "[http_finished]" + str(string)
		Task.processFinished(self, 0)

	def http_failed(self, failure_instance=None, error_message=""):
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			print "[http_failed] " + error_message
			Task.processFinished(self, 1)

class MyTubePlayerMainScreen(Screen, ConfigListScreen):
	Details = {}
	#(entry, Title, Description, TubeID, thumbnail, PublishedDate,Views,duration,ratings )
	skin = """
		<screen name="MyTubePlayerMainScreen" position="center,95"  size="920,570" title="MyTube - Browser">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on"/>
		<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<ePixmap pixmap="skin_default/icons/info.png" position="670,10" size="70,30" alphatest="on"/>
		<ePixmap pixmap="skin_default/icons/menu.png" position="755,10" size="70,30" alphatest="on"/>
		<widget name="VKeyIcon" pixmap="skin_default/icons/text.png" position="840,10" size="70,30" alphatest="on"/>
		<eLabel position="10,50" size="900,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="900,30" scrollbarMode="showNever" transparent="1"/>
		<eLabel position="10,95" size="900,1" backgroundColor="grey"/>
		<widget source="feedlist" render="Listbox" 	position="10,110" size="900,450" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1">
			<convert type="TemplatedMultiContent">
			{"templates":
				{"default": (90,[
						MultiContentEntryPixmapAlphaTest(pos=(2,3),size=(130,94),png=4),# index 4 is the thumbnail
						MultiContentEntryText(pos=(140,2),size=(750,26),font=0,flags=RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP,text=1),# index 1 is the Title
						MultiContentEntryText(pos=(150,35),size=(450,20),font=1,flags=RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP,text=5),# index 5 is the Published Date
						MultiContentEntryText(pos=(150,62),size=(450,20),font=1,flags=RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP,text=6),# index 6 is the Views Count
						MultiContentEntryText(pos=(600,35),size=(280,20),font=1,flags=RT_HALIGN_RIGHT | RT_VALIGN_TOP| RT_WRAP,text=7,color=0xa0a0a0),# index 7 is the duration
						MultiContentEntryText(pos=(600,62),size=(280,20),font=1,flags=RT_HALIGN_RIGHT | RT_VALIGN_TOP| RT_WRAP,text=8,color=0xa0a0a0),# index 8 is the ratingcount
					]),
				"state": (90,[
						MultiContentEntryText(pos=(10,5),size=(880,28),font=2,flags=RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP,text=0),# index 0 is the name
						MultiContentEntryText(pos=(10,37),size=(880,46),font=3,flags=RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP,text=1),# index 2 is the description
					])
				},
				"fonts": [gFont("Regular",23),gFont("Regular",18),gFont("Regular",26),gFont("Regular",20)],
				"itemHeight": 90
			}
			</convert>
		</widget>
		<widget name="HelpWindow" position="360,530" zPosition="1" size="1,1"/>
		<widget name="thumbnail" position="0,0" size="130,94" alphatest="on"/> # fake entry for dynamic thumbnail resizing,currently there is no other way doing this.
		<widget name="ButtonBlue" position="0,0" size="0,0"/>
	</screen>"""

	def __init__(self, session, l2key=None):
		Screen.__init__(self, session)
		self.session = session
		self._userCodeMbx = None
		self.l2key = l2key
		self.l3key = None
		self.skin_path = plugin_path
		self.FeedURL = None
		self.ytfeed = None
		self.currentFeedName = None
		self.videolist = []
		self.queryThread = None
		self.queryRunning = False

		self.video_playlist = []
		self.statuslist = []
		self.mytubeentries = None

		self.thumbnails = []
		self.index = 0
		self.maxentries = 0

		self.screenshotList = []
		self.pixmaps_to_load = []
		self.picloads = {}

		self.oldfeedentrycount = 0
		self.appendEntries = False
		self.lastservice = session.nav.getCurrentlyPlayingServiceReference()
		self.propagateUpDownNormally = True
		self.FirstRun = True
		self.HistoryWindow = None
		self.History = None
		self.searchtext = _("Welcome to the MyTube Youtube Player.\n\nWhile entering your search term(s) you will get suggestions displayed matching your search term.\n\nTo select a suggestion press DOWN on your remote, select the desired result and press OK on your remote to start the search.\n\nPress exit to get back to the input field.")
		self.feedtext = _("Welcome to the MyTube Youtube Player.\n\nUse the Bouqet+ button to navigate to the search field and the Bouqet- to navigate to the video entries.\n\nTo play a movie just press OK on your remote control.\n\nPress info to see the movie description.\n\nPress the Menu button for additional options.\n\nThe Help button shows this help again.")
		self.currList = "configlist"
		self.oldlist = None

		self["feedlist"] = List(self.videolist)
		self["thumbnail"] = Pixmap()
		self["thumbnail"].hide()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Std. Feeds"))
		self["key_yellow"] = Button(_("History"))
		self["ButtonBlue"] = Pixmap()
		self["VKeyIcon"] = Pixmap()
		self["ButtonBlue"].hide()
		self["VKeyIcon"].hide()
		self["result"] = Label("")


		self["searchactions"] = ActionMap(["ShortcutActions", "WizardActions", "HelpActions", "MediaPlayerActions"],
		{
			"ok": self.keyOK,
			"back": self.leavePlayer,
			"red": self.leavePlayer,
			"blue": self.openKeyboard,
			"yellow": self.handleHistory,
			"up": self.keyUp,
			"down": self.handleSuggestions,
			"left": self.keyLeft,
			"right": self.keyRight,
			"prevBouquet": self.switchToFeedList,
			"nextBouquet": self.switchToConfigList,
			"displayHelp": self.handleHelpWindow,
			"menu" : self.handleMenu,
		}, -2)

		self["suggestionactions"] = ActionMap(["ShortcutActions", "WizardActions", "MediaPlayerActions", "HelpActions", "NumberActions"],
		{
			"ok": self.keyOK,
			"back": self.switchToConfigList,
			"red": self.switchToConfigList,
			"nextBouquet": self.switchToConfigList,
			"prevBouquet": self.switchToFeedList,
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
			"0": self.toggleScreenVisibility
		}, -2)


		self["videoactions"] = ActionMap(["ShortcutActions", "WizardActions", "MediaPlayerActions", "MovieSelectionActions", "HelpActions"],
		{
			"ok": self.keyOK,
			"back": self.leavePlayer,
			"red": self.leavePlayer,
			"yellow": self.handleHistory,
			"up": self.keyUp,
			"down": self.keyDown,
			"nextBouquet": self.switchToConfigList,
			"green": self.keyStdFeed,
			"showEventInfo": self.showVideoInfo,
			"displayHelp": self.handleHelpWindow,
			"menu" : self.handleMenu,
		}, -2)

		self["statusactions"] = ActionMap(["ShortcutActions", "WizardActions", "HelpActions", "MediaPlayerActions"],
		{
			"back": self.leavePlayer,
			"red": self.leavePlayer,
			"nextBouquet": self.switchToConfigList,
			"green": self.keyStdFeed,
			"yellow": self.handleHistory,
			"menu": self.handleMenu
		}, -2)

		self["historyactions"] = ActionMap(["ShortcutActions", "WizardActions", "MediaPlayerActions", "MovieSelectionActions", "HelpActions"],
		{
			"ok": self.keyOK,
			"back": self.closeHistory,
			"red": self.closeHistory,
			"yellow": self.handleHistory,
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
		}, -2)

		self["videoactions"].setEnabled(False)
		self["statusactions"].setEnabled(False)
		self["historyactions"].setEnabled(False)

		self.timer_startDownload = eTimer()
		self.timer_startDownload_conn = self.timer_startDownload.timeout.connect(self.downloadThumbnails)
		self.timer_thumbnails = eTimer()
		self.timer_thumbnails_conn = self.timer_thumbnails.timeout.connect(self.updateFeedThumbnails)

		self.SearchConfigEntry = None
		self.searchContextEntries = []
		config.plugins.mytube.search.searchTerm.value = ""
		ConfigListScreen.__init__(self, self.searchContextEntries, session)
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.setWindowTitle)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		del self.timer_startDownload
		del self.timer_thumbnails
		self.Details = {}
		self.session.nav.playService(self.lastservice)
		myTubeService.cancelAuthFlow()

	def layoutFinished(self):
		self.currList = "status"
		current = self["config"].getCurrent()
		if current[1].help_window.instance is not None:
			current[1].help_window.instance.hide()

		l3cert = etpm.getData(eTPM.DT_LEVEL3_CERT)
		if l3cert is None or l3cert is "":
			self["videoactions"].setEnabled(False)
			self["searchactions"].setEnabled(False)
			self["config_actions"].setEnabled(False)
			self["historyactions"].setEnabled(False)
			self["statusactions"].setEnabled(True)
			self.hideSuggestions()
			self.statuslist = []
			self.statuslist.append(( _("Genuine Dreambox validation failed!"), _("Verify your Dreambox authenticity by running the genuine dreambox plugin!" ) ))
			self["feedlist"].style = "state"
			self['feedlist'].setList(self.statuslist)
			return

		self.l3key = validate_cert(l3cert, self.l2key)
		if self.l3key is None:
			print "l3cert invalid"
			return
		rnd = get_rnd()
		if rnd is None:
			print "random error"
			return

		val = etpm.computeSignature(rnd)
		result = decrypt_block(val, self.l3key)

		self.statuslist = []
		if result[80:88] != rnd:
			self.statuslist.append(( _("Genuine Dreambox validation failed!"), _("Verify your Dreambox authenticity by running the genuine dreambox plugin!" ) ))
			self["feedlist"].style = "state"
			self['feedlist'].setList(self.statuslist)
			return

		# we need to login here; startService() is fired too often for external curl
#		self.tryUserLogin()

		self.statuslist.append(( _("Fetching feed entries"), _("Trying to download the Youtube feed entries. Please wait..." ) ))
		self["feedlist"].style = "state"
		self['feedlist'].setList(self.statuslist)
		myTubeService.addReadyCallback(self._onServiceReady)
		if config.plugins.mytube.general.authenticate.value:
			myTubeService.startAuthenticatedService(self._onUserCodeReady)
		else:
			myTubeService.startService()

	def _onServiceReady(self, ready):
		Log.w("%s" %(ready,))
		if self._userCodeMbx:
			self._userCodeMbx.close()
			self._userCodeMbx = None

		if ready:
			if config.plugins.mytube.general.loadFeedOnOpen.value:
				self.getFeed()
				self.setState('getFeed')
			else:
				self.setState('byPass')

	def setWindowTitle(self):
		self.setTitle(_("MyTubePlayer"))

	def createSetup(self):
		self.searchContextEntries = []
		self.SearchConfigEntry = getConfigListEntry(_("Search Term(s)"), config.plugins.mytube.search.searchTerm)
		self.searchContextEntries.append(self.SearchConfigEntry)
		self["config"].list = self.searchContextEntries
		self["config"].l.setList(self.searchContextEntries)

	def setState(self,status = None):
		if status:
			self.currList = "status"
			self["videoactions"].setEnabled(False)
			self["searchactions"].setEnabled(False)
			self["config_actions"].setEnabled(False)
			self["historyactions"].setEnabled(False)
			self["statusactions"].setEnabled(True)
			self["ButtonBlue"].hide()
			self["VKeyIcon"].hide()
			self.statuslist = []
			self.hideSuggestions()
			result = None
			if self.l3key is not None:
				rnd = get_rnd()
				if rnd is None:
					return
				val = etpm.computeSignature(rnd)
				result = decrypt_block(val, self.l3key)
			if not result or result[80:88] != rnd:
				self["key_green"].show()
				self.statuslist.append(( _("Genuine Dreambox validation failed!"), _("Verify your Dreambox authenticity by running the genuine dreambox plugin!" ) ))
				self["feedlist"].style = "state"
				self['feedlist'].setList(self.statuslist)
				return

			print "Genuine Dreambox validation passed"

			if self.HistoryWindow is not None:
				self.HistoryWindow.deactivate()
				self.HistoryWindow.instance.hide()
			if status == 'getFeed':
				self.statuslist.append(( _("Fetching feed entries"), _("Trying to download the Youtube feed entries. Please wait..." ) ))
			elif status == 'getSearchFeed':
				self.statuslist.append(( _("Fetching search entries"), _("Trying to download the Youtube search results. Please wait..." ) ))
			elif status == 'Error':
				self.statuslist.append(( _("An error occured."), _("There was an error getting the feed entries. Please try again." ) ))
			elif status == 'noVideos':
				self["key_green"].show()
				self.statuslist.append(( _("No videos to display"), _("Please select a standard feed or try searching for videos." ) ))
			elif status == 'byPass':
				self.statuslist.append(( _("Not fetching feed entries"), _("Please enter your search term." ) ))
				self["feedlist"].style = "state"
				self['feedlist'].setList(self.statuslist)
				self.switchToConfigList()
			self["feedlist"].style = "state"
			self['feedlist'].setList(self.statuslist)


	def _onUserCodeReady(self, userCode):
		self._userCodeMbx = self.session.open(MessageBox, str(_("Please visit: %s\nAnd enter: %s") % (userCode.verification_url, userCode.user_code)), type=MessageBox.TYPE_INFO, title=_("Authentication awaiting"))
		Log.w(userCode)

	def handleHelpWindow(self):
		print "[handleHelpWindow]"
		if self.currList == "configlist":
			self.hideSuggestions()
			self.session.openWithCallback(self.ScreenClosed, MyTubeVideoHelpScreen, self.skin_path, wantedinfo = self.searchtext, wantedtitle = _("MyTubePlayer Help") )
		elif self.currList == "feedlist":
			self.session.openWithCallback(self.ScreenClosed, MyTubeVideoHelpScreen, self.skin_path, wantedinfo = self.feedtext, wantedtitle = _("MyTubePlayer Help") )

	def handleFirstHelpWindow(self):
		print "[handleFirstHelpWindow]"
		if config.plugins.mytube.general.showHelpOnOpen.value is True:
			if self.currList == "configlist":
				self.hideSuggestions()
				self.session.openWithCallback(self.firstRunHelpClosed, MyTubeVideoHelpScreen, self.skin_path,wantedinfo = self.feedtext, wantedtitle = _("MyTubePlayer Help") )
		else:
			self.FirstRun = False

	def firstRunHelpClosed(self):
		if self.FirstRun == True:
			self.FirstRun = False
			self.switchToConfigList()

	def handleMenu(self):
		if self.currList == "configlist" or self.currList == "status":
			menulist = (
					(_("MyTube Settings"), "settings"),
				)
			self.hideSuggestions()
			self.session.openWithCallback(self.openMenu, ChoiceBox, title=_("Select your choice."), list = menulist)

		elif self.currList == "feedlist":
			menulist = [(_("MyTube Settings"), "settings")]
			menulist.extend((
					(_("Related videos"), "related"),
					(_("Channel videos"), "channel_videos"),
				))
			
			if myTubeService.is_auth() is True:
				menulist.extend((
						(_("Subscribe to channel"), "subscribe"),
						(_("Add to favorites"), "favorite"),
					))				
			
			if config.usage.setup_level.index >= 2: # expert+
				menulist.extend((
					(_("Download Video"), "download"),
					(_("View active downloads"), "downview")
				))

			self.hideSuggestions()
			self.session.openWithCallback(self.openMenu, ChoiceBox, title=_("Select your choice."), list = menulist)

	def openMenu(self, answer):
		answer = answer and answer[1]
		if answer == "settings":
			print "settings selected"
			self.session.openWithCallback(self.ScreenClosed,MyTubeSettingsScreen, self.skin_path )
		elif answer == "related":
			current = self["feedlist"].getCurrent()[0]
			self.setState('getFeed')
			self.getRelatedVideos(current)
		elif answer == "channel_videos":
			current = self["feedlist"].getCurrent()[0]
			self.setState('getFeed')
			self.getChannelVideos(current)
		elif answer == "subscribe":
			current = self["feedlist"].getCurrent()[0]
			self.session.open(MessageBox, current.subscribeToUser(), MessageBox.TYPE_INFO)
		elif answer == "favorite":
			current = self["feedlist"].getCurrent()[0]
			self.session.open(MessageBox, current.addToFavorites(), MessageBox.TYPE_INFO)
					
		elif answer == "response":
			current = self["feedlist"].getCurrent()[0]
			self.setState('getFeed')
			self.getResponseVideos(current)
		elif answer == "download":
			if self.currList == "feedlist":
				current = self[self.currList].getCurrent()
				if current:
					video = current[0]
					if video:
						myurl = video.url
						filename = str(config.plugins.mytube.general.videodir.value)+ str(video.title) + '.mp4'
						job_manager.AddJob(downloadJob(myurl,filename, str(video.title)))
		elif answer == "downview":
			self.tasklist = []
			for job in job_manager.getPendingJobs():
				self.tasklist.append((job,job.name,job.getStatustext(),int(100*job.progress/float(job.end)) ,str(100*job.progress/float(job.end)) + "%" ))
			self.session.open(MyTubeTasksScreen, self.skin_path , self.tasklist)
		elif answer == None:
			self.ScreenClosed()

	def openKeyboard(self):
		self.hideSuggestions()
		self.session.openWithCallback(self.SearchEntryCallback, VirtualKeyBoard, title = (_("Enter your search term(s)")), text = config.plugins.mytube.search.searchTerm.value)

	def ScreenClosed(self):
		print "ScreenCLosed, restoring old window state"
		if self.currList == "historylist":
			if self.HistoryWindow.status() is False:
				self.HistoryWindow.activate()
				self.HistoryWindow.instance.show()
		elif self.currList == "configlist":
			self.switchToConfigList()
			ConfigListScreen.keyOK(self)
		elif self.currList == "feedlist":
			self.switchToFeedList()

	def SearchEntryCallback(self, callback = None):
		if callback is not None and len(callback):
			config.plugins.mytube.search.searchTerm.value = callback
			ConfigListScreen.keyOK(self)
			self["config"].getCurrent()[1].getSuggestions()
		current = self["config"].getCurrent()
		if current[1].help_window.instance is not None:
			current[1].help_window.instance.show()
		if current[1].suggestionsWindow.instance is not None:
			current[1].suggestionsWindow.instance.show()
		self.propagateUpDownNormally = True

	def openStandardFeedClosed(self, answer):
		answer = answer and answer[1]
		if answer is not None:
			self.setState('getFeed')
			self.appendEntries = False
			self.getFeed(videoCategoryId=answer)

	def handleLeave(self, how):
		self.is_closing = True
		if how == "ask":
			if self.currList == "configlist":
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue"),
					(_("No, but switch to video entries."), "switch2feed")
				)
			else:
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue"),
					(_("No, but switch to video search."), "switch2search")
				)
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Really quit MyTube Player?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		print "leavePlayer"
		if self.HistoryWindow is not None:
			self.HistoryWindow.deactivate()
			self.HistoryWindow.instance.hide()
		if self.currList == "configlist":
			current = self["config"].getCurrent()
			if current[1].suggestionsWindow.activeState is True:
				self.propagateUpDownNormally = True
				current[1].deactivateSuggestionList()
				self["config"].invalidateCurrent()
			else:
				self.hideSuggestions()
				self.handleLeave(config.plugins.mytube.general.on_exit.value)
		else:
			self.hideSuggestions()
			self.handleLeave(config.plugins.mytube.general.on_exit.value)

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer == "quit":
			self.doQuit()
		elif answer == "continue":
			if self.currList == "historylist":
				if self.HistoryWindow.status() is False:
					self.HistoryWindow.activate()
					self.HistoryWindow.instance.show()
			elif self.currList == "configlist":
				self.switchToConfigList()
			elif self.currList == "feedlist":
				self.switchToFeedList()
		elif answer == "switch2feed":
			self.switchToFeedList()
		elif answer == "switch2search":
			self.switchToConfigList()
		elif answer == None:
			if self.currList == "historylist":
				if self.HistoryWindow.status() is False:
					self.HistoryWindow.activate()
					self.HistoryWindow.instance.show()
			elif self.currList == "configlist":
				self.switchToConfigList()
			elif self.currList == "feedlist":
				self.switchToFeedList()

	def doQuit(self):
		myTubeService.onReady.remove(self._onServiceReady)

		if self["config"].getCurrent()[1].suggestionsWindow is not None:
			self.session.deleteDialog(self["config"].getCurrent()[1].suggestionsWindow)
		if self.HistoryWindow is not None:
			self.session.deleteDialog(self.HistoryWindow)
		if config.plugins.mytube.general.showHelpOnOpen.value is True:
			config.plugins.mytube.general.showHelpOnOpen.value = False
			config.plugins.mytube.general.showHelpOnOpen.save()
		if not config.plugins.mytube.general.clearHistoryOnClose.value:
			if self.History and len(self.History):
				config.plugins.mytube.general.history.value = ",".join(self.History)
		else:
			config.plugins.mytube.general.history.value = ""
		config.plugins.mytube.general.history.save()
		config.plugins.mytube.general.save()
		config.plugins.mytube.save()
		self.cancelThread()
		self.close()

	def keyOK(self):
		print "self.currList im KeyOK",self.currList
		if self.currList == "configlist" or self.currList == "suggestionslist":
			self["config"].invalidateCurrent()
			if config.plugins.mytube.search.searchTerm.value != "":
				self.add2History()
				searchTerm = config.plugins.mytube.search.searchTerm.value
				print "Search searchcontext",searchTerm
				if isinstance(self["config"].getCurrent()[1], ConfigTextWithGoogleSuggestions) and not self.propagateUpDownNormally:
					self.propagateUpDownNormally = True
					self["config"].getCurrent()[1].deactivateSuggestionList()
				self.setState('getSearchFeed')
				self.runSearch(searchTerm)
		elif self.currList == "feedlist":
			current = self[self.currList].getCurrent()
			if current:
				Log.d(current)
				video = current[0]
				if video is not None:
					hasUriResolver = False
					try:
						from enigma import eUriResolver
						hasUriResolver = True
					except:
						pass
					if hasUriResolver:
						uri = "yt://%s" %(video.id,)
						myreference = eServiceReference(eServiceReference.idURI,0,uri)
						myreference.setName(video.title)
						self.session.openWithCallback(self.onPlayerClosed, MyTubePlayer, myreference, self.lastservice, infoCallback = self.showVideoInfo, nextCallback = self.getNextEntry, prevCallback = self.getPrevEntry )
					else:
						myurl = video.url
						print "Playing URL",myurl
						if myurl is not None:
							myreference = eServiceReference(4097,0,myurl)
							myreference.setName(video.title)
							self.session.openWithCallback(self.onPlayerClosed, MyTubePlayer, myreference, self.lastservice, infoCallback = self.showVideoInfo, nextCallback = self.getNextEntry, prevCallback = self.getPrevEntry )
						else:
							self.session.open(MessageBox, _("Sorry, video is not available!"), MessageBox.TYPE_INFO)
		elif self.currList == "historylist":
			if self.HistoryWindow is not None:
				config.plugins.mytube.search.searchTerm.value = self.HistoryWindow.getSelection()
			self["config"].invalidateCurrent()
			if config.plugins.mytube.search.searchTerm.value != "":
				searchTerm = config.plugins.mytube.search.searchTerm.value
				print "Search searchcontext",searchTerm
				self.setState('getSearchFeed')
				self.runSearch(searchTerm)

	def onPlayerClosed(self):
		if config.plugins.mytube.general.resetPlayService.value:
			self.session.nav.playService(self.lastservice)

	def toggleScreenVisibility(self):
		if self.shown is True:
			self.hide()
		else:
			self.show()

	def keyUp(self):
		print "self.currList im KeyUp",self.currList
		if self.currList == "suggestionslist":
			if config.plugins.mytube.search.searchTerm.value != "":
				if not self.propagateUpDownNormally:
					self["config"].getCurrent()[1].suggestionListUp()
					self["config"].invalidateCurrent()
		elif self.currList == "feedlist":
			self[self.currList].selectPrevious()
		elif self.currList == "historylist":
			if self.HistoryWindow and self.HistoryWindow.shown:
				self.HistoryWindow.up()

	def keyDown(self):
		print "self.currList im KeyDown",self.currList
		if self.currList == "suggestionslist":
			if config.plugins.mytube.search.searchTerm.value != "":
				if not self.propagateUpDownNormally:
					self["config"].getCurrent()[1].suggestionListDown()
					self["config"].invalidateCurrent()
		elif self.currList == "feedlist":
			print self[self.currList].count()
			print self[self.currList].index
			if self[self.currList].index == self[self.currList].count()-1 and myTubeService.hasNextPage():
				# load new feeds on last selected item
				if config.plugins.mytube.general.AutoLoadFeeds.value is False:
					self.session.openWithCallback(self.getNextEntries, MessageBox, _("Do you want to see more entries?"))
				else:
					self.getNextEntries(True)
			else:
				self[self.currList].selectNext()
		elif self.currList == "historylist":
			if self.HistoryWindow is not None and self.HistoryWindow.shown:
				self.HistoryWindow.down()
	def keyRight(self):
		print "self.currList im KeyRight",self.currList
		if self.propagateUpDownNormally:
			ConfigListScreen.keyRight(self)
		else:
			if self.currList == "suggestionslist":
				if config.plugins.mytube.search.searchTerm.value != "":
					self["config"].getCurrent()[1].suggestionListPageDown()
					self["config"].invalidateCurrent()
			elif self.currList == "historylist":
				if self.HistoryWindow is not None and self.HistoryWindow.shown:
					self.HistoryWindow.pageDown()

	def keyLeft(self):
		print "self.currList im kEyLeft",self.currList
		if self.propagateUpDownNormally:
			ConfigListScreen.keyLeft(self)
		else:
			if self.currList == "suggestionslist":
				if config.plugins.mytube.search.searchTerm.value != "":
					self["config"].getCurrent()[1].suggestionListPageUp()
					self["config"].invalidateCurrent()
			elif self.currList == "historylist":
				if self.HistoryWindow is not None and self.HistoryWindow.shown:
					self.HistoryWindow.pageDown()
	def keyStdFeed(self):
		self.hideSuggestions()
		menulist = []
		for category in myTubeService.getCategories():
			menulist.append((category.title, category.id))
#		if myTubeService.is_auth():
#			menulist.extend((
#				(_("My Subscriptions"), "my_subscriptions"),
#				(_("My Favorites"), "my_favorites"),
#				(_("My History"), "my_history"),
#				(_("My Watch Later"), "my_watch_later"),
#				(_("My Recommendations"), "my_recommendations"),
#				(_("My Uploads"), "my_uploads"),
#			))

		self.session.openWithCallback(self.openStandardFeedClosed, ChoiceBox, title=_("Select new feed to view."), list = menulist)

	def handleSuggestions(self):
		print "handleSuggestions"
		print "self.currList",self.currList
		if self.currList == "configlist":
			self.switchToSuggestionsList()
		elif self.currList == "historylist":
			if self.HistoryWindow is not None and self.HistoryWindow.shown:
				self.HistoryWindow.down()

	def switchToSuggestionsList(self):
		print "switchToSuggestionsList"
		self.currList = "suggestionslist"
		self["ButtonBlue"].hide()
		self["VKeyIcon"].hide()
		self["statusactions"].setEnabled(False)
		self["config_actions"].setEnabled(False)
		self["videoactions"].setEnabled(False)
		self["searchactions"].setEnabled(False)
		self["suggestionactions"].setEnabled(True)
		self["historyactions"].setEnabled(False)
		self["key_green"].hide()
		self.propagateUpDownNormally = False
		self["config"].invalidateCurrent()
		if self.HistoryWindow is not None and self.HistoryWindow.shown:
			self.HistoryWindow.deactivate()
			self.HistoryWindow.instance.hide()

	def switchToConfigList(self):
		print "switchToConfigList"
		self.currList = "configlist"
		self["config_actions"].setEnabled(True)
		self["historyactions"].setEnabled(False)
		self["statusactions"].setEnabled(False)
		self["videoactions"].setEnabled(False)
		self["suggestionactions"].setEnabled(False)
		self["searchactions"].setEnabled(True)
		self["key_green"].hide()
		self["ButtonBlue"].show()
		self["VKeyIcon"].show()
		self["config"].invalidateCurrent()
		helpwindowpos = self["HelpWindow"].getPosition()
		current = self["config"].getCurrent()
		if current[1].help_window.instance is not None:
			current[1].help_window.instance.move(ePoint(helpwindowpos[0],helpwindowpos[1]))
			current[1].help_window.instance.show()
		if current[1].suggestionsWindow.instance is not None:
			current[1].suggestionsWindow.instance.show()
			self["config"].getCurrent()[1].getSuggestions()
		self.propagateUpDownNormally = True
		if self.HistoryWindow is not None and self.HistoryWindow.shown:
			self.HistoryWindow.deactivate()
			self.HistoryWindow.instance.hide()
		if self.FirstRun == True:
			self.handleFirstHelpWindow()

	def switchToFeedList(self, append = False):
		print "switchToFeedList"
		print "switching to feedlist from:",self.currList
		print "len(self.videolist):",len(self.videolist)
		if self.HistoryWindow is not None and self.HistoryWindow.shown:
			self.HistoryWindow.deactivate()
			self.HistoryWindow.instance.hide()
		self.hideSuggestions()
		if len(self.videolist):
			self.currList = "feedlist"
			self["ButtonBlue"].hide()
			self["VKeyIcon"].hide()
			self["videoactions"].setEnabled(True)
			self["suggestionactions"].setEnabled(False)
			self["searchactions"].setEnabled(False)
			self["statusactions"].setEnabled(False)
			self["historyactions"].setEnabled(False)
			self["key_green"].show()
			self["config_actions"].setEnabled(False)
			if not append:
				self[self.currList].setIndex(0)
			self["feedlist"].updateList(self.videolist)
		else:
			self.setState('noVideos')


	def switchToHistory(self):
		print "switchToHistory"
		self.oldlist = self.currList
		self.currList = "historylist"
		print "switchToHistory currentlist",self.currList
		print "switchToHistory oldlist",self.oldlist
		self.hideSuggestions()
		self["ButtonBlue"].hide()
		self["VKeyIcon"].hide()
		self["key_green"].hide()
		self["videoactions"].setEnabled(False)
		self["suggestionactions"].setEnabled(False)
		self["searchactions"].setEnabled(False)
		self["statusactions"].setEnabled(False)
		self["config_actions"].setEnabled(False)
		self["historyactions"].setEnabled(True)
		self.HistoryWindow.activate()
		self.HistoryWindow.instance.show()

	def handleHistory(self):
		if self.HistoryWindow is None:
			self.HistoryWindow = self.session.instantiateDialog(MyTubeHistoryScreen, zPosition=1000)
		if self.currList in ("configlist","feedlist"):
			if self.HistoryWindow.status() is False:
				print "status is FALSE,switchToHistory"
				self.switchToHistory()
		elif self.currList == "historylist":
			self.closeHistory()

	def closeHistory(self):
		print "closeHistory currentlist",self.currList
		print "closeHistory oldlist",self.oldlist
		if self.currList == "historylist":
			if self.HistoryWindow.status() is True:
				print "status is TRUE, closing historyscreen"
				self.HistoryWindow.deactivate()
				self.HistoryWindow.instance.hide()
				if self.oldlist == "configlist":
					self.switchToConfigList()
				elif self.oldlist == "feedlist":
					self.switchToFeedList()

	def add2History(self):
		if self.History is None:
			self.History = config.plugins.mytube.general.history.value.split(',')
		if self.History[0] == '':
			del self.History[0]
		print "self.History im add",self.History
		if config.plugins.mytube.search.searchTerm.value in self.History:
			self.History.remove((config.plugins.mytube.search.searchTerm.value))
		self.History.insert(0,(config.plugins.mytube.search.searchTerm.value))
		if len(self.History) == 30:
			self.History.pop()
		config.plugins.mytube.general.history.value = ",".join(self.History)
		config.plugins.mytube.general.history.save()
		print "configvalue",config.plugins.mytube.general.history.value

	def hideSuggestions(self):
		current = self["config"].getCurrent()
		if current[1].help_window.instance is not None:
			current[1].help_window.instance.hide()
		if current[1].suggestionsWindow.instance is not None:
			current[1].suggestionsWindow.instance.hide()
		self.propagateUpDownNormally = True

	def getFeed(self, chart=None, videoCategoryId=None, ids=[]):
		self.queryStarted()
		self.queryThread = myTubeService.getFeed(callback=self.gotFeed, chart=chart, videoCategoryId=videoCategoryId, ids=ids)

	def getNextEntries(self, result):
		if not result:
			return
		if myTubeService.hasNextPage():
			self.appendEntries = True
			myTubeService.getNextPage()

	def getRelatedVideos(self, video):
		if video:
			self.search(relatedToVideoId=video.id)

	def getChannelVideos(self, video):
		if video:
			self.search(channelId=video.channelId)

	def runSearch(self, searchTerm = None):
		Log.d(searchTerm)
		if searchTerm:
			self.search(searchTerm=searchTerm)

	def search(self, searchTerm=None, relatedToVideoId=None, channelId=None):
		Log.d("searchTerm=%s, relatedToVideoId=%s, channelId=%s" % (searchTerm, relatedToVideoId, channelId))
		self.queryStarted()
		self.appendEntries = False

#		categories = [ config.plugins.mytube.search.categories.value ],

		self.queryThread = myTubeService.search(
					searchTerm=searchTerm,
					orderby=config.plugins.mytube.search.orderBy.value,
					time=config.plugins.mytube.search.time.value,
					lr=config.plugins.mytube.search.lr.value,
					relatedToVideoId=relatedToVideoId,
					channelId=channelId,
					safeSearch=config.plugins.mytube.search.safeSearch.value,
					callback=self.gotSearchFeed)

	def queryStarted(self):
		if self.queryRunning:
			self.cancelThread()
		self.queryRunning = True

	def queryFinished(self):
		self.queryRunning = False

	def cancelThread(self):
		print "[MyTubePlayer] cancelThread"
		if self.queryThread is not None:
			self.queryThread.cancel()
		self.queryFinished()

	def gotFeed(self, success, items, data):
		print "[MyTubePlayer] gotFeed"
		if self.FirstRun:
			self.FirstRun = False
		self.queryFinished()
		if not success:
			self.gotFeedError(items)
		if success and items is not None:
			self.ytfeed = items
		myTubeService.feed = data
		self.buildEntryList()
		text = _("Results: %s - Page: %s " % (str(myTubeService.getTotalResults()), str(myTubeService.getCurrentPage())))
		#text = "TODO" #TODO text
		#auth_username = myTubeService.getAuthedUsername()
		#if auth_username:
		#			text = auth_username + ' - ' + text
		self["result"].setText(text)

	def gotFeedError(self, error):
		print "[MyTubePlayer] gotFeedError"
		self.queryFinished()
		self.setState('Error')

	def gotSearchFeed(self, success, feed, data):
		if self.FirstRun:
			self.FirstRun = False
		self.gotFeed(success, feed, data)

	def buildEntryList(self):
		self.mytubeentries = None
		self.screenshotList = []
		self.maxentries = 0
		self.mytubeentries = self.ytfeed
		self.maxentries = len(self.mytubeentries)-1
		if self.mytubeentries and len(self.mytubeentries):
			if self.appendEntries == False:
				self.videolist = []
				for video in self.mytubeentries:
					video_id = video.id
					thumbnailUrl = None
					thumbnailUrl = video.thumbnailUrl
					if thumbnailUrl is not None:
						self.screenshotList.append((video_id,thumbnailUrl))
					if not self.Details.has_key(video_id):
						self.Details[video_id] = { 'thumbnail': None}
					self.videolist.append(self.buildEntryComponent(video, video_id))
				if len(self.videolist):
					self["feedlist"].style = "default"
					self["feedlist"].disable_callbacks = True
					self["feedlist"].list = self.videolist
					self["feedlist"].disable_callbacks = False
					self["feedlist"].setIndex(0)
					self["feedlist"].setList(self.videolist)
					self["feedlist"].updateList(self.videolist)
					if self.FirstRun and not config.plugins.mytube.general.loadFeedOnOpen.value:
						self.switchToConfigList()
					else:
						self.switchToFeedList()
			else:
				self.oldfeedentrycount = 0 #TODO self["feedlist"].count()
				for video in self.mytubeentries:
					video_id = video.id
					thumbnailUrl = None
					thumbnailUrl = video.thumbnailUrl
					if thumbnailUrl is not None:
						self.screenshotList.append((video_id,thumbnailUrl))
					if not self.Details.has_key(video_id):
						self.Details[video_id] = { 'thumbnail': None}
					self.videolist.append(self.buildEntryComponent(video, video_id))
				if len(self.videolist):
					self["feedlist"].style = "default"
					old_index = self["feedlist"].index
					self["feedlist"].disable_callbacks = True
					self["feedlist"].list = self.videolist
					self["feedlist"].disable_callbacks = False
					self["feedlist"].setList(self.videolist)
					self["feedlist"].setIndex(old_index)
					self["feedlist"].updateList(self.videolist)
					self["feedlist"].selectNext()
					self.switchToFeedList(True)
			if not self.timer_startDownload.isActive():
				print "STARRTDOWNLOADTIMER IM BUILDENTRYLIST"
				self.timer_startDownload.start(5)
		else:
			self.setState('Error')
			pass

	def buildEntryComponent(self, entry,TubeID):
		title = entry.title
		description = entry.description
		myTubeID = TubeID
		publishedDate = entry.publishedDate
		if publishedDate is not "unknown":
			published = publishedDate.split("T")[0]
		else:
			published = "unknown"
		Views = entry.views
		if Views is not "not available":
			views = Views
		else:
			views = "not available"
		duration = entry.duration
		if duration is not 0:
			durationInSecs = int(duration)
			mins = int(durationInSecs / 60)
			secs = durationInSecs - mins * 60
			duration = "%d:%02d" % (mins, secs)
		else:
			duration = "not available"
		likes = entry.likes
		if likes is not "":
			likes = likes
		else:
			likes = ""
		thumbnail = None
		if self.Details[myTubeID]["thumbnail"]:
			thumbnail = self.Details[myTubeID]["thumbnail"]
		return((entry, title, description, myTubeID, thumbnail, _("Added: ") + str(published), _("Views: ") + str(views), _("Duration: ") + str(duration), _("Likes: ") + str(likes) ))

	def getNextEntry(self):
		i = self["feedlist"].getIndex() + 1
		if i < len(self.videolist):
			self["feedlist"].selectNext()
			current = self["feedlist"].getCurrent()
			if current:
				video = current[0]
				if video:
					myurl = video.url
					if myurl is not None:
						print "Got a URL to stream"
						myreference = eServiceReference(4097,0,myurl)
						myreference.setName(video.title)
						return myreference,False
					else:
						print "NoURL im getNextEntry"
						return None,True

		print "no more entries to play"
		return None,False

	def getPrevEntry(self):
		i = self["feedlist"].getIndex() - 1
		if i >= 0:
			self["feedlist"].selectPrevious()
			current = self["feedlist"].getCurrent()
			if current:
				video = current[0]
				if video:
					myurl = video.url
					if myurl is not None:
						print "Got a URL to stream"
						myreference = eServiceReference(4097,0,myurl)
						myreference.setName(video.title)
						return myreference,False
					else:
						return None,True
		return None,False

	def showVideoInfo(self):
		if self.currList == "feedlist":
			self.openInfoScreen()

	def openInfoScreen(self):
		if self.currList == "feedlist":
			current = self[self.currList].getCurrent()
			if current:
				video = current[0]
				if video:
					print "Title im showVideoInfo",video.title
					self.session.open(MyTubeVideoInfoScreen, self.skin_path, video = video )

	def downloadThumbnails(self):
		self.timer_startDownload.stop()
		for entry in self.screenshotList:
			thumbnailUrl = entry[1]
			tubeid = entry[0]
			thumbnailFile = "/tmp/"+str(tubeid)+".jpg"
			if self.Details.has_key(tubeid):
				if self.Details[tubeid]["thumbnail"] is None:
					if thumbnailUrl is not None:
						if tubeid not in self.pixmaps_to_load:
							self.pixmaps_to_load.append(tubeid)
							if (os_path.exists(thumbnailFile) == True):
								self.fetchFinished(False,tubeid)
							else:
								client.downloadPage(thumbnailUrl,thumbnailFile).addCallback(self.fetchFinished,str(tubeid)).addErrback(self.fetchFailed,str(tubeid))
					else:
						if tubeid not in self.pixmaps_to_load:
							self.pixmaps_to_load.append(tubeid)
							self.fetchFinished(False,tubeid, failed = True)

	def fetchFailed(self,string,tubeid):
		print "thumbnail-fetchFailed for: ",tubeid,string.getErrorMessage()
		self.fetchFinished(False,tubeid, failed = True)

	def fetchFinished(self,x,tubeid, failed = False):
		print "thumbnail-fetchFinished for:",tubeid
		self.pixmaps_to_load.remove(tubeid)
		if failed:
			thumbnailFile = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MyTube/plugin.png")
		else:
			thumbnailFile = "/tmp/"+str(tubeid)+".jpg"
		sc = AVSwitch().getFramebufferScale()
		if (os_path.exists(thumbnailFile) == True):
			self.picloads[tubeid] = ePicLoad()
			self.picloads[tubeid].conn = self.picloads[tubeid].PictureData.connect(boundFunction(self.finish_decode, tubeid))
			self.picloads[tubeid].setPara((self["thumbnail"].instance.size().width(), self["thumbnail"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
			self.picloads[tubeid].startDecode(thumbnailFile)
		else:
			self.pixmaps_to_load.append(tubeid)
			self.fetchFinished(False,tubeid, failed = True)

	def finish_decode(self,tubeid,info):
		print "thumbnail finish_decode:", tubeid,info
		ptr = self.picloads[tubeid].getData()
		thumbnailFile = "/tmp/"+str(tubeid)+".jpg"
		if ptr != None:
			if self.Details.has_key(tubeid):
				self.Details[tubeid]["thumbnail"] = ptr
			if (os_path.exists(thumbnailFile) == True):
				os_remove(thumbnailFile)
			del self.picloads[tubeid]
		else:
			del self.picloads[tubeid]
			if self.Details.has_key(tubeid):
				self.Details[tubeid]["thumbnail"] = None
		self.timer_thumbnails.start(1)

	def updateFeedThumbnails(self):
		self.timer_thumbnails.stop()
		if len(self.picloads) != 0:
			self.timer_thumbnails.start(1)
		else:
			idx = 0
			for entry in self.videolist:
				tubeid = entry[3]
				if self.Details.has_key(tubeid):
					if self.Details[tubeid]["thumbnail"] is not None:
						thumbnail = entry[4]
						if thumbnail == None:
							video = entry[0]
							self.videolist[idx] = self.buildEntryComponent(video, tubeid )
				idx += 1
			if self.currList == "feedlist":
				self["feedlist"].updateList(self.videolist)


class MyTubeVideoInfoScreen(Screen):
	skin = """
		<screen name="MyTubeVideoInfoScreen" position="center,120" size="920,520" title="MyTube - Video Info">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="starsbg" position="810,60" size="100,20" zPosition="5" pixmap="~/starsbar_empty.png" alphatest="on"/>
		<widget name="stars" position="810,60" size="100,20" zPosition="6" pixmap="~/starsbar_filled.png" transparent="1"/>
		<eLabel	position="0,49" size="920,1" backgroundColor="grey"/>
		<widget source="infolist" render="Listbox" position="33,56" size="240,180" scrollbarMode="showNever" selectionDisabled="1" transparent="1">
			<convert type="TemplatedMultiContent">
				{"templates":
					{"default": (180,[
						MultiContentEntryPixmapAlphaTest(pos=(0,0),size=(240,180),png=0),# index 0 is the thumbnail
						]),
					"state": (180,[
						MultiContentEntryText(pos=(0,0),size=(240,180),font=0,flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER| RT_WRAP,text=0,color=0xffffff,color_sel=0xffffff,backcolor=0x000000,backcolor_sel=0x000000),# index 0 is the name
						])
					},
					"fonts": [gFont("Regular",20)],
					"itemHeight": 180
				}
			</convert>
		</widget>
		<widget name="author" position="300,60" size="580,25" font="Regular;22"/>
		<widget name="duration" position="300,90" size="580,25" font="Regular;22"/>
		<widget name="published" position="300,120" size="590,25" font="Regular;22"/>
		<widget name="views" position="300,150" size="590,25" font="Regular;22"/>
		<widget name="tags" position="300,180" size="590,50" font="Regular;22"/>
		<eLabel	position="10,245" size="900,1" backgroundColor="grey"/>
		<widget name="detailtext" position="20,255" size="890,270" font="Regular;20"/>
		<widget name="thumbnail" position="0,0" size="240,180" alphatest="on"/> # fake entry for dynamic thumbnail resizing,currently there is no other way doing this.
		<widget name="title" position="0,0" size="0,0"/>
	</screen>"""

	def __init__(self, session, plugin_path, video = None):
		Screen.__init__(self, session)
		self.session = session
		self.skin_path = plugin_path
		self.video = video
		self.infolist = []
		self.thumbnails = []
		self.picloads = {}
		self["title"] = Label()
		self["key_red"] = Button(_("Close"))
		self["thumbnail"] = Pixmap()
		self["thumbnail"].hide()
		self["detailtext"] = ScrollLabel()
		self["starsbg"] = Pixmap()
		self["stars"] = ProgressBar()
		self["duration"] = Label()
		self["channelTitle"] = Label()
		self["author"] = self["channelTitle"] #skincompat
		self["published"] = Label()
		self["views"] = Label()
		self["tags"] = Label()
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions", "MovieSelectionActions"],
		{
			"back": self.close,
			"red": self.close,
			"up": self.pageUp,
			"down":	self.pageDown,
			"left":	self.pageUp,
			"right": self.pageDown,
		}, -2)

		self["infolist"] = List(self.infolist)
		self.timer = eTimer()
		self.timer_conn = self.timer.timeout.connect(self.picloadTimeout)
		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.setWindowTitle)

	def layoutFinished(self):
		self.statuslist = []
		self.statuslist.append(( _("Downloading screenshots. Please wait..." ),_("Downloading screenshots. Please wait..." ) ))
		self["infolist"].style = "state"
		self['infolist'].setList(self.statuslist)
		self.loadPreviewpics()
		if self.video.title is not None:
			self["title"].setText(self.video.title)
		description = None
		if self.video.description is not None:
			self["detailtext"].setText(self.video.description.strip())

		#TODO implement Likes
		self["stars"].hide()
		self["starsbg"].hide()

		if self.video.duration is not 0:
			durationInSecs = int(self.video.duration)
			mins = int(durationInSecs / 60)
			secs = durationInSecs - mins * 60
			duration = "%d:%02d" % (mins, secs)
			self["duration"].setText(_("Duration: ") + str(duration))

		if self.video.channelTitle:
			self["channelTitle"].setText(_("Channel: ") + self.video.channelTitle)

		if self.video.publishedDate is not "unknown":
			self["published"].setText(_("Added: ") + self.video.publishedDate.split("T")[0])

		if self.video.views is not "not available":
			self["views"].setText(_("Views: ") + str(self.video.views))

	def setWindowTitle(self):
		self.setTitle(_("MyTubeVideoInfoScreen"))

	def pageUp(self):
		self["detailtext"].pageUp()

	def pageDown(self):
		self["detailtext"].pageDown()

	def loadPreviewpics(self):
		self.thumbnails = []
		self.mythumbubeentries = None
		self.index = 0
		self.maxentries = 0
		self.picloads = {}
		self.mythumbubeentries = [self.video.thumbnailUrl]
		self.maxentries = len(self.mythumbubeentries)-1
		if self.mythumbubeentries:
			currindex = 0
			for entry in self.mythumbubeentries:
				thumbID = self.video.id + str(currindex)
				thumbnailFile = "/tmp/" + thumbID + ".jpg"
				currPic = [currindex,thumbID,thumbnailFile,None]
				self.thumbnails.append(currPic)
				thumbnailUrl = None
				thumbnailUrl = entry
				if thumbnailUrl is not None:
					client.downloadPage(thumbnailUrl,thumbnailFile).addCallback(self.fetchFinished,currindex,thumbID).addErrback(self.fetchFailed,currindex,thumbID)
				currindex +=1
		else:
			pass

	def fetchFailed(self, string, index, id):
		print "[fetchFailed] for index:" + str(index) + "for ThumbID:" + id + string.getErrorMessage()

	def fetchFinished(self, string, index, id):
		print "[fetchFinished] for index:" + str(index) + " for ThumbID:" + id
		self.decodePic(index)

	def decodePic(self, index):
		sc = AVSwitch().getFramebufferScale()
		self.picloads[index] = ePicLoad()
		self.picloads[index].conn = self.picloads[index].PictureData.connect(boundFunction(self.finish_decode, index))
		for entry in self.thumbnails:
			if entry[0] == index:
				self.index = index
				thumbnailFile = entry[2]
				if (os_path.exists(thumbnailFile) == True):
					print "[decodePic] DECODING THUMBNAIL for INDEX:"+  str(self.index) + "and file: " + thumbnailFile
					self.picloads[index].setPara((self["thumbnail"].instance.size().width(), self["thumbnail"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
					self.picloads[index].startDecode(thumbnailFile)
				else:
					print "[decodePic] Thumbnail file NOT FOUND !!!-->:",thumbnailFile

	def finish_decode(self, picindex = None, picInfo=None):
		print "finish_decode - of INDEX", picindex
		ptr = self.picloads[picindex].getData()
		if ptr != None:
			self.thumbnails[picindex][3] = ptr
			if (os_path.exists(self.thumbnails[picindex][2]) == True):
				print "removing", self.thumbnails[picindex][2]
				os_remove(self.thumbnails[picindex][2])
				del self.picloads[picindex]
				if len(self.picloads) == 0:
					self.timer.startLongTimer(3)

	def picloadTimeout(self):
		self.timer.stop()
		if len(self.picloads) == 0:
				self.buildInfoList()
		else:
			self.timer.startLongTimer(2)

	def buildInfoList(self):
		self.infolist = []
		thumb0 = None
		thumb1 = None
		thumb2 = None
		thumb3 = None
		count = len(self.thumbnails)
		if count > 0:
			thumb0 = self.thumbnails[0][3]
		if count > 1:
			thumb1 = self.thumbnails[1][3]
		if count > 2:
			thumb2 = self.thumbnails[2][3]
		if count > 3:
			thumb3 = self.thumbnails[3][3]
		self.infolist.append(( thumb0, thumb1, thumb2, thumb3))
		if len(self.infolist):
			self["infolist"].style = "default"
			self["infolist"].disable_callbacks = True
			self["infolist"].list = self.infolist
			self["infolist"].disable_callbacks = False
			self["infolist"].setIndex(0)
			self["infolist"].setList(self.infolist)
			self["infolist"].updateList(self.infolist)


class MyTubeVideoHelpScreen(Screen):
	skin = """
		<screen name="MyTubeVideoHelpScreen" position="center,120" size="820,520" title="MyTube - Help">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="detailtext" position="10,60" size="800,450" font="Regular;22" halign="left" valign="top"/>
		<widget name="title" position="0,0" size="0,0"/>
	</screen>"""

	def __init__(self, session, plugin_path, wantedinfo = None, wantedtitle = None):
		Screen.__init__(self, session)
		self.session = session
		self.skin_path = plugin_path
		self.wantedinfo = wantedinfo
		self.wantedtitle = wantedtitle
		self["title"] = Label()
		self["key_red"] = Button(_("Close"))
		self["detailtext"] = ScrollLabel()

		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"back": self.close,
			"red": self.close,
			"up": self.pageUp,
			"down":	self.pageDown,
			"left":	self.pageUp,
			"right": self.pageDown,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.setWindowTitle)

	def layoutFinished(self):
		if self.wantedtitle is None:
			self["title"].setText(_("Help"))
		else:
			self["title"].setText(self.wantedtitle)
		if self.wantedinfo is None:
			self["detailtext"].setText(_("This is the help screen. Feed me with something to display."))
		else:
			self["detailtext"].setText(self.wantedinfo)

	def setWindowTitle(self):
		self.setTitle(_("MyTubeVideohelpScreen"))

	def pageUp(self):
		self["detailtext"].pageUp()

	def pageDown(self):
		self["detailtext"].pageDown()


def MyTubeMain(session, **kwargs):
	l2 = False
	l2cert = etpm.getData(eTPM.DT_LEVEL2_CERT)
	if l2cert is None:
		print "l2cert not found"
		return

	l2key = validate_cert(l2cert, rootkey)
	if l2key is None:
		print "l2cert invalid"
		return
	l2 = True
	if l2:
		session.open(MyTubePlayerMainScreen, l2key)

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return PluginDescriptor(
		name=_("My TubePlayer"),
		description=_("Play YouTube movies"),
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon = "plugin.png", fnc = MyTubeMain)
