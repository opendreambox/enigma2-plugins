# -*- coding: utf-8 -*-
# for localized messages
#from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from AutoMount import iAutoMount
from MountEdit import AutoMountEdit

class AutoMountView(Screen):
	skin = """
	<screen name="AutoMountView" position="center,120" size="820,520" title="MountView">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="210,5" size="200,40" alphatest="on"/>
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget source="legend1" render="Label" position="20,55" zPosition="1" size="130,60" font="Regular;18" halign="center" valign="center" />
		<widget source="legend2" render="Label" position="180,53" zPosition="1" size="450,60" font="Regular;20" halign="center" valign="center" />
		<widget source="legend3" render="Label" position="690,53" zPosition="1" size="120,60" font="Regular;20" halign="center" valign="center" />
		<eLabel	position="10,120" size="800,1" backgroundColor="grey"/>
		<widget source="config" render="Listbox" position="10,130" size="800,300" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryPixmapAlphaTest(pos = (50,6),size = (48,48),png = 0),# index 0 is the isMounted pixmap
				MultiContentEntryText(pos = (200,5),size = (200,28),font=0,flags = RT_HALIGN_LEFT,text = 1),# index 1 is the sharename
				MultiContentEntryText(pos = (400,10),size = (250,20),font=1,flags = RT_HALIGN_LEFT,text = 2),# index 2 is the IPdescription
				MultiContentEntryText(pos = (200,32),size = (470,20),font=1,flags = RT_HALIGN_LEFT,text = 3),# index 3 is the DIRdescription
				MultiContentEntryPixmapAlphaTest(pos = (690,8),size = (48,48),png = 4),# index 4 is the activepng pixmap
				MultiContentEntryPixmapAlphaTest(pos = (740,6),size = (48,48),png = 5),# index 4 is the mounttype pixmap
				],
				"fonts": [gFont("Regular",22),gFont("Regular",18)],
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
		self.mounts = None
		self.applyConfigRef = None
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.keyOK,
			"back": self.exit,
			"cancel": self.exit,
			"red": self.exit,
			"yellow": self.delete,
		})
		self["legend1"] = StaticText(_("Mounted/\nUnmounted"))
		self["legend2"] = StaticText(_("Mount informations"))
		self["legend3"] = StaticText(_("Active/\nInactive"))
		self["introduction"] = StaticText(_("Press OK to edit the settings."))
		self["key_red"] = StaticText(_("Close"))
		self["key_yellow"] = StaticText(_("Delete mount"))

		self.list = []
		self["config"] = List(self.list)
		self.showMountsList()

	def showMountsList(self):
		self.list = []
		self.mounts = iAutoMount.getMounts()
		for sharename in self.mounts.keys():
			mountentry = iAutoMount.mounts[sharename]
			self.list.append(self.buildMountViewItem(mountentry))
		self["config"].setList(self.list)

	def buildMountViewItem(self, entry):
		sharename = entry["sharename"]
		ip = _("IP:") + " " + str(entry["ip"])
		mountpoint = _("Dir:") + " " + str(entry["sharedir"])
		if entry["isMounted"]:
			isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/ok.png"))
		else:
			isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/cancel.png"))
		if entry["active"]:
			activepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock_on.png"))
		else:
			activepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock_error.png"))
		if entry["mounttype"] == 'nfs':
			mounttypepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-nfs.png"))
		if entry["mounttype"] == 'cifs':
			mounttypepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-smb.png"))
		return((isMountedpng, sharename, ip, mountpoint, activepng, mounttypepng))

	def exit(self):
		self.close()

	def keyOK(self, returnValue = None):
		cur = self["config"].getCurrent()
		if cur:
			returnValue = cur[1]
			self.session.openWithCallback(self._onMountEditClosed, AutoMountEdit, self.skin_path, iAutoMount.mounts[returnValue])

	def _onMountEditClosed(self, returnValue = None):
		self.showMountsList()

	def delete(self, returnValue = None):
		cur = self["config"].getCurrent()
		if cur:
			returnValue = cur[1]
			self.applyConfigRef = self.session.openWithCallback(self._onDeleteFinished, MessageBox, _("Please wait while removing your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
			iAutoMount.removeMount(iAutoMount.MOUNT_BASE + returnValue + "kaputt", self._onMountRemoved)

	def _onMountRemoved(self, success):
		text = _("Your network mount has been removed.")
		if not success:
			text = _("Sorry! Your network mount has NOT been removed.")
		self.session.toastManager.showToast(text)
		iAutoMount.save()
		iAutoMount.reload(self._onMountsReloaded)

	def _onMountsReloaded(self, success):
		if self.applyConfigRef.execing:
			self.applyConfigRef.close(success)

	def _onDeleteFinished(self, success):
		self.showMountsList()
