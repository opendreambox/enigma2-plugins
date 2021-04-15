from twisted.web import resource, http, server, static

from Plugins.Extensions.WebInterface import webif

from os import path as os_path

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: application/xhtml+xml charset: UTF-8
"""
AppTextHeaderFiles = frozenset(('stream.m3u.xml', 'ts.m3u.xml', 'streamcurrent.m3u.xml', 'movielist.m3u.xml', 'services.m3u.xml', ))

"""
Actualy, the TextHtmlHeaderFiles should contain the updates.html.xml, but the IE then
has problems with unicode-characters
"""
TextHtmlHeaderFiles = frozenset(('wapremote.xml', 'stream.xml', ))

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: text/html charset: UTF-8
"""
NoExplicitHeaderFiles = frozenset(('getpid.xml', 'tvbrowser.xml', ))

"""
	define all files in /web with a text/javascript header
"""
TextJavascriptHeaderFiles = frozenset(('strings.js.xml', ))

resource.ErrorPage.template = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>%(code)s - %(brief)s</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>

        * {
            line-height: 1.2;
            margin: 0;
        }

        html {
            color: #888;
            display: table;
            font-family: sans-serif;
            height: 100%%;
            text-align: center;
            width: 100%%;
        }

        body {
            display: table-cell;
            vertical-align: middle;
            margin: 2em auto;
        }

        h1 {
            color: #555;
            font-size: 2em;
            font-weight: 400;
        }

        p {
            margin: 0 auto;
            width: 280px;
        }

        @media only screen and (max-width: 280px) {

            body, p {
                width: 95%%;
            }

            h1 {
                font-size: 1.5em;
                margin: 0 0 0.3em;
            }

        }

    </style>
</head>
<body>
    <h1>%(code)s - %(brief)s</h1>
    <p>%(detail)s</p>
</body>
</html>
<!-- IE needs 512+ bytes: https://blogs.msdn.microsoft.com/ieinternals/2010/08/18/friendly-http-error-pages/ -->
"""


class ScreenPage(resource.Resource):
	def __init__(self, session, path, addSlash=False):
		resource.Resource.__init__(self)

		self.session = session
		self.path = path
		self.addSlash = addSlash

	def render(self, request):
		path = self.path
		if os_path.isfile(path):
			lastComponent = path.split('/')[-1]

			# Set the Header according to what's requested
			if lastComponent in AppTextHeaderFiles:
				request.setHeader('Content-Type', 'application/text')
			elif lastComponent in TextHtmlHeaderFiles or (path.endswith(".html.xml") and lastComponent != "updates.html.xml"):
				request.setHeader('Content-Type', 'text/html; charset=UTF-8')
			elif lastComponent in TextJavascriptHeaderFiles:
				request.setHeader('Content-Type', 'text/javascript; charset=UTF-8')
			elif lastComponent not in NoExplicitHeaderFiles:
				request.setHeader('Content-Type', 'application/xhtml+xml; charset=UTF-8')
			# now go and write the Output
			# request.finish() is called inside webif.py (requestFinish() which is called via renderPage())
			webif.renderPage(request, path, self.session) # login?
			request.setResponseCode(http.OK)

		elif os_path.isdir(path) and self.addSlash is True:
			uri = "%s/" % (request.path)
			request.redirect(uri)
			return ""

		else:

			return resource.ErrorPage(http.NOT_FOUND, "Page Not Found", "Sorry, but the page you were trying to view does not exist.").render(request)

		return server.NOT_DONE_YET

	def getChild(self, path, request):
		path = "%s/%s" % (self.path, path)

		if path[-1] == "/":
			path += "index.html"

		path += ".xml"
		return ScreenPage(self.session, path)

