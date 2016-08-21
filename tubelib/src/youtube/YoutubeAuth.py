from enigma import HBBTV_USER_AGENT
from Tools.Log import Log

from oauth2client.client import OAuth2Credentials
from time import time
from twisted.internet import reactor
from twisted.internet.defer import succeed
from twisted.internet.ssl import ClientContextFactory
from twisted.web.client import Agent, PartialDownloadError
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implements
from readBody import readBody

import json

class StringProducer(object):
	implements(IBodyProducer)

	def __init__(self, body):
		self.body = body
		self.length = len(body)

	def startProducing(self, consumer):
		consumer.write(self.body)
		return succeed(None)

	def pauseProducing(self):
		pass

	def stopProducing(self):
		pass

class GoogleUserCode(object):
	def __init__(self, data):
		self._data = data
		self.device_code = self._data['device_code']
		self.interval = int(self._data['interval'])
		self.user_code = self._data['user_code']
		self.verification_url = data['verification_url']
		self._expires_at = time() + int(self._data['expires_in'])

	def expired(self):
		print "Expires in %s" % (self._expires_at - time())
		return time() >= self._expires_at

	def __str__(self):
		return "[GoogleUserCode] %s" % (self._data,)

class WebClientContextFactory(ClientContextFactory):
	def getContext(self, hostname, port):
		return ClientContextFactory.getContext(self)

