from enigma import eTimer, ePythonMessagePump
from MyTubeService import GoogleSuggestions
from Screens.Screen import Screen
from Components.config import config, ConfigText
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Sources.List import List
from Components.Task import job_manager
from Tools.Directories import resolveFilename, SCOPE_HDD

from threading import Thread
from ThreadQueue import ThreadQueue

#import urllib
from urllib import FancyURLopener
import json


class MyOpener(FancyURLopener):
	version = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'


class SuggestionsQueryThread(Thread):
	def __init__(self, query, param, callback, errorback):
		Thread.__init__(self)
		self.messagePump = ePythonMessagePump()
		self.messages = ThreadQueue()
		self.query = query
		self.param = param
		self.callback = callback
		self.errorback = errorback
		self.canceled = False
		self.messagePump_conn = self.messagePump.recv_msg.connect(self.finished)

	def cancel(self):
		self.canceled = True

	def run(self):
		if self.param not in (None, ""):
			try:
				suggestions = self.query.getSuggestions(self.param)
				self.messages.push((suggestions, self.callback))
				self.messagePump.send(0)
			except Exception, ex:
				self.messages.push((ex, self.errorback))
				self.messagePump.send(0)

	def finished(self, val):
		if not self.canceled:
			message = self.messages.pop()
			message[1](message[0])


