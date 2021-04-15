# GUI (Screens)
from Screens.Screen import Screen

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

# Tools
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

class FTPQueueManagerSummary(Screen):
	skin = (
	"""<screen id="1" position="0,0" size="132,64">
		<widget source="parent.Title" render="Label" position="6,4" size="120,21" font="Regular;18" />
		<widget source="parent.list" render="Label" position="6,25" size="120,21" font="Regular;16">
			<convert type="StringListSelection" />
		</widget>
		<widget source="global.CurrentTime" render="Label" position="56,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
	</screen>""",
	"""<screen id="3" position="0,0" size="400,240">
		<ePixmap position="0,0" size="400,240" pixmap="skin_default/display_bg.png" zPosition="-1"/>
		<widget font="Display;40" position="10,5" render="Label" size="380,42" source="parent.Title" transparent="1"/>
		<widget font="Display;60" halign="center" position="10,50" render="Label" size="380,120" source="parent.list" valign="center" transparent="1">
			<convert type="StringListSelection" />
		</widget>
		<widget source="global.CurrentTime" halign="right" render="Label" position="90,180" size="300,50" font="Regular;50" transparent="1">
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
	</screen>""")

class FTPQueueManager(Screen):
	skin = """
		<screen position="center,120" size="820,520" title="FTP Queue Manager" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget source="list" render="Listbox" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos=(55,2), size=(740,24), text = 0, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
							MultiContentEntryText(pos=(55,26), size=(740,24), text = 1, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
							MultiContentEntryPixmapAlphaTest(pos=(5,5), size=(40,40), png = 2),
						],
					  "fonts": [gFont("Regular", 18)],
					  "itemHeight": 50
					 }
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session, queue):
		Screen.__init__(self, session)
		self.queue = queue or []
		
		self["key_red"] = StaticText("")
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self['list'] = List([])

		self.pixmaps = (
			LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FTPBrowser/images/up.svg")),
			LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FTPBrowser/images/down.svg"))
		)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.exit,
				"ok": self.ok,
			}, -1)
		
		self.onLayoutFinish.extend((
			self.layoutFinished,
			self.updateList,
		))

	def createSummary(self):
		return FTPQueueManagerSummary

	def updateList(self, queue=None):
		if not queue:
			queue = self.queue

		pixmaps = self.pixmaps

		list = [(item[1], "-> " + item[2], pixmaps[item[0]]) for item in queue]

		# XXX: this is a little ugly but this way we have the least
		# visible distortion :-)
		index = min(self['list'].index, len(list) - 1)
		self['list'].setList(list)
		self['list'].index = index

	def layoutFinished(self):
		self.setTitle(_("FTP Queue Manager"))

	def exit(self):
		self.close()

	def ok(self):
		pass
