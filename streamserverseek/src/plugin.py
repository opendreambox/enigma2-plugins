from Plugins.Plugin import PluginDescriptor

from enigma import eEnv
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from WebChilds.ScreenPageCORS import ScreenPageCORS

from twisted.web import static
from twisted.python import util

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek
from WebChilds.Stream import StreamResource
from WebChilds.Proxy import ProxyResource

if hasattr(static.File, 'render_GET'):
	class File(static.File):
		def render_POST(self, request):
			return self.render_GET(request)
else:
	File = static.File

def autostart(reason,**kwargs):
	if "session" in kwargs:
		sss = StreamServerSeek(session = kwargs["session"])
		print "session %s" % sss

		root = File(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/StreamServerSeek/web-data"))
		root.putChild("web", ScreenPageCORS(kwargs["session"], util.sibpath(__file__, "web"), True) )
		root.putChild("stream", StreamResource(kwargs["session"]))
		root.putChild("proxy", ProxyResource(kwargs["session"]))
		addExternalChild( ("streamserverseek", root) )

def Plugins(**kwargs): 
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart)]
