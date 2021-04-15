from enigma import eListbox, eListboxPythonMultiContent, gFont, ePicLoad, RT_VALIGN_CENTER, RT_HALIGN_CENTER, RT_WRAP, SCALE_ASPECT
from skin import TemplatedListFonts, loadSkin, componentSizes, ComponentSizes
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Components.ActionMap import ActionMap
from Components.config import config, ConfigText, ConfigSubsection
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryTextAlphaBlend, MultiContentEntryPixmapAlphaBlend
from Plugins.Plugin import PluginDescriptor
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Log import Log

from Twitch import Twitch, TwitchStream, TwitchVideoBase
from TwitchMiddleware import TwitchMiddleware

from twisted.web.client import downloadPage, readBody, Agent, BrowserLikeRedirectAgent, HTTPConnectionPool
from twisted.internet import reactor, ssl
from twisted.internet._sslverify import ClientTLSOptions

PLUGIN_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/TwitchTV")
loadSkin("%s/skin.xml" % (PLUGIN_PATH))

config.plugins.twitchtv = ConfigSubsection()
config.plugins.twitchtv.user = ConfigText(default="", fixed_size=False)

class TwitchInputBox(InputBox):
	pass

class TLSSNIContextFactory(ssl.ClientContextFactory):
	def getContext(self, hostname=None, port=None):
		ctx = ssl.ClientContextFactory.getContext(self)
		ClientTLSOptions(hostname, ctx)
		return ctx

