from Components.config import config
# GUI (Screens)
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from AutoTimerEditor import AutoTimerEditor, AutoTimerChannelSelection
from AutoTimerImporter import AutoTimerImportSelector
from AutoTimerPreview import AutoTimerPreview
from AutoTimerSettings import AutoTimerSettings
from AutoTimerWizard import AutoTimerWizard

# for showSearchLog
from os import path as os_path, stat as os_stat
from time import localtime, strftime
from ShowLogScreen import ShowLogScreen
import AutoTimerFilterList

# GUI (Components)
from AutoTimerList import AutoTimerList
from Components.ActionMap import HelpableActionMap
from Components.Sources.StaticText import StaticText

class AutoTimerOverviewSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="parent.Title" render="Label" position="6,4" size="120,21" font="Regular;18" />
		<widget source="entry" render="Label" position="6,25" size="120,21" font="Regular;16" />
		<widget source="global.CurrentTime" render="Label" position="56,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)
		self["entry"] = StaticText("")
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)
		self.parent.selectionChanged()

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)

	def selectionChanged(self, text):
		self["entry"].text = text

class AutoTimerOverview(Screen, HelpableScreen):
	"""Overview of AutoTimers"""

	skin = """<screen name="AutoTimerOverview" position="center,120" size="820,520" title="AutoTimer Overview">
			<ePixmap pixmap="skin_default/buttons/green.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="410,5" size="200,40" alphatest="on" />
			<widget source="key_green" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_yellow" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="entries" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="750,15" size="60,30" alphatest="on" />
		</screen>"""

	def __init__(self, session, autotimer):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# Save autotimer
		self.autotimer = autotimer

		self.changed = False

		# Button Labels
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Delete"))
		self["key_blue"] = StaticText(_("Add"))

		# Create List of Timers
		self["entries"] = AutoTimerList(autotimer.getSortedTupleTimerList())
		

		# Summary
		self.onChangedEntry = []
		self["entries"].onSelectionChanged.append(self.selectionChanged)

		# Define Actions
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
				"ok": (self.ok, _("Edit selected AutoTimer")),
				"cancel": (self.cancel, _("Close and forget changes")),
			}
		)

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
			{
				"menu": (self.menu, _("Open Context Menu"))
			}
		)

		self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions",
			{
				"info":   (self.showSearchLog, _("Show last SearchLog")),
			}
		)

		self["InfobarActions"] = HelpableActionMap(self, "InfobarActions",
			{
				"showTv":   (self.showFilterTxt, _("Show AutoTimer FilterTxt")),
			}
		)

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
				"red": self.cancel,
				"green": (self.save, _("Close and save changes")),
				"yellow": (self.remove, _("Remove selected AutoTimer")),
				"blue": (self.add, _("Add new AutoTimer")),
			}
		)

		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.firstExec)

	def showSearchLog(self):
		
		searchlog_txt = ""
		logpath = config.plugins.autotimer.searchlog_path.value
		if logpath == "?likeATlog?":
			logpath = os_path.dirname(config.plugins.autotimer.log_file.value)
		path_search_log = os_path.join(logpath, "autotimer_search.log")
		if os_path.exists(path_search_log):
			self.session.open(ShowLogScreen, path_search_log, _("searchLog"), "","")
		else:
			self.session.open(MessageBox,_("no searchLog found!\n\n so you have no new or modified timer at last autotimer-search."), MessageBox.TYPE_INFO)

	def showFilterTxt(self):
		
		reload(AutoTimerFilterList)
		from AutoTimerFilterList import AutoTimerFilterListOverview
		self.session.open(AutoTimerFilterListOverview)


	def firstExec(self):
		from plugin import autotimerHelp
		if config.plugins.autotimer.show_help.value and autotimerHelp:
			config.plugins.autotimer.show_help.value = False
			config.plugins.autotimer.show_help.save()
			autotimerHelp.open(self.session)

	def setCustomTitle(self):
		from plugin import AUTOTIMER_VERSION
		self.setTitle(_("AutoTimer overview") + " - Version: " + AUTOTIMER_VERSION)

	def createSummary(self):
		return AutoTimerOverviewSummary

	def selectionChanged(self):
		sel = self["entries"].getCurrent()
		text = sel and sel.name or ""
		for x in self.onChangedEntry:
			try:
				x(text)
			except Exception:
				pass

	def add(self):
		newTimer = self.autotimer.defaultTimer.clone()
		newTimer.id = self.autotimer.getUniqueId()

		if config.plugins.autotimer.editor.value == "wizard":
			self.session.openWithCallback(
				self.addCallback,
				AutoTimerWizard,
				newTimer
			)
		else:
			self.session.openWithCallback(
				self.addCallback,
				AutoTimerEditor,
				newTimer
			)

	def editCallback(self, ret):
		if ret:
			self.changed = True
			self.refresh()

	def addCallback(self, ret):
		if ret:
			self.changed = True
			self.autotimer.add(ret)
			self.refresh()

	def importCallback(self, ret):
		if ret:
			self.session.openWithCallback(
				self.addCallback,
				AutoTimerEditor,
				ret
			)

	def refresh(self, res = None):
		# Re-assign List
		cur = self["entries"].getCurrent()
		self["entries"].setList(self.autotimer.getSortedTupleTimerList())
		self["entries"].moveToEntry(cur)

	def ok(self):
		# Edit selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(
				self.editCallback,
				AutoTimerEditor,
				current
			)

	def remove(self):
		# Remove selected Timer
		cur = self["entries"].getCurrent()
		if cur is not None:
			self.session.openWithCallback(
				self.removeCallback,
				MessageBox,
				_("Do you really want to delete %s?") % (cur.name),
			)

	def removeCallback(self, ret):
		cur = self["entries"].getCurrent()
		if ret and cur:
			self.autotimer.remove(cur.id)
			self.refresh()

	def cancel(self):
		if self.changed:
			self.session.openWithCallback(self.cancelConfirm, ChoiceBox, title=_('Really close without saving settings?\nWhat do you want to do?') , list=[(_('close without saving'), 'close'), (_('close with saving and start searching'), 'close_save_start'), (_('only close and save (without searching)'), 'close_save'),(_('cancel'), 'exit'), ])
		else:
			self.close(None)

	def cancelConfirm(self, ret):
		ret = ret and ret[1]
		if ret == 'close':
			# Invalidate config mtime to force re-read on next run
			self.autotimer.configMtime = -1
			# Close and indicated that we canceled by returning None
			self.close(None)
		elif ret == 'close_save_start':
			#close and save with start searching
			self.save()
		elif ret == 'close_save':
			#close and save without searching
			self.save(False)


	def menu(self):
		list = [
			(_("Preview"), "preview"),
			(_("Import existing Timer"), "import"),
			(_("Import from EPG"), "import_epg"),
			(_("Setup"), "setup"),
			(_("Edit new timer defaults"), "defaults"),
			(_("Clone selected timer"), "clone")
		]

		from plugin import autotimerHelp
		if autotimerHelp:
			list.insert(0, (_("Help"), "help"))
			list.insert(1, (_("Frequently asked questions") , "faq"))

		if config.plugins.autotimer.editor.value == "wizard":
			list.append((_("Create a new timer using the classic editor"), "newplain"))
		else:
			list.append((_("Create a new timer using the wizard"), "newwizard"))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = list,
		)

	def menuCallback(self, ret):
		ret = ret and ret[1]
		if ret:
			if ret == "help":
				from plugin import autotimerHelp
				autotimerHelp.open(self.session)
			elif ret == "faq":
				from Plugins.SystemPlugins.MPHelp import PluginHelp, XMLHelpReader
				from Tools.Directories import resolveFilename, SCOPE_PLUGINS
				reader = XMLHelpReader(resolveFilename(SCOPE_PLUGINS, "Extensions/AutoTimer/faq.xml"), translate=_)
				autotimerFaq = PluginHelp(*reader)
				autotimerFaq.open(self.session)
			elif ret == "preview":
				total, new, modified, timers, conflicts, similars = self.autotimer.parseEPG(simulateOnly = True)
				self.session.open(
					AutoTimerPreview,
					timers
				)
			elif ret == "import":
				newTimer = self.autotimer.defaultTimer.clone()
				newTimer.id = self.autotimer.getUniqueId()

				self.session.openWithCallback(
					self.importCallback,
					AutoTimerImportSelector,
					newTimer
				)
			elif ret == "import_epg":
				self.session.openWithCallback(
					self.refresh,
					AutoTimerChannelSelection,
					self.autotimer
				)
			elif ret == "setup":
				self.session.open(
					AutoTimerSettings
				)
			elif ret == "defaults":
				self.session.open(
					AutoTimerEditor,
					self.autotimer.defaultTimer,
					editingDefaults = True
				)
			elif ret == "newwizard":
				newTimer = self.autotimer.defaultTimer.clone()
				newTimer.id = self.autotimer.getUniqueId()

				self.session.openWithCallback(
					self.addCallback, # XXX: we could also use importCallback... dunno what seems more natural
					AutoTimerWizard,
					newTimer
				)
			elif ret == "newplain":
				newTimer = self.autotimer.defaultTimer.clone()
				newTimer.id = self.autotimer.getUniqueId()

				self.session.openWithCallback(
					self.addCallback,
					AutoTimerEditor,
					newTimer
				)
			elif ret == "clone":
				current = self["entries"].getCurrent()
				if current is not None:
					newTimer = current.clone()
					newTimer.id = self.autotimer.getUniqueId()

					self.session.openWithCallback(
						self.addCallback,
						AutoTimerEditor,
						newTimer
					)
				

	def save(self, startSearching=True):
		# Just close here, saving will be done by cb
		if startSearching:
			#close and save with start searching
			self.close(self.session)
		else:
			#close and save without start searching
			self.close(None)

