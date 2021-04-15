# GUI (System)
from enigma import getDesktop
# GUI (Screens)
from Screens.WizardLanguage import WizardLanguage
from Screens.Rc import Rc
from AutoTimerEditor import AutoTimerEditorBase, AutoTimerServiceEditor, \
		AutoTimerFilterEditor

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean

# Configuration
from Components.config import getConfigListEntry, KEY_0, KEY_DELETE, \
		KEY_BACKSPACE

# Wizard XML Path
from Tools import Directories

from Logger import doLog

sz_w = getDesktop(0).size().width()

class AutoTimerWizard(WizardLanguage, AutoTimerEditorBase, Rc):
	STEP_ID_BASIC = 2
	STEP_ID_TIMESPAN = 5
	STEP_ID_SERVICES = 7
	STEP_ID_FILTER = 8

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerWizard" position="center,110" size="1800,930" title="Wizard...">
		<eLabel backgroundColor="grey" position="480,80" size="1,840" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" size="300,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="languagetext" position="10,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="300,70" transparent="1" valign="center" zPosition="1" />
		<widget font="Regular;34" halign="right" position="1650,25" render="Label" size="120,40" source="global.CurrentTime">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget font="Regular;34" halign="right" position="1240,25" render="Label" size="400,40" source="global.CurrentTime" >
			<convert type="ClockToText">Date</convert>
		</widget>
		<eLabel backgroundColor="grey" position="10,80" size="1780,1" />
		<widget name="rc" pixmaps="skin_default/rc0.png,skin_default/rc1.png,skin_default/rc2.png" position="100,100" size="256,800" zPosition="1" />
		<widget name="arrowdown" pixmap="skin_default/arrowdown.png" position="-100,-100" size="37,70" zPosition="2" />
		<widget name="arrowdown2" pixmap="skin_default/arrowdown.png" position="-100,-100" size="37,70" zPosition="2" />
		<widget name="arrowup" pixmap="skin_default/arrowup.png" position="-100,-100" size="37,70" zPosition="2" />
		<widget name="arrowup2" pixmap="skin_default/arrowup.png" position="-100,-100" size="37,70" zPosition="2" />
		<widget font="Regular;34" name="text" position="550,160" size="1250,340" />
		<widget enableWrapAround="1" position="660,520" render="Listbox" scrollbarMode="showOnDemand" size="1000,240" source="list">
			<convert type="TemplatedMultiContent">
				{"template":[ MultiContentEntryText(pos=(20,3),size=(960,35),flags=RT_HALIGN_LEFT,text=0) ],
				"fonts":[gFont("Regular",30) ],"itemHeight":40}
			</convert>
		</widget>
		<widget name="HelpWindow" position="780,840" />
		<widget enableWrapAround="1" name="config" position="660,520" scrollbarMode="showOnDemand" size="1000,240" />
		<widget pixmap="Default-FHD/skin_default/icons/text.svg" position="1710,90" render="Pixmap" size="80,40" source="VKeyIcon">
			<convert type="ConditionalShowHide" />
		</widget>
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerWizard" position="center,80" size="1200,610" title="Welcome...">
		<ePixmap pixmap="skin_default/buttons/red.png" position="270,15" size="200,40"  />
		<widget name="languagetext" position="270,15" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
		<widget name="wizard" position="0,3" size="240,605" pixmap="skin_default/wizard.png" />
		<widget name="rc" position="40,60" size="160,500" zPosition="1" pixmaps="skin_default/rc0.png,skin_default/rc1.png,skin_default/rc2.png" />
		<widget name="arrowdown" position="-100,-100" size="37,70" pixmap="skin_default/arrowdown.png" zPosition="2"  />
		<widget name="arrowdown2" position="-100,-100" size="37,70" pixmap="skin_default/arrowdown.png" zPosition="2"  />
		<widget name="arrowup" position="-100,-100" size="37,70" pixmap="skin_default/arrowup.png" zPosition="2"  />
		<widget name="arrowup2" position="-100,-100" size="37,70" pixmap="skin_default/arrowup.png" zPosition="2"  />
		<widget name="text" position="280,70" size="880,350" font="Regular;23"  />
		<widget source="list" render="Listbox" position="280,330" size="880,270" zPosition="1" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1">
			<convert type="TemplatedMultiContent">
				{"template": [ MultiContentEntryText(pos=(10,4),size=(580,22),flags=RT_HALIGN_LEFT,text=0) ],
				"fonts": [gFont("Regular",20)],
				"itemHeight": 30
				}
			</convert>
		</widget>
		<widget name="config" position="280,330" size="880,270" zPosition="2" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1"/>
		<widget source="VKeyIcon" render="Pixmap" position="1110,20" size="70,30" zPosition="1" pixmap="skin_default/icons/text.png" >
			<convert type="ConditionalShowHide" />
		</widget>
		<widget name="HelpWindow" position="453,250" size="1,1" zPosition="1" transparent="1" />
		</screen>"""

	def __init__(self, session, newTimer):
		self.xmlfile = Directories.resolveFilename(Directories.SCOPE_PLUGINS, "Extensions/AutoTimer/autotimerwizard.xml")

		WizardLanguage.__init__(self, session, showSteps=True, showStepSlider=True)
		AutoTimerEditorBase.__init__(self, newTimer)
		Rc.__init__(self)

		self.skinName = ["AutoTimerWizard", "NetworkWizard"]
		self["wizard"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)

		self.doCancel = False
		self.emptyMatch = False
		self.tailingWhitespacesMatch = False

		# We might need to change shown items, so add some notifiers
		self.timespan.addNotifier(self.regenTimespanList, initial_call=False)
		self.generateTimespanList()

		self.servicesDlg = self.session.instantiateDialog(
				AutoTimerServiceEditor,
				self.serviceRestriction, self.services, self.bouquets
		)

		self.filterDlg = self.session.instantiateDialog(
				AutoTimerFilterEditor,
				self.filterSet, self.excludes, self.includes
		)

		self["TextEntryActions"] = ActionMap(["TextEntryActions"],
			{
				"deleteForward": self.deleteForward,
				"deleteBackward": self.deleteBackward
			}, -2
		)

	def getTranslation(self, text):
		return _(text)

	def regenTimespanList(self, *args, **kwargs):
		self.generateTimespanList()
		if self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN:
			self["config"].setList(self.timespanList)

	def generateTimespanList(self):
		self.timespanList = [
			getConfigListEntry(_("Only match during timespan"), self.timespan)
		]

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			self.timespanList.extend([
				getConfigListEntry(_("Begin of timespan"), self.timespanbegin),
				getConfigListEntry(_("End of timespan"), self.timespanend)
			])

	def getConfigList(self):
		if self.currStep == AutoTimerWizard.STEP_ID_BASIC: # Basic
			return [
				getConfigListEntry(_("Enabled"), self.enabled),
				getConfigListEntry(_("Description"), self.name),
				getConfigListEntry(_("Match title"), self.match),
				getConfigListEntry(_("Timer type"), self.justplay),
			]
		elif self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN: # Timespan
			return self.timespanList
		elif self.currStep == AutoTimerWizard.STEP_ID_SERVICES: # Services
			return self.servicesDlg["config"].getList()
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER: # Filters
			return self.filterDlg["config"].getList()
		return []

	def selectionMade(self):
		timer = self.timer
		if self.currStep == AutoTimerWizard.STEP_ID_BASIC: # Basic
			timer.enabled = self.enabled.value
			timer.name = self.name.value.strip() or self.match.value
			timer.match = self.match.value
			timer.justplay = self.justplay.value == "zap"
			self.emptyMatch = not timer.match.strip()
			self.trailingWhitespacesMatch = (timer.match[-1:] == " ")
		elif self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN: # Timespan
			if self.timespan.value:
				start = self.timespanbegin.value
				end = self.timespanend.value
				timer.timespan = (start, end)
			else:
				timer.timespan = None
		elif self.currStep == AutoTimerWizard.STEP_ID_SERVICES: # Services
			self.servicesDlg.refresh()

			if self.servicesDlg.enabled.value:
				timer.services = self.servicesDlg.services[0]
				timer.bouquets = self.servicesDlg.services[1]
			else:
				timer.services = []
				timer.bouquets = []
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER: # Filters
			self.filterDlg.refresh()

			if self.filterDlg.enabled.value:
				timer.includes = self.filterDlg.includes
				timer.excludes = self.filterDlg.excludes
			else:
				timer.includes = []
				timer.excludes = []

	def keyNumberGlobal(self, number):
		if self.currStep == AutoTimerWizard.STEP_ID_BASIC or self.currStep == AutoTimerWizard.STEP_ID_TIMESPAN:
			self["config"].handleKey(KEY_0 + number)
		else:
			WizardLanguage.keyNumberGlobal(self, number)

	def blue(self):
		if self.currStep == AutoTimerWizard.STEP_ID_SERVICES:
			self.servicesDlg.new()
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER:
			self.filterDlg.new()

	def yellow(self):
		if self.currStep == AutoTimerWizard.STEP_ID_SERVICES:
			self.servicesDlg.remove()
		elif self.currStep == AutoTimerWizard.STEP_ID_FILTER:
			self.filterDlg.remove()

	def maybeRemoveWhitespaces(self):
		# XXX: Hack alert
		if self["list"].current[1] == "removeTrailingWhitespaces":
			doLog("Next step would be to remove trailing whitespaces, removing them and redirecting to 'conf2'")
			self.timer.match = self.timer.match.rstrip()
			self.match.value = self.match.value.rstrip()
			self.currStep = self.getStepWithID("conf2")
		self.trailingWhitespacesMatch = False

	def deleteForward(self):
		self["config"].handleKey(KEY_DELETE)

	def deleteBackward(self):
		self["config"].handleKey(KEY_BACKSPACE)

	def exitWizardQuestion(self, ret=False):
		if ret:
			self.doCancel = True
			self.close()

	def cancel(self):
		self.doCancel = True
		self.currStep = len(self.wizard)

	def close(self, *args, **kwargs):
		if self.doCancel:
			WizardLanguage.close(self, None)
		else:
			WizardLanguage.close(self, self.timer)

