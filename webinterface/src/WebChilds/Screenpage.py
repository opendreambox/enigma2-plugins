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
		resource.Resource.__init__(self)
		
		self.session = session
		self.path = path

	def render(self, request):	
		if os.path.isfile(self.path):	

# Set the Header according to what's requested								
			if self.path.split("/")[-1] in AppTextHeaderFiles:				
				request.setResponseCode(http.OK)
				request.setHeader('Content-Type', 'application/text')
				
			elif self.path.split("/")[-1] in TextHtmlHeaderFiles or (self.path.endswith(".html.xml") and self.path.split("/")[-1] != "updates.html.xml"):
				request.setResponseCode(http.OK)
				request.setHeader('Content-Type', 'text/html; charset=UTF-8')				
																					
			elif self.path.split("/")[-1] in NoExplicitHeaderFiles:
				request.setResponseCode(http.OK)				
				
			else:
				request.setResponseCode(http.OK)				
				request.setHeader('Content-Type', 'application/xhtml+xml; charset=UTF-8')	

# now go and write the Output			
			webif.renderPage(request, self.path, self.session) # login?
								
		else:
			request.setResponseCode(http.NOT_FOUND)

# request.finish() and server.NOT_DONE_YET are called inside webif.py (very bottom)		

	def getChild(self, path, request):
		path = "%s/%s" %(self.path, path)

		if path[-1:] == "/":
			path += "index.html"
		path += ".xml"
		return ScreenPage(self.session, path)

