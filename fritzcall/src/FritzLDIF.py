# -*- coding: utf-8 -*-
'''
$Author: michael $
$Revision: 1561 $
$Date: 2020-10-12 15:32:07 +0200 (Mon, 12 Oct 2020) $
$Id: FritzLDIF.py 1561 2020-10-12 13:32:07Z michael $
'''
#
# needs python-ldap for ldif
#

from __future__ import print_function
import ldif
import re
try:
	from . import normalizePhoneNumber #@UnresolvedImport # pylint: disable-msg=F0401
except ValueError:
	def _(string): # pylint: disable-msg=C0103
		return string
	
	def normalizePhoneNumber(intNo):
		found = re.match('^\+49(.*)', intNo)
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

import logging
logger = logging.getLogger("[FritzCall] LDIF")
debug = logger.debug


def out(number, name):
	print(number + '#' + name)


class FindNumber(ldif.LDIFParser):
	def __init__(self, number, inp, outFun):
		ldif.LDIFParser.__init__(self, inp)
		self.outFun = outFun
		self.number = number
		try:
			self.parse()
		except ValueError:
			# this is to exit the parse loop
			pass

	def handle(self, dn, entry):
		# debug("[FritzCallPhonebook] LDIF handle: " + dn)
		found = re.match('.*cn=(.*),', str(dn))
		if found:
			name = found.group(1)
		else:
			return
	
		address = ""
		addressB = ""
		if 'telephoneNumber' in entry or ('homePhone' in entry and self.number == normalizePhoneNumber(entry['homePhone'][0])) or ('mobile' in entry and self.number == normalizePhoneNumber(entry['mobile'][0])):
			# debug("[FritzCallPhonebook] LDIF get address")
			if 'telephoneNumber' in entry:
				no = normalizePhoneNumber(entry['telephoneNumber'][0])
			else:
				no = 0
			if self.number == no or ('homePhone' in entry and self.number == normalizePhoneNumber(entry['homePhone'][0])) or ('mobile' in entry and self.number == normalizePhoneNumber(entry['mobile'][0])):
				nameB = (name + ' (' + _('business') + ')') if name else ""
				if 'company' in entry:
					nameB = (nameB + ', ' + entry['company'][0]) if nameB else entry['company'][0]
				if 'l' in entry:
					addressB = entry['l'][0]
					if 'postalCode' in entry:
						addressB = entry['postalCode'][0] + ' ' + addressB
					if 'c' in entry:
						addressB = addressB + ', ' + entry['c'][0]
					if 'street' in entry:
						addressB = entry['street'][0] + ', ' + addressB
					# debug("[FritzCallPhonebook] LDIF address: " + addressB)
					if self.number == no:
						result = nameB + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + result)
						self.outFun(no, result)
						self._input_file.close()
						return
				else:
					if self.number == no:
						result = nameB.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + result)
						self.outFun(no, result)
						self._input_file.close()
						return
		for i in ['homePhone', 'mobile']:
			if i in entry:
				no = normalizePhoneNumber(entry[i][0])
				if self.number == no:
					if i == 'mobile':
						name = name + ' (' + _('mobile') + ')'
					else:
						name = name + ' (' + _('home') + ')'
					if 'mozillaHomeLocalityName' in entry:
						address = entry['mozillaHomeLocalityName'][0]
						if 'mozillaHomePostalCode' in entry:
							address = entry['mozillaHomePostalCode'][0] + ' ' + address
						if 'mozillaHomeCountryName' in entry:
							address = address + ', ' + entry['mozillaHomeCountryName'][0]
							debug("[FritzCallPhonebook] LDIF home address: " + addressB)
						result = name + ', ' + address.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + result)
						self.outFun(no, result)
						self._input_file.close()
						return
					else:
						if addressB:
							name = name + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
						debug("[FritzCallPhonebook] LDIF result: " + name)
						self.outFun(no, name)
						self._input_file.close()
						return


class ReadNumbers(ldif.LDIFParser):
	def __init__(self, inPut, outFun):
		ldif.LDIFParser.__init__(self, inPut)
		self.outFun = outFun
		try:
			self.parse()
		except ValueError:
			#
			# this is to exit the parse loop:
			# we close the input file as soon as we have a result...
			#
			pass

	def handle(self, dn, entry):
		# debug("[FritzCallPhonebook] LDIF handle: " + dn)
		found = re.match('.*cn=(.*),', str(dn))
		if found:
			name = found.group(1)
		else:
			return
	
		address = ""
		addressB = ""
		if 'telephoneNumber' in entry or 'homePhone' in entry or 'mobile' in entry:
			# debug("[FritzCallPhonebook] LDIF get address")
			nameB = (name + ' (' + _('business') + ')') if name else ""
			if 'company' in entry:
				nameB = (nameB + ', ' + entry['company'][0]) if nameB else entry['company'][0]
			if 'l' in entry:
				addressB = entry['l'][0]
				if 'postalCode' in entry:
					addressB = entry['postalCode'][0] + ' ' + addressB
				if 'c' in entry:
					addressB = addressB + ', ' + entry['c'][0]
				if 'street' in entry:
					addressB = entry['street'][0] + ', ' + addressB
				# debug("[FritzCallPhonebook] LDIF address: " + addressB)
				if 'telephoneNumber' in entry:
					no = normalizePhoneNumber(entry['telephoneNumber'][0])
					result = nameB + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, result)
			else:
				if 'telephoneNumber' in entry:
					no = normalizePhoneNumber(entry['telephoneNumber'][0])
					result = nameB.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, result)
		for i in ['homePhone', 'mobile']:
			if i in entry:
				no = normalizePhoneNumber(entry[i][0])
				if i == 'mobile':
					nameHM = name + ' (' + _('mobile') + ')'
				else:
					nameHM = name + ' (' + _('home') + ')'
				if 'mozillaHomeLocalityName' in entry:
					address = entry['mozillaHomeLocalityName'][0]
					if 'mozillaHomePostalCode' in entry:
						address = entry['mozillaHomePostalCode'][0] + ' ' + address
					if 'mozillaHomeCountryName' in entry:
						address = address + ', ' + entry['mozillaHomeCountryName'][0]
					result = nameHM + ', ' + address.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, result)
				else:
					if addressB:
						nameHM = nameHM + ', ' + addressB.replace('\n', ', ').replace('\r', '').replace('#', '')
					self.outFun(no, nameHM)


def lookedUp(number, name):
	print(number + ' ' + name)


if __name__ == '__main__':
	import os
	import sys
	cwd = os.path.dirname(sys.argv[0])
	if (len(sys.argv) == 1):
		ReadNumbers(open("Kontakte.ldif"), out)
	elif (len(sys.argv) == 2):
		# nrzuname.py Nummer
		FindNumber(sys.argv[1], open("Kontakte.ldif"), lookedUp)
