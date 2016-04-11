from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.InfoBar import InfoBar
from Screens.Screen import Screen
from enigma import eTimer, eServiceReference, iPlayableService, iSubtitleFilterType_ENUMS, iSubtitleType_ENUMS

class Stream(object):
	def __init__(self, idx, codec, languages, selected=False, forced=False, description=""):
		self.idx = int(idx)
		self.codec = codec
		self.languages = languages
		self.selected = selected
		self.forced = forced
		self.description = description
	def __repr__(self):
		return "<stream idx=%i, codec=%s, languages='%s'%s%s%s>" % (self.idx, str(self.codec), str(self.languages), self.description and " description='"+self.description+"'" or "", self.selected and " SELECTED" or "", self.forced and " FORCED" or "")

class TrackAutoselector(object):
	instance = None
	(MATCHED_PRIMARY, MATCHED_ANY, MATCHED_NONE) = range(3)

	def __init__(self, session, track_autoselect_config):
		assert TrackAutoselector.instance is None, "TrackAutoselector is a singleton class and may only be initialized once!"
		TrackAutoselector.instance = self
		self.session = session
		self.track_autoselect_config = track_autoselect_config
		self.onClose = []
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		{
			iPlayableService.evStart: self.__initializeVars,
			iPlayableService.evEnd: self.__serviceStopped,
			iPlayableService.evUpdatedInfo: self.__updatedInfo,
			iPlayableService.evUpdatedEventInfo: self.__updatedEventInfo
		})
		self._infobar = InfoBar.instance
		self._nav = session.nav
		self._waitForEventInfoTimer = eTimer()
		self._waitForEventInfoTimer_conn = self._waitForEventInfoTimer.timeout.connect(self.__updatedInfoTimeoutCB)
		self.__initializeVars()

	def __initializeVars(self):
		self.audiostreams = []
		self._stype = None

	def __serviceStopped(self):
		self._waitForEventInfoTimer.stop()
		self.__initializeVars()

	def __updatedInfo(self):
		if not self._stype:
			currentSREF = self._nav.getCurrentlyPlayingServiceReference()
			stype = currentSREF and currentSREF.valid() and currentSREF.type or None
			if stype in self.track_autoselect_config.services_dict:
				self._stype = self.track_autoselect_config.services_dict[stype]
		if self.isDVB:
			self._waitForEventInfoTimer.start(config.plugins.TrackAutoselect.wait_for_eit.value, True)

	isDVB = property(lambda self: self._stype == self.track_autoselect_config.SERVICE_DVB)

	def __updatedInfoTimeoutCB(self):
		#print "[TrackAutoselector]:__updatedInfoTimeoutCB"
		self.doSelect()

	def __updatedEventInfo(self):
		#print "[TrackAutoselector]:__updatedEventInfo"
		self._waitForEventInfoTimer.stop()
		self.doSelect()

	def doSelect(self):
		print "[TrackAutoselector]:doSelect self._stype", self._stype, "in handle_services", config.plugins.TrackAutoselect.handle_services.getValue(), self._stype in config.plugins.TrackAutoselect.handle_services.getValue()
		if self._stype in config.plugins.TrackAutoselect.handle_services.getValue():
			if config.plugins.TrackAutoselect.audio_autoselect_enable.getValue():
				self.selectAudio()
			if config.plugins.TrackAutoselect.subtitle_autoselect_enable.getValue():
				self.selectSubtitles()

	def orderLanguageByPreference(self, stream, preference_list):
		#print "[TrackAutoselector]:orderLanguageByPreference", stream, "preference_list", preference_list
		ret = 1000 + stream.idx
		for language in stream.languages:
			if language in self.track_autoselect_config.language_comparison_dict:
				language = self.track_autoselect_config.language_comparison_dict[language]
				#print "[TrackAutoselector]:from comparison dict found id value=", language, language in preference_list
				if language in preference_list:
					idx = preference_list.index(language)
					#print "[TrackAutoselector]:from preference_list idx", idx, "<", ret, "?", idx < ret
					if idx < ret:
						ret = idx
		#print "[TrackAutoselector]:orderLanguageByPreference return", ret
		return ret

	def orderFormatByPreference(self, stream, preference_list):
		#print "[TrackAutoselector]:orderFormatByPreference", stream, "preference_list", preference_list
		ret = 1000 + stream.idx
		codec = stream.codec
		if codec in preference_list:
			ret = preference_list.index(codec)
		#print "[TrackAutoselector]:orderFormatByPreference return", ret
		return ret

	def matchAudiostreamPreference(self):
		language_preferences = config.plugins.TrackAutoselect.audio_language_preference.getValue()
		matched = self.MATCHED_NONE
		for stream in self.audiostreams:
			for language in stream.languages:
				if language in self.track_autoselect_config.language_comparison_dict:
					language = self.track_autoselect_config.language_comparison_dict[language]
					if language in language_preferences:
						if stream == self.audiostreams[0] and language == language_preferences[0]:
							print "[TrackAutoselector]:matchAudiostreamPreference primary audio language selected", stream
							self.primary_audio_matched = True
							return self.MATCHED_PRIMARY
						matched = self.MATCHED_ANY
						print "[TrackAutoselector]:matchAudiostreamPreference stream %i language '%s' matches one of preferred languages" % (stream.idx, language), language_preferences
		return matched

	def selectAudio(self):
		service = self._nav.getCurrentService()
		audioTracks = audio = service and service.audioTracks()
		n = audio and audio.getNumberOfTracks() or 0
		if n == 0:
			return

		C = self.track_autoselect_config
		selectedAudio = audioTracks.getCurrentTrack()

		for idx in range(n):
			info = audio.getTrackInfo(idx)
			codec = C.audio_format_dict[info.getType()]
			languages = info.getLanguage().split('/')
			description = info.getDescription() or ""
			self.audiostreams.append(Stream(idx, codec, languages, info.isSelected(), description=description))
		print "[TrackAutoselector]:selectAudio list of audio streams", self.audiostreams

		language_preferences = config.plugins.TrackAutoselect.audio_language_preference.getValue()

		if n > 1:
			for parameter in config.plugins.TrackAutoselect.audio_parameter_order.value[::-1]:
				if parameter == C.AUDIO_ORDER_SERVICE and self.isDVB:
					self.audiostreams.sort(key=lambda stream: not stream.selected)
					print "[TrackAutoselector]:selectAudio now sorted by dvb service cache", self.audiostreams
				elif parameter == C.AUDIO_ORDER_DEFAULT and not self.isDVB:
					self.audiostreams.sort(key=lambda stream: not stream.selected)
					print "[TrackAutoselector]:selectAudio now sorted by default (selected) flag (non-dvb service)", self.audiostreams
				elif parameter == C.AUDIO_ORDER_FORMAT:
					self.audiostreams.sort(key=lambda stream: self.orderFormatByPreference(stream, config.plugins.TrackAutoselect.audio_format_preference.getValue()))
					print "[TrackAutoselector]:selectAudio now sorted by codec format", self.audiostreams
				elif parameter == C.AUDIO_ORDER_LANGUAGE:
					self.audiostreams.sort(key=lambda stream: self.orderLanguageByPreference(stream, language_preferences))
					print "[TrackAutoselector]:selectAudio now sorted by language", self.audiostreams
			print "[TrackAutoselector]:selectAudio final resorted list of audio streams:", self.audiostreams, "selectedAudio:", selectedAudio

		top_idx = self.audiostreams[0].idx
		if top_idx != selectedAudio:
			audioTracks.selectTrack(top_idx)

	def selectSubtitles(self):
		subs = self._infobar.getCurrentServiceSubtitle()
		n = subs and subs.getNumberOfSubtitleTracks() or 0
		if n == 0:
			return

		C = self.track_autoselect_config
		audio_matched = self.matchAudiostreamPreference()
		playing_idx = self._infobar.subtitles_enabled and self._infobar.selected_subtitle or None

		streams = []
		for idx in range(n):
			info = subs.getSubtitleTrackInfo(idx)
			languages = info.getLanguage().split('/')
			iType = info.getType()
			if iType == iSubtitleType_ENUMS.GST:
				iType = info.getGstSubtype()
				codec = C.gstsub_format_dict[iType]
			else:
				codec = C.sub_format_dict[iType]
			streams.append(Stream(idx, codec, languages, info.isSelected(), info.isForced()))
		print "[TrackAutoselector]:selectSubtitles list of subtitle streams", streams

		if n > 1:
			for parameter in config.plugins.TrackAutoselect.subtitle_parameter_order.value[::-1]:
				if parameter == C.SUBTITLE_ORDER_SERVICE and self.isDVB:
					streams.sort(key=lambda stream: not stream.selected)
					print "[TrackAutoselector]:selectSubtitles now sorted by dvb service cache", streams
				elif parameter == C.SUBTITLE_ORDER_DEFAULT and not self.isDVB:
					streams.sort(key=lambda stream: not stream.selected)
					print "[TrackAutoselector]:selectSubtitles now sorted by default (selected) flag (non-dvb service)", streams
				elif parameter == C.SUBTITLE_ORDER_FORCED:
					streams.sort(key=lambda stream: not stream.forced)
					print "[TrackAutoselector]:selectSubtitles now sorted by forced flag", streams
				elif parameter == C.SUBTITLE_ORDER_LANGUAGE:
					streams.sort(key=lambda stream: self.orderLanguageByPreference(stream, config.plugins.TrackAutoselect.subtitle_language_preference.getValue()))
					print "[TrackAutoselector]:selectSubtitles now sorted by language", streams
				elif parameter == C.SUBTITLE_ORDER_FORMAT:
					streams.sort(key=lambda stream: self.orderFormatByPreference(stream, config.plugins.TrackAutoselect.subtitle_format_preference.getValue()))
					print "[TrackAutoselector]:selectSubtitles now sorted by codec format", streams
			print "[TrackAutoselector]:selectAudio resorted list of subtitle streams:", streams, "playing_idx:", playing_idx

		enable = False

		for parameter in config.plugins.TrackAutoselect.subtitle_enable_conditions.getValue():
			if parameter == C.SUBTITLE_ENABLE_ALWAYS:
				print "[TrackAutoselector]:selectSubtitles enable always"
				enable = True
			elif parameter == C.SUBTITLE_ENABLE_SERVICE and self.isDVB:
				selected = any([stream.selected for stream in streams])
				enable = enable or selected
				print "[TrackAutoselector]:selectSubtitles enable if selected (stored by dvb service)", selected
			elif parameter == C.SUBTITLE_ENABLE_DEFAULT and not self.isDVB:
				selected = any([stream.selected for stream in streams])
				enable = enable or selected
				print "[TrackAutoselector]:selectSubtitles enable if default (selected) flag set (non-dvb service)", selected
			elif parameter == C.SUBTITLE_ENABLE_FORCED:
				forced = any([stream.forced for stream in streams])
				enable = enable or forced
				print "[TrackAutoselector]:selectSubtitles enable if forced flag set", forced
			elif parameter == C.SUBTITLE_ENABLE_NOTFIRSTLANG:
				enable = enable or audio_matched != self.MATCHED_PRIMARY
				print "[TrackAutoselector]:selectSubtitles enable if not first audio language", not self.primary_audio_matched
			elif parameter == C.SUBTITLE_ENABLE_NOTANYLANG:
				enable = enable or audio_matched == self.MATCHED_NONE
				print "[TrackAutoselector]:selectSubtitles enable if no specified audio language", not self.any_audio_matched
			if enable:
				break

		if enable and len(self.audiostreams) and not config.plugins.TrackAutoselect.same_languages.getValue():
			for idx, stream in enumerate(streams):
				if not any(lang in stream.languages for lang in self.audiostreams[0].languages) or "und" in stream.languages:
					print "[TrackAutoselector]:selectSubtitles idx", idx, "stream", stream, "is different to autoselected audio language, enable!"
					enable = True
					break
				else:
					print "[TrackAutoselector]:selectSubtitles idx", idx, "stream", stream, "is the same as autoselected audio language, skip!!"
					enable = False

		if enable:
			print "[TrackAutoselector]:selectSubtitles enable stream", streams[0]
			self._infobar.setSelectedSubtitle(streams[0].idx)
			self._infobar.setSubtitlesEnable(True)
