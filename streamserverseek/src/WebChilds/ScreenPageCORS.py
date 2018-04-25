from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage

class ScreenPageCORS(ScreenPage):
	def render(self, request):
		request.setHeader('Access-Control-Allow-Origin', '*')
		return ScreenPage.render(self, request)

	def getChild(self, path, request):
		path = "%s/%s" % (self.path, path)

		if path[-1] == "/":
			path += "index.html"

		path += ".xml"
		return ScreenPageCORS(self.session, path)
