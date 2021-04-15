from __future__ import print_function
# GUI (Screens)
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ConfigList import ConfigListScreen
from Components.config import KEY_OK
from Screens.LocationBox import LocationBox
from EPGRefreshChannelEditor import EPGRefreshServiceEditor

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap, HelpableActionMap
from Screens.HelpMenu import HelpMenu, HelpableScreen
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, getConfigListEntry, configfile, NoSave
from Screens.FixedMenu import FixedMenu
from Tools.BoundFunction import boundFunction

from EPGRefresh import epgrefresh
from Components.SystemInfo import SystemInfo
from Screens.MessageBox import MessageBox

# Error-print
from traceback import print_exc
from sys import stdout
import os

VERSION = "2.3.1"
class EPGHelpContextMenu(FixedMenu):
	HELP_RETURN_MAINHELP = 0
	HELP_RETURN_KEYHELP = 1

	def __init__(self, session):
		menu = [(_("General Help"), boundFunction(self.close, self.HELP_RETURN_MAINHELP)),
			(_("Key Help"), boundFunction(self.close, self.HELP_RETURN_KEYHELP)),
			(_("Cancel"), self.close)]

		FixedMenu.__init__(self, session, _("EPGRefresh Configuration Help"), menu)
		self.skinName = ["EPGRefreshConfigurationHelpContextMenu", "Menu"]

class EPGFunctionMenu(FixedMenu):
	FUNCTION_RETURN_FORCEREFRESH = 0
	FUNCTION_RETURN_STOPREFRESH = 1
	FUNCTION_RETURN_SHOWPENDING = 2
	FUNCTION_RETURN_EPGRESET = 3


	def __init__(self, session):
		if epgrefresh.isRunning():
			menu = [(_("Stop running refresh"), boundFunction(self.close, self.FUNCTION_RETURN_STOPREFRESH)),
				(_("Pending Services"), boundFunction(self.close, self.FUNCTION_RETURN_SHOWPENDING))]
		else:
			if config.plugins.epgrefresh.epgreset.value:
				menu = [(_("Refresh now"), boundFunction(self.close, self.FUNCTION_RETURN_FORCEREFRESH)),
					(_("Reset") + " " + _("EPG.db"), boundFunction(self.close, self.FUNCTION_RETURN_EPGRESET))]
			else:
				menu = [(_("Refresh now"), boundFunction(self.close, self.FUNCTION_RETURN_FORCEREFRESH))]
		menu.append((_("Cancel"), self.close))

		FixedMenu.__init__(self, session, _("EPGRefresh Functions"), menu)
		self.skinName = ["EPGRefreshConfigurationFunctionContextMenu", "Menu"]

