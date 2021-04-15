# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import HelpableActionMap
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.Sources.StaticText import StaticText
from Components.Label import Label, MultiColorLabel

# Configuration
from Components.config import config

from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

import inspect
from enigma import getDesktop

LIST_PLUGINS = 0
LIST_EXTENSIONS = 1
LIST_EVENTINFO = 2
LIST_MOVIELIST = 3

sz_w = getDesktop(0).size().width()


class PluginHiderSetup(Screen, HelpableScreen):

	if sz_w == 1920:
		skin = """<screen name="PluginHiderSetup_New" position="center,170" size="1200,820" title="PluginHider Setup">
			<ePixmap pixmap="Default-FHD/skin_default/buttons/red.svg" position="10,5" scale="stretch" size="350,70" />
			<ePixmap pixmap="Default-FHD/skin_default/buttons/green.svg" position="360,5" scale="stretch" size="350,70" />
			<ePixmap pixmap="Default-FHD/skin_default/buttons/blue.svg" position="710,5" scale="stretch" size="350,70" />
			<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,70" source="key_red" transparent="1" valign="center" zPosition="1" />
			<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="360,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,70" source="key_green" transparent="1" valign="center" zPosition="1" />
			<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="710,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
			<ePixmap pixmap="Default-FHD/skin_default/icons/help.svg" position="1110,30" size="80,40" />
			<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
			<widget enableWrapAround="1" name="list" position="10,140" scrollbarMode="showOnDemand" size="1180,675" />
			<widget name="plugins" position="17,88" zPosition="2" size="285,35" font="Regular;28" halign="center" valign="center" />
			<widget name="extensions" position="312,88" zPosition="2" size="285,35" font="Regular;28" halign="center" valign="center" />
			<widget name="eventinfo" position="607,88" zPosition="2" size="285,35" font="Regular;28" halign="center" valign="center" />
			<widget name="movielist" position="902,88" zPosition="2" size="285,35" font="Regular;28" halign="center" valign="center" />
			<widget name="selectedlistColors" backgroundColors="#777777,background" foregroundColors="foreground,yellow"/>
			<eLabel backgroundColor="grey" position="10,130" size="1180,2" />
		</screen>"""
	else:
		skin = """<screen name="PluginHiderSetup_New" title="PluginHider Setup" position="center,120" size="820,520">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="410,5" size="200,40" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<ePixmap pixmap="skin_default/icons/help.png" position="750,15" size="60,30" />
			<widget name="list" position="10,93" size="800,420" enableWrapAround="1" scrollbarMode="showOnDemand" />
			<eLabel backgroundColor="grey" position="10,50" size="800,1" />
			<widget name="plugins" position="12,55" zPosition="2" size="195,25" font="Regular;20" halign="center" valign="center"/>
			<widget name="extensions" position="212,55" zPosition="2" size="195,25" font="Regular;20" halign="center" valign="center"/>
			<widget name="eventinfo" position="412,55" zPosition="2" size="195,25" font="Regular;20" halign="center" valign="center"/>
			<widget name="movielist" position="612,55" zPosition="2" size="195,25" font="Regular;20" halign="center" valign="center"/>
			<widget name="selectedlistColors" backgroundColors="#777777,background" foregroundColors="foreground,yellow"/>
			<eLabel backgroundColor="grey" position="10,85" size="800,1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.skinName = "PluginHiderSetup_New"

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Run"))
		self["plugins"] = Label(_("Pluginbrowser"))
		self["extensions"] = Label(_("Extensions"))
		self["eventinfo"] = Label(_("Eventinfo"))
		self["movielist"] = Label(_("Movielist"))
		self["selectedlistColors"] = MultiColorLabel()

		self["list"] = SelectionList([])
		self.selectedList = LIST_PLUGINS

		self["PluginHiderSetupActions"] = HelpableActionMap(self, "PluginHiderSetupActions",
			{
				"ok": (self["list"].toggleSelection, _("toggle selection")),
				"cancel": (self.cancel, _("end editing")),
				"green": (self.save, _("save")),
				"blue": (self.run, _("run selected plugin")),
				"next": (self.next, _("select next tab")),
				"previous": (self.previous, _("select previous tab")),
			}, -1
		)

		self.onLayoutFinish.append(self.setCustomTitle)

	def run(self):
		cur = self["list"].getCurrent()
		cur = cur and cur[0]
		if cur:
			plugin = cur[1]

			if self.selectedList == LIST_PLUGINS:
				plugin(session=self.session)
			elif self.selectedList == LIST_MOVIELIST:
					self.session.open(MessageBox, _("Could not start Plugin:") + "\n" + _("Could start only from the movie-menu."), type=MessageBox.TYPE_ERROR)
			else: #if self.selectedList == LIST_EXTENSIONS or self.selectedList == LIST_EVENTINFO:
				from Screens.InfoBar import InfoBar
				instance = InfoBar.instance
				args = inspect.getargspec(plugin.__call__)[0]
				if len(args) == 1:
					plugin(session=self.session)
				elif instance and instance.servicelist:
					plugin(session=self.session, servicelist=instance.servicelist)
				else:
					session.open(MessageBox, _("Could not start Plugin:") + "\n" + _("Unable to access InfoBar."), type=MessageBox.TYPE_ERROR)

	def cancel(self):
		config.plugins.pluginhider.hideplugins.cancel()
		config.plugins.pluginhider.hideextensions.cancel()
		config.plugins.pluginhider.hideeventinfo.cancel()
		config.plugins.pluginhider.hidemovielist.cancel()
		self.close()

	def save(self):
		self.keepCurrent()
		config.plugins.pluginhider.save()
		self.close()

	def previous(self):
		self.keepCurrent()
		self.selectedList -= 1
		if self.selectedList < 0:
			self.selectedList = LIST_MOVIELIST
		self.updateList()

	def next(self):
		self.keepCurrent()
		self.selectedList += 1
		if self.selectedList > LIST_MOVIELIST:
			self.selectedList = LIST_PLUGINS
		self.updateList()

	def setCustomTitle(self):
		self.setTitle(_("PluginHider Setup"))
		self.updateList()

	def updateSelectedColor(self):
		
		try:
			pluginColor = extensionsColor = eventinfoColor = movielistColor = 0
			
			if self.selectedList == 0: 
				pluginColor = 1
			elif self.selectedList == 1: 
				extensionsColor = 1
			elif self.selectedList == 2: 
				eventinfoColor = 1
			else: 
				movielistColor = 1
			
			self["plugins"].instance.setBackgroundColor(self["selectedlistColors"].backColors[pluginColor])
			self["plugins"].instance.setForegroundColor(self["selectedlistColors"].foreColors[pluginColor])
			self["plugins"].instance.invalidate()
			self['extensions'].instance.setBackgroundColor(self["selectedlistColors"].backColors[extensionsColor])
			self['extensions'].instance.setForegroundColor(self["selectedlistColors"].foreColors[extensionsColor])
			self['extensions'].instance.invalidate()
			self['eventinfo'].instance.setBackgroundColor(self["selectedlistColors"].backColors[eventinfoColor])
			self['eventinfo'].instance.setForegroundColor(self["selectedlistColors"].foreColors[eventinfoColor])
			self['eventinfo'].instance.invalidate()
			self['movielist'].instance.setBackgroundColor(self["selectedlistColors"].backColors[movielistColor])
			self['movielist'].instance.setForegroundColor(self["selectedlistColors"].foreColors[movielistColor])
			self['movielist'].instance.invalidate()
			
		except:
				import traceback
				traceback.print_exc()

	def updateList(self):
		if hasattr(plugins, 'pluginHider_baseGetPlugins'):
			fnc = plugins.pluginHider_baseGetPlugins
		else:
			fnc = plugins.getPlugins

		if self.selectedList == LIST_PLUGINS:
			list = fnc([PluginDescriptor.WHERE_PLUGINMENU])
			selected = config.plugins.pluginhider.hideplugins.value
		elif self.selectedList == LIST_EXTENSIONS:
			list = fnc([PluginDescriptor.WHERE_EXTENSIONSMENU])
			selected = config.plugins.pluginhider.hideextensions.value
		elif self.selectedList == LIST_EVENTINFO:
			list = fnc([PluginDescriptor.WHERE_EVENTINFO])
			selected = config.plugins.pluginhider.hideeventinfo.value
		else: #if self.selectedList == LIST_MOVIELIST:
			list = fnc([PluginDescriptor.WHERE_MOVIELIST])
			selected = config.plugins.pluginhider.hidemovielist.value
		self.updateSelectedColor()

		res = []
		i = 0
		for plugin in list:
			if plugin.description:
				name = "%s (%s)" % (plugin.name, plugin.description)
			else:
				name = plugin.name

			res.append(SelectionEntryComponent(
					name,
					plugin,
					i,
					plugin.name in selected,
			))
			i += 1
		self["list"].setList(res)
		if res:
			self["list"].moveToIndex(0)

	def keepCurrent(self):
		selected = self["list"].getSelectionsList()
		if self.selectedList == LIST_PLUGINS:
			config.plugins.pluginhider.hideplugins.value = [x[1].name for x in selected]
		elif self.selectedList == LIST_EXTENSIONS:
			config.plugins.pluginhider.hideextensions.value = [x[1].name for x in selected]
		elif self.selectedList == LIST_EVENTINFO:
			config.plugins.pluginhider.hideeventinfo.value = [x[1].name for x in selected]
		else: #if self.selectedList == LIST_MOVIELIST:
			config.plugins.pluginhider.hidemovielist.value = [x[1].name for x in selected]
