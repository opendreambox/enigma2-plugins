# -*- coding: UTF-8 -*-
# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.Sources.List import List
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox

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

	skin = """<screen name="EPGRefreshServiceEditor" position="center,50" size="820,640" title="Edit Services to refresh">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel position="10,50" size="800,1" backgroundColor="grey" />
		<widget name="config" position="10,60" size="800,550" enableWrapAround="1" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, services):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("EPGRefresh Services")
		self.onChangedEntry = []

		self.services_org = services #remember to check changes on close

		# We need to copy the list to be able to ignore changes
		self.services = (
			services[0][:],
			services[1][:]
		)
		

		self.reloadList()

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize StaticTexts
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("delete"))
		self["key_blue"] = StaticText(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.removeService,
				"blue": self.chooseType,
			}
		)

		# Trigger change
		self.changed()
		self.onLayoutFinish.append(self.setCustomTitle)

	def chooseType(self):
		self.session.openWithCallback(self.newService, ChoiceBox, list=[(_("Bouquet"), 1),(_("Channel"), 0)], windowTitle =  _("Please select what to add"))
	
	def setCustomTitle(self):
		self.setTitle(_("Edit Services to refresh"))

	def refresh(self, value=None):
		self.reloadList()
		self["config"].setList(self.list)

	def reloadList(self):
		self.list = []
		for i, typetext in [(1, _("Bouquets") ), (0, _("Channels"))]:

			cfgList = []
			cfgList.extend([
				getConfigListEntry(_("Refreshing"), NoSave(ConfigSelection(choices = [(x, ServiceReference(x.sref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])))
					for x in self.services[i]
				])
				
			if len(cfgList):
				self.list.append( getConfigListEntry(typetext) )
				cfgList = sorted(cfgList, key=lambda x: [x[1].getText()], reverse=False)
				self.list.extend(cfgList)

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		cur = self["config"].getCurrent()
		if cur and len(cur)>1:
			return cur[0]
		return ""

	def getCurrentValue(self):
		cur = self["config"].getCurrent()
		if cur and len(cur)>1:
			return str(cur[1].getText())
		return ""

	def createSummary(self):
		return SetupSummary

	def removeService(self):
		cur = self["config"].getCurrent()
		if cur:
			cur_index = self["config"].getCurrentIndex()
			# if only one list has length we know from which list to delete
			if len(self.services[1]) == 0:
				self.services[0].remove(cur[1].value)
			elif len(self.services[0]) == 0:
				self.services[1].remove(cur[1].value)
			else:
				# if both lists have length we know that bouquets come first
				if cur_index < self["config"]._headers[1]:	
					self.services[1].remove(cur[1].value)
				else: # channel
					self.services[0].remove(cur[1].value)
			
			self.refresh()

	def newService(self, selection):
		if selection:
			self.sel = selection[1]
			if selection[1] == 0: # channel
				self.session.openWithCallback(
					self.finishedServiceSelection,
					SimpleChannelSelection,
					_("Select channel to refresh")
				)
			else: # bouquet
				self.session.openWithCallback(
					self.finishedServiceSelection,
					SimpleBouquetSelection,
					_("Select bouquet to refresh")
				)

	def finishedServiceSelection(self, *args):
		if args:
			entry = EPGRefreshService(str(args[0].toString()), None)
			if entry not in self.services[self.sel]:
				self.services[self.sel].append(entry)
				self.refresh()
			else:
				self.session.open(MessageBox, _("%s is already configured for EPGRefresh") %(ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')),MessageBox.TYPE_INFO)
			self.setSelectionToEntry(entry)
	
	def setSelectionToEntry(self, entry):
		idx =0
		for item in self.list:
			if len(item)>1 and entry == item[1].value:
				self["config"].setCurrentIndex(idx)
				return
			idx +=1
		

	def cancel(self):
		if self.services != self.services_org:
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(None)
	
	def cancelConfirm(self, doCancel):
		if not doCancel:
			return
		self.close(None)

	def save(self):
		self.close(self.services)
