from __future__ import print_function

from . import _, ATLOG_LIST
from Components.config import config

ATLOG_DEBUG = "1"
ATLOG_INFO = "2"
ATLOG_WARN = "3"
ATLOG_ERROR = "4"

ATLOG_MESSAGES = {"1": "DEBUG",
				"2": "INFO ",
				"3": "WARN ",
				"4": "ERROR"}

logLevelEl = config.plugins.autotimer.loglevel

def atLog(logLevel, *args):
	if logLevel >= logLevelEl.value:
		logLevelText = ATLOG_MESSAGES[logLevel] if logLevel in ATLOG_MESSAGES.keys() else "?????"
		print("[AutoTimer", logLevelText + "]", *args)

		if config.plugins.autotimer.logwrite.value:
			try:
				with open(config.plugins.autotimer.logfile.value, 'a') as f:
					print("[" + logLevelText + "]", *args, file=f)
			except Exception, e:
				print("[AutoTimer] atLog exception", e)
