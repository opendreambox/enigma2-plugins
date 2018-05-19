from twisted.web import resource, server, proxy, http
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek

import urlparse
import math
import time

from io import BytesIO as StringIO

from ctypes import *

class M3u8Client(http.HTTPClient):
	_finished = False

	def __init__(self, command, rest, version, headers, data, responseEndCallback):
		self.command = command
		self.rest = rest
		if "proxy-connection" in headers:
			del headers["proxy-connection"]
		headers["connection"] = "close"
		headers.pop('keep-alive', None)
		self.headers = headers
		self.data = data
		self.version = version
		self.responseEndCallback = responseEndCallback

	def sendCommand(self, command, path):
		self.transport.writeSequence([command, b' ', path, b' ' + self.version + b'\r\n'])

	def connectionMade(self):
		self.sendCommand(self.command, self.rest)
		for header, value in self.headers.items():
			self.sendHeader(header, value)
		self.endHeaders()
		self.transport.write(self.data)

	def handleResponseEnd(self):
		if not self._finished:
			self._finished = True
			self.transport.loseConnection()
			buffer = None
			if self._HTTPClient__buffer is not None:
				buffer = self._HTTPClient__buffer
				self._HTTPClient__buffer = None
			if self.responseEndCallback is not None:
				self.responseEndCallback(buffer)

class M3u8ClientFactory(ClientFactory):
	protocol = M3u8Client

	def __init__(self, command, rest, version, headers, data, responseEndCallback):
		self.command = command
		self.rest = rest
		self.headers = headers
		self.data = data
		self.version = version
		self.responseEndCallback = responseEndCallback

	def buildProtocol(self, addr):
		return self.protocol(self.command, self.rest, self.version, self.headers, self.data, self.responseEndCallback)


class MyProxyClient(proxy.ProxyClient):
	def __init__(self, command, rest, version, headers, data, father, responseEndCallback, statusCallback):
		proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
		self.version = version
		self.responseEndCallback = responseEndCallback
		self.statusCallback = statusCallback
		father.notifyFinish().addBoth(self.disconnectChildConn)

	def sendCommand(self, command, path):
		self.transport.writeSequence([command, b' ', path, b' ' + self.version + b'\r\n'])

	def handleResponseEnd(self):
		if not self._finished and not self.father.finished and not self.father._disconnected:
			if self.responseEndCallback:
				self.responseEndCallback(self.father)
			proxy.ProxyClient.handleResponseEnd(self)

	def handleHeader(self, key, value):
		if not self.responseEndCallback or key.lower() != 'content-length':
			proxy.ProxyClient.handleHeader(self, key, value)

	def handleStatus(self, version, code, message):
		if int(code) == 404:
			self.father.setResponseCode(503, "Service Unavailable")
		else:
			self.father.setResponseCode(int(code), message)
		if self.statusCallback:
			self.statusCallback(int(code), self.rest)
	
	def disconnectChildConn(self, ignored):
		if self.father._disconnected:
			print "[StreamServerSeek] notifiyFinish close client conn"
# This seems to crash dreamliveserver:
#			self.quietLoss = True
#			self.transport.loseConnection()


class MyProxyClientFactory(proxy.ProxyClientFactory):
	protocol = MyProxyClient

	def __init__(self, command, rest, version, headers, data, father, responseEndCallback, statusCallback, setClientCallback):
		proxy.ProxyClientFactory.__init__(self, command, rest, version, headers, data, father)
		self.responseEndCallback = responseEndCallback
		self.statusCallback = statusCallback
		self.setClientCallback = setClientCallback

	def buildProtocol(self, addr):
		client = self.protocol(self.command, self.rest, self.version,
			self.headers, self.data, self.father, self.responseEndCallback, self.statusCallback)
		if self.setClientCallback:
			self.setClientCallback(client)
		return client

def getSegmentNoFromFilename(filename):
	try:
		if not filename.startswith("segment") or not filename.endswith(".ts"):
			return None
		return int(filename[7:-3])
	except Exception, e:
		return None


