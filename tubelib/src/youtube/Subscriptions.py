from Tools.Log import Log

from YoutubeQueryBase import YoutubeQueryBase

class Subscriptions(YoutubeQueryBase):
	def list(self, callback, maxResults=25):
		self._args = {
			'part' : 'id,snippet,contentDetails',
			'mine' : 'true',
			'maxResults' : 25,
		}
		return self._doQuery(callback)

	def _doQuery(self, callback):
		request = self._youtube.subscriptions().list(**self._args)
		return self._query(callback, request)

	def _onResult(self, success, data):
		subscriptions = []
		if success:
			for item in data['items']:
				subscriptions.append(Subscription(item))
		self._callback(success, subscriptions)

class Subscription(object):
	def __init__(self, entry):
		self._entry = entry

	@property
	def id(self):
		return str(self._entry["id"])

	@property
	def title(self):
		return str(self._entry["snippet"]["title"])

	@property
	def description(self):
		return str(self._entry["snippet"]["description"])

	@property
	def channelId(self):
		return str(self._entry["snippet"]["channelId"])

	@property
	def thumbnailUrl(self, best=False):
		prios = ["maxres", "standard", "high", "medium", "default"]
		if not best:
			prios.reverse()
		for prio in prios:
			if self._entry["snippet"]["thumbnails"].has_key(prio):
				return str(self._entry["snippet"]["thumbnails"][prio]["url"])
			else:
				Log.w(self.id)
		return None

	@property
	def totalItemCount(self):
		return str(self._entry["contentDetails"]["totalItemCount"])

	@property
	def newItemCount(self):
		return str(self._entry["contentDetails"]["newItemCount"])
