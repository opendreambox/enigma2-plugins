# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin

$Id: __init__.py 1561 2020-10-12 13:32:07Z michael $
$Author: michael $
$Revision: 1561 $
$Date: 2020-10-12 15:32:07 +0200 (Mon, 12 Oct 2020) $
'''

from Components.config import config #@UnresolvedImport
from enigma import eBackgroundFileEraser
from logging import NOTSET
import re

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
	out = ""
	for i in range(len(text) / 2):
		out = out + text[i * 2] + '.'
	return out

def normalizePhoneNumber(intNo):
	
	found = re.match('^\+' + config.plugins.FritzCall.country.value.replace('00', '') + '(.*)', intNo)
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
