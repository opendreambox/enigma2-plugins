# -*- coding: iso-8859-1 -*-
from Tools.Log import Log

from socket import gaierror, error
import os, httplib
from urllib import quote
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine

HTTPConnection.debuglevel = 1

from Plugins.SystemPlugins.TubeLib.youtube.Base import buildYoutube, loadCredentials, saveCredentials
from Plugins.SystemPlugins.TubeLib.youtube.Search import Search
from Plugins.SystemPlugins.TubeLib.youtube.Videos import Videos
from Plugins.SystemPlugins.TubeLib.youtube.VideoCategories import VideoCategories
from Plugins.SystemPlugins.TubeLib.youtube.YoutubeAuth import YoutubeAuth

from Tools.Directories import resolveFilename, SCOPE_CONFIG

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
	YT_CREDENTIALS_FILE = resolveFilename(SCOPE_CONFIG, "youtube-credentials-oauth2.json")

	cached_auth_request = {}
	current_auth_token = None
	yt_service = None

	def __init__(self):
		print "[MyTube] MyTubePlayerService - init"
		self.feedentries = []
		self.feed = None
		self.onReady = []
		self._ready = False
		self._youtube = None
		self._currentQuery = None
		self._categories = []
		self._categoriesQuery = None
		self._ytauth = None
		self._authenticated = False

	def addReadyCallback(self, callback):
		self.onReady.append(callback)
		if self.ready:
			callback(self.ready)

	def _onReady(self):
		Log.w()
		for fnc in self.onReady:
			fnc(self._ready)

	def isReady(self):
		return self._ready

	def setReady(self, ready):
		Log.w()
		self._ready = ready
		self._onReady()

	ready = property(isReady, setReady)

	def startService(self):
		print "[MyTube] MyTubePlayerService - startService"
		self._youtube = buildYoutube()
		self._authenticated = False
		self.loadCategories()
		self.setReady(True)

	def startAuthenticatedService(self, userCodeCallback):
		credentials = loadCredentials(self.YT_CREDENTIALS_FILE)
		if not credentials or credentials.invalid:
			self.startAuthFlow(userCodeCallback)
		else:
			self._onCredentialsReady(credentials)

	def startAuthFlow(self, userCodeCallback):
		Log.w()
		self._ytauth = YoutubeAuth()
		self._ytauth.onUserCodeReady.append(userCodeCallback)
		self._ytauth.onCredentialsReady.append(self._onCredentialsReady)
		self._ytauth.startAuthFlow()

	def cancelAuthFlow(self):
		if self._ytauth:
			self._ytauth.cancelAuthFlow()

	def _onCredentialsReady(self, credentials):
		saveCredentials(self.YT_CREDENTIALS_FILE, credentials)
		self._ytauth = None
		self._youtube = buildYoutube(credentials=credentials)
		self._authenticated = True
		self.loadCategories()
		self.setReady(True)

	def stopService(self):
		self.onReady = []
		self.cancelAuthFlow()
		print "[MyTube] MyTubePlayerService - stopService"

	def supportsSSL(self):
		return 'HTTPSConnection' in dir(httplib)

	def is_auth(self):
		return self._authenticated

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

