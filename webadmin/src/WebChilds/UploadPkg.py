# -*- coding: utf-8 -*-
from __future__ import absolute_import
from os import close, unlink, write
from os.path import basename
from tempfile import mkstemp
from twisted.web import http, resource, server

from .PKG import PKGConsoleStream

class UploadPkgResource(resource.Resource):
	res="""
	<?xml version="1.0" encoding="UTF-8"?>
	<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
			"http://www.w3.org/TR/html4/loose.dtd">
	<html>
					
	<head>
		<link rel="shortcut icon" type="/web-data/image/x-icon" href="/web-data/img/favicon.ico">
		<meta content="text/html; charset=UTF-8" http-equiv="content-type">
		<script type="text/javascript">
		</script>
	</head>
	<body onunload="javascript:opener.location.reload()" >
		<p>DEB: %s</p>
		<br>
		<form>
			<input type="button" value="%s" onClick="javascript:window.close();">
			<input type="button" value="Package %s" onClick="javascript:location='uploadpkg'";>
		</form>
	</body>
	</html>
	"""
			
	def render_POST(self, req):
		data = req.args['file'][0]
		if not data:
			req.setResponseCode(http.OK)
			return self.res % ( _("filesize was 0, not uploaded") ,
					_("Close"),
					 _("Add")
					)
		
		fd, fn = mkstemp(suffix='.deb')
		cnt = write(fd, data)
		close(fd)
		if cnt < len(data):
			try:
				unlink(fn)
			except OSError:
				pass
			req.setResponseCode(http.OK)
			return self.res % (_("error writing to disk, not uploaded"), _("Close"), _("Add"))

		cmd = ['/usr/bin/dpkg', 'dpkg', '-i', fn]
		req.setResponseCode(http.OK)
		PKGConsoleStream(req, cmd)
		return server.NOT_DONE_YET

	def render_GET(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		return """
				<?xml version="1.0" encoding="UTF-8"?>
				<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
						"http://www.w3.org/TR/html4/loose.dtd">
				<html>
					
				<head>
				<link rel="shortcut icon" type="/web-data/image/x-icon" href="/web-data/img/favicon.ico">
				<meta content="text/html; charset=UTF-8" http-equiv="content-type">
				<script type="text/javascript">
				function getPkgFilename(){
					var frm = document.forms["form_uploadpkg"];
					frm.filename.value = frm.file.value;
				}
				</script>
				</head>
				<body onunload="javascript:opener.location.reload()" onload="window.scrollBy(0,1000000);" >
				<form name="form_uploadpkg" method="POST" enctype="multipart/form-data">
				DEB %s:
				<input name="file" type="file" size="50" maxlength="100000" accept="text/*" onchange="getPkgFilename();">
				<br>
				<input type="hidden" name="filename" value="">
				<input type="submit">
				</form>
				</body>
				</html>
		""" % _("Add")
