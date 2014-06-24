# Parts of Code and idea by Homey
from Components.Sources.Source import Source
from Plugins.SystemPlugins.NetworkManager.NetworkConfig import getIfaceConfigs

class About(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def handleCommand(self, cmd):
		self.result = False, "unknown command"

	def command(self):
		ConvertIP = lambda l: "%s.%s.%s.%s" % tuple(l) if len(l) == 4 else "0.0.0.0"
		ifaces = getIfaceConfigs()
		for key in ifaces.iterkeys():
			iface = ifaces[key]
			print "[WebComponents.About] iface: %s" % iface
			ip4 = iface["IPv4"]
			l = (
				iface.get("Address", "N/A"),
				ip4.get("Method", "N/A"),
				ip4.get("Address", "N/A"),
				ip4.get("Netmask", "N/A"),
				ip4.get("Gateway", "N/A"),
			)
			break
		else:
			print "[WebComponents.About] no network iface configured!"
			l = (
				"N/A",
				"N/A",
				"N/A",
				"N/A",
				"N/A",
			)

		return (l,)

	list = property(command)
	lut = { "lanMac": 0
			, "lanDHCP": 1
			, "lanIP": 2
			, "lanMask": 3
			, "lanGW": 4
		}
