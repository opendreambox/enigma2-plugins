# -*- coding: utf-8 -*-

# for localized messages
from . import _x

from Plugins.Plugin import PluginDescriptor
from SerienFilm import SerienFilmVersion, SerienFilmCfg
from traceback import print_exc
from sys import stdout, exc_info
from Screens.InfoBar import MoviePlayer
from MovieSelection import MovieSelection


def pluginConfig(session, **kwargs):
	print "[SF-Plugin] Config\n"
	try:
		session.open(SerienFilmCfg)
	except Exception, e:
		print "[SF-Plugin] pluginConfig Config exception:\n" + str(e)


gLeavePlayerConfirmed = None

def showMoviesSF(self):
	try:
#		print "[SF-Plugin] showMoviesSF.InfoBar"
		self.session.openWithCallback(self.movieSelected, MovieSelection)
	except Exception, e:
		print "[SF-Plugin] showMoviesSF exception:\n" + str(e)

def showMoviesMP(self):
	ref = self.session.nav.getCurrentlyPlayingServiceReference()
#	print "[SF-Plugin] SF:MoviePlayer.showMoviesMP"
#	print "[SF-Plugin] SF:MoviePlayer.showMoviesMP, ref=" + str(ref)
	self.session.openWithCallback(self.movieSelected, MovieSelection, ref)

def leavePlayerConfirmedMP(self, answer):
	answer1 = answer and answer[1]

	if answer1 == "movielist":
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.returning = True
		self.session.openWithCallback(self.movieSelected, MovieSelection, ref)
		self.session.nav.stopService()
	else:
		gLeavePlayerConfirmed(self, answer)

RUNPLUGIN = 1

def autostart(reason, **kwargs):
	if RUNPLUGIN != 1: return
	if reason == 0: # start
		if kwargs.has_key("session"):
			global gLeavePlayerConfirmed
			Session = kwargs["session"]
			print "[SF-Plugin] autostart, Session = " +  str(Session) + "\n"
			try:
				from Screens.InfoBar import InfoBar
				InfoBar.showMovies = showMoviesSF
				MoviePlayer.showMovies = showMoviesMP
				if gLeavePlayerConfirmed is None:
					gLeavePlayerConfirmed = MoviePlayer.leavePlayerConfirmed
				MoviePlayer.leavePlayerConfirmed = leavePlayerConfirmedMP

			except Exception, e:
				print "[SF-Plugin] autostart MovieList launch override exception:\n" + str(e)

		else:
			print "[SF-Plugin] autostart without session\n"


def Plugins(**kwargs):
	descriptors = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)]
	descriptors.append( PluginDescriptor(
		name = "SerienFilm "+SerienFilmVersion,
		description = _x("group movies of a series to virtual directories"),
		icon = "SerienFilm.png",
		where = PluginDescriptor.WHERE_PLUGINMENU,
		fnc = pluginConfig) )
	print "[SF-Plugin] autostart descriptors = " + str(descriptors)
	return descriptors
