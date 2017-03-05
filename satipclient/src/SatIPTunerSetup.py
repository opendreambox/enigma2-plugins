from Components.ActionMap import ActionMap
from Components.Console import Console
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Tools.Log import Log

from SatIPTuner import SatIPTunerOverview, SatIPTuner
from ClientConfig import vtunerClientConfig, TunerEntry


class SatIPTunerSetup(Screen):
	SATIP_CLIENT_SERVICE_NAME = "satip-client"
	skin = """
		<screen name="SatIPTunerSetup" position="center,120" size="720,520" title="Sat>IP Tuner Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,0" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="200,0" zPosition="1" size="200,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="5,50" size="710,450" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>"""

	_console = None

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Sat>IP Tuner Setup"))
		self["list"] = MenuList([], enableWrapAround=True)
		self["key_red"] = StaticText(_("Remove"))
		self["key_green"] = StaticText(_("Add"))

		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok" : self._close,
			"cancel" : self._close,
			"green" : self._add,
			"red" : self._remove,
		})
		self._changed = False
		self._console = Console()
		self._check_count_lut = {}
		self._reload()

	def _countTuner(self, tunerEntry):
		if not tunerEntry.ipAddress in self._check_count_lut:
			self._check_count_lut[tunerEntry.ipAddress] = {}
		host_entry = self._check_count_lut[tunerEntry.ipAddress]
		if not tunerEntry.tunerType in host_entry:
			host_entry[tunerEntry.tunerType] = 0
		host_entry[tunerEntry.tunerType] += 1
		Log.i("tuner count for %s is now %s" % (tunerEntry, host_entry[tunerEntry.tunerType]))

	def _getTunerCount(self, ip, type):
		if not ip in self._check_count_lut:
			Log.w("ip not in lut!")
			return 0
		host_entry = self._check_count_lut[ip]
		if not type in host_entry:
			Log.w("type not in lut!")
			return 0
		count = host_entry[type]
		Log.w(count)
		return count

	def _reload(self):
		self._check_count_lut = {}
		content = [(_("Count - Type (host)"),)]
		entries = vtunerClientConfig.getConfig()
		for index, tunerEntry in entries.iteritems():
			if not tunerEntry.isValidSatIPEntry():
				#Log.w("filtering %s, it's not a satip tuner!" % (tunerEntry,))
				text = "%s - %s (%s)" % (index, tunerEntry.tunerType, tunerEntry.entryType)
				content.append((text,))
				continue
			self._countTuner(tunerEntry)
			text = "%s - %s (%s)" % (index, tunerEntry.tunerType, tunerEntry.ipAddress)
			content.append((text, tunerEntry, index))
		self["list"].setList(content)

	def _close(self):
		if self._changed:
			self._restartDaemon()
		self.close()

	def _add(self):
		self.session.openWithCallback(self._onTunerSelected, SatIPTunerOverview)

	def _remove(self):
		current = self["list"].getCurrent()
		Log.w(current)
		if current and len(current) == 3:
			text, tunerEntry, index = current
			if vtunerClientConfig.removeTuner(index, tunerEntry):
				self._changed = True
				vtunerClientConfig.save()
				self.session.toastManager.showToast(_("Tuner {0} / {1} removed").format(tunerEntry.ipAddress, tunerEntry.tunerType))
			else:
				self.session.toastManager.showToast(_("Tuner {0} / {1} NOT REMOVED. Consicentcy Check failed!").format(tunerEntry.ipAddress, tunerEntry.tunerType))
			self._reload()

	def _onTunerSelected(self, data):
		Log.d(data)
		if data and len(data) > 1:
			name, tuner = data
			self._selectModulationType(tuner)

	def _selectModulationType(self, tuner):
		choices = []
		caps_keys = tuner.caps.keys()
		type = mapped_type = count = None
		for caps_key in caps_keys:
			type = caps_key
			count = tuner.caps[type]
			mapped_type = TunerEntry.MAP_FROM_DLNA.get(type)
			if count > self._getTunerCount(tuner.host, mapped_type):
				choices.append((type, tuner))
		if choices:
			if len(choices) == 1:
				self._addTuner(tuner.host, mapped_type)
				return
			self.session.openWithCallback(
					self._onModulationTypeSelected,
					ChoiceBox,
					title=_("Please select the type of tuner you want to add!"),
					titlebartext=_("Multiple Tuner Types available!"),
					list=choices
				)
			return
		self.session.toastManager.showToast(_("Maximum amount of tuners for {0} configured!").format(tuner.name))

	def _onModulationTypeSelected(self, choice):
		if choice:
			type, tuner = choice
			type = TunerEntry.MAP_FROM_DLNA.get(type)
			self._addTuner(tuner.host, type)

	def _addTuner(self, host, type):
		self._changed = True
		vtunerClientConfig.addTuner(host, type)
		vtunerClientConfig.save()
		self._reload()
		self.session.toastManager.showToast(_("New Tuner added! GUI restart required!"))

	def _restartDaemon(self):
		self._console.ePopen('systemctl restart %s' % (self.SATIP_CLIENT_SERVICE_NAME,))
