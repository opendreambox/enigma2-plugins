from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.ResourceManager import resourcemanager
from Screens.Screen import Screen
from Tools.Log import Log


class SatIPTuner(object):
	TUNER_TYPE_S = "DVBS"
	TUNER_TYPE_S2 = "DVBS2"
	TUNER_TYPE_T = "DVBT"
	TUNER_TYPE_T2 = "DVBT2"
	TUNER_TYPE_C = "DVBC"
	TUNER_TYPE_C2 = "DVBC2"

	def __repr__(self):
		return "Sat>IPTuner~%s (%s) %s" % (self.name, self.host, self.readableCaps)

	def __init__(self, device):
		self._host = self._name = None
		self._caps = {}
		self._parseDevice(device)

	def _parseDevice(self, device):
		self._name = str(device.get_friendly_name())
		self._host = str(device.get_host())
		self._parseCaps(device.get_satipcap())

	def _parseCaps(self, caps):
		caps = str(caps)
		caps = caps.split(",")
		for cap in caps:
			type, count = cap.split("-")
			self._caps[type] = int(count)

	def getName(self):
		return self._name
	name = property(getName)

	def getHost(self):
		return self._host
	host = property(getHost)

	def getCaps(self):
		return self._caps
	caps = property(getCaps)

	def getReadableCaps(self):
		caps = []
		for ttype, tcount in self.caps.iteritems():
			caps.append(_("{0}x {1}").format(tcount, ttype))
		return ", ".join(caps)
	readableCaps = property(getReadableCaps)


class SatIPTunerOverview(Screen):
	skin = """
		<screen name="SatIPTunerOverview" position="center,120" size="720,520" title="Sat>IP Tuner Overview">
			<widget name="list" position="5,5" size="510,510" scrollbarMode="showOnDemand" zPosition="1"/>
		</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self._cp = resourcemanager.getResource("UPnPControlPoint")
		assert self._cp is not None

		self.setTitle(_("Sat>IP Tuner Overview"))
		self["list"] = MenuList([], enableWrapAround=True)
		self["tunerActions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self._ok,
			"cancel": self._close,
		}, -2)

		self._devices = []
		self._reload()

		self._cp.onSatIpServerDetected.append(self._reload)
		self._cp.onSatIpServerRemoved.append(self._reload)
		self.onClose.append(self.__onClose)

	def _ok(self):
		self.close(self["list"].getCurrent())

	def _close(self):
		self.close(None)

	def __onClose(self):
		self._cp.onSatIpServerDetected.remove(self._reload)
		self._cp.onSatIpServerRemoved.remove(self._reload)

	def _reload(self, *args):
		devices = self._cp.getSatIPDevices()
		lst = []
		for device in devices:
			tuner = SatIPTuner(device)
			text = str("%s: %s" % (tuner.name, tuner.readableCaps))
			lst.append((text, tuner))
		self["list"].setList(lst)
