# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigSelection, getConfigListEntry, NoSave
from Components.Button import Button
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from enigma import getDesktop
from SkipIntroDatabase import SIDatabase
from Plugins.SystemPlugins.Toolkit.NTIVirtualKeyBoard import NTIVirtualKeyBoard

version = "1.1"

sz_w = getDesktop(0).size().width()


class SISetupScreen(ConfigListScreen, Screen):

	if sz_w == 1920:
		skin = """
		<screen name="SISetupScreen" position="center,170" size="1200,820" title="SkipIntro">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="295,70" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="305,5" size="295,70" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="600,5" size="295,70" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="895,5" size="295,70" scale="stretch" alphatest="on" />
			<widget name="key_red" position="10,5" zPosition="1" size="300,70" font="Regular;30" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_green" position="310,5" zPosition="1" size="300,70" font="Regular;30" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_yellow" position="610,5" zPosition="1" size="300,70" font="Regular;30" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_blue" position="910,5" zPosition="1" size="300,70" font="Regular;30" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="config" position="10,90" itemHeight="35" size="1180,540" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="10,650" zPosition="2" size="1180,2" />
			<widget name="help" position="10,655" size="1180,145" font="Regular;32" />
			<eLabel text="MENU" position="1110,770" size="80,35" backgroundColor="#777777" valign="center" halign="center" font="Regular;24"/>
			<eLabel text="HELP" position="1020,770" size="80,35" backgroundColor="#777777" valign="center" halign="center" font="Regular;24"/>
		</screen>"""
	else:
		skin = """
		<screen name="SISetupScreen" position="center,120" size="800,530" title="SkipIntro">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="200,40" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,0" size="200,40" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="400,0" size="200,40" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="600,0" size="200,40" scale="stretch" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_green" position="200,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_yellow" position="400,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_blue" position="600,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="config" position="5,50" itemHeight="30" size="790,390" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,445" zPosition="2" size="800,2" />
			<widget name="help" position="5,450" size="790,65" font="Regular;22" />
			<eLabel text="MENU" position="735,497" size="60,25" backgroundColor="#777777" valign="center" halign="center" font="Regular;18"/>
			<eLabel text="HELP" position="665,497" size="60,25" backgroundColor="#777777" valign="center" halign="center" font="Regular;18"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session
		self.list = []
		self.database = SIDatabase()
		self.database.initialize()
		self.database.beginTransaction()

		ConfigListScreen.__init__(self, self.list, session=session)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Delete"))
		self["key_blue"] = Button(_("Setup"))
		self["help"] = Label("")

		self.itemChanged = False
		self.populateList()
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions", "HelpActions"],
										 {
											 "red": self.cancel,
											 "green": self.save,
											 "yellow": self.delete,
											 "blue": self.setup,
											 "save": self.save,
											 "cancel": self.cancel,
											 "ok": self.save,
											 "menu": self.menu,
											 "displayHelp": self.help,
										 }, -2)

		self.onLayoutFinish.append(self.layoutFinished)
		self["config"].onSelectionChanged.append(self.updateHelp)

	def layoutFinished(self):
		self.setTitle(_("SkipIntro Version %s") % version)

	def populateList(self):
		self.list = []

		skipTimes = self.database.getAllSkipTimes()
		for name, skipTime in skipTimes:
			skipTimeConfig = NoSave(ConfigInteger(default=skipTime / 90000, limits=(0, 3600)))
			self.list.append(getConfigListEntry(name, skipTimeConfig, _("Skip time saved for '%s'") % name))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def delete(self):
		currentSelection = self["config"].getCurrent()
		if currentSelection:
			self.session.openWithCallback(self.deleteCallBack, MessageBox, _("Do you really want to delete this entry?") + "\n'" + currentSelection[0] + "'")

	def deleteCallBack(self, result):
		if result:
			currentSelection = self["config"].getCurrent()
			self.database.removeSkipTime(currentSelection[0])
			self.itemChanged = True
			self.populateList()

	def save(self):
		#save skiptimes to database
		for item in self.list:
			self.database.setSkipTime(item[0], item[1].value * 90000)
		self.database.commit()
		self.close()

	def cancelConfirm(self, result):
		if not result:
			return
		self.database.rollback()
		self.close()

	def cancel(self):
		if self["config"].isChanged() or self.itemChanged:
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Do you really want to close without saving settings?"))
		else:
			self.database.rollback()
			self.close()

	def help(self):
		self.session.open(SIHelpScreen)

	def setup(self):
		self.session.open(SISettingsScreen)

	def menu(self):
		currentSelection = self["config"].getCurrent()
		if not currentSelection:
			return

		list = []
		#list.append(("--", ""))
		list.append((_("Change series name"), "change_series_name"))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title=_('Menu SkipIntro'),
			list=list,
		)

	def menuCallback(self, ret):
		ret = ret and ret[1]
		if ret:
			if ret == "change_series_name":
				currentSelection = self["config"].getCurrent()
				if currentSelection:
					self.session.openWithCallback(
						self.NTIVirtualKeyBoardCallback,
						NTIVirtualKeyBoard,
						title=_("Enter series name"),
						text=currentSelection[0]
						)

	def NTIVirtualKeyBoardCallback(self, ret):
		if ret:
			currentSelection = self["config"].getCurrent()
			if currentSelection:
				self.database.renameSeries(currentSelection[0], ret)
				self.itemChanged = True
				self.populateList()

class SISettingsScreen(ConfigListScreen, Screen):

	if sz_w == 1920:
		skin = """
		<screen name="SISettingsScreen" position="center,170" size="1200,820" title="SkipIntro">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="295,70" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="305,5" size="295,70" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="600,5" size="295,70" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="895,5" size="295,70" scale="stretch" alphatest="on" />
			<widget name="key_red" position="10,5" zPosition="1" size="295,70" font="Regular;30" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_green" position="310,5" zPosition="1" size="300,70" font="Regular;30" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_yellow" position="610,5" zPosition="1" size="300,70" font="Regular;30" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_blue" position="910,5" zPosition="1" size="300,70" font="Regular;30" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="config" position="10,90" itemHeight="35" size="1180,540" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="10,650" zPosition="2" size="1180,2" />
			<widget name="help" position="10,655" size="1180,145" font="Regular;32" />
		</screen>"""
	else:
		skin = """
		<screen name="SISettingsScreen" position="center,120" size="800,530" title="SkipIntro">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="200,40" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,0" size="200,40" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="400,0" size="200,40" scale="stretch" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="600,0" size="200,40" scale="stretch" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_green" position="200,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_yellow" position="400,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_blue" position="600,0" zPosition="1" size="200,40" font="Regular;22" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="config" position="5,50" itemHeight="30" size="790,390" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,445" zPosition="2" size="800,2" />
			<widget name="help" position="5,450" size="790,65" font="Regular;22" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session
		self.list = []

		ConfigListScreen.__init__(self, self.list, session=session)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_(" "))
		self["key_blue"] = Button(_(" "))
		self["help"] = Label("")

		self.populateList()
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
										 {
											 "red": self.keyCancel,
											 "green": self.keySave,
											 "save": self.keySave,
											 "cancel": self.keyCancel,
											 "ok": self.keySave,
										 }, -2)

		self.onLayoutFinish.append(self.layoutFinished)
		self["config"].onSelectionChanged.append(self.updateHelp)

	def layoutFinished(self):
		self.setTitle(_("SkipIntro Version %s") % version)

	def populateList(self):
		self.list = [
			getConfigListEntry(_("Show message when skipping intro"), config.plugins.skipintro.show_skipmsg, _("Displays a message when button '2' is pressed to skip the intro.")),
			getConfigListEntry(_("Show message when playback of recording starts"), config.plugins.skipintro.show_videostartmsg, _("Displays a message when the playback of the recording starts and a skip time has already been saved for this series.")),
			getConfigListEntry(_("Auto-reduce calculated skip time (in seconds)"), config.plugins.skipintro.skiptime_decrease, _("Automatically reduces the skip time by the defined number of seconds when saving the skip time.")),
			getConfigListEntry(_("Pattern for series name (title)"), config.plugins.skipintro.title_pattern, _("Select the title pattern to identify the series from the recording title. If disabled the complete recording title is used.")),
		#self.list.append( getConfigListEntry(_("Identify series with season"), config.plugins.skipintro.save_season, _("Identify the series from the record title with the season. So you can use different skip times with different seasons.")) )
		]
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]