class TwitchStreamGrid(Screen):
	TMP_PREVIEW_FILE_PATH = "/tmp/twitch_channel_preview.jpg"
	SKIN_COMPONENT_KEY = "TwitchStreamGrid"
	SKIN_COMPONENT_HEADER_HEIGHT = "headerHeight"
	SKIN_COMPONENT_FOOTER_HEIGHT = "footerHeight"
	SKIN_COMPONENT_ITEM_PADDING = "itemPadding"

	def __init__(self, session, windowTitle=_("TwitchTV")):
		Screen.__init__(self, session, windowTitle=windowTitle)
		self.skinName = "TwitchStreamGrid"
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self._onOk,
			"cancel": self.close,
			"red": self._onRed,
			"green": self._onGreen,
			"yellow": self._onYellow,
			"blue": self._onBlue,
		}, -1)

		self["key_red"] = StaticText()
		self["key_green"] = StaticText()
		self["key_blue"] = StaticText()
		self["key_yellow"] = StaticText()
		self._setupButtons()

		sizes = componentSizes[TwitchStreamGrid.SKIN_COMPONENT_KEY]
		self._itemWidth = sizes.get(ComponentSizes.ITEM_WIDTH, 280)
		self._itemHeight = sizes.get(ComponentSizes.ITEM_HEIGHT, 162)
		self._bannerHeight = sizes.get(TwitchStreamGrid.SKIN_COMPONENT_HEADER_HEIGHT, 30)
		self._footerHeight = sizes.get(TwitchStreamGrid.SKIN_COMPONENT_FOOTER_HEIGHT, 60)
		self._itemPadding = sizes.get(TwitchStreamGrid.SKIN_COMPONENT_ITEM_PADDING, 5)
		#one-off calculations
		pad = self._itemPadding * 2
		self._contentWidth = self._itemWidth - pad
		self._contentHeight = self._itemHeight - pad
		self._footerOffset = self._itemHeight - self._itemPadding - self._footerHeight

		self._items = []
		self._list = MenuList(self._items, mode=eListbox.layoutGrid, content=eListboxPythonMultiContent, itemWidth=self._itemWidth, itemHeight=self._itemHeight)
		self["list"] = self._list

		tlf = TemplatedListFonts()
		self._list.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self._list.l.setFont(1, gFont(tlf.face(tlf.SMALLER), tlf.size(tlf.SMALL)))
		self._list.l.setBuildFunc(self._buildFunc, True)

		self.twitch = Twitch()
		self.twitchMiddleware = TwitchMiddleware.instance

		self._picload = ePicLoad()
		self._picload.setPara((self._itemWidth, self._itemHeight, self._itemWidth, self._itemHeight, False, 0, '#000000'))
		self._picload_conn = self._picload.PictureData.connect(self._onDefaultPixmapReady)

		agent = Agent(reactor, contextFactory=TLSSNIContextFactory(), pool=HTTPConnectionPool(reactor))
		self._agent = BrowserLikeRedirectAgent(agent)
		self._cachingDeferred = None

		self._loadDefaultPixmap()

		self._pixmapCache = {}
		self._currentEntry = 0
		self._endEntry = 0
		self.onLayoutFinish.append(self._onLayoutFinish)
		self.onClose.append(self.__onClose)

	def __onClose(self):
		if self._cachingDeferred:
			Log.w("Cancelling pending image download...")
			self._cachingDeferred.cancel()
		self._picload_conn = None
		self._picload = None

	def _setupButtons(self):
		pass

	def _onLayoutFinish(self):
		self.validateCache(True)

	def reload(self):
		self._items = [("loading",)]
		self._list.setList(self._items)
		self._loadContent()

	def _onRed(self):
		pass

	def _onGreen(self):
		pass

	def _onYellow(self):
		pass

	def _onBlue(self):
		pass

	def _loadContent(self):
		raise NotImplementedError

	def _getCurrent(self):
		return self._list.getCurrent()[0]
	current = property(_getCurrent)

	def _buildFunc(self, stream, selected):
		raise NotImplementedError

	def _onOk(self):
		raise NotImplementedError

	def goDetails(self):
		stream = self.current
		if stream is None or not isinstance(stream, TwitchVideoBase):
			return
		self.session.open(TwitchChannelDetails, stream=stream)

	def validateCache(self, clear=False):
		if not self._list.instance:
			return
		if clear:
			self._pixmapCache = {}
		self._currentEntry = -1
		self._endEntry = len(self._items) - 1
		self._nextForCache()

	def _nextForCache(self):
		self._currentEntry += 1
		if self._currentEntry > self._endEntry:
			return

		if self._currentEntry < len(self._items):
			item = self._items[self._currentEntry][0]
			Log.d(item.preview)
			self._loadPixmapForCache(self._currentEntry, item.preview)

	def _onDownloadPageResponse(self, response, index, url):
		self._cachingDeferred = readBody(response)
		self._cachingDeferred.addCallbacks(self._onDownloadPageBody, self._errorPixmapForCache, callbackArgs=[index, url])

	def _onDownloadPageBody(self, body, index, url):
		with open(self.TMP_PREVIEW_FILE_PATH, 'w') as f:
			f.write(body)
		self._gotPixmapForCache(index, url, None)

	def _loadPixmapForCache(self, index, url):
		self._cachingDeferred = self._agent.request('GET', url)
		self._cachingDeferred.addCallbacks(self._onDownloadPageResponse, self._errorPixmapForCache, callbackArgs=[index, url])

	def _gotPixmapForCache(self, index, url, data):
		self._cachingDeferred = None
		callback = boundFunction(self._decodedPixmapForCache, index, url)
		self._picload_conn = self._picload.PictureData.connect(callback)
		self._picload.startDecode(self.TMP_PREVIEW_FILE_PATH)

	def _decodedPixmapForCache(self, index, url, picInfo=None):
		Log.d(url)
		self._pixmapCache[url] = self._picload.getData()
		self._list.setList(self._items[:])
		self._nextForCache()

	def _errorPixmapForCache(self, *args):
		Log.w(args)
		self._cachingDeferred = None
		if self._picload:
			self._nextForCache()

	def _onAllStreams(self, streams):
		self._items = []
		for stream in streams:
			self._items.append((stream,))
		self._list.setList(self._items)
		if self._list.instance:
			self.validateCache(True)

	def addToFavs(self):
		stream = self.current
		if stream is None or not isinstance(stream, TwitchVideoBase):
			return
		self.twitchMiddleware.addToFavorites(stream.channel)

	def _loadDefaultPixmap(self, *args):
		self._picload.startDecode(resolveFilename(SCOPE_PLUGINS, "Extensions/TwitchTV/twitch.svg"))

	def _errorDefaultPixmap(self, *args):
		Log.w(args)

	def _onDefaultPixmapReady(self, picInfo=None):
		self._defaultPixmap = self._picload.getData()
		self.reload()

