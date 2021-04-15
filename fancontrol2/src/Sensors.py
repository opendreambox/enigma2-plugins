class Sensors:
	# (type, name, unit, directory)
	TYPE_TEMPERATURE = 0
	# (type, name, unit, fanid)
#	TYPE_FAN_RPM = 1

	def __init__(self):
		# (type, name, unit, sensor_specific_dict/list)
		self.sensors_list = []
		self.addSensors()

	def getSensorsCount(self, type=None):
		if type is None:
			return len(self.sensors_list)
		count = 0
		for sensor in self.sensors_list:
			if sensor[0] == type:
				count += 1
		return count

	# returns a list of sensorids of type "type"
	def getSensorsList(self, type=None):
		if type is None:
			return range(len(self.sensors_list))
		list = []
		for sensorid in range(len(self.sensors_list)):
			if self.sensors_list[sensorid][0] == type:
				list.append(sensorid)
		return list

	def getSensorType(self, sensorid):
		return self.sensors_list[sensorid][0]

	def getSensorName(self, sensorid):
		return self.sensors_list[sensorid][1]

	def getSensorDir(self, sensorid):
		return self.sensors_list[sensorid][3]

	def getSensorValue(self, sensorid):
		value = -1
		sensor = self.sensors_list[sensorid]
		if sensor[0] == self.TYPE_TEMPERATURE:
			f = open("%s/value" % sensor[3], "r")
			value = int(f.readline().strip() or "0")
			f.close()
		return value

	def addSensors(self):
		import os
		if os.path.exists("/proc/stb/sensors"):
			sd = []
			sd = os.listdir("/proc/stb/sensors")
			sd.sort()
			for dirname in sd:
				if dirname.find("temp", 0, 4) == 0:
					f = open("/proc/stb/sensors/%s/name" % dirname, "r")
					name = f.readline().strip()
					f.close()

					f = open("/proc/stb/sensors/%s/unit" % dirname, "r")
					unit = f.readline().strip()
					f.close()

					self.sensors_list.append((self.TYPE_TEMPERATURE, name, unit, "/proc/stb/sensors/%s" % dirname))


sensors = Sensors()
