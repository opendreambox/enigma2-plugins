from enigma import eServiceReference, eServiceCenter, eEPGCache
from Components.StreamServerControl import streamServerControl
from Plugins.Extensions.WebInterface.auth import check_passwd
from Tools.Log import Log

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource

import voluptuous as vol
import json

from base64 import b64decode
from binascii import hexlify
from os import urandom


class DreamboxServerProtocol(WebSocketServerProtocol):
	API_VERSION = 1

	AUTH_FAIL_LIMIT = 3

	TYPE_RESULT = "result"
	TYPE_PING = "ping"
	TYPE_AUTH_REQUIRED = "auth_required"
	TYPE_AUTH_OK = "auth_ok"
	TYPE_AUTH = "auth"
	TYPE_GET_SERVICES = "get_services"
	TYPE_GET_EPG_NOWNEXT = "get_epg_nownext"
	TYPE_GET_STREAM_SETTINGS = "get_stream_settings"

	KEY_EPG_NOWNEXT = -1
	KEY_EPG_NOW = 0
	KEY_EPG_NEXT = 1

	REQUEST_BASE_SCHEMA = vol.Schema({
		vol.Required('id'): int,
		vol.Optional('cookie'): unicode,
	})

	BASE_MESSAGE_SCHEMA = REQUEST_BASE_SCHEMA.extend({
		vol.Required('type'): vol.Any(
				TYPE_AUTH,
				TYPE_GET_SERVICES,
				TYPE_GET_EPG_NOWNEXT,
				TYPE_GET_STREAM_SETTINGS,
				TYPE_PING
			)
	}, extra=vol.ALLOW_EXTRA)

	AUTH_MESSAGE_SCHEMA = REQUEST_BASE_SCHEMA.extend({
		vol.Required('type'): TYPE_AUTH,
		vol.Exclusive('token', 'auth'): unicode,
		vol.Exclusive('session', 'auth'): unicode,
	})

	GET_SERVICES_MESSAGE_SCHEMA = REQUEST_BASE_SCHEMA.extend({
		vol.Required('type'): TYPE_GET_SERVICES,
		vol.Required('reference'): unicode,
	})

	GET_EPG_NOWNEXT_MESSAGE_SCHEMA = REQUEST_BASE_SCHEMA.extend({
		vol.Required('type'): TYPE_GET_EPG_NOWNEXT,
		vol.Required('reference'): unicode,
		vol.Required('which'): vol.Any(
				KEY_EPG_NOWNEXT,
				KEY_EPG_NOW,
				KEY_EPG_NEXT
			)
	})

	GET_STREAM_SETTINGS_SCHEMA = REQUEST_BASE_SCHEMA.extend({
		vol.Required('type'): TYPE_GET_STREAM_SETTINGS
	})

	server = None
	session = None

	def __init__(self, *args, **kwargs):
		#we do have http basic auth, so whenever the user manages to load the page he is already authenticated
		self._authenticated = True
		self._failedAuthCount = 0
		self._sessionId = None
		self._requestID = 0
		Log.i("Protocol instance spawned!")

	def _disconnect(self, code=3401, reason=u'Authentication failed'):
		self.sendClose(code=code, reason=reason)

	def _genSID(self):
		return hexlify(urandom(32))

	def onConnect(self, request):
		Log.d("Client connecting: {0}".format(request.peer))
		return None

	def onOpen(self):
		self.checkAuth()

	def checkAuth(self):
		if self._authenticated:
			self.sendAuthOk()
			return
		else:
			self.sendAuthRequest()

	def onMessage(self, payload, isBinary):
		if isBinary:
			Log.w("Binary message received: {0} bytes".format(len(payload)))
		else:
			msg = json.loads(payload, 'utf8')
			Log.d("> %s" % (msg))
			self.onJSONMessage(msg)

	def onJSONMessage(self, msg):
		msg = self.validate(msg, self.BASE_MESSAGE_SCHEMA)
		if not msg:
			return
		self._requestID = msg["id"]
		do = 'do_{}'.format(msg['type'])
		getattr(self, do)(msg)

	def sendAuthOk(self):
		if not self._sessionId:
			self._sessionId = self._genSID()
			self.server.addSession(self._sessionId)
		self.sendJSON({"type": self.TYPE_AUTH_OK, "session": self._sessionId})

	def sendAuthRequest(self):
		self.sendJSON({"type": self.TYPE_AUTH_REQUIRED})

	def sendResult(self, id, result=None):
		msg = {
			"id": id,
			"type": self.TYPE_RESULT,
			"success": True,
			"result": result,
		}
		self.sendJSON(msg)

	def sendError(self, id, code, message=None):
		data = {
			"id": id,
			"type": self.TYPE_RESULT,
			"success": False,
			"error": {
				"code": code,
				"message": message,
			}
		}
		self.sendJSON(data)

	def sendJSON(self, msg):
		if not msg.has_key("id"):
			self._requestID += 1
			msg['id'] = self._requestID
		msg = json.dumps(msg).encode('utf8')
		Log.d("< %s" % (msg))
		self.sendMessage(msg)

	def onClose(self, wasClean, code, reason):
		print "WebSocket connection closed: {0}".format(code)

	def validate(self, msg, validator):
		try:
			return validator(msg)
		except Exception as e:
			self.sendError(msg.get("id", -1), -1, "INVALID CALL! %s" % e)

	def do_auth(self, msg):
		msg = self.validate(msg, self.AUTH_MESSAGE_SCHEMA)
		if not msg:
			return
		id = msg['id']
		if 'session' in msg:
			session = msg['session']
			if self.server.checkSession(session):
				Log.w("session: %s" % (session))
				self._sessionId = session
				self.sendAuthOk()
				return
			else:
				self.sendAuthRequest()
				return
		token = msg['token']
		login = b64decode(token)
		user, password = login.split(":", 1)
		if check_passwd(user, password):
			self._authenticated = True
			self.sendAuthOk()
			return

		self._authenticated = False
		self._failedAuthCount += 1
		if self._failedAuthCount >= self.AUTH_FAIL_LIMIT:
			self._disconnect()
		result = {}
		self.sendError(id, 401, "Login failed! Wrong Credentials?")

	def do_get_services(self, msg):
		msg = self.validate(msg, self.GET_SERVICES_MESSAGE_SCHEMA)
		if not msg:
			return
		id = msg['id']
		ref = msg['reference']
		sref = eServiceReference(str(msg['reference']))

		svcs = []
		serviceHandler = eServiceCenter.getInstance()
		info = serviceHandler.info(sref)
		sref.setName(info and info.getName(sref) or '')

		services = serviceHandler.list(sref)
		services = (services and services.getContent('SN', True)) or []
		for service in services:
			svcs.append({
				"reference": service[0],
				"name": service[1]
			})

		res = {
			"reference": ref,
			"name": sref.getName(),
			"data": svcs
		}
		self.sendResult(id, res)

	def do_get_epg_nownext(self, msg):
		msg = self.validate(msg, self.GET_EPG_NOWNEXT_MESSAGE_SCHEMA)
		if not msg:
			return
		id = msg['id']
		ref = str(msg['reference'])
		which = msg['which']

		serviceHandler = eServiceCenter.getInstance()
		sref = eServiceReference(ref)

		info = serviceHandler.info(sref)
		sref.setName(info and info.getName(sref) or '')

		lst = serviceHandler.list(sref)
		services = lst and lst.getContent('S', True)
		search = ['IBDCTSERNX']

		if services: # It's a Bouquet
			self.isBouquet = True
			if which == -1: #Now AND Next at once!
				append = search.append
				for service in services:
					append((service, 0, -1))
					append((service, 1, -1))
			else:
				search.extend([(service, which, -1) for service in services])
		else:
			search.append(ref, which, -1)
		events = eEPGCache.getInstance().lookupEvent(search)

		def evtToDict(event):
			return {
					"id": event[0],					#I
					"begin": event[1],					#B
					"duration": event[2],				#D
					"current": event[3],				#C
					"title": event[4],					#T
					"short_description": event[5],		#S
					"extended_description": event[6],	#E
					"reference": event[7],				#R
					"name": event[8],					#N
				}

		evts = []
		if self.isBouquet:
			for event in events:
				#IBDCTSERNX
				evts.append(evtToDict(event))
		else:
			evts.append(evtToDict(events))

		res = {
			"reference": ref,
			"name": sref.getName(),
			"data": evts or ()
		}
		self.sendResult(id, res)

	def do_get_stream_settings(self, msg):
		msg = self.validate(msg, self.GET_STREAM_SETTINGS_SCHEMA)
		if not msg:
			return
		id = msg['id']
		result = {
			"source": streamServerControl.config.streamserver.source.value,
			"audioBitrate": streamServerControl.config.streamserver.audioBitrate.value,
			"videoBitrate": streamServerControl.config.streamserver.videoBitrate.value,
			"resolution": streamServerControl.config.streamserver.resolution.value,
			"framerate": streamServerControl.config.streamserver.framerate.value,
			"gopLength": streamServerControl.config.streamserver.gopLength.value,
			"gopOnSceneChange": streamServerControl.config.streamserver.gopOnSceneChange.value,
			"openGop": streamServerControl.config.streamserver.openGop.value,
			"bFrames": streamServerControl.config.streamserver.bFrames.value,
			"pFrames": streamServerControl.config.streamserver.pFrames.value,
			"slices": streamServerControl.config.streamserver.slices.value,
			"level": streamServerControl.config.streamserver.level.value,
			"profile": streamServerControl.config.streamserver.profile.value,
			"lastService": streamServerControl.config.streamserver.lastservice.value,
		}
		self.sendResult(id, result)

	def do_ping(self, msg):
		self.sendJSON({"type": self.TYPE_PING})
