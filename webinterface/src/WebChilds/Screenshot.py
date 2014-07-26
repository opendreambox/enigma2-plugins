from enigma import ePixmap, getDesktop
from twisted.web import resource, http, http_headers, server

from Tools.Log import Log

class ScreenshotResource(resource.Resource):
	SPECIAL_ARGS = ('format', 'filename', 'save')

	def render(self, request):
		args = []
		append = args.append

		# some presets
		filename = 'screenshot'
		imageformat = ePixmap.FMT_JPEG
		extension = 'jpg'
		jpgquali = '80'
		osd = False
		video = False
		save = False

		for key, value in request.args.items():
			if key in ScreenshotResource.SPECIAL_ARGS:
				if key == 'extension':
					extension = value[0]

					if extension == 'jpg':
						#-j (quality) produce jpg files instead of bmp
						#Quality Setting
						if 'jpgquali' in request.args:
							jpgquali = request.args["jpgquali"][0]
							del request.args['jpgquali']
					if extension == 'png':
						imageformat = ePixmap.FMT_PNG
					if extension == 'gif':
						imageformat = ePixmap.FMT_GIF
				elif key == 'filename':
					filename = value[0]

				elif key == 'save':
					save = True
			else:
				if key == "o":
					osd = True
				if key == "v":
					video = True
		if not osd and not video:
			osd = video = True
		
		filename = "%s.%s" %(filename, extension)
		
		request.setHeader('Content-Disposition', 'inline; filename=%s;' %filename)
		mimetype = {'jpg' : 'jpeg'}.get(extension, extension)
		request.setHeader('Content-Type','image/%s' %mimetype)
		pixmap = ePixmap(None)
		size = getDesktop(0).size()
		if osd:
			if video:
				pixmap.setPixmapFromScreen(size)
			else:
				pixmap.setPixmapFromUI(size)
		elif video:
			pixmap.setPixmapFromVideo(0, size)

#		if save:
#			pixmap.save(imageformat, "/tmp/%s" %filename)
		
		buffer = pixmap.save(imageformat)
		buffer.data()
		return bytes
