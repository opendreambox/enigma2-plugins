﻿# -*- coding: utf-8 -*-
import os
import sys
import traceback

# Config
from Components.config import *
from Components.Sources.StaticText import StaticText

# Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from enigma import eSize, ePoint, getDesktop
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS


class ShowLogScreen(Screen):
	def __init__(self, session, logFile, titleText, firstLineText, lastLineText):
		Screen.__init__(self, session)
		self.skinName = ["TestBox", "Console"]
		title = ""
		text = ""
		self.logFile = logFile
		self.titleText = titleText
		self.firstLineText = firstLineText
		self.lastLineText = lastLineText
		
		self["text"] = ScrollLabel("")
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ChannelSelectBaseActions"], 
		{
			"ok": self.cancel,
			"back": self.cancel,
			"up": self["text"].pageUp,
			"down": self["text"].pageDown,
			"left": self["text"].pageUp,
			"right": self["text"].pageDown,
			"nextBouquet": self["text"].lastPage,
			"prevBouquet": self.firstPage,
		}, -1)
		
		self.onLayoutFinish.append(self.readLog)

	def cancel(self):
		self.close()

	def setText(self, text):
		self["text"].setText(text)

	def close(self):
		Screen.close(self)

	def firstPage(self):
		self["text"].long_text.move(ePoint(0, 0))
		self["text"].updateScrollbar()

	def readLog(self):
		
		# Set title and text
		title = _("Show Log file") + " - AutoTimer " + self.titleText
		text = _("Reading log file...\n") + self.logFile + _("\nCancel?")
		
		self.setTitle(title)
		self.setText(text)
		
		if not fileExists(self.logFile):
			self.setText(_("No file found"))

		elif not os.path.getsize(self.logFile) == 0:
			file = open(self.logFile, "r")
			text = file.read()
			file.close()
			
			try:
				if self.firstLineText != "":
					text = self.firstLineText + text
				if self.lastLineText != "":
					text = text + self.lastLineText
				self.setText(text)
				self["text"].lastPage()
			except:
				pass
