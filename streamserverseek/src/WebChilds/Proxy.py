from twisted.web import resource, server, proxy
from twisted.internet import reactor

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek

import urlparse


class MyProxyClient(proxy.ProxyClient):
	def __init__(self, command, rest, version, headers, data, father, responseEndCallback):
		proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
		self.headers["connection"] = "keep-alive"
		self.version = version
		self.responseEndCallback = responseEndCallback

	def sendCommand(self, command, path):
		self.transport.writeSequence([command, b' ', path, b' ' + self.version + b'\r\n'])

	def handleResponseEnd(self):
		self.transport.abortConnection()
		if not self._finished:
			if self.responseEndCallback:
				self.responseEndCallback(self.father)
			proxy.ProxyClient.handleResponseEnd(self)

	def handleHeader(self, key, value):
		if not self.responseEndCallback or key.lower() != 'content-length':
			proxy.ProxyClient.handleHeader(self, key, value)


class MyProxyClientFactory(proxy.ProxyClientFactory):
	protocol = MyProxyClient

	def __init__(self, command, rest, version, headers, data, father, responseEndCallback):
		proxy.ProxyClientFactory.__init__(self, command, rest, version, headers, data, father)
		self.responseEndCallback = responseEndCallback

	def buildProtocol(self, addr):
		return self.protocol(self.command, self.rest, self.version,
			self.headers, self.data, self.father, self.responseEndCallback)


class ProxyResource(resource.Resource):
	isLeaf = True
	session = None

	proxyClientFactoryClass = MyProxyClientFactory

	def __init__(self, session):
		resource.Resource.__init__(self)
		self.session = session
		self.streamServerSeek = StreamServerSeek()

	def render(self, request):
		request.requestHeaders.setRawHeaders(b"host", [request.getRequestHostname().encode('ascii') + b":8080"])
		request.content.seek(0, 0)

		path = "/" + "/".join(request.postpath)

		qs = urlparse.urlparse(request.uri)[4]
		if qs:
			path = path + '?' + qs

		print "[StreamServerSeek] Reverse-Proxy %s" % path

		clientFactory = self.proxyClientFactoryClass(
			request.method, path, request.clientproto,
			request.getAllHeaders(), request.content.read(), request, self.responseEndCallback)
		reactor.connectTCP(request.getRequestHostname(), 8080, clientFactory)

		return server.NOT_DONE_YET

	def responseEndCallback(self, request):
		#not in use anymore
		return