class TwitchLiveStreams(TwitchStreamGrid):
	def __init__(self, session, game=None, windowTitle=_("Live Streams")):
		TwitchStreamGrid.__init__(self, session, windowTitle=windowTitle)
		self.game = game

	def _onRed(self):
		self.goDetails()
	def _onGreen(self):
		self.addToFavs()
	def _onBlue(self):
		self.reload()

	def _setupButtons(self):
		self["key_red"].text = _("Details")
		self["key_green"].text = _("Add to Fav")
		self["key_yellow"].text = ""
		self["key_blue"].text = _("Refresh")

	def _loadContent(self):
		self.twitch.livestreams(self._onAllStreams, (self.game and self.game.name) or None)

	def _buildFunc(self, stream, selected):
		if stream == "loading":
			return [None,
				MultiContentEntryText(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0x000000, backcolor_sel=0x000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=_("Loading...")),
			]

		pixmap = self._pixmapCache.get(stream.preview, self._defaultPixmap)

		content = [stream,
			MultiContentEntryText(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0, text=""),
			MultiContentEntryPixmapAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), png=pixmap, backcolor=0x000000, backcolor_sel=0x000000, scale_flags=SCALE_ASPECT),
			MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._bannerHeight), font=1, backcolor=0x50000000, backcolor_sel=0x50000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=stream.channel.display_name),
			MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._footerOffset), size=(self._contentWidth, self._footerHeight), font=1, backcolor=0x50000000, backcolor_sel=0x50000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER | RT_WRAP, text="plays %s" % (stream.channel.game,)),
		]
		if not selected:
			content.append(MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0x80000000, text=""))
		return content

	def _onOk(self):
		stream = self.current
		if stream is None or not isinstance(stream, TwitchVideoBase):
			return
		self.twitchMiddleware.watchLivestream(self.session, stream.channel)

class TwitchChannelVideos(TwitchStreamGrid):
	TYPE_ARCHIVE = "archive"
	TYPE_HIGHLIGHT = "highlight"
	TYPE_UPLOAD = "upload"

	def __init__(self, session, channel):
		TwitchStreamGrid.__init__(self, session)
		self._channel = channel
		self._vodType = self.TYPE_ARCHIVE
		self._updateTitle()

	def _updateTitle(self):
		vodType = _("Archive")
		if self._vodType == self.TYPE_HIGHLIGHT:
			vodType = _("Highlights")
		elif self._vodType == self.TYPE_UPLOAD:
			vodType = _("Uploads")
		self.setTitle("%s - %s" % (self._channel.display_name, vodType))

	def _setupButtons(self):
		self["key_red"].text = _("Archive")
		self["key_green"].text = _("Highlights")
		self["key_yellow"].text = _("Uploads")
		self["key_blue"].text = ""

	def _onRed(self):
		self._vodType = self.TYPE_ARCHIVE
		self._updateTitle()
		self.reload()

	def _onGreen(self):
		self._vodType = self.TYPE_HIGHLIGHT
		self._updateTitle()
		self.reload()

	def _onYellow(self):
		self._vodType = self.TYPE_UPLOAD
		self._updateTitle()
		self.reload()

	def _loadContent(self):
		self.twitch.videosForChannel(self._channel.id, self._vodType, self._onVODs)

	def _onVODs(self, total, streams):
		self._onAllStreams(streams)

	def _getCurrent(self):
		return self._list.getCurrent()[0]
	current = property(_getCurrent)

	def _buildFunc(self, stream, selected):
		if stream == "loading":
			return [None,
				MultiContentEntryText(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0x000000, backcolor_sel=0x000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=_("Loading...")),
			]

		pixmap = self._pixmapCache.get(stream.preview, self._defaultPixmap)

		content = [stream,
			MultiContentEntryText(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0, text=""),
			MultiContentEntryPixmapAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), png=pixmap, backcolor=0x000000, backcolor_sel=0x000000, scale_flags=SCALE_ASPECT),
			MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._footerOffset), size=(self._contentWidth, self._footerHeight), font=1, backcolor=0x50000000, backcolor_sel=0x50000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER | RT_WRAP, text=stream.title),
		]
		if not selected:
			content.append(MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0x80000000, text=""))
		return content

	def _onOk(self):
		vod = self.current
		if vod is None or not isinstance(vod, TwitchVideoBase):
			return
		self.twitchMiddleware.watchVOD(self.session, vod)

