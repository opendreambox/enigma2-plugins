# -*- coding: iso-8859-1 -*-
from enigma import ePythonMessagePump

from __init__ import decrypt_block
from ThreadQueue import ThreadQueue
import gdata.youtube
import gdata.youtube.service
from gdata.service import BadAuthentication

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

if 'HTTPSConnection' not in dir(httplib):
	# python on enimga2 has no https socket support
	gdata.youtube.service.YOUTUBE_USER_FEED_URI = 'http://gdata.youtube.com/feeds/api/users'

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

std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}

#config.plugins.mytube = ConfigSubsection()
#config.plugins.mytube.general = ConfigSubsection()
#config.plugins.mytube.general.useHTTPProxy = ConfigYesNo(default = False)
#config.plugins.mytube.general.ProxyIP = ConfigIP(default=[0,0,0,0])
#config.plugins.mytube.general.ProxyPort = ConfigNumber(default=8080)
#class MyOpener(FancyURLopener):
#	version = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'


class GoogleSuggestions():
	def __init__(self):
		self.hl = "en"
		self.conn = None

	def prepareQuery(self):
		#GET /complete/search?output=toolbar&client=youtube-psuggest&xml=true&ds=yt&hl=en&jsonp=self.gotSuggestions&q=s
		#self.prepQuerry = "/complete/search?output=toolbar&client=youtube&xml=true&ds=yt&"
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

