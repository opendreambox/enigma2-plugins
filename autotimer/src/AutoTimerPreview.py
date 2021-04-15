# -*- coding: UTF-8 -*-

# GUI (System)
from enigma import getDesktop

# GUI (Screens)
from Screens.Screen import Screen

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

from ServiceReference import ServiceReference
from Tools.FuzzyDate import FuzzyTime

sz_w = getDesktop(0).size().width()

class AutoTimerPreview(Screen):
	"""Preview Timers which would be set"""

	if sz_w == 1920:
		skin = """
		<screen name="AutoTimerPreview" position="center,170" size="1200,820" title="Preview AutoTimer">
		<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" scale="stretch" size="350,70" />
		<ePixmap pixmap="Default-FHD/skin_default/buttons/yellow.svg" position="360,5" scale="stretch" size="350,70" />
		<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,70" source="key_red" transparent="1" valign="center" zPosition="1" />
		<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="360,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
		<widget font="Regular;34" halign="right" position="1050,25" render="Label" size="120,40" source="global.CurrentTime">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget font="Regular;34" halign="right" position="800,25" render="Label" size="240,40" source="global.CurrentTime">
			<convert type="ClockToText">Date</convert>
		</widget>
		<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
		<widget backgroundColor="background" enableWrapAround="1" position="10,90" render="Listbox" scrollbarMode="showOnDemand" size="1180,721" source="timerlist" transparent="1">
			<convert type="TemplatedMultiContent">
			{"template":[
			MultiContentEntryText(pos=(10,0),size=(1160,38),text=0,font=0,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER),
			MultiContentEntryText(pos=(10,38),size=(1160,32),text=3,font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,color=0xa0a0a0),
			MultiContentEntryText(pos=(10,70),size=(730,32),text=4,font=1,flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER,color=0xa0a0a0),
			MultiContentEntryText(pos=(760,70),size=(410,32),text=2,font=1,flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER,color=0xa0a0a0),
			],
			"fonts":[gFont("Regular",32),gFont("Regular",28) ],"itemHeight":103}
			</convert>
		</widget>
		</screen>"""
	else:
		skin = """
		<screen name="AutoTimerPreview" title="Preview AutoTimer" position="center,120" size="820,520">
		position="center,120" size="820,520">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="210,5" size="200,40" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget source="timerlist" render="Listbox" position="10,60" size="800,432" enableWrapAround="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
			{"template": [
			MultiContentEntryText(pos=(2,2), size=(790,24), text = 3, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
			MultiContentEntryText(pos=(2,26), size=(790,30), text = 0, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
			MultiContentEntryText(pos=(2,50), size=(300,20), text = 4, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
			MultiContentEntryText(pos=(320,50), size=(470,20), text = 2, font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
			],
			"fonts": [gFont("Regular",20),gFont("Regular",18)],
			"itemHeight": 72
			}
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session, timers):
		Screen.__init__(self, session)

		# Sort timers by begin
		timers.sort(key=lambda x: x[1])
		self.sort_type = 0

		# name, begin, end, serviceref, timername -> name, begin, timername, sname, timestr
		self.timers = [
			(x[0], x[1], x[4],
			ServiceReference(x[3]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8', 'ignore'),
			(("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(x[1]) + FuzzyTime(x[2])[1:] + ((x[2] - x[1]) / 60,))))
			for x in timers
		]

		self["timerlist"] = List(self.timers)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_yellow"] = StaticText()

		self.setSortDescription()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.sort
			}
		)

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Preview AutoTimer"))

	def setSortDescription(self):
		if self.sort_type == 1:
			self["key_yellow"].text = _("Sort Time")
		else:
			self["key_yellow"].text = _("Sort AutoTimer")

	def sort(self):
		timers = self.timers
		if timers:
			current = self["timerlist"].current
			idx = 0
			for timer in timers:
				if timer == current:
					break
				idx += 1
			if self.sort_type == 1:
				timers.sort(key=lambda x: x[1])
				self.sort_type = 0
			else:
				timers.sort(key=lambda x: x[4].lower())
				self.sort_type = 1
			self["timerlist"].updateList(timers)
			self["timerlist"].index = idx
			self.setSortDescription()

	def cancel(self):
		self.close(None)

	def save(self):
		self.close(True)

