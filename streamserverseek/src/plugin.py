from Plugins.Plugin import PluginDescriptor

from enigma import eStreamServer, eEnv
from Components.StreamServerControl import streamServerControl

import os.path
import urllib

from Tools.Log import Log
from urlparse import parse_qs

from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage

from twisted.web import static
from twisted.python import util

def StreamServerControl__onUriParametersChanged(parameters):
	self = streamServerControl

	Log.i("%s" %(parameters))
	params = parse_qs(parameters)

	print "[StreamserverSeek] Old params: %s" % params
	self._seekToMin = 0
	if int(self.config.streamserver.source.value) == eStreamServer.INPUT_MODE_BACKGROUND:
		ts = False
		if "ts" in params:
			ts = params.get("ts", [False])[0]
			del params["ts"]
		self._seekToMin = 0
		min = 0
		if "min" in params:
			tmp = params.get("min", [False])[0]
			if "min" in params:
				del params["min"]
			try:
				min = int(tmp)
			except Exception, e:
				pass
		if ts and os.path.isfile(ts):
			params["ref"] = ["1:0:0:0:0:0:0:0:0:0:" + urllib.quote(ts)]
			if min and min > 0:
				self._seekToMin = min
				print "[StreamserverSeek] Will seek to %d minutes" % self._seekToMin
		print "[StreamserverSeek] New params: %s" % params

	self._applyUriParameters(params)
	for fnc in self.onUriParametersChanged:
		fnc(params)

streamServerControl._onUriParametersChanged_conn = streamServerControl._streamServer.uriParametersChanged.connect(StreamServerControl__onUriParametersChanged)

Orig_StreamServerControl__startEncoderService = streamServerControl._startEncoderService

def StreamServerControl__startEncoderService(service):
	self = streamServerControl
	result = Orig_StreamServerControl__startEncoderService(service)

	if result == self.ENCODER_SERVICE_SET or result == self.ENCODER_SERVICE_ALREADY_ACTIVE:
		if self._seekToMin and self.sourceState == True and self._encoderService and int(self.config.streamserver.source.value) == eStreamServer.INPUT_MODE_BACKGROUND:
			seek = self._encoderService.seek()
			if seek:
				print "[StreamserverSeek] Seeking to %d minutes" % self._seekToMin
				seek.seekTo(self._seekToMin * 60 * 90000)
			self._seekToMin = 0

streamServerControl._startEncoderService = StreamServerControl__startEncoderService

streamServerControl._seekToMin = 0

File = static.File

def autostart(reason,**kwargs):
	if "session" in kwargs:
		print "[StreamserverSeek] init"
		session = kwargs["session"]
		root = File(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/StreamServerSeek/web-data"))
		root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True) )
		addExternalChild( ("streamserverseek", root) )

def Plugins(**kwargs): 
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart)]