class VodRequestHandler(object):
	_m3u8 = StringIO()
	_segmentBuffer = None
	_client = None

	def __init__(self, resource, request):
		self._resource = resource
		self._request = request
		self._origWrite = request.write
		self.streamServerSeek = StreamServerSeek()
	
	def setClient(self, client):
		self._client = client
	
	def streamWrite(self, buffer):
		self._m3u8.write(buffer)
	
	def streamEndCallback(self, request):
		seek = self.streamServerSeek.getSeek()
		if not seek:
			self.streamServerSeek._isVodActive = False
			self._origWrite(self._m3u8.getvalue())
			return

		self.streamServerSeek._isVodActive = True
		self.streamServerSeek._expectedSegment = 0
		self.streamServerSeek._lastSuccessfullSegment = -1
		
		self.m3u8EndCallback(self._m3u8)

		response = StringIO()
		response.write("#EXTM3U\n")
		response.write("#EXT-X-PLAYLIST-TYPE:VOD\n")
		response.write("#EXT-X-ALLOW-CACHE:NO\n")
		response.write("#EXT-X-TARGETDURATION:2\n")
		response.write("#EXT-X-VERSION:3\n")
		response.write("#EXT-X-MEDIA-SEQUENCE:0\n")

		movieSegments = 0
		movieLength = seek.getLength()
		if not movieLength[0] and movieLength[1]:
			movieSegments = int(math.ceil(movieLength[1] / 90000 / 2))

		for i in range(0, movieSegments):
			response.write("#EXTINF:%s,\n" % self._resource.segmentLength)
			response.write("segment%d.ts\n" % i)
			
		response.write("#EXT-X-ENDLIST\n")

		self._origWrite(response.getvalue())

	def m3u8EndCallback(self, m3u8):
		segmentLength = 0
		segments = []
		segmentFollows = False

		m3u8.seek(0,0)
		line = m3u8.readline()
		while line:
			line = line.rstrip()
			if segmentFollows:
				segment = getSegmentNoFromFilename(line)
				not segment is None and segments.append(segment)
			segmentFollows = False
			if line.startswith("#EXTINF:"):
				segmentLength = line[8:-1]
				segmentFollows = True
			line = m3u8.readline()
		
		self.streamServerSeek._vodSegments = segments
		self._resource.segmentLength = segmentLength
		
		if self.streamServerSeek._lastSegmentRequest + 30 > time.time():
			if self.streamServerSeek._m3u8CallId is None or not self.streamServerSeek._m3u8CallId.active():
				print "[StreamServerSeek] ReRequestM3u8"
				self.streamServerSeek._m3u8CallId = reactor.callLater(1, self.doReRequestM3u8)
		else:
			print "[StreamServerSeek] Stop requesting m3u8 repeatedly"
			if not self.streamServerSeek._m3u8CallId is None and self.streamServerSeek._m3u8CallId.active():
				self.streamServerSeek._m3u8CallId.cancel()

	def segmentStatusCallback(self, status, path):
		self._status = status
		segment = getSegmentNoFromFilename(path[1:])
		if status == 200:
			self.streamServerSeek._expectedSegment = self._resource._nextExpectedSegment
			self.streamServerSeek._lastSuccessfullSegment = segment
		if status == 404:
			if self._realSegment <= self.streamServerSeek._vodSegments[0]:
				print "[StreamServerSeek] Requested Segment %d doesn't exist anymore -> rewrite next request to %d. Client connection is probably too slow - consider lowering bitrate." % (segment, self.streamServerSeek._vodSegments[0] + 1)
				self.streamServerSeek._lastSuccessfullSegment = self.streamServerSeek._vodSegments[0]
				if segment == 0:
					# most probably restart/reload of player, force jump to begin
					self.streamServerSeek._expectedSegment = -1

	def segmentWrite(self, buffer):
		if self._request._disconnected:
