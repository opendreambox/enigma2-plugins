# -*- coding: iso-8859-1 -*-
from enigma import ePythonMessagePump
from Components.config import config
from Tools.Log import Log


from __init__ import decrypt_block
from ThreadQueue import ThreadQueue

from youtube_dl import YoutubeDL

from twisted.web import client
from twisted.internet import reactor
from urllib2 import Request, URLError, urlopen as urlopen2
from socket import gaierror, error
import os, socket, httplib
from urllib import quote, unquote_plus, unquote, urlencode
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException

from urlparse import parse_qs, parse_qsl
from threading import Thread

HTTPConnection.debuglevel = 1

from youtube.Base import buildYoutube
from youtube.Search import Search
from youtube.Videos import Videos
from youtube.VideoCategories import VideoCategories

def validate_cert(cert, key):
	buf = decrypt_block(cert[8:], key)
	if buf is None:
		return None
	return buf[36:107] + cert[139:196]

def get_rnd():
	try:
		rnd = os.urandom(8)
		return rnd
	except:
		return None

class GoogleSuggestions():
	def __init__(self):
		self.hl = "en"
		self.conn = None

	def prepareQuery(self):
		self.prepQuerry = "/complete/search?output=chrome&client=chrome&"
		if self.hl is not None:
			self.prepQuerry = self.prepQuerry + "hl=" + self.hl + "&"
		self.prepQuerry = self.prepQuerry + "jsonp=self.gotSuggestions&q="
		print "[MyTube - GoogleSuggestions] prepareQuery:",self.prepQuerry

	def getSuggestions(self, queryString):
		self.prepareQuery()
		if queryString is not "":
			query = self.prepQuerry + quote(queryString)
			self.conn = HTTPConnection("google.com")
			try:
				self.conn = HTTPConnection("google.com")
				self.conn.request("GET", query, "", {"Accept-Encoding": "UTF-8"})
			except (CannotSendRequest, gaierror, error):
				self.conn.close()
				print "[MyTube - GoogleSuggestions] Can not send request for suggestions"
				return None
			else:
				try:
					response = self.conn.getresponse()
				except BadStatusLine:
					self.conn.close()
					print "[MyTube - GoogleSuggestions] Can not get a response from google"
					return None
				else:
					if response.status == 200:
						data = response.read()
						header = response.getheader("Content-Type", "text/xml; charset=ISO-8859-1")
						charset = "ISO-8859-1"
						try:
							charset = header.split(";")[1].split("=")[1]
							print "[MyTube - GoogleSuggestions] Got charset %s" %charset
						except:
							print "[MyTube - GoogleSuggestions] No charset in Header, falling back to %s" %charset
						data = data.decode(charset).encode("utf-8")
						self.conn.close()
						return data
					else:
						self.conn.close()
						return None
		else:
			return None

class MyTubePlayerService():
#	Do not change the client_id and developer_key in the login-section!
#	ClientId: ytapi-dream-MyTubePlayer-i0kqrebg-0
#	DeveloperKey: AI39si4AjyvU8GoJGncYzmqMCwelUnqjEMWTFCcUtK-VUzvWygvwPO-sadNwW5tNj9DDCHju3nnJEPvFy4WZZ6hzFYCx8rJ6Mw

	cached_auth_request = {}
	current_auth_token = None
	yt_service = None

	def __init__(self):
		print "[MyTube] MyTubePlayerService - init"
		self.feedentries = []
		self.feed = None
		self._youtube = None
		self._currentQuery = None
		self._categories = []
		self._categoriesQuery = None

	def startService(self):
		print "[MyTube] MyTubePlayerService - startService"
		self._youtube = buildYoutube()
		self.loadCategories()
		#TODO Login
		# yt_service is reinit on every feed build; cache here to not reauth. remove init every time?
#		if self.current_auth_token is not None:
#			print "[MyTube] MyTubePlayerService - auth_cached"
#			self.yt_service.SetClientLoginToken(self.current_auth_token)
		
#		self.loggedIn = False
		#os.environ['http_proxy'] = 'http://169.229.50.12:3128'
		#proxy = os.environ.get('http_proxy')
		#print "FOUND ENV PROXY-->",proxy
		#for a in os.environ.keys():
		#	print a

	def stopService(self):
		print "[MyTube] MyTubePlayerService - stopService"

	def getLoginTokenOnCurl(self, email, pw):

		opts = {
		  'service':'youtube',
		  'accountType': 'HOSTED_OR_GOOGLE',
		  'Email': email,
		  'Passwd': pw,
		  'source': self.yt_service.client_id,
		}
		
		print "[MyTube] MyTubePlayerService - Starting external curl auth request"
		result = os.popen('curl -s -k -X POST "%s" -d "%s"' % (gdata.youtube.service.YOUTUBE_CLIENTLOGIN_AUTHENTICATION_URL , urlencode(opts))).read()
		
		return result

	def supportsSSL(self):
		return 'HTTPSConnection' in dir(httplib)

	def getFormattedTokenRequest(self, email, pw):
		return dict(parse_qsl(self.getLoginTokenOnCurl(email, pw).strip().replace('\n', '&')))
	
	def getAuthedUsername(self):
		# on external curl we can get real username
		if self.cached_auth_request.get('YouTubeUser') is not None:
			return self.cached_auth_request.get('YouTubeUser')

		if self.is_auth() is False:
			return ''

		# current gdata auth class save doesnt save realuser
		return 'Logged In'

	def auth_user(self, username, password):
		#todo auth_user
