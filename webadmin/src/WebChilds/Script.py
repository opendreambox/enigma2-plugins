# -*- coding: utf-8 -*-
from __future__ import absolute_import
from os import access, X_OK
from os.path import basename, dirname, isfile, join, realpath
from twisted.web import server, resource, http
from .PKG import PKGConsoleStream

class Script(resource.Resource):
	def render(self, request):
		command = request.args.get('command', [None])[0]
		if not command:
			request.setResponseCode(http.BAD_REQUEST)
			request.setHeader('Content-type', 'text/plain')
			return 'Missing parameter: command'

		args = command.split()
		if basename(args[0]) != args[0]:
			request.setResponseCode(http.BAD_REQUEST)
			request.setHeader('Content-type', 'text/plain')
			return 'Invalid command: %s' % args[0]

		path = join('/usr/script', args[0])
		if not isfile(path):
			request.setResponseCode(http.NOT_FOUND)
			request.setHeader('Content-type', 'text/plain')
			return 'Requested command not found.'

		if path.endswith('.sh') and access(path, X_OK):
			request.setResponseCode(http.OK)
			PKGConsoleStream(request, [ path ] + args)
			return server.NOT_DONE_YET

		request.setResponseCode(http.FORBIDDEN)
		request.setHeader('Content-type', 'text/plain')
		return 'Requested command is not an executable script.'