# This seems to crash dreamliveserver:
#			if not self._client is None:
#				self._client.quietLoss = True
#				self._client.transport.loseConnection()
			return
		if self._segmentBuffer is None:
			self._segmentBuffer = create_string_buffer(buffer, len(buffer))
		else:
			self._segmentBuffer = create_string_buffer(self._segmentBuffer.raw + buffer, len(self._segmentBuffer.raw) + len(buffer))
	
	def segmentEndCallback(self, request):
		if request.finished or request._disconnected:
			return
		if self._status == 200:
			length = len(self._segmentBuffer)
			segmentOffsetFunc = self.streamServerSeek.getSegmentOffsetFunc()
			if not segmentOffsetFunc is None:
				start_time = time.time()
				segmentOffsetFunc(self._segmentBuffer, length, self._requestedSegment - self._realSegment)
				print("[StreamServerSeek] segmentOffsetFunc took %s seconds" % (time.time() - start_time))
			if request.responseHeaders.getRawHeaders(b'content-length') is None:
				request.responseHeaders.setRawHeaders(b'content-length', [("%d" % length).encode("ascii")])
		if not self._segmentBuffer is None:
			self._origWrite(self._segmentBuffer.raw)
		else:
			self._origWrite("")

	def doReRequestM3u8(self):
		clientFactory = M3u8ClientFactory(
			"GET", "/stream.m3u8", "HTTP/1.1",
			self._resource._requestHeaders, None, self.m3u8EndCallback)
		reactor.connectTCP(self._resource._requestHostname, 8080, clientFactory)

class VodResource(resource.Resource):
	isLeaf = True
	session = None
	_status = None
	
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
		
		responseEndCallback = False
		statusCallback = False
		setClientCallback = False

		if path == "/stream.m3u8":
			handler = VodRequestHandler(self, request)
			request.write = handler.streamWrite
			responseEndCallback = handler.streamEndCallback
			setClientCallback = handler.setClient

			self._requestHeaders = request.getAllHeaders()
			self._requestHostname = request.getRequestHostname()
			self.streamServerSeek._lastSegmentRequest = time.time()
		elif self.streamServerSeek._isVodActive:
			segment = getSegmentNoFromFilename(path[1:])
			if not segment is None:
				self.streamServerSeek._lastSegmentRequest = time.time()
				handler = VodRequestHandler(self, request)
				statusCallback = handler.segmentStatusCallback
				setClientCallback = handler.setClient
				if segment == self.streamServerSeek._expectedSegment:
					self._nextExpectedSegment = self.streamServerSeek._expectedSegment + 1
				else:
					print "[StreamServerSeek] expected segment %d, but got %d -> jump to sec %d" % (self.streamServerSeek._expectedSegment, segment, segment * 2)
					seek = self.streamServerSeek.getSeek()
					if seek:
						seek.seekTo(segment * 2 * 90000)
					self._nextExpectedSegment = segment + 1
					
					index = -2
					if len(self.streamServerSeek._vodSegments) == 1:
						index = -1
					self.streamServerSeek._lastSuccessfullSegment = self.streamServerSeek._vodSegments[index] - 1
				
				handler._realSegment = self.streamServerSeek._lastSuccessfullSegment + 1
				if segment != handler._realSegment:
					request.write = handler.segmentWrite
					responseEndCallback = handler.segmentEndCallback
					handler._requestedSegment = segment
				
				oldpath = path
				path = "/segment%d.ts" % (self.streamServerSeek._lastSuccessfullSegment + 1)
				print "[StreamServerSeek] Vod-Proxy %s -> %s" % (oldpath, path)

		clientFactory = self.proxyClientFactoryClass(
			request.method, path, request.clientproto,
			request.getAllHeaders(), request.content.read(), request, responseEndCallback, statusCallback, setClientCallback)
		reactor.connectTCP(request.getRequestHostname(), 8080, clientFactory)

		return server.NOT_DONE_YET
