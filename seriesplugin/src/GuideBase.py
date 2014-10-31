# by betonme @2012

import os, sys, traceback
from time import time

from twisted.web.client import getPage as twGetPage

from Tools.BoundFunction import boundFunction

# Plugin internal
from ModuleBase import ModuleBase
from Logger import splog


# Max Age (in seconds) of each feed in the cache
INTER_QUERY_TIME = 600


# This dict structure will be the following:
# { 'URL': (TIMESTAMP, value) }
cache = {}


class GuideBase(ModuleBase):
	def __init__(self):
		ModuleBase.__init__(self)
		self.deferreds = []


	def getPage(self, callback, url, expires=INTER_QUERY_TIME):
		splog("GSBase getPage")
		splog(url)
		cached = self.getCached(url, expires)
		
		if cached:
			splog("GSBase cached")
			self.base_callback(callback, url, cached)
		
		else:
			splog("GSBase not cached")
			#TODO think about throttling http://code.activestate.com/recipes/491261/
			try:
				deferred = twGetPage(url, timeout = 5)
				deferred.addCallback(boundFunction(self.base_callback, callback, url))
				deferred.addErrback(boundFunction(self.base_errback, callback))
				self.deferreds.append(deferred)
			except Exception as e:
				splog(_("SeriesPlugin getPage exception ") + str(e))
				exc_type, exc_value, exc_traceback = sys.exc_info()
				#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
				#splog( exc_type, exc_value, exc_traceback.format_exc() )
				splog( exc_type, exc_value, exc_traceback )
				callback()

	def base_callback(self, callback, url, page=None, *args, **kwargs):
		try:
			splog("callback", args, kwargs)
			#splog(page)
			#splog(args)
			#splog(kwargs)
			if page:
				cache[url] = (time(), page)
				callback( page )
			else:
				callback( None )
		except Exception as e:
			splog(_("SeriesPlugin base_callback exception ") + str(e))
			exc_type, exc_value, exc_traceback = sys.exc_info()
			#traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
			#splog( exc_type, exc_value, exc_traceback.format_exc() )
			splog( exc_type, exc_value, exc_traceback )

	def base_errback(self, callback, *args, **kwargs):
		splog("errback", args, kwargs)
		callback( None )

	#def cancel(self):
	#	if self.deferreds:
	#		for deferred in deferreds:
	#			deferred.cancel
	#			#connector.disconnect()


	################################################
	# Service prototypes
	def getSeriesList(self, callback, show_name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		callback( None )
		
	def getEpisode(self, callback, show_name, short, description, begin, end, channel):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		callback( None )

#TODO
