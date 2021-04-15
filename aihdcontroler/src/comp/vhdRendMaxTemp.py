# -*- coding: utf-8 -*-
#
#    Maximum Temperature Renderer for Dreambox/Enigma-2
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
from Components.Sensors import sensors
from Tools.HardwareInfo import HardwareInfo
from enigma import eLabel
from Renderer import Renderer


class vhdRendMaxTemp(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		if "8000" in HardwareInfo().get_device_name() or "500" in HardwareInfo().get_device_name() or "800se" in HardwareInfo().get_device_name():
			self.ZeigeTemp = True
		else:
			self.ZeigeTemp = False
	GUI_WIDGET = eLabel

	def changed(self, what):
		if not self.suspended:
			if self.ZeigeTemp:
				maxtemp = 0
				try:
					templist = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
					tempcount = len(templist)
					for count in range(tempcount):
						id = templist[count]
						tt = sensors.getSensorValue(id)
						if tt > maxtemp:
							maxtemp = tt
				except:
					pass
				self.text = str(maxtemp) + "�C"
			else:
				loada = 0
				try:
					out_line = open("/proc/loadavg").readline()
					loada = out_line[:4]	
				except:
					pass
				self.text = loada

	def onShow(self):
		self.suspended = False
		self.changed(None)

	def onHide(self):
		self.suspended = True
