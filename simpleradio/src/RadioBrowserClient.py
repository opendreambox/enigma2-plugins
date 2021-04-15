
from __future__ import absolute_import

from Tools.Log import Log

from collections import OrderedDict
import zope

from twisted.web._newclient import (
	RequestGenerationFailed,
	RequestTransmissionFailed,
	ResponseFailed,
)

from twisted.web.client import Agent, BrowserLikeRedirectAgent, readBody, Headers
from twisted.web.iweb import IBodyProducer
from twisted.internet import reactor, threads
from twisted.internet import defer

import json
from urllib import quote

from .RadioBrowser import Station, Country


@zope.interface.implementer(IBodyProducer)
class StringBodyProducer(object):
	"""An IBodyProducer implementation that directly produces a string."""

	def __init__(self, body_str, mime_type=None):
		self._body_str = body_str
		self.body_str = body_str

	@property
	def length(self):
		return len(self.body_str)

	def reset(self):
		self.body_str = self._body_str

	def startProducing(self, consumer):
		consumer.write(self.body_str)
		self.body_str = ''
		return defer.succeed(None)

	def stopProducing(self):
		pass

	def pauseProducing(self):
		pass

	def resumeProducing(self):
		pass


class RadioBrowserClient(object):
	URL_BASE = "https://de1.api.radio-browser.info/json"
	URL_COUNTRIES = "/countries"
	URL_STATIONS = "/stations"
	URL_STATIONS_BY_NAME = "/stations/byname"
	URL_STATIONS_BY_COUNTRY = "/stations/bycountry"

	def __init__(self):
		self._agent = BrowserLikeRedirectAgent(Agent(reactor))

	@property
	def stations(self):
		return self._byCountry

	def request(self, uri, callback, options={}):
		self._agent.request(
			'POST',
			uri.encode("utf-8"),
			Headers({'Content-Type': ['application/json']}),
			StringBodyProducer(json.dumps(options)),
		).addCallbacks(self._onResponse, errback=self._onReloadError, callbackArgs=(callback,))

	def _parseJson(self, jsonString, callback):
		def doParse(data):
			try:
				data = json.loads(data)
				return data
			except Exception as e:
				Log.w(e)
				Log.w(jsonString)
			return {}
		threads.deferToThread(doParse, jsonString).addCallback(callback)

	def countries(self, callback):
		def onReloadFinished(data):
			def _onJson(countries):
				callback([Country(data) for data in countries])
			self._parseJson(data, _onJson)
		self.request("{}{}".format(self.URL_BASE, self.URL_COUNTRIES), onReloadFinished, options={"order": "name", "hidebroken": True})

	def stations(self, country, callback, offset=0, limit=2000):
		def onReloadFinished(data):
			def _onJson(jsonData):
				lst = OrderedDict()
				for entry in jsonData:
					name = entry["name"]
					station = lst.get(name, Station(entry))
					station.extend(entry)
					lst[name] = station
				callback(lst)
			self._parseJson(data, _onJson)
		options = {
			"order": "clickcount",
			"reverse": True,
			"offset": offset,
			"limit": limit,
			"hidebroken": True
		}
		self.request("{}{}/{}".format(self.URL_BASE, self.URL_STATIONS_BY_COUNTRY, quote(country)), onReloadFinished, options=options)

	def _onResponse(self, response, callback):
		readBody(response).addCallbacks(callback, errback=self._onReloadError)

	def _onReloadError(self, failure, *args):
		Log.w("RELOAD ERROR! {}".format(failure))
		if failure.check(
			RequestGenerationFailed,
			RequestTransmissionFailed,
			ResponseFailed,
		):
			failure.value.reasons[0].printTraceback()
		else:
			failure.printTraceback()
