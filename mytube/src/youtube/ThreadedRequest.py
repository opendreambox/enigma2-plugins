from Tools.Log import Log
from twisted.internet import threads, reactor
from threading import Lock

class ThreadedRequest(object):
	# Pythons HttpConnection (used by googles python client api) is not thread safe
	# We have to use locking to ensure serialized requests
	_lock = Lock()

	def __init__(self, query, callback, subquery=None):
		self._canceled = False
		self._callback = callback
		self._query = query
		self._subquery = subquery
		threads.deferToThread(self._doQuery)

	def _doQuery(self):
		self._lock.acquire()
		try:
			data = self._query.execute()
			if self._subquery:
				query = self._subquery(data)
				data = query.execute()
			self._onResult(True, data)
		except Exception as e:
			Log.w(e)
			self._onResult(False, e)
		self._lock.release()

	def _onResult(self, success, data):
		reactor.callFromThread(self._finish, success, data)

	def _finish(self, success, data):
		if self._canceled:
			return
		self._callback(success, data)

	def cancel(self):
		self._canceled = True
