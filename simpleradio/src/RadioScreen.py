from __future__ import absolute_import
from enigma import eServiceReference, iPlayableService
from skin import loadSkin
from Components.config import config, ConfigSubsection, ConfigText
from Components.ActionMap import NumberActionMap
from Components.Label import Label
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.List import List
from Screens.ChoiceBox import ChoiceBox
from Components.Sources.StaticText import StaticText
from Screens.InfoBarGenerics import InfoBarServiceErrorPopupSupport, InfoBarGstreamerErrorPopupSupport, InfoBarStateInfo
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ServiceStopScreen import ServiceStopScreen
from Tools.NumericalTextInput import NumericalTextInput

import os

from .RadioBrowserClient import RadioBrowserClient

loadSkin("%s/skin.xml" % (os.path.dirname(__file__)))

config.plugins.simpleradio = ConfigSubsection()
config.plugins.simpleradio.country = ConfigText(default="Germany", fixed_size=False)

class RadioScreen(Screen, ServiceStopScreen, InfoBarServiceErrorPopupSupport, InfoBarGstreamerErrorPopupSupport):
	def __init__(self, session):
		Screen.__init__(self, session, windowTitle=_("Radio"))
		self.skinName = "SimpleRadioScreen"
		ServiceStopScreen.__init__(self)
		self.stopService()
		self._list = List([], buildfunc=self._buildFunc)
		self._serviceLabel = Label("")

		InfoBarServiceErrorPopupSupport.__init__(self)
		InfoBarGstreamerErrorPopupSupport.__init__(self)

		self._service = None

		self.numericalTextInput = NumericalTextInput()
		self.numericalTextInput.setUseableChars(u'1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')

		self["attribution"] = Label(_("powered by www.radio-browser.info"))
		self["country"] = StaticText("")
		self["list"] = self._list
		self["service"] = self._serviceLabel
		self["actions"] = NumberActionMap(["OkCancelActions", "NumberActions", "ColorActions"],
		{
			"ok": self._onOk,
			"cancel": self.close,
			"blue": self._onBlue,
			"1": self._onKeyChar,
			"2": self._onKeyChar,
			"3": self._onKeyChar,
			"4": self._onKeyChar,
			"5": self._onKeyChar,
			"6": self._onKeyChar,
			"7": self._onKeyChar,
			"8": self._onKeyChar,
			"9": self._onKeyChar,
			"0": self._onKeyChar
		}, -1)

		self._country = config.plugins.simpleradio.country.value
		self._browser = RadioBrowserClient()
		self._onLoadFinished({})
		self._browser.stations(self._country.lower(), self._onLoadFinished)
		self["country"].setText(_(self._country.capitalize()))
		self._browser.countries(self._onCountriesReady)
		self._stateInfo = self.session.instantiateDialog(InfoBarStateInfo,zPosition=50)
		self._infoBarStateInfo = InfoBarServiceErrorPopupSupport._stateInfo
		InfoBarServiceErrorPopupSupport._stateInfo = self._stateInfo
		self.onClose.append(self.__onClose)

	def __onClose(self):
		InfoBarServiceErrorPopupSupport._stateInfo = self._infoBarStateInfo

	@property
	def list(self):
		return self._list.list

	def _buildFunc(self, station):
		return [station.name, station.country, station.clickcount, station.bitrate]

	def _onCountriesReady(self, countries):
		self._countries = countries

	def _onBlue(self):
		if self._countries:
			self._selectCountry()

	def _selectCountry(self):
		if not self._countries:
			return
		countries = [("{} ({})".format(_(c.name), c.stationCount), c) for c in self._countries]
		choices = sorted(countries, key=lambda x: x[0])
		self.session.openWithCallback(self._onCountrySelected, ChoiceBox, list=choices, windowTitle=_("Select a country"))

	def _onCountrySelected(self, country):
		country = country and country[1]
		if country:
			config.plugins.simpleradio.country.value = country.name
			config.plugins.simpleradio.save()
			self._country = country.name
			self._onLoadFinished({})
			self._browser.stations(country.name.lower(), self._onLoadFinished)
			self["country"].setText(_(country.name.capitalize()))

	def _onLoadFinished(self, stations):
		lst = []
		keys = sorted(stations.keys(), key=lambda x: str(x).lower())
		for key in keys:
			station = stations[key]
			lst.append((station,))
		self._list.list = lst

	def _onOk(self):
		station = self._list.getCurrent()
		station = station and station[0]
		if station:
			ref = eServiceReference(eServiceReference.idGST, eServiceReference.isLive, station.urlsResolved[0])
			ref.setName(station.name)
			self._play(ref)

	def _play(self, service):
		self._stop()
		self._service = service
		self.session.nav.playService(service)
		self._serviceLabel.setText(self._service.getName())

	def _stop(self):
		self._serviceLabel.setText(_("Please pick a radio stream..."))
		self._service = None
		self.session.nav.stopService()

	def _onKeyChar(self, number):
		unichar = self.numericalTextInput.getKey(number)
		charstr = unichar.encode("utf-8")
		if len(charstr) != 1:
			return
		index = 0
		for s in self.list:
			if s[0].name.upper().startswith(charstr):
				self._list.index = index
				break
			index += 1

