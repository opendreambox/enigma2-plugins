# Parts of Code and idea by Homey
from Components.Sources.Source import Source
from Components.Network import iNetworkInfo

class About(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def handleCommand(self, cmd):
		self.result = False, "unknown command"

	def command(self):
		ConvertIP = lambda l: "%s.%s.%s.%s" % tuple(l) if len(l) == 4 else "0.0.0.0"
		ifaces = iNetworkInfo.getConfiguredInterfaces()
		for key in ifaces.iterkeys():
			iface = ifaces[key]
			print "[WebComponents.About] iface: %s" % iface
			l = (
				iface.ethernet.mac,
				iface.ipv4.method,
				iface.ipv4.address,
				iface.ipv4.netmask,
				iface.ipv4.gateway,
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
