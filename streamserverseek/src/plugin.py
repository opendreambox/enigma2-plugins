from Plugins.Plugin import PluginDescriptor

from enigma import eEnv
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from WebChilds.ScreenPageCORS import ScreenPageCORS

from twisted.web import static
from twisted.python import util

from Plugins.Extensions.StreamServerSeek.StreamServerSeek import StreamServerSeek
from WebChilds.Stream import StreamResource
from WebChilds.Proxy import ProxyResource

import Plugins.Extensions.WebInterface.WebChilds.Toplevel

if hasattr(static.File, 'render_GET'):
	class File(static.File):
		def render_POST(self, request):
			return self.render_GET(request)
else:
	File = static.File

class MyFile(File):
	def getChild(self, path, request):
		if (request.path == '/web-data/tpl/default/tplMovieList.htm'):
			print "[StreamserverSeek] Serve own version of /web-data/tpl/default/tplMovieList.htm"
			return self.createSimilarFile(util.sibpath(__file__, "webinterface-data/tpl/default/tplMovieList.htm"))

		return File.getChild(self, path, request)

Orig_Toplevel_getToplevel = Plugins.Extensions.WebInterface.WebChilds.Toplevel.getToplevel

def Toplevel_getToplevel(session):
	result = Orig_Toplevel_getToplevel(session)
	result.putChild("web-data", MyFile(util.sibpath(__file__, "../WebInterface/web-data")))
	print "[StreamserverSeek] hooked WebInterface.WebChilds.Toplevel.getToplevel"
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
		addExternalChild( ("streamserverseek", root) )

def Plugins(**kwargs): 
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart)]
