#enigma2
from Components.config import config
from Videos import Videos


class Search(Videos):
	ORDER_DATE = "date"
	ORDER_RATING = "rating"
	ORDER_RELEVANCE = "relevance"
	ORDER_TITLE = "title"
	ORDER_VIDEOCOUNT = "videoCount"
	ORDER_VIEWCOUNT = "viewCount"

	SAFE_SEARCH_NONE = "none"
	SAFE_SEARCH_MODERATE = "moderate"
	SAFE_SEARCH_STRICT = "strict"

	def list(self, callback, searchTerm=None, order=ORDER_RELEVANCE, maxResults=25, relatedToVideoId=None, channelId=None, safeSearch=SAFE_SEARCH_NONE):
		self._listrequest = None
		self._args = {
			'part': 'id',
			'type': 'video',
			'maxResults': maxResults,
			'order': order,
			'safeSearch': safeSearch
		}
		if searchTerm:
			self._args['q'] = searchTerm
		if relatedToVideoId:
			self._args['relatedToVideoId'] = relatedToVideoId
		if channelId:
			self._args['channelId'] = channelId
		self._doQuery(callback)

	def _doQuery(self, callback):
		request = self._youtube.search().list(**self._args)

		def subquery(data):
			if not data:
				self._onResult(False, [])
			items = []
			for item in data['items']:
				items.append(item["id"]["videoId"])
			kwargs = {
				"part": "id,snippet,statistics,contentDetails",
				"maxResults": 50,
				"hl": config.osd.language.value.split("_")[0],
				"id": ",".join(items)
			}
			request = self._youtube.videos().list(**kwargs)
			return request
		return self._query(callback, request, subquery=subquery)
