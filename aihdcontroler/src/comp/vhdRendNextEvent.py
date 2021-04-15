#######################################################################
#
#    Next Event Renderer for Dreambox/Enigma-2
#    Coded by Vali (c)2010-2011
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Property GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#######################################################################

from Components.VariableText import VariableText
from enigma import eLabel, eEPGCache
from Renderer import Renderer
from time import localtime

class vhdRendNextEvent(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.epgcache = eEPGCache.getInstance()
	GUI_WIDGET = eLabel
	
	def changed(self, what):
		ref = self.source.service
		info = ref and self.source.info
		if info is None:
			self.text = ""
			return
		ENext = ""
		eventNext = self.epgcache.lookupEvent(['IBDCTSERNX', (ref.toString(), 1, -1)])
		if eventNext:
			if eventNext[0][4]:
				t = localtime(eventNext[0][1])
				duration = "%d min" % (eventNext[0][2] / 60)
				ENext = "next:   %02d:%02d   %s   %s" % (t[3], t[4], duration, eventNext[0][4])
		self.text = ENext

