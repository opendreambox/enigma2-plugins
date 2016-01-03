# -*- coding: utf-8 -*-
# by betonme @2012

# Internal

class PluginBase(object):
	def __init__(self):
		pass
	
	################################################
	# Base classmethod functions
	@classmethod
	def getClass(cls):
		# Return the Class
		return cls.__name__

	################################################
	# Base functions
	def getPluginName(self):
		# Return the Class Name
		return self.__class__.__name__

	################################################
	# To be implemented by subclass
	def getText(self):
		# Short text to be displayed in GUI
		pass

	def getType(self):
		from Plugins.Extensions.InfoBarTunerState.InfoBarTunerState import INFO, RECORD, STREAM, FINISHED
		# Pixmap number to be displayed as icon
		return INFO

	def getOptions(self):
		# Return a list of (text, config element ) tuples
		pass

	def appendEvent(self):
		pass

	def removeEvent(self):
		pass

	def onInit(self):
		pass

	def onEvent(self):
		pass

	def onShow(self, tunerstates):
		pass

	def update(self, id, tunerstate):
		# Return true if entry is still valid
		return True
