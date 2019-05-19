from __future__ import print_function
from Plugins.Plugin import PluginDescriptor

from enigma import eEnv
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from WebChilds.ScreenPageCORS import ScreenPageCORS

from twisted.web import static
from twisted.python import util
from twisted.web.server import GzipEncoderFactory
from twisted.web.resource import EncodingResourceWrapper

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek
from WebChilds.Stream import StreamResource
from WebChilds.Proxy import ProxyResource
from WebChilds.Vod import VodResource

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

def autostart(reason,**kwargs):
	if "session" in kwargs:
		sss = StreamServerSeek(session = kwargs["session"])
		print("session %s" % sss)

		root = File(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/StreamServerSeek/web-data"))
		root.putChild("web", ScreenPageCORS(kwargs["session"], util.sibpath(__file__, "web"), True) )
		root.putChild("stream", StreamResource(kwargs["session"]))
		root.putChild("proxy", ProxyResource(kwargs["session"]))
		root.putChild("vod", EncodingResourceWrapper(VodResource(kwargs["session"]), [M3u8GzipEncoderFactory()]))
		addExternalChild( ("streamserverseek", root) )

def Plugins(**kwargs): 
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart)]