class TwitchChannelDetails(Screen):
	TMP_BANNER_FILE_PATH = "/tmp/twitch_channel_banner.jpg"

	def __init__(self, session, stream=None, channel=None):
		Screen.__init__(self, session, windowTitle=_("TwitchTV - Channel Details"))

		self.twitch = Twitch()
		self.twitchMiddleware = TwitchMiddleware.instance
		self.stream = stream
		self.channel = channel or stream.channel
		self.setTitle(_("TwitchTV - %s") % (self.channel.name,))
		self.is_online = False
		self.is_live = self.stream and self.stream.type == TwitchStream.TYPE_LIVE

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self.close,
			"red": self.addToFav,
			"green": self.startLive,
			"blue": self.getChannelDetails,
			"yellow": self.getChannelVideos
		}, -1)

		self["key_red"] = StaticText(_("Add to Fav"))
		self["key_green"] = StaticText(_("Watch Live"))
		self["key_yellow"] = StaticText(_("Videos"))
		self["key_blue"] = StaticText(_("Refresh"))

		self["channel_name"] = StaticText()
		self["channel_status"] = StaticText()
		self["channel_game"] = StaticText()
		self["channel_viewers"] = StaticText()

		self._banner = Pixmap()
		self["banner"] = self._banner

		self._cachingDeferred = None
		self._picload = ePicLoad()
		self._picload.setPara((1000, 480, 0, 0, False, 0, '#ffff0000'))
		self._picload_conn = self._picload.PictureData.connect(self._onBannerReady)

		if self.channel.banner and self.stream:
			self.showChannelDetails()
		else:
			if self.channel.banner:
				self.checkLiveStream()
			else:
				self.getChannelDetails()

		self.onClose.append(self.__onClose)

	def __onClose(self):
		if self._cachingDeferred:
			Log.w("Cancelling pending image download...")
			self._cachingDeferred.cancel()
		self._picload_conn = None
		self._picload = None

	def addToFav(self):
		self.twitchMiddleware.addToFavorites(self.channel)

	def startLive(self):
		self.twitchMiddleware.watchLivestream(self.session, self.channel)

	def showChannelDetails(self, isvod=False):
		if self.is_live:
			if isvod:
				self["channel_name"].setText(self.channel_name + _(" (Live VOD)"))
			else:
				self["channel_name"].setText(self.channel.display_name)
		else:
			self["channel_name"].setText(self.channel.display_name + " " + _("is currently offline"))
		self["channel_status"].setText(self.channel.status)
		self["channel_game"].setText(self.channel.game)
		if self.stream:
			self["channel_viewers"].setText(_("Viewers: %s") % (self.stream.viewers,))
		else:
			self["channel_viewers"].setText("")

		if self.channel.banner:
			self.getBanner()

	def getBanner(self):
		Log.i(self.channel.banner)
		if self.channel.banner:
			self._cachingDeferred = downloadPage(self.channel.banner, self.TMP_BANNER_FILE_PATH).addCallbacks(self._onBannerLoadFinished, self._onBannerError)

	def _onBannerLoadFinished(self, *args):
		self._cachingDeferred = None
		self._picload.startDecode(self.TMP_BANNER_FILE_PATH)

	def _onBannerError(self, *args):
		self._cachingDeferred = None
		Log.w(args)

	def _onBannerReady(self, info):
		pixmap = self._picload.getData()
		self._banner.setPixmap(pixmap)

	def getChannelDetails(self):
		self["channel_name"].setText("loading ...")
		self["channel_status"].setText("")
		self["channel_game"].setText("")
		self["channel_viewers"].setText("")
		self.twitch.channelDetails(self.channel.id, self._onChannelDetails)

	def _onChannelDetails(self, channel):
		if not channel:
			return
		self.channel = channel
		self.getBanner()
		self.checkLiveStream()

	def checkLiveStream(self):
		self.twitch.liveStreamDetails(self.channel.id, self._onLiveStreamDetails)

	def _onLiveStreamDetails(self, stream):
		isvod = False
		self.is_live = False
		if not stream:
			self["channel_viewers"].setText("")
		else:
			self.is_live = True
			self.stream = stream
			isvod = self.stream.type != TwitchStream.TYPE_LIVE
		self.showChannelDetails(isvod)

	def getChannelVideos(self):
		self.session.open(TwitchChannelVideos, self.channel)

