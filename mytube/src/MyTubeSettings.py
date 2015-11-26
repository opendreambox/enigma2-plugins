from Components.config import config, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.ConfigList import ConfigListScreen

from Screens.LocationBox import MovieLocationBox
from Screens.Screen import Screen

class MyTubeSettingsScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="MyTubeSettingsScreen" flags="wfNoBorder" position="0,0" size="720,576" title="MyTube - Settings" >
			<ePixmap position="0,0" zPosition="-1" size="720,576" pixmap="~/mytubemain_bg.png" alphatest="on" transparent="1" backgroundColor="transparent"/>
			<widget name="title" position="60,50" size="600,50" zPosition="5" valign="center" halign="left" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" zPosition="2" position="60,120" size="610,370" scrollbarMode="showOnDemand" transparent="1" />

			<ePixmap position="100,500" size="100,40" zPosition="0" pixmap="~/plugin.png" alphatest="on" transparent="1" />
			<ePixmap position="220,500" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="360,500" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="220,500" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="360,500" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, plugin_path):
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.session = session

		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions", "MediaPlayerActions"],
		{
			"ok": self.keyOK,
			"back": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"up": self.keyUp,
			"down": self.keyDown,
			"left": self.keyLeft,
			"right": self.keyRight,
		}, -1)

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Save"))
		self["title"] = Label()

		self._configListEntries = []
		self.ProxyEntry = None
		self._cfgLoadFeedEntry = None
		self._cfgVideoDirname = None
		ConfigListScreen.__init__(self, self._configListEntries, session)
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.setWindowTitle)

	def layoutFinished(self):
		self["title"].setText(_("MyTubePlayer settings"))

	def setWindowTitle(self):
		self.setTitle(_("MyTubePlayer settings"))

	def createSetup(self):
		self._cfgLoadFeedEntry = getConfigListEntry(_("Load feed on startup:"), config.plugins.mytube.general.loadFeedOnOpen)
		self._cfgVideoDirname = getConfigListEntry(_("Download location"), config.plugins.mytube.general.videodir)

		self._configListEntries = [
				getConfigListEntry(_("Display search results by:"), config.plugins.mytube.search.orderBy),
				getConfigListEntry(_("Filter restricted content:"), config.plugins.mytube.search.safeSearch),
				getConfigListEntry(_("Search region:"), config.plugins.mytube.search.lr),
				self._cfgLoadFeedEntry
			]

		if config.plugins.mytube.general.loadFeedOnOpen.value:
			self._configListEntries.append(getConfigListEntry(_("Start with following feed:"), config.plugins.mytube.general.startFeed))

		self._configListEntries.extend([
				getConfigListEntry(_("Videoplayer stop/exit behavior:"), config.plugins.mytube.general.on_movie_stop),
				getConfigListEntry(_("Videobrowser exit behavior:"), config.plugins.mytube.general.on_exit)
			])

		if config.usage.setup_level.index >= 2: # expert+
			self._configListEntries.append(self._cfgVideoDirname)
		self._configListEntries.extend([
				getConfigListEntry(_("Clear history on Exit:"), config.plugins.mytube.general.clearHistoryOnClose),
				getConfigListEntry(_("Auto paginate on last entry:"), config.plugins.mytube.general.AutoLoadFeeds),
				getConfigListEntry(_("Reset tv-screen after playback:"), config.plugins.mytube.general.resetPlayService),
				getConfigListEntry(_("Authenticate with Youtube"), config.plugins.mytube.general.authenticate),
			])
		self["config"].list = self._configListEntries

	def newConfig(self):
		print "newConfig", self["config"].getCurrent()
		if self["config"].getCurrent() == self._cfgLoadFeedEntry:
			self.createSetup()

	def keyOK(self):
		cur = self["config"].getCurrent()
		if config.usage.setup_level.index >= 2 and cur == self._cfgVideoDirname:
			self.session.openWithCallback(
				self.pathSelected,
				MovieLocationBox,
				_("Choose target folder"),
				config.plugins.mytube.general.videodir.value,
				minFree=100 # We require at least 100MB free space
			)
		else:
			self.keySave()

	def pathSelected(self, res):
		if res is not None:
			if config.movielist.videodirs.value != config.plugins.mytube.general.videodir.choices:
				config.plugins.mytube.general.videodir.setChoices(config.movielist.videodirs.value, default=res)
			config.plugins.mytube.general.videodir.value = res

	def keyUp(self):
		self["config"].instance.moveSelection(self["config"].instance.moveUp)

	def keyDown(self):
		self["config"].instance.moveSelection(self["config"].instance.moveDown)

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyCancel(self):
		print "cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keySave(self):
		print "saving"
		for x in self["config"].list:
			x[1].save()
		config.plugins.mytube.save()
		self.close()
