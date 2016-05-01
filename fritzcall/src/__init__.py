# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin

$Id: __init__.py 1291 2016-05-01 16:41:25Z michael $
$Author: michael $
$Revision: 1291 $
$Date: 2016-05-01 18:41:25 +0200 (Sun, 01 May 2016) $
'''

from Components.config import config #@UnresolvedImport
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE #@UnresolvedImport
import gettext, os
from enigma import eBackgroundFileEraser
from logging import NOTSET

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("FritzCall", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/FritzCall/locale/"))

def _(txt): # pylint: disable=C0103
	td = gettext.dgettext("FritzCall", txt)
	if td == txt:
		td = gettext.gettext(txt)
	return td

# scramble text
def __(text, front=True):
	#===========================================================================
	# if len(text) > 5:
	#	if front:
	#		return '.....' + text[5:]
	#	else:
	#		return text[:-5] + '.....'
	# else:
	#	return '.....' 
	#===========================================================================
	out =""
	for i in range(len(text)/2):
		out = out + text[i*2] + '.'
	return out

import logging
def initDebug():
# 
# 	logging.basicConfig(filename='/tmp/FritzDebug.log',
# 					filemode='w',
# 					level=config.plugins.FritzCall.debug.value,
# 					# format='%(asctime)s %(levelname)s %(module)s %(name)s %(funcName)s %(message)s',
# 					format='%(asctime)s %(levelname)-8s %(name)-26s %(funcName)s %(message)-15s',
# 					datefmt='%Y-%m-%d %H:%M:%S')
# 	logger = logging.getLogger("FritzCall")
	logger = logging.getLogger("FritzCall")
	logger.setLevel(config.plugins.FritzCall.debug.value)
	fileHandler = logging.FileHandler('/tmp/FritzDebug.log', mode='w')
	fileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(name)-26s %(funcName)s %(message)-15s', '%Y-%m-%d %H:%M:%S'))
	logger.addHandler(fileHandler)

#from time import localtime
#def debug(message):
#	if config.plugins.FritzCall.debug.value:
#		try:
#			# ltim = localtime()
#			# headerstr = u"%04d%02d%02d %02d:%02d " %(ltim[0],ltim[1],ltim[2],ltim[3],ltim[4])
#			deb = open("/tmp/FritzDebugOld.log", "aw")
#			# deb.write(headerstr + message.decode('utf-8') + u"\n")
#			deb.write(message + "\n")
#			deb.close()
#		except Exception, e:
#			debug("%s (retried debug: %s)" % (repr(message), str(e)))
#		logging.debug(message)

import re
def normalizePhoneNumber(intNo):
	
	found = re.match('^\+' + config.plugins.FritzCall.country.value.replace('00','') + '(.*)', intNo)
	if found:
		intNo = '0' + found.group(1)
	found = re.match('^\+(.*)', intNo)
	if found:
		intNo = '00' + found.group(1)
	intNo = intNo.replace('(', '').replace(')', '').replace(' ', '').replace('/', '').replace('-', '')
	found = re.match('^49(.*)', intNo) # this is most probably an error
	if found:
		intNo = '0' + found.group(1)
	found = re.match('.*?([0-9]+)', intNo)
	if found:
		return found.group(1)
	else:
		return '0'