class MyTubeFeedEntry():
	def __init__(self, feed, entry, favoritesFeed = False):
		self.feed = feed
		self.entry = entry
		self.favoritesFeed = favoritesFeed
		self.thumbnail = {}
		"""self.myopener = MyOpener()
		urllib.urlopen = MyOpener().open
		if config.plugins.mytube.general.useHTTPProxy.value is True:
			proxy = {'http': 'http://'+str(config.plugins.mytube.general.ProxyIP.getText())+':'+str(config.plugins.mytube.general.ProxyPort.value)}
			self.myopener = MyOpener(proxies=proxy)
			urllib.urlopen = MyOpener(proxies=proxy).open
		else:
			self.myopener = MyOpener()
			urllib.urlopen = MyOpener().open"""

	def isPlaylistEntry(self):
		return False

	def getTubeId(self):
		#print "[MyTubeFeedEntry] getTubeId"
		ret = None
		if self.entry.media.player:
			split = self.entry.media.player.url.split("=")
			ret = split.pop()
			if ret.startswith('youtube_gdata'):
				tmpval=split.pop()
				if tmpval.endswith("&feature"):
					tmp = tmpval.split("&")
					ret = tmp.pop(0)
		return ret

	def getTitle(self):
		#print "[MyTubeFeedEntry] getTitle",self.entry.media.title.text
		return self.entry.media.title.text

	def getDescription(self):
		#print "[MyTubeFeedEntry] getDescription"
		if self.entry.media is not None and self.entry.media.description is not None:
			return self.entry.media.description.text
		return "not vailable"

	def getThumbnailUrl(self, index = 0):
		#print "[MyTubeFeedEntry] getThumbnailUrl"
		if index < len(self.entry.media.thumbnail):
			return self.entry.media.thumbnail[index].url
		return None

	def getPublishedDate(self):
		if self.entry.published is not None:
			return self.entry.published.text
		return "unknown"

	def getViews(self):
		if self.entry.statistics is not None:
			return self.entry.statistics.view_count
		return "not available"

	def getDuration(self):
		if self.entry.media is not None and self.entry.media.duration is not None:
			return self.entry.media.duration.seconds
		else:
			return 0

	def getRatingAverage(self):
		if self.entry.rating is not None:
			return self.entry.rating.average
		return 0


	def getNumRaters(self):
		if self.entry.rating is not None:
			return self.entry.rating.num_raters
		return ""

	def getAuthor(self):
		authors = []
		for author in self.entry.author:
			authors.append(author.name.text)
		author = ", ".join(authors)
		return author

	def getUserFeedsUrl(self):
		for author in self.entry.author:
			return author.uri.text

		return False

	def getUserId(self):
		return self.getUserFeedsUrl().split('/')[-1]

	def subscribeToUser(self):
		username = self.getUserId()
		return myTubeService.SubscribeToUser(username)
		
	def addToFavorites(self):
		video_id = self.getTubeId()
		return myTubeService.addToFavorites(video_id)

	def PrintEntryDetails(self):
		EntryDetails = { 'Title': None, 'TubeID': None, 'Published': None, 'Published': None, 'Description': None, 'Category': None, 'Tags': None, 'Duration': None, 'Views': None, 'Rating': None, 'Thumbnails': None}
		EntryDetails['Title'] = self.entry.media.title.text
		EntryDetails['TubeID'] = self.getTubeId()
		EntryDetails['Description'] = self.getDescription()
		EntryDetails['Category'] = self.entry.media.category[0].text
		EntryDetails['Tags'] = self.entry.media.keywords.text
		EntryDetails['Published'] = self.getPublishedDate()
		EntryDetails['Views'] = self.getViews()
		EntryDetails['Duration'] = self.getDuration()
		EntryDetails['Rating'] = self.getNumRaters()
		EntryDetails['RatingAverage'] = self.getRatingAverage()
		EntryDetails['Author'] = self.getAuthor()
		# show thumbnails
		list = []
		for thumbnail in self.entry.media.thumbnail:
			print 'Thumbnail url: %s' % thumbnail.url
			list.append(str(thumbnail.url))
		EntryDetails['Thumbnails'] = list
		#print EntryDetails
		return EntryDetails

	def getVideoUrl(self):
		VIDEO_FMT_PRIORITY_MAP = {
			1 : '38', #MP4 Original (HD)
			2 : '37', #MP4 1080p (HD)
			3 : '22', #MP4 720p (HD)
			4 : '18', #MP4 360p
			5 : '35', #FLV 480p
			6 : '34', #FLV 360p
		}
		KEY_FORMAT_ID = u"format_id"
		KEY_URL = u"url"
		KEY_ENTRIES = u"entries"
		KEY_FORMATS = u"formats"

		video_url = None
		video_id = str(self.getTubeId())

		# Getting video webpage
		#URLs for YouTube video pages will change from the format http://www.youtube.com/watch?v=ylLzyHk54Z0 to http://www.youtube.com/watch#!v=ylLzyHk54Z0.
		watch_url = 'http://www.youtube.com/watch?v=%s' % video_id
		format_prio = "/".join(VIDEO_FMT_PRIORITY_MAP.itervalues())
		ytdl = YoutubeDL(params={"youtube_include_dash_manifest": False, "format" : format_prio})
		result = ytdl.extract_info(watch_url, download=False)
		if KEY_ENTRIES in result: # Can be a playlist or a list of videos
			entry = result[KEY_ENTRIES][0] #TODO handle properly
		else:# Just a video
			entry = result

		video_url = entry.get(KEY_URL)
		return str(video_url)

	def getRelatedVideos(self):
		print "[MyTubeFeedEntry] getRelatedVideos()"
		for link in self.entry.link:
			#print "Related link: ", link.rel.endswith
			if link.rel.endswith("video.related"):
				print "Found Related: ", link.href
				return link.href

	def getResponseVideos(self):
		print "[MyTubeFeedEntry] getResponseVideos()"
		for link in self.entry.link:
			#print "Responses link: ", link.rel.endswith
			if link.rel.endswith("video.responses"):
				print "Found Responses: ", link.href
				return link.href

	def getUserVideos(self):
		print "[MyTubeFeedEntry] getUserVideos()"
		username = self.getUserId()
		myuri = 'http://gdata.youtube.com/feeds/api/users/%s/uploads' % username
		print "Found Uservideos: ", myuri
		return myuri

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

	def startService(self):
		print "[MyTube] MyTubePlayerService - startService"

		self.yt_service = gdata.youtube.service.YouTubeService()

		# missing ssl support? youtube will help us on some feed urls
		self.yt_service.ssl = self.supportsSSL()

		# dont use it on class init; error on post and auth
		self.yt_service.developer_key = 'AI39si4AjyvU8GoJGncYzmqMCwelUnqjEMWTFCcUtK-VUzvWygvwPO-sadNwW5tNj9DDCHju3nnJEPvFy4WZZ6hzFYCx8rJ6Mw'
		self.yt_service.client_id = 'ytapi-dream-MyTubePlayer-i0kqrebg-0'

		# yt_service is reinit on every feed build; cache here to not reauth. remove init every time?
		if self.current_auth_token is not None:
			print "[MyTube] MyTubePlayerService - auth_cached"
			self.yt_service.SetClientLoginToken(self.current_auth_token)
		
