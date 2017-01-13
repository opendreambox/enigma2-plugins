from twisted.web import proxy

class TerminalResource(proxy.ReverseProxyResource):
	def __init__(self):
		proxy.ReverseProxyResource.__init__(self, "127.0.0.1", 4200, '')
