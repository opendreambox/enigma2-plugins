from enigma import eEnv
from Tools.Log import Log
from Tools.Directories import fileExists
from SatIPTuner import SatIPTuner
import six

class TunerEntry():
	VTUNER_TYPE_SATIP_CLIENT = "satip_client"

	TUNER_TYPE_C = "DVB-C"
	TUNER_TYPE_S = "DVB-S"
	TUNER_TYPE_S = "DVB-S"
	TUNER_TYPE_T = "DVB-T"

	KEY_IPADDR = "ipaddr"
	KEY_TUNER_TYPE = "tuner_type"
	KEY_VTUNER_TYPE = "vtuner_type"

	MAP_FROM_DLNA = {
		SatIPTuner.TUNER_TYPE_S : TUNER_TYPE_S,
		SatIPTuner.TUNER_TYPE_S2 : TUNER_TYPE_S,
		SatIPTuner.TUNER_TYPE_T : TUNER_TYPE_T,
		SatIPTuner.TUNER_TYPE_T2 : TUNER_TYPE_T,
		SatIPTuner.TUNER_TYPE_C : TUNER_TYPE_C,
		SatIPTuner.TUNER_TYPE_C2 : TUNER_TYPE_C
	}

	@staticmethod
	def create(ip, tunerType, entryType=VTUNER_TYPE_SATIP_CLIENT):
		data = {
			TunerEntry.KEY_VTUNER_TYPE : entryType,
			TunerEntry.KEY_TUNER_TYPE : tunerType,
			TunerEntry.KEY_IPADDR : ip,
		}
		return TunerEntry(data)

	def __init__(self, data):
		self._data = data

	def getEntryType(self):
		return self._data.get(self.KEY_VTUNER_TYPE, None)
	def setEntryType(self, type):
		self._data[self.KEY_VTUNER_TYPE] = type
	entryType = property(getEntryType, setEntryType)

	def getIpAddress(self):
		return self._data.get(self.KEY_IPADDR, None)
	def setIpAddress(self, ip):
		self._data[self.KEY_IPADDR] = ip
	ipAddress = property(getIpAddress, setIpAddress)

	def getTunerType(self):
		return self._data.get(self.KEY_TUNER_TYPE, None)
	def setTunerType(self, type):
		self._data[self.KEY_TUNER_TYPE] = type
	tunerType = property(getTunerType, setTunerType)

	def setProperty(self, key, value):
		self._data[key] = value

	def getProperty(self, key, value, default=None):
		return self._data.get(key, default)

	def isValidSatIPEntry(self):
		return 	self.entryType == self.VTUNER_TYPE_SATIP_CLIENT \
			and self.ipAddress \
			and self.tunerType

	def data(self):
		return self._data

	def __str__(self):
		return "TunerEntry~%s" % (self._data)

	def __repr__(self):
		return self.__str__()

class ClientConfig(object):
	CONFIG_FILE = eEnv.resolve("${sysconfdir}/vtuner.conf")
	def __init__(self):
		self._config = {}
		self.reload()

	def getConfig(self):
		return self._config

	def addTuner(self, ip, tunerType, entryType=TunerEntry.VTUNER_TYPE_SATIP_CLIENT):
		entry = TunerEntry.create(ip, tunerType, entryType=entryType)
		self._config[len(list(self._config.keys()))] = entry

	def removeTuner(self, index, tunerEntry):
		if index in self._config:
			tE = self._config[index]
			if tE.ipAddress == tunerEntry.ipAddress and tE.tunerType == tunerEntry.tunerType and tE.entryType == tunerEntry.entryType:
				del self._config[index]
				return True
			else:
				Log.w("%s not equal %s, so not deleted!")
		return False

	def reload(self):
		if not fileExists(self.CONFIG_FILE):
			return True
		try:
			with open(self.CONFIG_FILE) as f:
				self._config = {}
				for line in f:
					Log.i("parsing: %s" % (line,))
					if line.startswith("#"):
						Log.d("skipping comment")
						continue
					try:
						num, data = line.strip().split("=")
						pairs = data.split(",")
						tuner_data = {}
						for pair in pairs:
							key, value = pair.split(":")
							tuner_data[key] = value
						self._config[int(num)] = TunerEntry(tuner_data)
					except Exception as e:
						Log.w(e)
						continue
		except Exception as e:
			Log.w(e)
			return False
		Log.i(self._config)
		return True

	def save(self):
		with open(self.CONFIG_FILE, 'w') as f:
			f.write("#This file is managed by your dreambox! All comments will be lost on next save using the UI!\n")
			index = 0
			for tunerEntry in six.itervalues(self._config):
				tmp = []
				for key, value in six.iteritems(tunerEntry.data()):
					tmp.append("%s:%s" % (key, value))
				tuner_data = ",".join(tmp)
				cfgline = "%s=%s\n" % (index, tuner_data)
				f.write(cfgline)
				index += 1
		self.reload()

vtunerClientConfig = ClientConfig()
