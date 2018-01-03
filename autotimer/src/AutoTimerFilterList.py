from Components.config import config
# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

# for showSearchLog
from os import path as os_path

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT

from skin import parseColor, parseFont, TemplatedListFonts

import time
import datetime

class AutoTimerFilterList(MenuList):
	"""Defines a simple Component to show Timer name"""

	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(25)
		self.colorDisabled = 12368828
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))

	def applySkin(self, desktop, parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				elif attrib == "colorDisabled":
					self.colorDisabled = parseColor(value).argb()
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)


	def buildListboxEntry(self, filter_txt):
		
		size = self.l.getItemSize()
		color = None

		return [
			None,
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, size.width() - 5, size.height(), 0, RT_HALIGN_LEFT, filter_txt[1], color, color)
		]

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if x[0] == entry:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1



class AutoTimerFilterListOverview(Screen):

	skin = """<screen name="AutoTimerEditor" title="Edit AutoTimer" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on"/>
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,360" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		<eLabel	position="10,430" size="800,1" backgroundColor="grey"/>
		<widget source="help" render="Label" position="10,440" size="800,70" font="Regular;20" halign="center" valign="center" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		
		try:
			self.skinName = "AutoTimerEditor"

			self.changed = False

			# Button Labels
			self["key_green"] = StaticText(_("Save"))
			self["key_yellow"] = StaticText(_("Delete"))
			self["key_blue"] = StaticText(_("Add"))
			self["key_red"] = StaticText(_("Close"))
			self["help"] = StaticText()
			
			filter_txt = ""
			path_filter_txt = "/etc/enigma2/autotimer_filter.txt"
			if os_path.exists(path_filter_txt):
				filter_txt = open(path_filter_txt).read()
				filter_txt = filter_txt.split("\n")

			self.FilterList = []
			
			for count, filter in enumerate(filter_txt):
				filter1 = filter.split(' - "')
				if len(filter1)>1:
					time1 = time.mktime(datetime.datetime.strptime(filter1[0], "%d.%m.%Y, %H:%M").timetuple())
					Filter = ([count,filter1[1][:-1],time1],)
					self.FilterList.append(Filter)
			
			#sort alphabetically
			self.FilterList.sort(key=lambda x: x[0][1].lower())
			self.sorted = 1

			self["config"] = AutoTimerFilterList(self.FilterList)
			self.updateFilterDate()
			
			# Summary
			#self.onChangedEntry = []
			#self["config"].onSelectionChanged.append(self.selectionChanged)
			self["config"].onSelectionChanged.append(self.updateFilterDate)

			# Define Actions
			self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "InfobarActions"],
				{
					"ok": 			self.ok, 
					"cancel": 	self.cancel,
					"red": 			self.cancel,
					"green": 		self.save, 
					"yellow":		self.remove, 
					"blue": 		self.add,
					"showTv":		self.sortList,
					#"info":   self.showSearchLog,
				}
			)

			self.onLayoutFinish.append(self.setCustomTitle)
			#self.onFirstExecBegin.append(self.firstExec)
		
		except Exception:
			import traceback
			traceback.print_exc()

	def setCustomTitle(self):
		self.setTitle("AutoTimer " + _("Filterlist"))


	def updateFilterDate(self):
		cur = self["config"].getCurrent()
		if cur is not None:
			#show timertime of filter as helptext
			timertime = datetime.datetime.fromtimestamp(cur[2]).strftime("%d.%m.%Y, %H:%M")
			self["help"].text = "Timer from:\n" + timertime
			pass

	def sortList(self):

		if self.sorted == 1:
			#sort by org order in filterlist
			self.sorted=0
			self.FilterList.sort(key=lambda x: x[0][0])
		elif self.sorted == 0:
			#sort by timertime
			self.sorted=2
			self.FilterList.sort(key=lambda x: x[0][2])
		else:
			#sort alphabetically
			self.FilterList.sort(key=lambda x: x[0][1].lower())
			self.sorted=1
		
		self["config"].setList(self.FilterList)
		

	def selectionChanged(self):
		#sel = self["entries"].getCurrent()
		#text = sel and sel.name or ""
		#for x in self.onChangedEntry:
			#try:
				#x(text)
			#except Exception:
				#pass
		pass

	def add(self):
		
		self.session.open(MessageBox,_("add FilterEntry - Aktion noch nicht verfuegbar"), MessageBox.TYPE_INFO)
		#self.session.openWithCallback(self.addCallback,	AutoTimerEditor,newTimer)

	def addCallback(self, ret):
		if ret:
			#self.changed = True
			#self.autotimer.add(ret)
			#self.refresh()
			pass


	def refresh(self, res = None):
		# Re-assign List
		#cur = self["entries"].getCurrent()
		#self["entries"].setList(self.autotimer.getSortedTupleTimerList())
		#self["entries"].moveToEntry(cur)
		pass

	def ok(self):
		# ok on selected filter
		current = self["config"].getCurrent()
		if current is not None:
			self.session.open(MessageBox,_("edit") + " FilterEntry '" + str(current[1]) + "'\nAktion noch nicht verfuegbar", MessageBox.TYPE_INFO)
			#self.session.openWithCallback(self.editCallback, AutoTimerEditor, current)
		#pass

	def editCallback(self, ret):
		if ret:
			#self.changed = True
			#self.refresh()
			pass


	def remove(self):
		# Remove selected Filter
		current = self["config"].getCurrent()
		if current is not None:
			self.session.openWithCallback(self.removeCallback, MessageBox, _("Do you really want to delete %s?") % (_("FilterEntry") +" '"+str(current[1])+"'"), )

	def removeCallback(self, ret):
		cur = self["config"].getCurrentIndex()
		if ret and cur:
			print ("=== index: ", int(cur))
			del self.FilterList[cur]
			
			self["config"].setList(self.FilterList)
			
			self.changed = True


	def cancel(self):
		if self.changed:
			self.session.openWithCallback(self.cancelConfirm, ChoiceBox, title=_('Really close without saving settings?\nWhat do you want to do?') , list=[(_('close without saving'), 'close'), (_('close and save'), 'close_save'),(_('cancel'), 'exit'), ])
		else:
			self.close()


	def cancelConfirm(self, ret):
		ret = ret and ret[1]
		if ret == 'close':
			# Close and indicated that we canceled by returning None
			self.close()
		elif ret == 'close_save':
			#close and save without searching
			self.save()


	def save(self):
			
			if self.changed:
				self.FilterList.sort(key=lambda x: x[0][0])
				path_filter_txt = "/etc/enigma2/autotimer_filter.txt"
				filter_txt=""
				file_search_log = open(path_filter_txt, "w")
				for filter in self.FilterList:
					timertime = datetime.datetime.fromtimestamp(filter[0][2]).strftime("%d.%m.%Y, %H:%M")
					filter_txt += timertime + ' - "' + filter[0][1] + '"\n'
				file_search_log.write(filter_txt)
				file_search_log.close()
			
			self.close()

