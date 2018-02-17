# -*- coding: utf-8 -*-
#
# WeatherPlugin E2
#
# Coded by Dr.Best (c) 2012-2013
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Property GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Property GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Property GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#
from twisted.internet import defer
from twisted.web.client import getPage, downloadPage
from enigma import eEnv
from os import path as os_path, mkdir as os_mkdir, remove as os_remove, listdir as os_listdir
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_SKIN
from urllib import quote as urllib_quote
import time
import json

#this is for translation support only...
possible_conditions= ( 	_("Tornado"), _("Tropical Storm"), _("Severe Thunderstorms"), _("Thunderstorms"), _("Mixed Rain and Snow"), _("Mixed Rain and Sleet"), _("Mixed Snow and Sleet"), _("Freezing Drizzle"),
			_("Drizzle"), _("Freezing Rain"), _("Showers"), _("Snow Flurries"), _("Light Snow Showers"), _("Blowing Snow"), _("Snow"), _("Rain And Snow"),
			_("Hail"), _("Sleet"), _("Dust"), _("Foggy"), _("Haze"), _("Smoky"), _("Blustery"), _("Windy"),
			_("Cold"), _("Cloudy"), _("Mostly Cloudy"), _("Partly Cloudy"), _("Clear"), _("Sunny"), _("Rain"), 
			_("Fair"), _("Mixed Rain and Hail"), _("Hot"), _("Isolated Thunderstorms"), _("Scattered Thunderstorms"), _("Scattered Showers"),
			_("Heavy Snow"), _("Scattered Snow Showers"), _("Thundershowers"), _("Snow Showers"), _("Isolated Thundershowers"), _("Not Available")
			)

class WeatherIconItem:
	def __init__(self, url = "", filename = "", index = -1, error = False):
		self.url = url
		self.filename = filename
		self.index = index
		self.error = error
		
class MSNWeatherItem:
	def __init__(self):
		self.temperature = ""
		self.skytext = ""
		self.humidity = ""
		self.winddisplay = ""
		self.observationtime = ""
		self.observationpoint = ""
		self.feelslike = ""
		self.skycode = ""
		self.date = ""
		self.day = ""
		self.low = ""
		self.high = ""
		self.skytextday = ""
		self.skycodeday = ""
		self.shortday = ""
		self.iconFilename = ""
		self.code = ""
		
