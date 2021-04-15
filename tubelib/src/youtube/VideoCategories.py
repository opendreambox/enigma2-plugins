#enigma2
from Components.config import config

from YoutubeQueryBase import YoutubeQueryBase


class VideoCategories(YoutubeQueryBase):
	def list(self, callback, lang=None, region=None):
		if not lang:
			lang = config.osd.language.value.split("_")[0]
		if not region:
			region = lang
		self._args = {
			'part': 'id,snippet',
			'hl': lang,
			'regionCode': region,
			'fields': 'items(id,snippet(title))'
		}
		return self._doQuery(callback)

	def _doQuery(self, callback):
		request = self._youtube.videoCategories().list(**self._args)
		return self._query(callback, request)

	def _onResult(self, success, data):
		categories = []
		if success:
			for item in data['items']:
				categories.append(VideoCategory(item))
		self._callback(success, categories)


class VideoCategory(object):
	def __init__(self, entry):
		self._entry = entry

	def getId(self):
		return str(self._entry["id"])
	id = property(getId)

	def getTitle(self):
		return str(self._entry["snippet"]["title"])
	title = property(getTitle)
