# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================


from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from pyexpat import ExpatError

from VlcFileList import VlcFileList
from VlcPlayList import VlcPlayList

class VlcMediaListScreen(Screen):
	skin ="""
		<screen name="VlcMediaListScreen" position="center,center" size="820,410" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget size="950,35" alphatest="on" position="0,50" zPosition="1" name="filelist_button_sel" pixmap="skin_default/epg_now.png" />
			<widget size="950,35" alphatest="on" position="0,50" zPosition="1" name="playlist_button_sel" pixmap="skin_default/epg_next.png" />
			<widget name="filelist_text" position="31,55" zPosition="2" size="200,25" font="Regular;20" halign="center" valign="center" backgroundColor="background" transparent="1" />
			<widget name="playlist_text" position="231,55" zPosition="2" size="200,25" font="Regular;20" halign="center" valign="center" backgroundColor="background" transparent="1" />
			<widget name="filelist" position="10,95" size="800,300" enableWrapAround="1" scrollbarMode="showOnDemand"/>
			<widget name="playlist" position="10,95" size="800,300" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		</screen>"""
	
	defaultFilter = "(?i)\.(avi|mpeg|mpg|divx|xvid|mp4|mov|ts|vob|wmv|mkv|iso|m3u|pls|xspf|flv)$"

	def __init__(self, session, server):
		Screen.__init__(self, session)
		self.session = session
		self.server = server
		self["filelist"] = VlcFileList(self.getFilesAndDirsCB, server.getBasedir(), self.defaultFilter)
		self["playlist"] = VlcPlayList(self.getPlaylistEntriesCB)
		self["key_red"] = Button(_("filter off"))
		self["key_green"] = Button(_("refresh"))
		self["key_yellow"] = Button(_("Serverlist"))
		self["key_blue"] = Button(_("play DVD"))
		self["filelist_button_sel"] = Pixmap()
		self["playlist_button_sel"] = Pixmap()
		self["more_button_sel"] = Pixmap()
		self["filelist_text"] = Label(_("Filelist"))
		self["playlist_text"] = Label(_("Playlist"))
		self["server_name"] = Label(server.getName())
		self["current_dir"] = Label()
		
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions", "MoviePlayerActions", "EPGSelectActions"],
			{
			 "back": 	self.close,
			 "red": 	self.keyToggleFilter,
			 "green":	self.keyUpdate,
			 "yellow":	self.keyOpenServerlist,
			 "blue":	self.keyDvd,
			 "up": 		self.up,
			 "down": 	self.down,
			 "left": 	self.left,
			 "right": 	self.right,
			 "ok":		self.ok,
			 "prevBouquet": self.switchToFileList,
			 "nextBouquet": self.switchToPlayList,
			 }, -1)
		self.currentList = None
		self.playlistIds = []

		self.onClose.append(self.__onClose)
		self.onFirstExecBegin.append(self.__onFirstExecBegin)

	def __onFirstExecBegin(self):
		self.setTitle("vlc://" + (self.server.getName() or self.server.getHost()) + "/" + self.server.getBasedir())
		self["current_dir"].setText(self.server.getBasedir())
			
	def __onClose(self):
		try:
			for id in self.playlistIds:
				self.server.delete(id)
		except Exception, e:
			pass
			
	def close(self, proceed = False):
		Screen.close(self, proceed)

	def keyUpdate(self):
		self.updateFilelist()
		self.updatePlaylist()
		if self.currentList == self["playlist"]:
			self.switchToPlayList()
		else:
			self.switchToFileList()

	def updatePlaylist(self):
		self["playlist"].update()

	def updateFilelist(self):
		self["filelist"].update()

	def keyToggleFilter(self):
		if self["filelist"].regex is None:
			self["filelist"].changeRegex(self.defaultFilter)
			self["key_red"].setText(_("filter off"))
		else:
			self["filelist"].changeRegex(None)
			self["key_red"].setText(_("filter on"))
		try:
			self.updateFilelist()
		except Exception, e:
			self.session.open(
				MessageBox, _("Error updating filelist from server %(server)s:\n%(error)s" % (
						{"server" : self.server.getName(), "error" : e})
					), MessageBox.TYPE_ERROR)

	def keyDvd(self):
		self.play("dvdsimple://" + self.server.getDvdPath(), "DVD")

	def keyOpenServerlist(self):
		self.close(True)

	def up(self):
		self.currentList.up()

	def down(self):
		self.currentList.down()

	def left(self):
		self.currentList.pageUp()

	def right(self):
		self.currentList.pageDown()

	def play(self, media, name):
		self.server.play(self.session, media, name, self.currentList)

	def ok(self):
		media, name = self.currentList.activate()
		if media is not None:
			if media.lower().endswith(".m3u") or media.lower().endswith(".pls") or media.lower().endswith(".xspf"):
				try:
					id = self.server.loadPlaylist(media)
					if id is not None:
						self.playlistIds.append(id)
						self.updatePlaylist()
						self.switchToPlayList()
				except Exception, e:
					self.session.open(
						MessageBox, _("Error loading playlist %(media)s into server %(server)s:\n%(error)s" % (
								{"media" : media, "server" : self.server.getName(), "error" : e})
							), MessageBox.TYPE_ERROR)
			elif media.lower().endswith(".iso"):
				self.play("dvdsimple://" + media, "DVD")
			else:
				self.play(media, name)
		elif name is not None:
			self.setTitle("vlc://" + (self.server.getName() or self.server.getHost()) + "/" + name)
			self["current_dir"].setText(name)

	def getFilesAndDirsCB(self, currentDirectory, regex):
		try:
			return self.server.getFilesAndDirs(currentDirectory, regex)
		except ExpatError, e:
			self.session.open(
				MessageBox, _("Error loading playlist into server %(server)s:\n%(error)s" % (
						{"server" : self.server.getName(), "error" : e })
					), MessageBox.TYPE_ERROR)
			raise ExpatError, e
		except Exception, e:
			self.session.open(
				MessageBox, _("Error loading filelist into server %(server)s:\n%(error)s" % (
						{"server" : self.server.getName(), "error" : e })
					), MessageBox.TYPE_ERROR)
		return None

	def getPlaylistEntriesCB(self):
		try:
			return self.server.getPlaylistEntries()
		except ExpatError, e:
			self.session.open(
				MessageBox, _("Error loading playlist into server %(server)s:\n%(error)s" % (
						{"server" : self.server.getName(), "error" : e })
					), MessageBox.TYPE_ERROR)
		except Exception, e:
			self.session.open(
				MessageBox, _("Error loading playlist into server %(server)s:\n%(error)s" % (
						{"server" : self.server.getName(), "error" : e })
					), MessageBox.TYPE_ERROR)
		return None

	def switchLists(self):
		if self.currentList == self["filelist"]:
			self.switchToPlayList()
		else:
			self.switchToFileList()

	def switchToFileList(self):
		self["filelist"].selectionEnabled(1)
		self["filelist"].show()
		self["filelist_button_sel"].show()
		self["playlist"].selectionEnabled(0)
		self["playlist"].hide()
		self["playlist_button_sel"].hide()
		self.currentList = self["filelist"]

	def switchToPlayList(self):
		self["filelist"].selectionEnabled(0)
		self["filelist"].hide()
		self["filelist_button_sel"].hide()
		self["playlist"].selectionEnabled(1)
		self["playlist"].show()
		self["playlist_button_sel"].show()
		self.currentList = self["playlist"]