class TwitchChannelList(Screen):
	def __init__(self, session, channels=[], windowTitle=_("Favorites")):
		Screen.__init__(self, session, windowTitle=windowTitle)
		self.twitch = Twitch()
		self.twitchMiddleware = TwitchMiddleware.instance

		self["key_red"] = StaticText(_("Details"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")

		self["list"] = MenuList([])

		self["myActionMap"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.go,
			"cancel": self.close,
			"red": self.goDetails,
			"green": self.addToFav,
			"yellow": self.removeFromFav
		}, -1)
		self._channels = channels
		self.reload()

	def _getCurrentChannel(self):
		channel = self["list"].getCurrent()
		return channel and channel[1]

	currentChannel = property(_getCurrentChannel)

	def reload(self):
		l = []
		channels = self._channels
		if not channels:
			channels = self.twitchMiddleware.favorites
			self["key_green"].text = _("Add")
			self["key_yellow"].text = _("Remove")

		for channel in channels:
			l.append((channel.display_name, channel))
		self["list"].setList(l)

	def go(self):
		if not self.currentChannel:
			return
		self.twitchMiddleware.watchLivestream(self.session, self.currentChannel)

	def goDetails(self):
		if not self.currentChannel:
			return
		self.session.open(TwitchChannelDetails, channel=self.currentChannel)

	def addToFav(self):
		if self._channels:
			return
		self.session.openWithCallback(self.callbackAddToFav, TwitchInputBox, title=_("Which channel do you want to add?"), text="")

	def callbackAddToFav(self, answer):
		if answer is None:
			return
		self.twitch.channelDetails(answer, self.addToFavGetDetails)

	def addToFavGetDetails(self, channel):
		if not channel:
			self.session.toastManager.showToast(_("The channel wasn't found on Twitch"))
			return
		self.twitchMiddleware.addToFavorites(channel)
		self.reload()

	def removeFromFav(self):
		if self._channels:
			return
		if not self.currentChannel:
			return
		boundCallback = boundFunction(self.callbackRemoveFromFav, self.currentChannel)
		self.session.openWithCallback(boundCallback, MessageBox, _("Are you sure to remove %s from your favorites?") % self.currentChannel.display_name)

	def callbackRemoveFromFav(self, channel, answer):
		if not answer:
			return
		self.twitchMiddleware.removeFromFavorites(channel)
		self.reload()

class TwitchGamesGrid(TwitchStreamGrid):
	TMP_PREVIEW_FILE_PATH = "/tmp/twitch_game_cover.jpg"
	SKIN_COMPONENT_KEY = "TwitchGamesGrid"
	SKIN_COMPONENT_HEADER_HEIGHT = "headerHeight"
	SKIN_COMPONENT_FOOTER_HEIGHT = "footerHeight"
	SKIN_COMPONENT_ITEM_PADDING = "itemPadding"

	def __init__(self, session):
		TwitchStreamGrid.__init__(self, session, windowTitle=_("Top Games"))
		self.skinName = "TwitchGameGrid"
		sizes = componentSizes[TwitchGamesGrid.SKIN_COMPONENT_KEY]
		self._itemWidth = sizes.get(ComponentSizes.ITEM_WIDTH, 185)
		self._itemHeight = sizes.get(ComponentSizes.ITEM_HEIGHT, 258)
		self._bannerHeight = sizes.get(TwitchGamesGrid.SKIN_COMPONENT_HEADER_HEIGHT, 30)
		self._footerHeight = sizes.get(TwitchGamesGrid.SKIN_COMPONENT_FOOTER_HEIGHT, 60)
		self._itemPadding = sizes.get(TwitchGamesGrid.SKIN_COMPONENT_ITEM_PADDING, 5)
		#one-off calculations
		pad = self._itemPadding * 2
		self._contentWidth = self._itemWidth - pad
		self._contentHeight = self._itemHeight - pad
		self._footerOffset = self._itemHeight - self._itemPadding - self._footerHeight

		self._items = []
		self._list = MenuList(self._items, mode=eListbox.layoutGrid, content=eListboxPythonMultiContent, itemWidth=self._itemWidth, itemHeight=self._itemHeight)
		self["list"] = self._list

		tlf = TemplatedListFonts()
		self._list.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self._list.l.setFont(1, gFont(tlf.face(tlf.SMALLER), tlf.size(tlf.SMALL)))
		self._list.l.setBuildFunc(self._buildFunc, True)

		self._picload.setPara((self._itemWidth, self._itemHeight, self._itemWidth, self._itemHeight, False, 0, '#000000'))

	def _loadContent(self):
		self.twitch.topGames(self._onAllGames)

	def _onAllGames(self, games):
		self._items = []
		for game in games:
			self._items.append((game,))
		self._list.setList(self._items)
		if self._list.instance:
			self.validateCache(True)

	def _buildFunc(self, game, selected):
		if game == "loading":
			return [None,
				MultiContentEntryText(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0x000000, backcolor_sel=0x000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=_("Loading...")),
			]

		pixmap = self._pixmapCache.get(game.preview, self._defaultPixmap)

		content = [game,
			MultiContentEntryText(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0, text=""),
			MultiContentEntryPixmapAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), png=pixmap, backcolor=0x000000, backcolor_sel=0x000000, scale_flags=SCALE_ASPECT),
			MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._bannerHeight), font=1, backcolor=0x50000000, backcolor_sel=0x50000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text="%s" % (game.viewers,)),
			MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._footerOffset), size=(self._contentWidth, self._footerHeight), font=1, backcolor=0x50000000, backcolor_sel=0x50000000, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER | RT_WRAP, text=game.name),
		]
		if not selected:
			content.append(MultiContentEntryTextAlphaBlend(pos=(self._itemPadding, self._itemPadding), size=(self._contentWidth, self._contentHeight), font=0, backcolor=0x80000000, text=""))
		return content

	def _onOk(self):
		game = self.current
		if not game:
			return
		self.session.open(TwitchLiveStreams, game=game, windowTitle=_("%s - Livestreams") % (game.name,))


