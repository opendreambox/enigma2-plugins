# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin

$Id: __init__.py 1454 2017-06-11 13:24:13Z michael $
$Author: michael $
$Revision: 1454 $
$Date: 2017-06-11 15:24:13 +0200 (Sun, 11 Jun 2017) $
'''

from __future__ import division
from Components.config import config #@UnresolvedImport
from enigma import eBackgroundFileEraser
from logging import NOTSET

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
	for i in range(len(text)//2):
		out = out + text[i*2] + '.'
	return out

import re
def normalizePhoneNumber(intNo):
	
	found = re.match(r'^\+' + config.plugins.FritzCall.country.value.replace('00','') + '(.*)', intNo)
	if found:
		intNo = '0' + found.group(1)
	found = re.match(r'^\+(.*)', intNo)
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
