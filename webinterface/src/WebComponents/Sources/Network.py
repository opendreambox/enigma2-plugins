from Components.Sources.Source import Source
from Plugins.SystemPlugins.NetworkManager.NetworkConfig import getIfaceConfigs
from Tools.Log import Log
class Interface:
	def __init__(self, name):
		self.name = name
		self.mac = None
		self.dhcp = None
		self.ip = None
		self.netmask = None
		self.gateway = None

class Network(Source):
	LAN = 0
	WLAN = 1

	def __init__(self, device=LAN):
		Source.__init__(self)
		if device is self.LAN:
			self.iface = "eth0"
		elif device is self.WLAN:
			self.iface = "ath0"

	ConvertIP = lambda self, l: "%s.%s.%s.%s" % tuple(l) if l and len(l) == 4 else "0.0.0.0"

	def __getInterfaceAttribs(self, iface):
		Log.i(iface)
		attribs = [iface["Interface"], iface["Address"]]
		ip4 = iface["IPv4"]
		ip6 = iface["IPv6"]
		if ip4:
			attribs.extend((
				ip4.get("Method", "N/A"),
				ip4.get("Address", "N/A"),
				ip4.get("Netmask", "N/A"),
				ip4.get("Gateway", "N/A"),)
			)
		else:
			attribs.extend(["N/A", "N/A", "N/A", "N/A"])

		if ip6:
			attribs.extend((
				ip6.get("Method", "N/A"),
				ip6.get("Address", "N/A"),
				ip6.get("Netmask", "N/A"),
				ip6.get("Gateway", "N/A"),)
			)
		else:
			attribs.extend(["N/A", "N/A", "N/A", "N/A"])
		return attribs

	def getInterface(self):
		ifaces = getIfaceConfigs()
		Log.i(ifaces)
		for key in ifaces.iterkeys():
			iface = ifaces[key]
			if iface["Interface"] == self.iface:
				return self.__getInterfaceAttribs(iface)
		return ["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]

	interface = property(getInterface)

	def getList(self):
		lst = []
		ifaces = getIfaceConfigs()
		Log.i(ifaces)
		for key in ifaces.iterkeys():
			iface = ifaces[key]
			lst.append(self.__getInterfaceAttribs(iface))

		return lst
	list = property(getList)

	lut = {
			"Name": 0,
			"Mac" : 1,
			"Dhcp" : 2,
			"Ip" : 3,
			"Netmask" : 4,
			"Gateway" : 5,
			"Method6": 6,
			"Ip6" : 7,
			"Netmask6" : 8,
			"Gateway6" : 9,
	}

