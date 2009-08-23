from twisted.web import resource, static
from twisted.python import util

from Components.config import config

from Plugins.Extensions.WebInterface import __file__ 
from Screenpage import ScreenPage
from FileStreamer import FileStreamer
from Screengrab import GrabResource
from IPKG import IPKGResource
from PlayService import ServiceplayerResource
from Uploader import UploadResource
#from ServiceListSave import ServiceList
from RedirecToCurrentStream import RedirecToCurrentStreamResource

from External.__init__ import importExternalModules
externalChildren = []

def addExternalChild(child):
	externalChildren.append(child)

def getToplevel(session):
	print "[Webinterface.Toplevel].__init__ %s" %util.sibpath(__file__, "web-data/tpl/default")		
		
	file = static.File(util.sibpath(__file__, "web-data/tpl/default"))
	
	file.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"))) # "/web/*"
	file.putChild("web-data", static.File(util.sibpath(__file__, "web-data")))
	file.putChild("file", FileStreamer())
	file.putChild("grab", GrabResource())
	file.putChild("ipkg", IPKGResource())
	file.putChild("play", ServiceplayerResource(session))
	file.putChild("wap", RedirectorResource("/mobile/"))
	file.putChild("mobile", ScreenPage(session, util.sibpath(__file__, "mobile")))
	file.putChild("upload", UploadResource())
	#self.putChild("servicelist", ServiceList(session))
	file.putChild("streamcurrent", RedirecToCurrentStreamResource(session))
		
	if config.plugins.Webinterface.includemedia.value is True:
		file.putChild("media", static.File("/media"))
		file.putChild("hdd", static.File("/media/hdd"))
		
	
	importExternalModules()

	for child in externalChildren:
		if len(child) == 2:
			file.putChild(child[0], child[1])
	
	return file
		
class RedirectorResource(resource.Resource):
	"""
		this class can be used to redirect a request to a specified uri
	"""
	def __init__(self, uri):
		self.uri = uri
		resource.Resource.__init__(self)
	
	def render(self, request):
		request.redirect(self.uri)
		request.NOT_DONE_YET		

