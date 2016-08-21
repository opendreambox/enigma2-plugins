from Components.config import config, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.ConfigList import ConfigListScreen

from Screens.LocationBox import MovieLocationBox
from Screens.Screen import Screen

class MyTubeSettingsScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="MyTubeSettingsScreen" position="center,120" size="820,520" title="MyTube - Settings">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
		<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		<widget name="title" position="0,0" size="0,0"/>
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
