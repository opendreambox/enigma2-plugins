"""
	{
		"changeuuid": "9b571681-ae09-44c9-a712-e774370334bb",
		"stationuuid": "e7193c8a-a18f-4ec1-a214-df9c78698713",
		"name": "_Funky Corner Radio (Germany)",
		"url": "https://ais-sa2.cdnstream1.com/2447_192.mp3",
		"url_resolved": "https://ais-sa2.cdnstream1.com/2447_192.mp3",
		"homepage": "https://www.funkycorner.it",
		"favicon": "https://www.funkycorner.it/FCR300.png",
		"tags": "funk,funky,r&b,r'n'b,rnb,disco,70s disco,70s,80s,soul,black music,black,music,musica,rare groove,oldies,motown,p-funk,the sound of philadelphia,philadelphia",
		"country": "Germany",
		"countrycode": "DE",
		"state": "Bavaria",
		"language": "english",
		"votes": 3,
		"lastchangetime": "2020-11-16 02:58:46",
		"codec": "MP3",
		"bitrate": 192,
		"hls": 0,
		"lastcheckok": 1,
		"lastchecktime": "2020-11-26 06:40:26",
		"lastcheckoktime": "2020-11-26 06:40:26",
		"lastlocalchecktime": "2020-11-26 06:40:26",
		"clicktimestamp": "2020-11-25 21:30:10",
		"clickcount": 32,
		"clicktrend": 1
	}
"""


class Station(object):
	def __init__(self, data):
		self._data = data

	def extend(self, data):
		urls = self._data.get("urls", [])
		urls.append(str(data["url"]))
		self._data["urls"] = urls
		urls_resolved = self._data.get("urls_resolved", [])
		urls_resolved.append(str(data["url_resolved"]))
		self._data["urls_resolved"] = urls_resolved

	@property
	def data(self):
		return self._data

	@property
	def changeUUID(self):
		return str(self._data["changeuuid"])

	@property
	def stationUUID(self):
		return str(self._data["stationuuid"])

	@property
	def name(self):
		return str(self._data["name"])

	@property
	def urls(self):
		return self._data["urls"]

	@property
	def urlsResolved(self):
		return self._data["urls_resolved"]

	@property
	def homepage(self):
		return str(self._data["homepage"])

	@property
	def tags(self):
		return ",".split(str(self._data["tags"]))

	@property
	def country(self):
		return str(self._data["country"])

	@property
	def countrycode(self):
		return str(self._data["countrycode"])

	@property
	def state(self):
		return str(self._data["state"])

	@property
	def language(self):
		return str(self._data["language"])

	@property
	def votes(self):
		return self._data["votes"]

	@property
	def codec(self):
		return str(self._data["codec"])

	@property
	def bitrate(self):
		return self._data["bitrate"]

	@property
	def clickcount(self):
		return self._data["clickcount"]


"""
	{
		"name": "Afghanistan",
		"stationcount": 196
	},
"""


class Country(object):
	def __init__(self, data):
		self._data = data

	@property
	def name(self):
		return str(self._data["name"])

	@property
	def stationCount(self):
		return self._data["stationcount"]
