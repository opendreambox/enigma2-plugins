from __future__ import print_function
from Components.config import config, getConfigListEntry, ConfigClock, ConfigDateTime, ConfigText, NoSave
# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

# for showSearchLog
from os import path as os_path

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen

from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, getDesktop

from skin import parseColor, parseFont, TemplatedListFonts

import time
import datetime

sz_w = getDesktop(0).size().width()

class AutoTimerFilterList(MenuList):
	"""Defines a simple Component to show Timer name"""

	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(30)
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
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, size.width() - 5, size.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, filter_txt[1], color, color)
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

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerEditor" position="center,170" size="1200,820" title="Edit AutoTimer">
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="305,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/yellow.svg" position="600,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/blue.svg" position="895,5" size="295,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
		<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
		<widget enableWrapAround="1" name="config" itemHeight="40" position="10,90" scrollbarMode="showOnDemand" size="1180,590" />
		<eLabel backgroundColor="grey" position="10,700" size="1180,1" />
		<widget font="Regular;32" halign="center" position="10,690" render="Label" size="1180,145" source="help" valign="center" />
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerEditor" title="Edit AutoTimer" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
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
			
			self["config"].onSelectionChanged.append(self.updateFilterDate)

			# Define Actions
			self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "InfobarActions", "MenuActions"],
				{
					"ok": 			self.ok, 
					"cancel": 	self.cancel,
					"red": 			self.cancel,
					"green": 		self.save, 
					"yellow":		self.remove, 
					"blue": 		self.add,
					"showTv":		self.sortList,
					"menu": self.add_copy,
					#"info":   self.showSearchLog,
				}
			)

			self.onLayoutFinish.append(self.setCustomTitle)
		
		except Exception:
			import traceback
			traceback.print_exc()

	def setCustomTitle(self):
		self.setTitle("AutoTimer " + _("Filter List"))


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
		
		self.session.openWithCallback(self.add_edit_Callback, AutoTimerFilterListEditor, None, 'add')

	def add_copy(self):
		# blue long on selected filter
		current = self["config"].getCurrent()
		if current is not None:
			self.session.openWithCallback(self.add_edit_Callback, AutoTimerFilterListEditor, current, 'add')


	def ok(self):
		# ok on selected filter
		current = self["config"].getCurrent()
		if current is not None:
			self.session.openWithCallback(self.add_edit_Callback, AutoTimerFilterListEditor, current, 'edit')


	def add_edit_Callback(self, ret, add_edit):
		
		if ret:
			
			date1  = ret[0][1].value
			time1  = ret[1][1].value
			filtertext = ret[2][1].value.strip().replace('"', "")
			
			for filter in self.FilterList:
				if filter[0][1] == filtertext:
					self.session.open(MessageBox,_("'%s' already exists in filter list!\nThe change was cancelled.") % filtertext, MessageBox.TYPE_INFO)
					return

			date1 = datetime.datetime.fromtimestamp(date1)
			datetime1 = datetime.datetime(date1.year, date1.month, date1.day, time1[0], time1[1])
			filtertime = time.mktime(datetime1.timetuple())
			
			Filter = ([len(self.FilterList),filtertext,filtertime],)

			if add_edit == "add":
				self.FilterList.append(Filter)
				
			elif add_edit == "edit":
				cur_index = self["config"].getCurrentIndex()
				self.FilterList[cur_index] = Filter
			
			self.FilterList.sort(key=lambda x: x[0][self.sorted])
			self["config"].setList(self.FilterList)
			
			self.changed = True


	def remove(self):
		# Remove selected Filter
		current = self["config"].getCurrent()
		if current is not None:
			self.session.openWithCallback(self.removeCallback, MessageBox, _("Do you really want to delete %s?") % (_("Filter List Entry") +" '"+str(current[1])+"'"), )

	def removeCallback(self, ret):
		cur = self["config"].getCurrentIndex()
		if ret and cur is not None:
			print(("=== index: ", int(cur)))
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


#=============== Editor for FilterEntry ==========================

class AutoTimerFilterListEditor(Screen, ConfigListScreen):
	"""Edit AutoTimer Filter"""

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerFilterEditor" position="center,170" size="1200,820" title="Edit AutoTimer Filters">
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="305,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/yellow.svg" position="600,5" size="295,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/blue.svg" position="895,5" size="295,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
		<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
		<widget enableWrapAround="1" name="config" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerFilterEditor" title="Edit AutoTimer Filters" position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget name="config" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand"/>
	</screen>"""



	def __init__(self, session, filterEntry, add_edit):
		Screen.__init__(self, session)

		try:
			self.skinName = "AutoTimerFilterEditor"
			self.onChangedEntry = []
			self.add_edit = add_edit
			
			if filterEntry is not None:
				self.EntryDate  = NoSave(ConfigDateTime(filterEntry[2], _("%d.%B %Y"), increment = 86400))
				self.EntryTime  = NoSave(ConfigClock(default = filterEntry[2]))
				self.EntryTitle = NoSave(ConfigText(default = filterEntry[1], fixed_size = False))
			else:
				self.EntryDate  = NoSave(ConfigDateTime(time.time(), _("%d.%B %Y"), increment = 86400))
				self.EntryTime  = NoSave(ConfigClock(default = time.time()))
				self.EntryTitle = NoSave(ConfigText(default = "", fixed_size = False))

			self.list = [
				getConfigListEntry(_("Date"), self.EntryDate),
				getConfigListEntry(_("Time"), self.EntryTime),
				getConfigListEntry(_("Title"), self.EntryTitle),
			]
			ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

			# Initialize Buttons
			self["key_red"] = StaticText(_("Cancel"))
			self["key_green"] = StaticText(_("Save"))
			self["key_yellow"] = StaticText(_(" "))
			self["key_blue"] = StaticText(_(" "))

			# Define Actions
			self["actions"] = ActionMap(["SetupActions", "ColorActions"],
				{
					"cancel": self.cancel,
					"save": self.save,
				}
			)

			# Trigger change
			self.changed()

			self.onLayoutFinish.append(self.setCustomTitle)

		except Exception:
			import traceback
			traceback.print_exc()


	def setCustomTitle(self):
		self.setTitle(_("AutoTimer %s Filter List Entry") % self.add_edit)


	def changed(self):
		pass
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass


	def cancel(self):
		
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), )
		else:
			self.close(None, self.add_edit)


	def cancelConfirm(self, ret):
		
		if ret:
			self.close(None, self.add_edit)


	def save(self):
		
		if not self.list[2][1].value.strip():
			self.session.open( MessageBox, _("The title attribute is mandatory."), type = MessageBox.TYPE_ERROR, timeout = 5 )
		else:
			if self["config"].isChanged():
				self.close(self.list, self.add_edit)
			else:
				self.close(None, self.add_edit)


