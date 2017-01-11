# -*- coding: utf-8 -*-
from os import chmod, close, rename, statvfs, unlink, write
from os.path import basename, isdir, isfile, join, realpath
from tempfile import mkstemp
from twisted.web import resource, http

class UploadTextResource(resource.Resource):
	default_uploaddir = '/tmp'
	modelist = {
		'/etc/apt/sources.list.d': 0644,
		'/usr/script': 0755,
		'/tmp': 0644,
	}

	def getArg(self, req, key, default=None):
		return req.args.get(key, [default])[0]

	def render_POST(self, req):
		print "[UploadTextResource] req.args ",req.args
		path = self.getArg(req, 'path', self.default_uploaddir)
		filename = self.getArg(req, 'filename')
		text = self.getArg(req, 'text')
		if not path or not filename or text is None:
			req.setResponseCode(http.BAD_REQUEST)
			req.setHeader('Content-type', 'text/plain')
			return 'Required parameters are path, filename and text.'

		if basename(filename) != filename:
			req.setResponseCode(http.BAD_REQUEST)
			req.setHeader('Content-type', 'text/plain')
			return 'Invalid filename specified.'

		path = realpath(path)
		if path not in self.modelist.keys():
			req.setResponseCode(http.FORBIDDEN)
			req.setHeader('Content-type', 'text/plain')
			return 'Invalid path specified.'

		if not isdir(path):
			req.setResponseCode(http.NOT_FOUND)
			req.setHeader('Content-type', 'text/plain')
			return 'Path does not exist.'

		filename = join(path, filename)
		if not text:
			if not isfile(filename):
				req.setResponseCode(http.NOT_FOUND)
				return ''
			unlink(filename)
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'text/plain')
			return 'Deleted %s' % filename

		text = text.replace('\r\n','\n')
		print "[UploadTextResource] text:", text

		fd, fn = mkstemp(dir=path)
		cnt = write(fd, text)
		close(fd)
		if cnt < len(text):
			try:
				unlink(fn)
			except OSError:
				pass
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'text/plain')
			return "error writing to disk, not uploaded"

		chmod(fn, self.modelist[path])
		rename(fn, filename)
		return """
					<?xml version="1.0" encoding="UTF-8"?>
					<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
							"http://www.w3.org/TR/html4/loose.dtd">
					<html>
					
					<head>
					<meta content="text/html; charset=UTF-8" http-equiv="content-type">
					
					<link href="/web-data/tpl/default/style.min.css" type="text/css" rel="stylesheet">
					<link rel="shortcut icon" type="image/x-icon" href="/web-data/img/favicon.ico">
					</head>
					<body onunload="javascript:opener.location.reload()" >
						<hr>
						<p align="left">
						uploaded to %s
						</p>
						<hr>
						<form>
							<input type="button" value="%s" onClick="window.close();">
						</form>
					</body>
					</html>""" %(filename, _("Close"))

	def render_GET(self, req):
		try:
			stat = statvfs(self.default_uploaddir)
		except OSError, e:
			req.setResponseCode(http.INTERNAL_SERVER_ERROR)
			return str(e)

		freespace = stat.f_bfree / 1000 * stat.f_bsize / 1000

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		return """
				<form method="POST" enctype="multipart/form-data">
				<table>
				<tr><td>Path to save (default: '%s')</td><td><input name="path"></td></tr>
				<tr><td>Filename to save<input name="filename"></td></tr>
				<tr><td><textarea name="textarea" rows=10 cols=100></textarea></td></tr>
				<tr><td colspan="2">Maximum file size: %d MB</td></tr>
				<tr><td colspan="2"><input type="submit"><input type="reset"></td><tr>
				</table>
				</form>
		""" % (self.default_uploaddir, freespace)