class YoutubeAuth(object):
	AUTH_SCOPE_YT = "https://www.googleapis.com/auth/youtube"
	AUTH_SCOPE_YT_RO = "https://www.googleapis.com/auth/youtube.readonly"
	AUTH_SCOPE_YT_FORCE_SSL = "https://www.googleapis.com/auth/youtube.force-ssl"

	AUTH_REQUEST_URI = "https://accounts.google.com/o/oauth2/device/code"
	AUTH_RESPONSE_URI = "https://accounts.google.com/o/oauth2/token"
	GRANT_TYPE_DEVICE_AUTH = "http://oauth.net/grant_type/device/1.0"
	GRANT_TYPE_REFRESH_CREDENTIALS = "refresh_token"

	CLIENT_ID = "59698529433-7n49jvm74m8mfkpjp2i1s2l18vsj35fu.apps.googleusercontent.com"
	CLIENT_SECRET = "QaAAkmuTmYDo35vZt8aQ093N"

	ERROR_AUTH_REQUEST = 0
	ERROR_AUTH_REQUEST_PARSE = 1
	ERROR_CREDENTIALS_REQUEST = 2
	ERROR_CREDENTIALS_REQUEST_PARSE = 3
	ERROR_CREDENTIALS_REQUEST_EXPIRED = 4
	ERROR_CREDENTIALS_UNKOWN = 5

	USER_AGENT = HBBTV_USER_AGENT

	def __init__(self, scope=AUTH_SCOPE_YT_RO):
		self._auth_scope = scope
		self._agent = Agent(reactor, WebClientContextFactory())
		self.onUserCodeReady = []
		self.onCredentialsReady = []
		self.onError = []
		self._user_code = None
		self._requestDeferred = None
		self._responseDeferred = None
		self._canceled = False

	def cleanup(self):
		if self._requestDeferred:
			self._requestDeferred.cancel()
		if self._responseDeferred:
			self._responseDeferred.cancel()

	def startAuthFlow(self):
		self._canceled = False
		d = self._agent.request(
			'POST',
			self.AUTH_REQUEST_URI,
			Headers({
				'User-Agent' : [self.USER_AGENT],
				'Content-Type' : ["application/x-www-form-urlencoded"],
			}),
			StringProducer("client_id=%s&scope=%s" % (self.CLIENT_ID, self._auth_scope))
		)
		d.addCallbacks(self._onRequestResponse, self._onRequestError)
		self._requestDeferred = d
		return d;

	def cancelAuthFlow(self):
		self._canceled = True

	def _onError(self, type, errorText=""):
		print "ERROR! %s, %s" % (type, errorText)
		self._requestDeferred = None
		for fnc in self.onError:
			fnc(type, errorText)

	def _onRequestResponse(self, response):
		self._requestDeferred = None
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		readBody(response).addCallback(self._onRequestBodyReady).addErrback(self._onRequestBodyError)

	def _onRequestError(self, error):
		self._requestDeferred = None
		if self._canceled:
			Log.d("Auth Request canceled")
		self._onError(self.ERROR_AUTH_REQUEST, str(error))

	def _onRequestBodyReady(self, body):
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		self._parseAuthRequestResponse(body)
		self._pollForResult()

	def _onRequestBodyError(self, failure):
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		if isinstance(failure.value, PartialDownloadError):
			self._onRequestBodyReady(failure.value.response)
		else:
			self._onError(self.ERROR_AUTH_REQUEST, str(failure))

	def _parseAuthRequestResponse(self, body):
		response = json.loads(body)
		self._user_code = GoogleUserCode(response)
		for fnc in self.onUserCodeReady:
			fnc(self._user_code)

	def _pollForResult(self):
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		if self._user_code.expired():
			self._onError(self.ERROR_CREDENTIALS_REQUEST_EXPIRED)
			return
		d = self._agent.request(
			'POST',
			self.AUTH_RESPONSE_URI,
			Headers({
				'User-Agent' : [self.USER_AGENT],
				'Content-Type' : ["application/x-www-form-urlencoded"],
			}),
			StringProducer("client_id=%s&client_secret=%s&code=%s&grant_type=%s" % (self.CLIENT_ID, self.CLIENT_SECRET, str(self._user_code.device_code), self.GRANT_TYPE_DEVICE_AUTH))
		)
		d.addCallbacks(self._onCredentialsPollResponse, self._onCredentialsPollError)
		self._responseDeferred = d
		return d;

	def _onCredentialsPollResponse(self, response):
		self._responseDeferred = None
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		readBody(response).addCallback(self._onCredentialsPollBodyReady).addErrback(self._onCredentialsPollBodyError)

	def _onCredentialsPollError(self, error):
		self._responseDeferred = None
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		self._onError(self.ERROR_CREDENTIALS_REQUEST, str(error))

	def _onCredentialsPollBodyReady(self, body):
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		result = json.loads(body)
		error = result.get("error", None)
		if error:
			if error == "authorization_pending":
				print "not ready, yet"
				reactor.callLater(self._user_code.interval, self._pollForResult)
			elif error == "slow_down":
				print "too fast, slowing down"
				self._device_code.interval = self._device_code.interval * 2
			elif error == "expired_token":
				self._onError(self.ERROR_CREDENTIALS_REQUEST_EXPIRED)
			else:
				print result
				self._onError(self.ERROR_CREDENTIALS_REQUEST_PARSE, error)
		elif "access_token" in result:
			access_token = result.get("access_token")
			refresh_token = result.get("refresh_token")
			token_expiry = str( int(time()) + int(result.get("expires_in")) )
			self._credentials = OAuth2Credentials(access_token, self.CLIENT_ID, self.CLIENT_SECRET, refresh_token, token_expiry, self.AUTH_REQUEST_URI, self.USER_AGENT)
			for fnc in self.onCredentialsReady:
				fnc(self._credentials)
		else:
			self._onError(self.ERROR_CREDENTIALS_REQUEST_PARSE, error)

	def _onCredentialsPollBodyError(self, failure):
		if self._canceled:
			Log.d("Auth Request canceled")
			return
		if isinstance(failure.value, PartialDownloadError):
			self._onCredentialsPollBodyReady(failure.value.response)
		else:
			self._onError(self.ERROR_CREDENTIALS_REQUEST_PARSE, str(failure))

if __name__ == "__main__":
	def userCodeReady(userCode):
		print "%s => %s" % (userCode.verification_url, userCode.user_code)

	def credentialsReady(credentials):
		print "CREDENTIALS READY: %s" % (credentials.to_json(),)

	yta = YoutubeAuth()
	yta.onUserCodeReady.append(userCodeReady)
	yta.onCredentialsReady.append(credentialsReady)
	yta.startAuthFlow()
	reactor.run()