class EPGRefreshConfiguration(Screen, HelpableScreen, ConfigListScreen):
	"""Configuration of EPGRefresh"""
        
        skin = """<screen name="EPGRefreshConfiguration" position="center,120" size="820,520" >
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel position="10,50" size="800,1" backgroundColor="grey" />
		<widget name="config" position="10,60" size="800,330" enableWrapAround="1" scrollbarMode="showOnDemand" />
		<eLabel position="10,400" size="800,1" backgroundColor="grey" />
		<widget source="help" render="Label" position="60,410" size="700,100" font="Regular;22" valign="center" halign="center" />
		<ePixmap position="760,490" size="50,25" pixmap="skin_default/buttons/key_info.png" alphatest="on" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.list = []
		# Summary
		self.setup_title = _("EPGRefresh Configuration")
		self.onChangedEntry = []
		
		self.session = session
		
		# Although EPGRefresh keeps services in a Set we prefer a list
		self.services = (
			[x for x in epgrefresh.services[0]],
			[x for x in epgrefresh.services[1]]
		)

		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changed)
		self._getConfig()

		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Functions"))
		self["key_blue"] = StaticText(_("Edit Services"))

		self["help"] = StaticText()

		# Define Actions
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
				"yellow": (self.showFunctionMenu, _("Show more Functions")),
				"blue": (self.editServices, _("Edit Services")),
			}
		)
		self["actions"] = HelpableActionMap(self, "ChannelSelectEPGActions",
			{
				"showEPGList": (self.keyInfo, _("Show last EPGRefresh - Time")),
			}
		)
		self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
			{
				"nextBouquet": (self.pageup, _("Move page up")),
				"prevBouquet": (self.pagedown, _("Move page down")),
			}
		)
		self["actionstmp"] = ActionMap(["HelpActions"],
			{
				"displayHelp": self.showHelp,
			}
		)
		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
			{
				"cancel": (self.keyCancel, _("Close and forget changes")),
				"save": (self.keySave, _("Close and save changes")),
			}
		)
		
		# Trigger change
		self.changed()
		self.needsEnigmaRestart = False
		self.ServicesChanged = False
		
		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.firstExec)
		self["config"].isChanged = self._ConfigisChanged

	def _getConfig(self):
		# Name, configElement, HelpTxt, reloadConfig
		self.list = [] 
		self.list.append(getConfigListEntry(_("Refresh EPG automatically"), config.plugins.epgrefresh.enabled, _("Unless this is enabled, EPGRefresh won't automatically run but needs to be explicitly started by the yellow button in this menu."), True))
		if config.plugins.epgrefresh.enabled.value:
			# temporary until new mode is successfully tested
			self.list.append(getConfigListEntry(_("Use time-based duration to stay on service"), config.plugins.epgrefresh.usetimebased, _("Duration to stay can be automatically detected by enigma2 or manually set by the user"), True))
			if config.plugins.epgrefresh.usetimebased.value:
				self.list.append(getConfigListEntry(_("Duration to stay on service (seconds)"), config.plugins.epgrefresh.interval_seconds, _("This is the duration each service/channel will stay active during a refresh."), False))
			self.list.append(getConfigListEntry(_("EPG refresh auto-start earliest (hh:mm)"), config.plugins.epgrefresh.begin, _("An automated refresh will start after this time of day, but before the time specified in next setting."), False))
			self.list.append(getConfigListEntry(_("EPG refresh auto-start latest (hh:mm)"), config.plugins.epgrefresh.end, _("An automated refresh will start before this time of day, but after the time specified in previous setting."), False))
			self.list.append(getConfigListEntry(_("Delay if not in standby (minutes)"), config.plugins.epgrefresh.delay_standby, _("If the receiver currently isn't in standby, this is the duration which EPGRefresh will wait before retry."), False))
			self.list.append(getConfigListEntry(_("Refresh EPG using"), config.plugins.epgrefresh.adapter, _("If you want to refresh the EPG in background, you can choose the method which best suits your needs here, e.g. hidden, fake reocrding or regular Picture in Picture."), False))
			self.list.append(getConfigListEntry(_("Show Advanced Options"), NoSave(config.plugins.epgrefresh.showadvancedoptions), _("Display more Options"), True))
			if config.plugins.epgrefresh.showadvancedoptions.value:
				if config.ParentalControl.configured.value and config.ParentalControl.servicepinactive.value:
					self.list.append(getConfigListEntry(_("Skip protected Services"), config.plugins.epgrefresh.skipProtectedServices, _("Should protected services be skipped if refresh was started in interactive-mode?"), False))
				self.list.append(getConfigListEntry(_("Show Setup in extension menu"), config.plugins.epgrefresh.show_in_extensionsmenu, _("Enable this to be able to access the EPGRefresh configuration from within the extension menu."), False))
				self.list.append(getConfigListEntry(_("Show 'EPGRefresh Start now' in extension menu"), config.plugins.epgrefresh.show_run_in_extensionsmenu, _("Enable this to be able to start the EPGRefresh from within the extension menu."), False))
				self.list.append(getConfigListEntry(_("Show popup when refresh starts and ends"), config.plugins.epgrefresh.enablemessage, _("This setting controls whether or not an informational message will be shown at start and completion of refresh."), False))
				self.list.append(getConfigListEntry(_("Wake up from standby for EPG refresh"), config.plugins.epgrefresh.wakeup, _("If this is enabled, the plugin will wake up the receiver from standby if possible. Otherwise it needs to be switched on already."), False))
				self.list.append(getConfigListEntry(_("Force scan even if receiver is in use"), config.plugins.epgrefresh.force, _("This setting controls whether or not the refresh will be initiated even though the receiver is active (either not in standby or currently recording)."), False))
				self.list.append(getConfigListEntry(_("After EPG refresh"), config.plugins.epgrefresh.afterevent, _("This setting controls whether the receiver should be set to standby after refresh is completed."), True))
				if config.plugins.epgrefresh.afterevent.value:
					self.list.append(getConfigListEntry(_("Don't shutdown after manual abort of automated refresh"), config.plugins.epgrefresh.dontshutdownonabort, _("Activate this setting to avoid shutdown after manual abort of automated refresh"), False))
				self.list.append(getConfigListEntry(_("Force save EPG.db"), config.plugins.epgrefresh.epgsave, _("If this is enabled, the Plugin save the epg.db /etc/enigma2/epg.db."), False)) 
				self.list.append(getConfigListEntry(_("Reset") + " " + _("EPG.db"), config.plugins.epgrefresh.epgreset, _("If this is enabled, the Plugin shows the Reset EPG.db function."), False)) 
				try:
					# try to import autotimer module to check for its existence
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
		
					self.list.append(getConfigListEntry(_("Inherit Services from AutoTimer"), config.plugins.epgrefresh.inherit_autotimer, _("Extend the list of services to refresh by those your AutoTimers use?"), True))
					self.list.append(getConfigListEntry(_("Run AutoTimer after refresh"), config.plugins.epgrefresh.parse_autotimer, _("After a successful refresh the AutoTimer will automatically search for new matches if this is enabled. The options 'Ask*' has only affect on a manually refresh. If EPG-Refresh was called in background the default-Answer will be executed!"), False))
				except ImportError as ie:
					print("[EPGRefresh] AutoTimer Plugin not installed:", ie)
			
		self["config"].list = self.list
		self["config"].setList(self.list)

	def firstExec(self):
		from plugin import epgrefreshHelp
		if config.plugins.epgrefresh.show_help.value and epgrefreshHelp:
			config.plugins.epgrefresh.show_help.value = False
			config.plugins.epgrefresh.show_help.save()
			epgrefreshHelp.open(self.session)

	def setCustomTitle(self):
		self.setTitle(' '.join((_("EPGRefresh Configuration"), _("Version"), VERSION)))

	# overwrites / extendends
	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self._onKeyChange()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self._onKeyChange()
	
	# overwrite configlist.isChanged
	def _ConfigisChanged(self):
		is_changed = False
		for x in self["config"].list:
			if not x[1].save_disabled:
				is_changed |= x[1].isChanged()
		return is_changed
	
	def isConfigurationChanged(self):
		return self.ServicesChanged or self._ConfigisChanged()
	
	def _onKeyChange(self):
		cur = self["config"].getCurrent()
		if cur and cur[3]:
			self._getConfig()

	def showHelp(self):
		self.session.openWithCallback(self._HelpMenuCallback, EPGHelpContextMenu)

	def _HelpMenuCallback(self, *result):
		if not len(result):
			return
		result = result[0]

		if result == EPGHelpContextMenu.HELP_RETURN_MAINHELP:
			self._showMainHelp()
		else:
			self._showKeyhelp()
	
	def _showMainHelp(self):
		from plugin import epgrefreshHelp
		if epgrefreshHelp:
			epgrefreshHelp.open(self.session)
	
	def _showKeyhelp(self):
		self.session.openWithCallback(self.callHelpAction, HelpMenu, self.helpList)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def showFunctionMenu(self):
		self.session.openWithCallback(self._FunctionMenuCB, EPGFunctionMenu)

	def _FunctionMenuCB(self, *result):
		if not len(result):
			return
		result = result[0]

		try:
			if result == EPGFunctionMenu.FUNCTION_RETURN_FORCEREFRESH:
				self.forceRefresh()
			if result == EPGFunctionMenu.FUNCTION_RETURN_STOPREFRESH:
				self.stopRunningRefresh()
			if result == EPGFunctionMenu.FUNCTION_RETURN_SHOWPENDING:
				self.showPendingServices()
			if result == EPGFunctionMenu.FUNCTION_RETURN_EPGRESET:
				self.resetEPG()
		except:
			print("[EPGRefresh] Error in Function - Call")
			print_exc(file=stdout)
	
	def forceRefresh(self):
		if not epgrefresh.isRefreshAllowed():
			return
	
		self._saveConfiguration()
		epgrefresh.services = (set(self.services[0]), set(self.services[1]))
		epgrefresh.forceRefresh(self.session)
		self.keySave(False)

	def resetEPG(self):
		epgrefresh.resetEPG(self.session)

	def showPendingServices(self):
		epgrefresh.showPendingServices(self.session)
	
	def stopRunningRefresh(self):
		epgrefresh.stopRunningRefresh(self.session)

	def editServices(self):
		self.session.openWithCallback(
			self.editServicesCallback,
			EPGRefreshServiceEditor,
			self.services
		)

	def editServicesCallback(self, ret):
		if ret:
			self.services = ret
			self.ServicesChanged = True

	# for Summary
	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass
	
	# for Summary
	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]

	# for Summary
	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].getText())

	# for Summary
	def createSummary(self):
		return SetupSummary

	def pageup(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pagedown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def keyInfo(self):
		lastscan = config.plugins.epgrefresh.lastscan.value
		if lastscan:
			from Tools.FuzzyDate import FuzzyTime
			scanDate = ', '.join(FuzzyTime(lastscan))
		else:
			scanDate = _("never")

		self.session.open(
				MessageBox,
				_("Last refresh was %s") % (scanDate,),
				type=MessageBox.TYPE_INFO
		)

	def cancelConfirm(self, doCancel):
		if not doCancel:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close(self.session, False)

	def keyCancel(self):
		if self.isConfigurationChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(self.session, False)
	
	def _saveConfiguration(self):
		epgrefresh.services = (set(self.services[0]), set(self.services[1]))
		epgrefresh.saveConfiguration()

		for x in self["config"].list:
			x[1].save()		
		configfile.save()
		
	def keySave(self, doSaveConfiguration=True):
		if self.isConfigurationChanged():
			if not epgrefresh.isRefreshAllowed():
				return
			else:
				epgrefresh.stop()
				if doSaveConfiguration:
					self._saveConfiguration()

		if len(self.services[0]) == 0 and len(self.services[1]) == 0 and config.plugins.epgrefresh.enabled.value:
			self.session.openWithCallback(self.checkAnswer, MessageBox, _("EPGRefresh requires services/bouquets to be configured. Configure now?"), MessageBox.TYPE_YESNO, timeout=0)
		else:					
			self.close(self.session, self.needsEnigmaRestart)

	def checkAnswer(self, answer):
		if answer:
			self.editServices()
		else:		
			self.close(self.session, self.needsEnigmaRestart)