class ConfigTextWithGoogleSuggestions(ConfigText):
	def __init__(self, default="", fixed_size=True, visible_width=False):
		ConfigText.__init__(self, default, fixed_size, visible_width)
		self.suggestions = GoogleSuggestions()
		self.suggestionsThread = None
		self.suggestionsThreadRunning = False
		self.suggestionsListActivated = False

	def prepareSuggestionsThread(self):
		self.suggestions.hl = "en"
		if config.plugins.mytube.search.lr.value is not None:
			self.suggestions.hl = config.plugins.mytube.search.lr.value

	def suggestionsThreadStarted(self):
		if self.suggestionsThreadRunning:
			self.cancelSuggestionsThread()
		self.suggestionsThreadRunning = True

	def suggestionsThreadFinished(self):
		self.suggestionsThreadRunning = False

	def cancelSuggestionsThread(self):
		if self.suggestionsThread is not None:
			self.suggestionsThread.cancel()
		self.suggestionsThreadFinished()

	def propagateSuggestions(self, suggestionsList):
		self.cancelSuggestionsThread()
		print "[MyTube - ConfigTextWithGoogleSuggestions] propagateSuggestions:", suggestionsList
		if self.suggestionsWindow:
			self.suggestionsWindow.update(suggestionsList)

	def gotSuggestionsError(self, val):
		print "[MyTube - ConfigTextWithGoogleSuggestions] gotSuggestionsError:", val

	def getSuggestions(self):
		self.prepareSuggestionsThread()
		self.suggestionsThreadStarted()
		self.suggestionsThread = SuggestionsQueryThread(self.suggestions, self.value, self.propagateSuggestions, self.gotSuggestionsError)
		self.suggestionsThread.start()

	def handleKey(self, key):
		if not self.suggestionsListActivated:
			ConfigText.handleKey(self, key)
			if key in [KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT]:
				self.getSuggestions()

	def onSelect(self, session):
		ConfigText.onSelect(self, session)
		if session is not None:
			self.suggestionsWindow = session.instantiateDialog(MyTubeSuggestionsListScreen, self, zPosition=1000)
			self.suggestionsWindow.deactivate()
			self.suggestionsWindow.hide()
		self.getSuggestions()

	def onDeselect(self, session):
		self.cancelSuggestionsThread()
		ConfigText.onDeselect(self, session)
		if self.suggestionsWindow:
			session.deleteDialog(self.suggestionsWindow)
			self.suggestionsWindow = None

	def suggestionListUp(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.up()

	def suggestionListDown(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.down()

	def suggestionListPageDown(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.pageDown()

	def suggestionListPageUp(self):
		if self.suggestionsWindow.getlistlenght() > 0:
			self.value = self.suggestionsWindow.pageUp()

	def activateSuggestionList(self):
		ret = False
		if self.suggestionsWindow is not None and self.suggestionsWindow.shown:
			self.tmpValue = self.value
			self.value = self.suggestionsWindow.activate()
			self.allmarked = False
			self.suggestionsListActivated = True
			ret = True
		return ret

	def deactivateSuggestionList(self):
		ret = False
		if self.suggestionsWindow is not None:
			self.suggestionsWindow.deactivate()
			self.getSuggestions()
			self.allmarked = True
			self.suggestionsListActivated = False
			ret = True
		return ret

	def cancelSuggestionList(self):
		self.value = self.tmpValue
		return self.deactivateSuggestionList()

	def enableSuggestionSelection(self, value):
		if self.suggestionsWindow is not None:
			self.suggestionsWindow.enableSelection(value)


default = resolveFilename(SCOPE_HDD)
tmp = config.movielist.videodirs.value
if default not in tmp:
	tmp.append(default)


class MyTubeSuggestionsListScreen(Screen):
	skin = """
		<screen name="MyTubeSuggestionsListScreen" position="center,205" size="920,450" zPosition="6" title="MyTube - Search" flags="wfNoBorder">
		<widget source="suggestionslist" render="Listbox" position="10,10" size="900,270" zPosition="2" enableWrapAround="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryText(pos=(5,2),size=(590,26),font=0,flags=RT_HALIGN_LEFT,text=0),# index 0 is the name
				MultiContentEntryText(pos=(610,2),size=(300,26),font=1,flags=RT_HALIGN_RIGHT,text=1),# index 1 are the rtesults
				],
				"fonts": [gFont("Regular",22),gFont("Regular",18)],
				"itemHeight": 30
				}
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session, configTextWithGoogleSuggestion):
		Screen.__init__(self, session)
		self.activeState = False
		self.list = []
		self.suggestlist = []
		self["suggestionslist"] = List(self.list)
		self.configTextWithSuggestion = configTextWithGoogleSuggestion

	def update(self, suggestions):
		if suggestions and len(suggestions) > 0:
			if not self.shown:
				self.show()
			suggestions_tree = json.loads(str(suggestions[20:-1]))
			if suggestions_tree:
				self.list = []
				self.suggestlist = []
				suggested = suggestions_tree[1]
				count = 0
				if suggested:
					suggestrelevance = suggestions_tree[4]["google:suggestrelevance"]
					suggesttype = suggestions_tree[4]["google:suggesttype"]
					for suggest in suggested:
						name = None
						numresults = None
						if suggesttype[count] == u'NAVIGATION':
							count += 1
							continue
						name = str(suggest)
						numresults = suggestrelevance[count]
						if name and numresults:
							self.suggestlist.append((name, numresults))
						count += 1
				"""for suggestion in suggestions_tree.findall("CompleteSuggestion"):
					name = None
					numresults = None
					for subelement in suggestion:
						if subelement.attrib.has_key('data'):
							name = subelement.attrib['data'].encode("UTF-8")
						if subelement.attrib.has_key('int'):
							numresults = subelement.attrib['int']
						if name and numresults:
							self.suggestlist.append((name, numresults ))"""
				if len(self.suggestlist):
					self.suggestlist.sort(key=lambda x: int(x[1]))
					self.suggestlist.reverse()
					for entry in self.suggestlist:
						self.list.append((entry[0], str(entry[1]) + _(" Results")))
					self["suggestionslist"].setList(self.list)
					self["suggestionslist"].setIndex(0)
		else:
			self.hide()

	def getlistlenght(self):
		return len(self.list)

	def up(self):
		print "up"
		if self.list and len(self.list) > 0:
			self["suggestionslist"].selectPrevious()
			return self.getSelection()

	def down(self):
		print "down"
		if self.list and len(self.list) > 0:
			self["suggestionslist"].selectNext()
			return self.getSelection()

	def pageUp(self):
		print "up"
		if self.list and len(self.list) > 0:
			self["suggestionslist"].selectPrevious()
			return self.getSelection()

	def pageDown(self):
		print "down"
		if self.list and len(self.list) > 0:
			self["suggestionslist"].selectNext()
			return self.getSelection()

	def activate(self):
		print "activate"
		self.activeState = True
		return self.getSelection()

	def deactivate(self):
		print "deactivate"
		self.activeState = False
		return self.getSelection()

	def getSelection(self):
		if self["suggestionslist"].getCurrent() is None:
			return None
		print self["suggestionslist"].getCurrent()[0]
		return self["suggestionslist"].getCurrent()[0]

	def enableSelection(self, value):
		self["suggestionslist"].selectionEnabled(value)


class MyTubeTasksScreen(Screen):
	skin = """
		<screen name="MyTubeTasksScreen" position="center,120" size="920,520" title="MyTube - Tasks">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="900,1" backgroundColor="grey"/>
		<widget source="tasklist" render="Listbox" position="10,60" size="900,450" enableWrapAround="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryText(pos=(10,2),size=(420,25),flags=RT_HALIGN_LEFT,text=1),# index 1 is the name
				MultiContentEntryText(pos=(440,2),size=(160,25),flags=RT_HALIGN_RIGHT,text=2),# index 2 is the state
				MultiContentEntryProgress(pos=(630,5),size=(150,20),percent=-3),# index 3 should be progress
				MultiContentEntryText(pos=(790,2),size=(80,25),flags=RT_HALIGN_RIGHT,text=4),# index 4 is the percentage
				],
				"fonts": [gFont("Regular",21)],
				"itemHeight": 30
				}
			</convert>
		</widget>
		<widget name="title" position="0,0" size="0,0"/>
	</screen>"""

	def __init__(self, session, plugin_path, tasklist):
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.session = session
		self.tasklist = tasklist
		self["tasklist"] = List(self.tasklist)

		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions", "MediaPlayerActions"],
		{
			"ok": self.keyOK,
			"back": self.keyCancel,
			"red": self.keyCancel,
		}, -1)

		self["key_red"] = Button(_("Close"))
		self["title"] = Label()

		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.setWindowTitle)
		self.onClose.append(self.__onClose)
		self._searchTimer = eTimer()
		self.__searchTimer_conn = self._searchTimer.timeout.connect(self.TimerFire)

	def __onClose(self):
		del self._searchTimer

	def layoutFinished(self):
		self["title"].setText(_("MyTubePlayer active video downloads"))
		self._searchTimer.startLongTimer(2)

	def TimerFire(self):
		self._searchTimer.stop()
		self.rebuildTaskList()

	def rebuildTaskList(self):
		self.tasklist = []
		for job in job_manager.getPendingJobs():
			self.tasklist.append((job, job.name, job.getStatustext(), int(100 * job.progress / float(job.end)), str(100 * job.progress / float(job.end)) + "%"))
		self['tasklist'].setList(self.tasklist)
		self['tasklist'].updateList(self.tasklist)
		self._searchTimer.startLongTimer(2)

	def setWindowTitle(self):
		self.setTitle(_("MyTubePlayer active video downloads"))

	def keyOK(self):
		current = self["tasklist"].getCurrent()
		print current
		if current:
			job = current[0]
			from Screens.TaskView import JobView
			self.session.openWithCallback(self.JobViewCB, JobView, job)

	def JobViewCB(self, why):
		print "WHY---", why

	def keyCancel(self):
		self.close()

	def keySave(self):
		self.close()


class MyTubeHistoryScreen(Screen):
	skin = """
		<screen name="MyTubeHistoryScreen" position="center,205" size="920,450" zPosition="6" title="MyTube - History" flags="wfNoBorder">
		<widget source="historylist" render="Listbox" position="10,10" size="900,420" zPosition="2" enableWrapAround="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryText(pos=(5,2),size=(900,26),flags=RT_HALIGN_LEFT,text=0),# index 0 is the name
				],
				"fonts": [gFont("Regular",22)],
				"itemHeight": 30
				}
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.historylist = []
		print "self.historylist", self.historylist
		self["historylist"] = List(self.historylist)
		self.activeState = False

	def activate(self):
		print "activate"
		self.activeState = True
		self.history = config.plugins.mytube.general.history.value.split(',')
		if self.history[0] == '':
			del self.history[0]
		print "self.history", self.history
		self.historylist = []
		for entry in self.history:
			self.historylist.append((str(entry),))
		self["historylist"].setList(self.historylist)
		self["historylist"].updateList(self.historylist)

	def deactivate(self):
		print "deactivate"
		self.activeState = False

	def status(self):
		print self.activeState
		return self.activeState

	def getSelection(self):
		if self["historylist"].getCurrent() is None:
			return None
		print self["historylist"].getCurrent()[0]
		return self["historylist"].getCurrent()[0]

	def up(self):
		print "up"
		self["historylist"].selectPrevious()
		return self.getSelection()

	def down(self):
		print "down"
		self["historylist"].selectNext()
		return self.getSelection()

	def pageUp(self):
		print "up"
		self["historylist"].selectPrevious()
		return self.getSelection()

	def pageDown(self):
		print "down"
		self["historylist"].selectNext()
		return self.getSelection()

