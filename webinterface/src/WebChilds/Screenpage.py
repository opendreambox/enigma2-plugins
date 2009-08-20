from twisted.web import resource, http

from Plugins.Extensions.WebInterface import webif

import os

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: application/xhtml+xml charset: UTF-8
"""
AppTextHeaderFiles = ['stream.m3u.xml', 'ts.m3u.xml', 'streamcurrent.m3u.xml', 'movielist.m3u.xml', 'services.m3u.xml', ]

"""
 Actualy, the TextHtmlHeaderFiles should contain the updates.html.xml, but the IE then
 has problems with unicode-characters
"""
TextHtmlHeaderFiles = ['wapremote.xml', 'stream.xml', ]

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: text/html charset: UTF-8
"""
NoExplicitHeaderFiles = ['getpid.xml', 'tvbrowser.xml', ]

class ScreenPage(resource.Resource):
	def __init__(self, session, path):
		self.session = session
		self.path = path

	def render(self, req):

		if os.path.isfile(self.path):
			webif.renderPage(request, self.path, self.session) # login?
			if self.path.split("/")[-1] in AppTextHeaderFiles:
				request.setResponseCode(http.OK)
				request.setHeader('Content-type', 'application/text; charset=UTF-8')				
				#return http.Response(responsecode.OK,{'Content-type': http_headers.MimeType('application', 'text', (('charset', 'UTF-8'),))},stream=s)
				
			elif self.path.split("/")[-1] in TextHtmlHeaderFiles or (self.path.endswith(".html.xml") and self.path.split("/")[-1] != "updates.html.xml"):
				request.setResponseCode(http.OK)
				request.setHeader('Content-type', 'text/html; charset=UTF-8')								
				#return http.Response(responsecode.OK,{'Content-type': http_headers.MimeType('text', 'html', (('charset', 'UTF-8'),))},stream=s)
				
			elif self.path.split("/")[-1] in NoExplicitHeaderFiles:
				request.setResponseCode(http.OK)				
				
			else:
				request.setResponseCode(http.OK)

				request.setHeader('Content-type', 'application/xhtml+xml; charset=UTF-8')					
		else:
			request.setResponseCode(http.NOT_FOUND)			
		
		request.finish()

	def locateChild(self, request, segments):
		path = self.path + '/' + '/'.join(segments)
		if path[-1:] == "/":
			path += "index.html"
		path += ".xml"
		return ScreenPage(self.session, path), ()