class SIHelpScreen(Screen):

	if sz_w == 1920:
		skin = """
		<screen name="SIHelpScreen" position="center,170" size="1200,820" title="SkipIntro Help">
			<widget name="help" position="20,5" size="1100,780" font="Regular;30" />
		</screen>"""
	else:
		skin = """
		<screen name="SIHelpScreen" position="center,120" size="800,530" title="SkipIntro Help">
			<widget name="help" position="10,5" size="760,500" font="Regular;21" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session

		help_txt = _("==== Remote control button definitions when playing a recording ====\n\n")
		help_txt += _("=== Remote control button 2 ===\n")
		help_txt += _("- skip by a stored skip time or\n")
		help_txt += _("- start timekeeping when no skip time is stored or\n")
		help_txt += _("- stop timekeeping (save without season number)\n\n")
		help_txt += _("=== Remote control button 2 (long press) ===\n")
		help_txt += _("- start timekeeping when skip time is already stored or \n")
		help_txt += _("- stop timekeeping (save with season number)\n\n")
		help_txt += _("Remote control button 8 can be used as an alternative to 2 (long press).\n\n")
		help_txt += _("==== Configuration of title pattern ====\n\n")
		help_txt += _("Pattern stored in '/etc/enigma2/SkipIntro.pattern.json' can be selected in settings")

		self["help"] = ScrollLabel(help_txt)

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
										 {
											 "red": self.close,
											 "cancel": self.close,
											 "ok": self.close,
										 }, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("SkipIntro Version %s - Help") % version)
