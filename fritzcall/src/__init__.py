# -*- coding: utf-8 -*-
'''
general functions for FritzCall plugin

$Id: __init__.py 1296 2016-05-02 13:52:11Z michael $
$Author: michael $
$Revision: 1296 $
$Date: 2016-05-02 15:52:11 +0200 (Mon, 02 May 2016) $
'''

from Components.config import config

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