#		print "[MyTube] MyTubePlayerService - auth_use - " + str(username)
#
##		if self.yt_service is None:
##			self.startService()
#		
##		if self.current_auth_token is not None:
##			print "[MyTube] MyTubePlayerService - auth_cached"
##			self.yt_service.SetClientLoginToken(self.current_auth_token)
##			return
#
#		if self.supportsSSL() is False:
#			print "[MyTube] MyTubePlayerService - HTTPSConnection not found trying external curl"
#			self.cached_auth_request = self.getFormattedTokenRequest(username, password)
#			if self.cached_auth_request.get('Auth') is None:
#				raise Exception('Got no auth token from curl; you need curl and valid youtube login data')
#			
#			self.yt_service.SetClientLoginToken(self.cached_auth_request.get('Auth'))
#		else:
#			print "[MyTube] MyTubePlayerService - Using regularly ProgrammaticLogin for login"
#			self.yt_service.email = username
#			self.yt_service.password  = password
#			self.yt_service.ProgrammaticLogin()
#			
#		# double check login: reset any token on wrong logins
#		if self.is_auth() is False:
#			print "[MyTube] MyTubePlayerService - auth_use - auth not possible resetting"
#			self.resetAuthState()
#			return
#
#		print "[MyTube] MyTubePlayerService - Got successful login"
#		self.current_auth_token = self.auth_token()
		pass

	def resetAuthState(self):
		print "[MyTube] MyTubePlayerService - resetting auth"
		self.cached_auth_request = {}
		self.current_auth_token = None

#		if self.yt_service is None:
#			return
#
#		self.yt_service.current_token = None
#		self.yt_service.token_store.remove_all_tokens()

	def is_auth(self):
		return False
#		if self.current_auth_token is not None:
#			return True		
#		
#		if self.yt_service.current_token is None:
#			return False
		
#		return self.yt_service.current_token.get_token_string() != 'None'

	def auth_token(self):
		return ""
#		return self.yt_service.current_token.get_token_string()

	def getCategories(self):
		return self._categories

	def loadCategories(self):
		categories = VideoCategories(self._youtube)
		self._categoriesQuery = categories.list(self._onCategoriesReady)

	def _onCategoriesReady(self, success, data):
		if success:
			self._categories = data
		else:
			Log.w(data)

	def getFeed(self, callback = None, errorback = None, chart=None, videoCategoryId=None, ids=[]):
		Log.i()
		self.feedentries = []
		self._currentQuery = Videos(self._youtube)
		return self._currentQuery.list(callback, chart=chart, videoCategoryId=videoCategoryId, ids=ids)

	def search(self, searchTerm=None, startIndex=1, maxResults=50,
					orderby=Search.ORDER_RELEVANCE, time='all_time',
					lr="", categories="", relatedToVideoId=None,
					safeSearch=Search.SAFE_SEARCH_NONE, channelId=None,
					callback=None):
		Log.d()
		self._currentQuery = Search(self._youtube)
		return self._currentQuery.list(callback, searchTerm=searchTerm, order=orderby, maxResults=maxResults, relatedToVideoId=relatedToVideoId, channelId=channelId, safeSearch=safeSearch)

	def SubscribeToUser(self, username):
		try:
			new_subscription = self.yt_service.AddSubscriptionToChannel(username_to_subscribe_to=username)
	
			if isinstance(new_subscription, gdata.youtube.YouTubeSubscriptionEntry):
				print '[MyTube] MyTubePlayerService: New subscription added'
				return _('New subscription added')
			
			return _('Unknown error')
		except gdata.service.RequestError as req:
			return str('Error: ' + str(req[0]["body"]))
		except Exception as e:
			return str('Error: ' + e)
	
	def addToFavorites(self, video_id):
		try:
			video_entry = self.yt_service.GetYouTubeVideoEntry(video_id=video_id)
			response = self.yt_service.AddVideoEntryToFavorites(video_entry)
			
			# The response, if succesfully posted is a YouTubeVideoEntry
			if isinstance(response, gdata.youtube.YouTubeVideoEntry):
				print '[MyTube] MyTubePlayerService: Video successfully added to favorites'
				return _('Video successfully added to favorites')	
	
			return _('Unknown error')
		except gdata.service.RequestError as req:
			return str('Error: ' + str(req[0]["body"]))
		except Exception as e:
			return str('Error: ' + e)
	
	def getTitle(self):
		return ""

	def getEntries(self):
		return self.feedentries

	def itemCount(self):
		return ""

	def getTotalResults(self):
		return self._currentQuery and self._currentQuery.getTotalResults()

	def hasNextPage(self):
		return self._currentQuery and self._currentQuery.hasNextPage()

	def getNextPage(self):
		return self._currentQuery and self._currentQuery.nextPage()

	def getCurrentPage(self):
		return 1

myTubeService = MyTubePlayerService()

