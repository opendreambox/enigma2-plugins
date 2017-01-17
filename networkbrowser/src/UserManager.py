# -*- coding: utf-8 -*-
from enigma import eEnv
from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.Sources.List import List

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from UserDialog import UserDialog
from os import unlink, listdir, path as os_path

class UserManager(Screen):
	skin = """
		<screen name="UserManager" position="center,120" size="820,520" title="UserManager">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="210,5" size="200,40" alphatest="on"/>
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget source="config" render="Listbox" position="10,55" size="800,420" enableWrapAround="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryText(pos = (80,7),size = (690,50),font=0,flags = RT_HALIGN_LEFT,text = 0),# index 0 is the name
				MultiContentEntryPixmapAlphaTest(pos = (10,6),size = (48,48),png = 3),# index 4 is the status pixmap
				],
				"fonts": [gFont("Regular",40)],
				"itemHeight": 60
				}
			</convert>
		</widget>
		<eLabel	position="10,480" size="800,1" backgroundColor="grey"/>
		<widget source="introduction" render="Label" position="10,488" size="800,25" font="Regular;22" halign="center" transparent="1"/>
	</screen>"""

	def __init__(self, session, plugin_path):
		self.skin_path = plugin_path
		self.session = session
		Screen.__init__(self, session)
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.keyOK,
			"back": self.exit,
			"cancel": self.exit,
			"red": self.exit,
			"yellow": self.delete,
		})

		self["key_red"] = StaticText(_("Close"))
		self["introduction"] = StaticText(_("Press OK to edit selected settings."))
		self["key_yellow"] = StaticText(_("Delete"))

		self.list = []
		self["config"] = List(self.list)
		self.updateList()
		self.onShown.append(self.setWindowTitle)

	def setWindowTitle(self):
		self.setTitle(_("Usermanager"))

	def updateList(self):
		self.list = []
		for file in listdir(eEnv.resolve("${sysconfdir}/enigma2")):
			if file.endswith('.cache'):
				if file == 'networkbrowser.cache':
					continue
				else:
					hostpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/host.png"))
					self.list.append(( file[:-6],'edit',file,hostpng ))
		self["config"].setList(self.list)

	def exit(self):
		self.close()

	def keyOK(self, returnValue = None):
		cur = self["config"].getCurrent()
		if cur:
			returnValue = cur[1]
			hostinfo = cur[0]
			if returnValue is "edit":
				self.session.open(UserDialog, self.skin_path,hostinfo)

	def delete(self, returnValue = None):
		cur = self["config"].getCurrent()
		if cur:
			returnValue = cur[2]
			cachefile = eEnv.resolve("${sysconfdir}/enigma2/") + returnValue.strip()
			if os_path.exists(cachefile):
				unlink(cachefile)
				self.updateList()