class TwitchMain(Screen):
	ITEM_LIVESTREAMS = "livestreams"
	ITEM_TOP_GAMES = "topgames"
	ITEM_FAVORITES = "favorites"
	ITEM_SEARCH_CHANNEL = "search_channel"
	ITEM_FOLLOWED_CHANNELS = "followed_channels"
	ITEM_SETUP = "setup"

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("TwitchTV")

		self._list = MenuList(list)
		self["list"] = self._list
		self.createSetup()

		self.twitch = Twitch()

		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.go,
			"cancel": self.close
		}, -1)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("TwitchTV"))

	def createSetup(self):
		items = [
			(_("Livestreams"), self.ITEM_LIVESTREAMS),
			(_("Top Games"), self.ITEM_TOP_GAMES),
			(_("Favorites"), self.ITEM_FAVORITES),
		]
		if config.plugins.twitchtv.user.value:
			items.append((_("Followed Channels"), self.ITEM_FOLLOWED_CHANNELS))
		items.extend([
			(_("Search for channel"), self.ITEM_SEARCH_CHANNEL),
			(_("Setup"), self.ITEM_SETUP),
		])
		self._list.setList(items)

	def go(self):
		selection = self["list"].getCurrent()
		selection = selection and selection[1]
		if not selection:
			return

		if selection == self.ITEM_LIVESTREAMS:
			self.session.open(TwitchLiveStreams)
		elif selection == self.ITEM_TOP_GAMES:
			self.session.open(TwitchGamesGrid)
		elif selection == self.ITEM_FAVORITES:
			self.session.open(TwitchChannelList)
		elif selection == self.ITEM_SEARCH_CHANNEL:
			self.session.openWithCallback(self.callbackSearchChannel, TwitchInputBox, title=_("Enter the name of the channel you're searching for"), text="")
		elif selection == self.ITEM_FOLLOWED_CHANNELS:
			self.session.toastManager.showToast(_("Loading followed channels for %s") % (config.plugins.twitchtv.user.value,), duration=3)
			self.twitch.followedChannels(config.plugins.twitchtv.user.value, self._onFollowedChannelsResult)
		elif selection == self.ITEM_SETUP:
			self.session.openWithCallback(self.callbackSetupUser, TwitchInputBox, title=_("Enter your twitch user"), text=config.plugins.twitchtv.user.value)

	def callbackSetupUser(self, user):
		Log.w(user)
		config.plugins.twitchtv.user.value = user or ""
		config.plugins.twitchtv.save()
		config.save()
		self.createSetup()

	def callbackSearchChannel(self, needle):
		if not needle:
			return
		boundCallback = boundFunction(self._onSearchChannelResult, needle)
		self.session.toastManager.showToast(_("Searching for channels containing '%s'") % (needle,))
		self.twitch.searchChannel(needle, boundCallback)

	def _onSearchChannelResult(self, needle, channels):
		if channels:
			self.session.open(TwitchChannelList, channels=channels, windowTitle=_("%s results for '%s'") % (len(channels), needle))
		else:
			self.session.toastManager.showToast(_("Nothing found for '%s'...") % (needle,))

	def _onFollowedChannelsResult(self, channels):
		if channels:
			self.session.open(TwitchChannelList, channels=channels, windowTitle=_("%s folllows %s channels") % (config.plugins.twitchtv.user.value, len(channels)))
		else:
			self.session.toastManager.showToast(_("%s does not follow any channel") % (config.plugins.twitchtv.user.value,))

def main(session, **kwargs):
	session.open(TwitchMain)


def Plugins(path, **kwwargs):
	return [PluginDescriptor(name="TwitchTV", description=_("Watch twitch.tv Streams and VODs"), where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)]
