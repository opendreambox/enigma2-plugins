# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Components.ScrollLabel import ScrollLabel
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry

VERSION = "1.6"

class VPS_Setup(Screen, ConfigListScreen):

	skin = """<screen name="vpsConfiguration" position="center,120" size="820,520" title="VPS-Plugin">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel position="10,50" size="800,1" backgroundColor="grey" />
		<widget name="config" position="10,60" size="800,330" enableWrapAround="1" scrollbarMode="showOnDemand" />
		<eLabel position="10,400" size="800,1" backgroundColor="grey" />
		<widget source="help" render="Label" position="10,410" size="800,96" font="Regular;22" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)

		#Summary
		self.setup_title = _("VPS Setup Version %s") %VERSION

		self.vps_enabled = getConfigListEntry(_("Enable VPS-Plugin"), config.plugins.vps.enabled)
		self.vps_initial_time = getConfigListEntry(_("Starting time"), config.plugins.vps.initial_time)
		self.vps_margin_after = getConfigListEntry(_("Margin after record (in seconds)"), config.plugins.vps.margin_after)
		self.vps_allow_wakeup = getConfigListEntry(_("Wakeup from Deep-Standby is allowed"), config.plugins.vps.allow_wakeup)
		self.vps_allow_seeking_multiple_pdc = getConfigListEntry(_("Seeking connected events"), config.plugins.vps.allow_seeking_multiple_pdc)
		self.vps_default = getConfigListEntry(_("VPS enabled by default"), config.plugins.vps.vps_default)
		self.vps_instanttimer = getConfigListEntry(_("Enable VPS on instant records"), config.plugins.vps.instanttimer)
		
		self.list = []
		self.list.append(self.vps_enabled)
		self.list.append(self.vps_initial_time)
		self.list.append(self.vps_margin_after)
		self.list.append(self.vps_allow_wakeup)
		self.list.append(self.vps_allow_seeking_multiple_pdc)
		self.list.append(self.vps_default)
		self.list.append(self.vps_instanttimer)

		ConfigListScreen.__init__(self, self.list, session = session)
		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Information"))

		self["help"] = StaticText()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"blue": self.show_info,
			}
		)
		
		self.onLayoutFinish.append(self.setCustomTitle)
		
	def setCustomTitle(self):
		self.setTitle(self.setup_title)
	
	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur == self.vps_enabled:
			self["help"].text = _("This plugin can determine whether a programme begins earlier or lasts longer. The channel has to provide reliable data.")
		elif cur == self.vps_initial_time:
			self["help"].text = _("If possible, x minutes before a timer starts VPS-Plugin will control whether the programme begins earlier. (0 disables feature)")
		elif cur == self.vps_margin_after:
			self["help"].text = _("The recording will last n seconds longer after the channel sent the stop signal.")
		elif cur == self.vps_default:
			self["help"].text = _("Enable VPS by default (new timers)")
		elif cur == self.vps_allow_wakeup:
			self["help"].text = _("If enabled and necessary, the plugin will wake up the Dreambox from Deep-Standby for the defined starting time to control whether the programme begins earlier.")
		elif cur == self.vps_allow_seeking_multiple_pdc:
			self["help"].text = _("If a programme is interrupted and divided into separate events, the plugin will search for the connected events.")
		elif cur == self.vps_instanttimer:
			self["help"].text = _("When yes, VPS will be enabled on instant records (stop after current event), if the channel supports VPS.")

	def show_info(self):
		VPS_show_info(self.session)
	
	def cancelConfirm(self, result):
		if not result:
			return

		for x in self["config"].list:
			x[1].cancel()

		self.close(self.session)

	def keyCancel(self):
		if self["config"].isChanged():
			from Screens.MessageBox import MessageBox

			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(self.session)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()

		self.close(self.session)



class VPS_Screen_Info(Screen):
	skin = """<screen name="vpsInfo" position="center,120" size="820,520" title="VPS-Plugin Information">
		<widget name="text" position="10,10" size="800,500" font="Regular;22" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		
		#Summary
		self.info_title = _("VPS-Plugin Information")
		
		self["text"] = ScrollLabel(_("VPS-Plugin can react on delays arising in the startTime or endTime of a programme. VPS is only supported by certain channels!\n\nIf you enable VPS, the recording will only start, when the channel flags the programme as running.\n\nIf you select \"yes (safe mode)\", the recording is definitely starting at the latest at the startTime you defined. The recording may start earlier or last longer.\n\n\nSupported channels\n\nGermany:\n ARD and ZDF\n\nAustria:\n ORF\n\nSwitzerland:\n SF\n\nCzech Republic:\n CT\n\nIf a timer is programmed manually (not via EPG), it is necessary to set a VPS-Time to enable VPS. VPS-Time (also known as PDC) is the first published start time, e.g. given in magazines. If you set a VPS-Time, you have to leave timer name empty."))
		
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], 
			{
				"cancel": self.close,
				"ok": self.close,
				"up": self["text"].pageUp,
				"down": self["text"].pageDown,
			}, -1)
		
		self.onLayoutFinish.append(self.setCustomTitle)
		
	def setCustomTitle(self):
		self.setTitle(self.info_title)
		
	
def VPS_show_info(session):
	session.open(VPS_Screen_Info)
	
