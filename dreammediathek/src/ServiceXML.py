# -*- coding: utf-8 -*-
from os.path import exists
from xml.etree.cElementTree import parse as cet_parse
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN

WEBTV_STATIONS = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/dreamMediathek/webtv_stations.xml")


class WebTVStations():
	"""Manages WebTVStations declared in a XML-Document."""
	def __init__(self):
		print "[WebTVStations] INIT"
		self.webtv_stations = {}

	def getWebTVStations(self, callback=None):
		self.webtv_stations = {}

		if not exists(WEBTV_STATIONS):
			return
		tree = cet_parse(WEBTV_STATIONS).getroot()

		def getValue(definitions, default):
			Len = len(definitions)
			return Len > 0 and definitions[Len-1].text or default

		for tvstation in tree.findall("tvstation"):
			data = { 'provider': None, 'title': None, 'streamurl': None }
			try:
				data['provider'] = getValue(tvstation.findall("provider"), False).encode("UTF-8")
				data['title'] = getValue(tvstation.findall("title"), False).encode("UTF-8")
				data['streamurl'] = getValue(tvstation.findall("streamurl"), False).encode("UTF-8")

				print "TVSTATION--->",data
				self.webtv_stations[data['title']] = data
			except Exception, e:
				print "[WebTVStations] Error reading Stations:", e

	def getWebTVStationsList(self):
		return sorted(self.webtv_stations.iterkeys())

iWebTVStations = WebTVStations()
