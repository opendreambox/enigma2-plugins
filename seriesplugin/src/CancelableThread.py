# by betonme @2012

from Queue import Queue
import threading
import inspect
import ctypes

from time import time

# Localization
from . import _

# Plugin internal
from Logger import splog


## {{{ http://code.activestate.com/recipes/465057/ (r1)
from threading import Lock

myLock = Lock()

def synchronized(lock):
    """ Synchronization decorator. """
    def wrap(f):
        def newFunction(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
				lock.release()
        return newFunction
    return wrap
## end of http://code.activestate.com/recipes/465057/ }}}


class QueueWithTimeOut(Queue):
	def __init__(self):
		Queue.__init__(self)
	
	def join_with_timeout(self, timeout):
		self.all_tasks_done.acquire()
		endtime = time() + timeout
		#splog("SeriesPluginWorker for while")
		while self.unfinished_tasks:
			remaining = endtime - time()
			#splog("SeriesPluginWorker while", remaining)
			if remaining <= 0.0:
				break
			#splog("SeriesPluginWorker before all_tasks_done wait")
			self.all_tasks_done.wait(remaining)
		#splog("SeriesPluginWorker before all_tasks_done release")
		self.all_tasks_done.release()
		
		# Release our semaphore
		try: myLock.release()
		except: pass


def _async_raise(tid, exctype):
	"""raises the exception, performs cleanup if needed"""
	if not inspect.isclass(exctype):
		raise TypeError("Only types can be raised (not instances)")
	res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
	if res == 0:
		raise ValueError("invalid thread id")
	elif res != 1:
		# """if it returns a number greater than one, you're in trouble, 
		# and you should call it again with exc=NULL to revert the effect"""
		ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
		raise SystemError("PyThreadState_SetAsyncExc failed")


class CancelableThread(threading.Thread):
	def _get_my_tid(self):
		"""determines this (self's) thread id"""
		if not self.isAlive():
			raise threading.ThreadError("the thread is not active")
		
		# do we have it cached?
		if hasattr(self, "_thread_id"):
			return self._thread_id
		
		# no, look for it in the _active dict
		for tid, tobj in threading._active.items():
			if tobj is self:
				self._thread_id = tid
				return tid
		
		raise AssertionError("could not determine the thread's id")
	
	def raise_exc(self, exctype):
		"""raises the given exception type in the context of this thread"""
		_async_raise(self._get_my_tid(), exctype)
	
	def terminate(self):
		# Release our semaphore
		try: myLock.release()
		except: pass
		
		"""raises SystemExit in the context of the given thread, which should 
		cause the thread to exit silently (unless caught)"""
		self.raise_exc(SystemExit)