class MSNWeather:

	ERROR = 0
	OK = 1

	def __init__(self):
		path = "/etc/enigma2/weather_icons/"
		extension = self.checkIconExtension(path)
		if extension is None:
			path = os_path.dirname(resolveFilename(SCOPE_SKIN, config.skin.primary_skin.value)) + "/weather_icons/"
			extension = self.checkIconExtension(path)
		if extension is None:
			path = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/WeatherPlugin/weather_icons/")
			extension = ".png"
		self.setIconPath(path)
		self.setIconExtension(extension)
		self.initialize()

	def checkIconExtension(self, path):
		filename = None
		extension = None
		if os_path.exists(path):
			try:
				filename = os_listdir(path)[0]
			except:
				filename = None
		if filename is not None:
			try:
				extension = os_path.splitext(filename)[1].lower()
			except: pass
		return extension
		
	def initialize(self):
		self.city = ""
		self.degreetype = ""
		self.imagerelativeurl = ""
		self.url = ""
		self.weatherItems = {}
		self.callback = None
		self.callbackShowIcon = None
		self.callbackAllIconsDownloaded = None
		
	def cancel(self):
		self.callback = None
		self.callbackShowIcon = None
		
	def setIconPath(self, iconpath):
		if not os_path.exists(iconpath):
			os_mkdir(iconpath)
		self.iconpath = iconpath
		
	def setIconExtension(self, iconextension):
		self.iconextension = iconextension
		
	def getWeatherData(self, degreetype, locationcode, city, callback, callbackShowIcon, callbackAllIconsDownloaded = None ):
		self.initialize()
		self.city = city
		self.callback = callback
		self.callbackShowIcon  = callbackShowIcon
		self.callbackAllIconsDownloaded = callbackAllIconsDownloaded
		u = "+and+u='c'"
		if degreetype == "F":
			u = ""
		url = "http://query.yahooapis.com/v1/public/yql?q=select+*+from+weather.forecast+where+woeid=%s%s&format=json" % (urllib_quote(locationcode), u)
		getPage(url).addCallback(self.jsonCallback).addErrback(self.error)
		
	def getDefaultWeatherData(self, callback = None, callbackAllIconsDownloaded = None):
		self.initialize()
		weatherPluginEntryCount = config.plugins.WeatherPlugin.entrycount.value
		if weatherPluginEntryCount >= 1:
			weatherPluginEntry = config.plugins.WeatherPlugin.Entry[0]
			self.getWeatherData(weatherPluginEntry.degreetype.value, weatherPluginEntry.weatherlocationcode.value, weatherPluginEntry.city.value, callback, None, callbackAllIconsDownloaded)
			return 1
		else:
			return 0
		
	def error(self, error = None):
		errormessage = ""
		if error is not None:
			errormessage = str(error.getErrorMessage())
		if self.callback is not None:
			self.callback(self.ERROR, errormessage)
			
	
	def errorIconDownload(self, error = None, item = None):
		item.error = True
		if os_path.exists(item.filename): # delete 0 kb file
			os_remove(item.filename)

	def finishedIconDownload(self, result, item):
		if not item.error:
			self.showIcon(item.index,item.filename)
		
	def showIcon(self, index, filename):
		if self.callbackShowIcon is not None:
				self.callbackShowIcon(index, filename)
				
	def finishedAllDownloadFiles(self, result):
		if self.callbackAllIconsDownloaded is not None:
			self.callbackAllIconsDownloaded()
	
	def shortMonthToStringNumber(self, shortMonth):
		return {
			'Jan' : "1",
			'Feb' : "2",
			'Mar' : "3",
			'Apr' : "4",
			'May' : "5",
			'Jun' : "6",
			'Jul' : "7",
			'Aug' : "8",
			'Sep' : "9", 
			'Oct' : "10",
			'Nov' : "11",
			'Dec' : "12"
		}[shortMonth]
		
	def windDirection(self, deg):
		if deg >= 12 and deg <= 34:
			wind = _("NNE")
		elif deg >= 35 and deg <= 56:
			wind = _("NE")
		elif deg >= 57 and deg <= 79:
			wind = _("ENE")
		elif deg >= 80 and deg <= 101:
			wind = _("E")
		elif deg >= 102 and deg <= 124:
			wind = _("ESE")
		elif deg >= 125 and deg <= 146:
			wind = _("SE")
		elif deg >= 147 and deg <= 169:
			wind = _("SSE")
		elif deg >= 170 and deg <= 191:
			wind = _("S")
		elif deg >= 192 and deg <= 214:
			wind = _("SSW")
		elif deg >= 215 and deg <= 236:
			wind = _("SW")
		elif deg >= 237 and deg <= 259:
			wind = _("WSW")
		elif deg >= 260 and deg <= 281:
			wind = _("W")
		elif deg >= 282 and deg <= 304:
			wind = _("WNW")
		elif deg >= 305 and deg <= 326:
			wind = _("NW")
		elif deg >= 327 and deg <= 349:
			wind = _("NNW")
		else:
			wind = _("N")
		return wind
		
	def feelslike(self, T, V):
	    FeelsLike = T
	    if round( ( V + .0 ) / 1.609344 ) > 4:
		FeelsLike = ( 13.12 + ( 0.6215 * T ) - ( 11.37 * V**0.16 ) + ( 0.3965 * T * V**0.16 ) )
	    return str( int(round( FeelsLike )))
	    
		
	def jsonCallback(self, jsonstring):
		IconDownloadList = []
		response = json.loads(jsonstring)
		humidity = ""
		temperature = "0"
		skytext = ""
		winddisplay = ""
		speed = ""
		windspeed = "0.0"
		code = ""
		observationtime = ""
		data = response["query"]["results"]["channel"]
		self.url = data['link'].encode("utf-8", 'ignore')
		if 'units' in data:
			item = data['units']
			self.degreetype = item['temperature'].encode("utf-8", 'ignore')
			speed = item['speed'].encode("utf-8", 'ignore')
		if 'atmosphere' in data:
			item = data['atmosphere']
			humidity = item['humidity'].encode("utf-8", 'ignore')
		if 'wind' in data:
			item = data['wind']
			windspeed = item['speed'].encode("utf-8", 'ignore')
			winddisplay = "%s %s %s" % (windspeed, speed, self.windDirection(int(item['direction'].encode("utf-8", 'ignore'))))
		if 'item' in data:
			if 'condition' in data['item']:
				item = data['item']['condition']
				temperature = item['temp'].encode("utf-8", 'ignore')
				skytext = _(item['text'].encode("utf-8", 'ignore'))
				code = item['code'].encode("utf-8", 'ignore')
				t = item['date'].encode("utf-8", 'ignore')
				observationtime = t[17:]
				# Wed, 08 Mar 2017 10:00 PM CET
				#da = t[5:16]
				#d = da.replace(da[3:6], self.shortMonthToStringNumber(da[3:6]))
				#c = time.strptime(d,"%d %m %Y")
				#observationtime = "%s, %s %s" % (_(t[0:3]), time.strftime("%d. %b",c), t[17:])
				currentWeather = MSNWeatherItem()
				currentWeather.observationpoint  = "" # no chance to get this info with yahooapi
				currentWeather.humidity = humidity
				currentWeather.temperature = temperature
				currentWeather.winddisplay = winddisplay
				if self.degreetype != "F":
					currentWeather.feelslike = self.feelslike(int(temperature), int(round(float(windspeed) + 0.5)))
				currentWeather.skytext = skytext
				currentWeather.observationtime = observationtime
				currentWeather.skycode = "%s%s" % (code, self.iconextension)
				currentWeather.code = code
				filename = "%s%s"  % (self.iconpath, currentWeather.skycode)
				currentWeather.iconFilename = filename
				#if not os_path.exists(filename):
				#	url = "http://l.yimg.com/a/i/us/we/52/%s.gif" % (currentWeather.skycode)
				#	IconDownloadList.append(WeatherIconItem(url = url,filename = filename, index = -1))
				#else:
				self.showIcon(-1,filename)
				self.weatherItems[str(-1)] = currentWeather
			if 'forecast' in data['item']:
				forecast = data['item']['forecast']
				for count, item in enumerate(forecast):
					if count >= 5:
						break
					weather = MSNWeatherItem()
					date = item['date'].encode("utf-8", 'ignore')
					weather.date = date.replace(date[3:6], self.shortMonthToStringNumber(date[3:6]))
					c = time.strptime(weather.date,"%d %m %Y")
					weather.day = time.strftime("%A",c) #_(item['day'].encode("utf-8", 'ignore'))
					weather.shortday = _(item['day'].encode("utf-8", 'ignore'))
					weather.low = item['low'].encode("utf-8", 'ignore')
					weather.high = item['high'].encode("utf-8", 'ignore')
					weather.skytextday = _(item['text'].encode("utf-8", 'ignore'))
					weather.skycodeday = "%s%s" % (item['code'].encode("utf-8", 'ignore'), self.iconextension)
					weather.code = item['code'].encode("utf-8", 'ignore')
					filename = "%s%s"  % (self.iconpath, weather.skycodeday)
					weather.iconFilename = filename
					#if not os_path.exists(filename):
					#	url = "http://l.yimg.com/a/i/us/we/52/%s.gif" % (weather.skycodeday)
					#	IconDownloadList.append(WeatherIconItem(url = url,filename = filename, index = count+1))
					#else:
					self.showIcon(count+1,filename)
					self.weatherItems[str(count+1)] = weather
		
		if len(IconDownloadList) != 0:
			ds = defer.DeferredSemaphore(tokens=len(IconDownloadList))
			downloads = [ds.run(download,item ).addErrback(self.errorIconDownload, item).addCallback(self.finishedIconDownload,item) for item in IconDownloadList]
			finished = defer.DeferredList(downloads).addErrback(self.error).addCallback(self.finishedAllDownloadFiles)
		else:
			self.finishedAllDownloadFiles(None)
			
		if self.callback is not None:
			self.callback(self.OK, None)
		
def download(item):
	return downloadPage(item.url, file(item.filename, 'wb'))
