from ThreadedRequest import ThreadedRequest

class YoutubeQueryBase(object):
	def __init__(self, youtube):
		self._youtube = youtube
		self._callback = None
		self._request = None
		self._data = None
		self._args = {}

	def _query(self, callback, query, subquery=None):
		self._callback = callback
		self._request = ThreadedRequest(query, self.__onResult, subquery=subquery)
		return self._request

	def __onResult(self, success, data):
		if success:
			self._data = data
		else:
			self._data = {}
		self._onResult(success, data)

	def getData(self):
		return self._data
	data = property(getData)

	def hasNextPage(self):
		return "nextPageToken" in self._data

	def nextPage(self):
		if self.hasNextPage():
			self._args['pageToken'] = self._data['nextPageToken']
			self._doQuery(self._callback)
			return True
		return False

	def hasPrevPage(self):
		return "prevPageToken" in self._data

	def prevPage(self):
		if self.hasPrevPage():
			self._args['pageToken'] = self._data['prevPageToken']
			self._doQuery(self._callback)
			return True
		return False

	def getTotalResults(self):
		if "pageInfo" not in self._data:
			return 0
		return self._data["pageInfo"]["totalResults"] or 0

	def _doQuery(self, callback):
		raise Exception("Not Implemented")

	def _onResult(self, success, data):
		raise Exception("Not Implemented")
