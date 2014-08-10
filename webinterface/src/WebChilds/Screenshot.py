from enigma import ePixmap, getDesktop
from twisted.web import resource, http, http_headers, server

from Tools.Log import Log

class ScreenshotResource(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)
		self._buffer = None

	def render(self, request):
		args = []
		append = args.append

		# some presets
		filename = 'screenshot'
		imageformat = ePixmap.FMT_JPEG
		format = 'jpg'
		jpgquali = '80'
		osd = False
		video = False

		for key, value in request.args.items():
			if key == 'format':
				format = value[0]
				if format == 'jpg':
					#-j (quality) produce jpg files instead of bmp
					#Quality Setting
					if 'jpgquali' in request.args:
						jpgquali = request.args["jpgquali"][0]
						del request.args['jpgquali']
				if format == 'png':
					imageformat = ePixmap.FMT_PNG
				if format == 'gif':
					imageformat = ePixmap.FMT_GIF
			elif key == 'filename':
				filename = value[0]
			else:
				if key == "osd":
					osd = True
				if key == "video":
					video = True
		if not osd and not video:
			osd = video = True
		
		filename = "%s.%s" %(filename, format)
		Log.i("osd=%s, video=%s, filename=%s" %(osd, video, filename))
		request.setHeader('Content-Disposition', 'inline; filename=%s;' %filename)
		mimetype = {'jpg' : 'jpeg'}.get(format, format)
		request.setHeader('Content-Type','image/%s' %mimetype)
		pixmap = ePixmap(None)
		size = getDesktop(0).size()
		if osd:
			if video:
				if not pixmap.setPixmapFromScreen(size):
					Log.w("Failed setting pixmap from Screen!")
			else:
				if not pixmap.setPixmapFromUI(size):
					Log.w("Failed setting pixmap from UI!")
		elif video:
			if not pixmap.setPixmapFromVideo(0, size):
				Log.w("Failed setting pixmap from Video!")

		buffer = pixmap.save(imageformat)
		if buffer:
			bytes = buffer.data()
			request.write(str(bytes))
			request.finish()
		return server.NOT_DONE_YET