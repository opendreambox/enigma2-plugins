from Plugins.Plugin import PluginDescriptor

from enigma import eEnv
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from WebChilds.ScreenPageCORS import ScreenPageCORS

from twisted.web import static
from twisted.python import util
from twisted.internet import reactor
from twisted.web.server import GzipEncoderFactory
from twisted.web.resource import EncodingResourceWrapper

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek
from WebChilds.Stream import StreamResource
from WebChilds.Proxy import ProxyResource
from WebChilds.Vod import VodResource

import Plugins.Extensions.WebInterface.WebChilds.Toplevel

import os.path
import tempfile

if hasattr(static.File, 'render_GET'):
	class File(static.File):
		def render_POST(self, request):
			return self.render_GET(request)
else:
	File = static.File

class M3u8GzipEncoderFactory(GzipEncoderFactory):
	def encoderForRequest(self, request):
		if request.postpath[0].startswith("stream.m3u8"):
			return GzipEncoderFactory.encoderForRequest(self, request)

class MyFile(File):
	def removeTmpFile(self):
		# close delayed, otherwise server returns 404
		self.tempFile.close()
		self.tempFile = None

	def getChild(self, path, request):
		if request.path == '/stream/js/main.js':
			print "[StreamServerSeek] Manipulating main.js"
			with open(os.path.abspath(util.sibpath(__file__, "../WebInterface/stream/js/main.js"))) as origFile:
				self.tempFile = tempfile.NamedTemporaryFile()
				for line in origFile:
					if line.strip("\t").startswith("var _streamHost"):
						self.tempFile.write("\tvar _streamHost = 'http://' + window.document.location.host + '/streamserverseek/proxy';\n")
					elif line.strip("\t").startswith("loadServicesInternal("):
						self.tempFile.write(line)
						self.tempFile.write("		if (window.location.href.match(/sss-vod$/)) {\n")
						self.tempFile.write("			_streamHost = 'http://' + window.document.location.host + '/streamserverseek/vod';\n")
						self.tempFile.write("			playInternal();\n")
						self.tempFile.write("			$('.plyr__progress').css('visibility', 'visible');\n")
						self.tempFile.write("			if (window.history.pushState)\n")
						self.tempFile.write("				window.history.replaceState({}, document.title, '/stream/');\n")
						self.tempFile.write("			$('.mdl-snackbar__text').html('StreamServerSeek - Loading...');\n")
						self.tempFile.write("		}\n")
					elif line.strip("\t").startswith("_hls = new Hls("):
						self.tempFile.write("		config.maxMaxBufferLength = 15;\n")
						self.tempFile.write(line)
					elif line.strip("\t").startswith("_hls.attachMedia(_videoElement);"):
						self.tempFile.write(line)
						self.tempFile.write("		$('.plyr__progress input').change(function(){\n")
						self.tempFile.write("			_hls.currentLevel = -1; // clear buffer, so segments will be redownloaded - otherwise streamserverseek doesn't know where to seek to\n")
						self.tempFile.write("			notify('StreamServerSeek - Seeking...');\n")
						self.tempFile.write("		});\n")
					elif line.strip("\t").startswith("function onServiceClick("): #)
						self.tempFile.write(line)
						self.tempFile.write("		if (_streamHost.match(/vod$/)) {\n")
						self.tempFile.write("			_streamHost = 'http://' + window.document.location.host + '/streamserverseek/proxy';\n")
						self.tempFile.write("			if (_hls != null) {\n")
						self.tempFile.write("				_hls.loadSource(_streamHost + '/stream.m3u8');\n")
						self.tempFile.write("				_hls.attachMedia(_videoElement);\n")
						self.tempFile.write("			}\n")
						self.tempFile.write("			$('.plyr__progress').css('visibility', 'hidden');\n")
						self.tempFile.write("		}\n")
					else:
						self.tempFile.write(line)
				self.tempFile.flush()
				self.defaultType = "application/javascript"
				reactor.callLater(1, self.removeTmpFile)
				return self.createSimilarFile(self.tempFile.name)

		return File.getChild(self, path, request)

Orig_Toplevel_getToplevel = Plugins.Extensions.WebInterface.WebChilds.Toplevel.getToplevel

def Toplevel_getToplevel(session):
	result = Orig_Toplevel_getToplevel(session)
	result.putChild("stream", MyFile(util.sibpath(__file__, "../WebInterface/stream")))
	print "[StreamServerSeek] hooked WebInterface.WebChilds.Toplevel.getToplevel"
	return result

Plugins.Extensions.WebInterface.WebChilds.Toplevel.getToplevel = Toplevel_getToplevel

def autostart(reason,**kwargs):
	if "session" in kwargs:
		sss = StreamServerSeek(session = kwargs["session"])
		print "session %s" % sss

		root = File(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/StreamServerSeek/web-data"))
		root.putChild("web", ScreenPageCORS(kwargs["session"], util.sibpath(__file__, "web"), True) )
		root.putChild("stream", StreamResource(kwargs["session"]))
		root.putChild("proxy", ProxyResource(kwargs["session"]))
		root.putChild("vod", EncodingResourceWrapper(VodResource(kwargs["session"]), [M3u8GzipEncoderFactory()]))
		addExternalChild( ("streamserverseek", root) )

def Plugins(**kwargs): 
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart)]
