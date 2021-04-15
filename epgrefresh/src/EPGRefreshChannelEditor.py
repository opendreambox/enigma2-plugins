# -*- coding: UTF-8 -*-
# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import getConfigListEntry, ConfigSelection, \
	NoSave

from EPGRefreshService import EPGRefreshService

# Show ServiceName instead of ServiceReference
from ServiceReference import ServiceReference


class SimpleBouquetSelection(SimpleChannelSelection):
	def __init__(self, session, title):
		SimpleChannelSelection.__init__(self, session, title)
		self.skinName = "SimpleChannelSelection"

	def channelSelected(self): # just return selected service
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.close(ref)
		else:
			# We return the currently active path here
			# Asking the user if this is what he wants might be better though
			self.close(self.servicePath[-1])


class EPGRefreshServiceEditor(Screen, ConfigListScreen):
	"""Edit Services to be refreshed by EPGRefresh"""

	skin = """<screen name="EPGRefreshServiceEditor" position="center,120" size="820,520" title="Edit Services to refresh">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel position="10,50" size="800,1" backgroundColor="grey" />
		<widget name="config" position="10,60" size="800,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, services):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("EPGRefresh Services")
		self.onChangedEntry = []

		# We need to copy the list to be able to ignore changes
		self.services = (
			services[0][:],
			services[1][:]
		)

		self.typeSelection = NoSave(ConfigSelection(choices=[
			("channels", _("Channels")),
			("bouquets", _("Bouquets"))]
		))
		self.typeSelection.addNotifier(self.refresh, initial_call=False)

		self.reloadList()

		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changed)

		# Initialize StaticTexts
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("delete"))
		self["key_blue"] = StaticText(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.removeService,
				"blue": self.newService
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Edit Services to refresh"))

	def saveCurrent(self):
		del self.services[self.idx][:]

		# Warning, accessing a ConfigListEntry directly might be considered evil!

		myl = self["config"].getList()
		myl.pop(0)
		for item in myl:
			self.services[self.idx].append(item[1].value)

	def refresh(self, value):
		self.saveCurrent()

		self.reloadList()
		self["config"].setList(self.list)

	def reloadList(self):
		self.list = [
			getConfigListEntry(_("Editing"), self.typeSelection)
		]

		if self.typeSelection.value == "channels":
			self.idx = 0
		else: # self.typeSelection.value == "bouquets":
			self.idx = 1

		self.list.extend([
			getConfigListEntry(_("Refreshing"), NoSave(ConfigSelection(choices=[(x, ServiceReference(x.sref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])))
				for x in self.services[self.idx]
		])

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		cur = self["config"].getCurrent()
		if cur:
			return cur[0]
		return ""

	def getCurrentValue(self):
		cur = self["config"].getCurrent()
		if cur:
			return str(cur[1].getText())
		return ""

	def createSummary(self):
		return SetupSummary

	def removeService(self):
		cur = self["config"].getCurrent()
		if cur and cur[1] is not self.typeSelection:
			list = self["config"].getList()
			list.remove(cur)
			self["config"].setList(list)

	def newService(self):
		if self.typeSelection.value == "channels":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleChannelSelection,
				_("Select channel to refresh")
			)
		else: # self.typeSelection.value == "bouquets":
			self.session.openWithCallback(
				self.finishedServiceSelection,
				SimpleBouquetSelection,
				_("Select bouquet to refresh")
			)

	def finishedServiceSelection(self, *args):
		if args:
			list = self["config"].getList()
			list.append(getConfigListEntry(
				_("Refreshing"),
				NoSave(ConfigSelection(choices=[(
					EPGRefreshService(str(args[0].toString()), None),
					ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
				)]))
			))
			self["config"].setList(list)

	def cancel(self):
		self.close(None)

	def save(self):
		self.saveCurrent()

		self.close(self.services)
