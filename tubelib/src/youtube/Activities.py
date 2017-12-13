from Tools.Log import Log

from YoutubeQueryBase import YoutubeQueryBase
from Subscriptions import Subscription

class Activities(YoutubeQueryBase):
	def list(self, callback, home=True, maxResults=25):
		self._args = {
			'part' : 'id,snippet,contentDetails',
			'home' : 'true' if home else 'false',
			'maxResults' : 25,
		}
		return self._doQuery(callback)

	def _doQuery(self, callback):
		request = self._youtube.activities().list(**self._args)
		return self._query(callback, request)

	def _onResult(self, success, data):
		activities = []
		if success:
			for item in data['items']:
				activities.append(Subscription(item))
		self._callback(success, activities)

class Activity(object):
	TYPE_UPLOAD = "upload"
	TYPE_RECOMMENDATION = "recommendation"
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

	def isUpload(self):
		return str(self._entry["snippet"]["type"]) == self.TYPE_UPLOAD

	def isRecommendation(self):
		return str(self._entry["snippet"]["type"]) == self.TYPE_RECOMMENDATION

	@property
	def type(self):
		return str(self._entry["snippet"]["type"])

	@property
	def videoId(self):
		if self.isUpload():
			return str(self._entry["contentDetails"]["totalItemCount"])
		elif self.isRecommendation():
			resourceId = self._entry["contentDetails"]["recommendation"]["resourceId"]
			if resourceId["kind"] == "youtube#video":
				return resourceId["videoId"]
		return None