#		self.loggedIn = False
		#os.environ['http_proxy'] = 'http://169.229.50.12:3128'
		#proxy = os.environ.get('http_proxy')
		#print "FOUND ENV PROXY-->",proxy
		#for a in os.environ.keys():
		#	print a

	def stopService(self):
		print "[MyTube] MyTubePlayerService - stopService"
		del self.ytService

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
		print "[MyTube] MyTubePlayerService - auth_use - " + str(username)

		if self.yt_service is None:
			self.startService()
		
		if self.current_auth_token is not None:
			print "[MyTube] MyTubePlayerService - auth_cached"
			self.yt_service.SetClientLoginToken(self.current_auth_token)
			return

		if self.supportsSSL() is False:
			print "[MyTube] MyTubePlayerService - HTTPSConnection not found trying external curl"
			self.cached_auth_request = self.getFormattedTokenRequest(username, password)
			if self.cached_auth_request.get('Auth') is None:
				raise Exception('Got no auth token from curl; you need curl and valid youtube login data')
			
			self.yt_service.SetClientLoginToken(self.cached_auth_request.get('Auth'))
		else:
			print "[MyTube] MyTubePlayerService - Using regularly ProgrammaticLogin for login"
			self.yt_service.email = username
			self.yt_service.password  = password
			self.yt_service.ProgrammaticLogin()
			
		# double check login: reset any token on wrong logins
		if self.is_auth() is False:
			print "[MyTube] MyTubePlayerService - auth_use - auth not possible resetting"
			self.resetAuthState()
			return

		print "[MyTube] MyTubePlayerService - Got successful login"
		self.current_auth_token = self.auth_token()

	def resetAuthState(self):
		print "[MyTube] MyTubePlayerService - resetting auth"
		self.cached_auth_request = {}
		self.current_auth_token = None

		if self.yt_service is None:
			return

		self.yt_service.current_token = None
		self.yt_service.token_store.remove_all_tokens()

	def is_auth(self):
		if self.current_auth_token is not None:
			return True		
		
		if self.yt_service.current_token is None:
			return False
		
		return self.yt_service.current_token.get_token_string() != 'None'

	def auth_token(self):
		return self.yt_service.current_token.get_token_string()

	def getFeedService(self, feedname):
		if feedname == "top_rated":
			return self.yt_service.GetTopRatedVideoFeed
		elif feedname == "most_viewed":
			return self.yt_service.GetMostViewedVideoFeed
		elif feedname == "recently_featured":
			return self.yt_service.GetRecentlyFeaturedVideoFeed
		elif feedname == "top_favorites":
			return self.yt_service.GetTopFavoritesVideoFeed
		elif feedname == "most_recent":
			return self.yt_service.GetMostRecentVideoFeed
		elif feedname == "most_discussed":
			return self.yt_service.GetMostDiscussedVideoFeed
		elif feedname == "most_linked":
			return self.yt_service.GetMostLinkedVideoFeed
		elif feedname == "most_responded":
			return self.yt_service.GetMostRespondedVideoFeed
		return self.yt_service.GetYouTubeVideoFeed

	def getFeed(self, url, feedname = "", callback = None, errorback = None):
		print "[MyTube] MyTubePlayerService - getFeed:",url, feedname
		self.feedentries = []
		ytservice = self.yt_service.GetYouTubeVideoFeed
		
		if feedname == "my_subscriptions":
			url = "http://gdata.youtube.com/feeds/api/users/default/newsubscriptionvideos"
		elif feedname == "my_favorites":
			url = "http://gdata.youtube.com/feeds/api/users/default/favorites"
		elif feedname == "my_history":
			url = "http://gdata.youtube.com/feeds/api/users/default/watch_history?v=2"
		elif feedname == "my_recommendations":
			url = "http://gdata.youtube.com/feeds/api/users/default/recommendations?v=2"
		elif feedname == "my_watch_later":
			url = "http://gdata.youtube.com/feeds/api/users/default/watch_later?v=2"
		elif feedname == "my_uploads":
			url = "http://gdata.youtube.com/feeds/api/users/default/uploads"
		elif feedname in ("hd", "most_popular", "most_shared", "on_the_web"):
			if feedname == "hd":
				url = "http://gdata.youtube.com/feeds/api/videos/-/HD"
			else:
				url = url + feedname
		elif feedname in ("top_rated","most_viewed","recently_featured","top_favorites","most_recent","most_discussed","most_linked","most_responded"):
			url = None
			ytservice = self.getFeedService(feedname)

		queryThread = YoutubeQueryThread(ytservice, url, self.gotFeed, self.gotFeedError, callback, errorback)
		queryThread.start()
		return queryThread

	def search(self, searchTerms, startIndex = 1, maxResults = 25,
					orderby = "relevance", time = 'all_time', racy = "include",
					author = "", lr = "", categories = "", sortOrder = "ascending",
					callback = None, errorback = None):
		print "[MyTube] MyTubePlayerService - search()"
		self.feedentries = []
		query = gdata.youtube.service.YouTubeVideoQuery()
		query.vq = searchTerms
		query.orderby = orderby
		query.time = time
		query.racy = racy
		query.sortorder = sortOrder
		if lr is not None:
			query.lr = lr
		if categories[0] is not None:
			query.categories = categories
		query.start_index = startIndex
		query.max_results = maxResults
		queryThread = YoutubeQueryThread(self.yt_service.YouTubeQuery, query, self.gotFeed, self.gotFeedError, callback, errorback)
		queryThread.start()
		return queryThread

	def gotFeed(self, feed, callback):
		if feed is not None:
			self.feed = feed
			for entry in self.feed.entry:
				MyFeedEntry = MyTubeFeedEntry(self, entry)
				self.feedentries.append(MyFeedEntry)
		if callback is not None:
			callback(self.feed)

	def gotFeedError(self, exception, errorback):
		if errorback is not None:
			errorback(exception)

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
		return self.feed.title.text

	def getEntries(self):
		return self.feedentries

	def itemCount(self):
		return self.feed.items_per_page.text

	def getTotalResults(self):
		if self.feed.total_results is None:
			return 0
				
		return self.feed.total_results.text

	def getNextFeedEntriesURL(self):
		for link in self.feed.link:
			if link.rel == "next":
				return link.href
		return None

	def getCurrentPage(self):
		if self.feed.start_index is None:
			return 1
		
		return int(int(self.feed.start_index.text) / int(self.itemCount())) + 1

class YoutubeQueryThread(Thread):
	def __init__(self, query, param, gotFeed, gotFeedError, callback, errorback):
		Thread.__init__(self)
		self.messagePump = ePythonMessagePump()
		self.messages = ThreadQueue()
		self.gotFeed = gotFeed
		self.gotFeedError = gotFeedError
		self.callback = callback
		self.errorback = errorback
		self.query = query
		self.param = param
		self.canceled = False
		self.messagepPump_conn = self.messagePump.recv_msg.connect(self.finished)

	def cancel(self):
		self.canceled = True

	def run(self):
		try:
			if self.param is None:
				feed = self.query()
			else:
				feed = self.query(self.param)
			self.messages.push((True, feed, self.callback))
			self.messagePump.send(0)
		except Exception, ex:
			self.messages.push((False, ex, self.errorback))
			self.messagePump.send(0)

	def finished(self, val):
		if not self.canceled:
			message = self.messages.pop()
			if message[0]:
				self.gotFeed(message[1], message[2])
			else:
				self.gotFeedError(message[1], message[2])

myTubeService = MyTubePlayerService()

