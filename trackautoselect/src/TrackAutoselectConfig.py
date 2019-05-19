from __future__ import print_function
from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigInteger, ConfigSet
from Components.Language import language
from Tools.ISO639 import ISO639Language
from enigma import eServiceReference
import six

class Autoselect639Language(ISO639Language):
		def __init__(self):
			ISO639Language.__init__(self, self.SECONDARY)

		def getTranslatedChoicesDictAndSortedListAndDefaults(self):
			syslang = language.getLanguage()[:2]
			choices_dict = {}
			choices_list = []
			defaults = []
			for lang, id_list in six.iteritems(self.idlist_by_name):
				if syslang not in id_list and 'en' not in id_list:
					name = _(lang)
					short_id = sorted(id_list, key=len)[0]
					choices_dict[short_id] = name
					choices_list.append((short_id, name))
			choices_list.sort(key=lambda x: x[1])
			syslangname = _(self.name_by_shortid[syslang])
			choices_list.insert(0, (syslang, syslangname))
			choices_dict[syslang] = syslangname
			defaults.append(syslang)
			if syslang != "en":
				enlangname = _(self.name_by_shortid["en"])
				choices_list.insert(1, ("en", enlangname))
				choices_dict["en"] = enlangname
				defaults.append("en")
			return (choices_dict, choices_list, defaults)

class TrackAutoselectConfig():
	CATEGORY_AUDIO_ORDER = _("Sort order of audio parameters")
	CATEGORY_AUDIO_LANGUAGE = _("Preference of audio language")
	CATEGORY_AUDIO_FORMAT = _("Preference of audio format")
	CATEGORY_AUDIO_DESCRIPTION = _("Preference of audio description")
	CATEGORY_SUBTITLE_ENABLE = _("Auto-enable conditions for subtitles")
	CATEGORY_SUBTITLE_ORDER = _("Sort order of subtitle parameters")
	CATEGORY_SUBTITLE_LANGUAGE = _("Preference of subtitle language")
	CATEGORY_SUBTITLE_FORMAT = _("Preference of subtitle format")
	CATEGORY_HANDLE_SERVICES = _("Selection of handled Services")

	audio_order_choices = [("saved",_("saved")), ("default",_("default")), ("format",_("format")), ("language",_("Language")), ("Description",_("Description"))]
	[AUDIO_ORDER_SAVED, AUDIO_ORDER_DEFAULT, AUDIO_ORDER_FORMAT, AUDIO_ORDER_LANGUAGE, AUDIO_ORDER_DESCRIPTION] = [x[0] for x in audio_order_choices]

	subtitle_order_choices = [("saved",_("saved")), ("default",_("default")), ("forced",_("forced")), ("language",_("Language")), ("format",_("format"))]
	[SUBTITLE_ORDER_SAVED, SUBTITLE_ORDER_DEFAULT, SUBTITLE_ORDER_FORCED, SUBTITLE_ORDER_LANGUAGE, SUBTITLE_ORDER_FORMAT] = [x[0] for x in subtitle_order_choices]

	subtitle_enable_choices = [("saved",_("saved")), ("default",_("default")), ("forced",_("forced")), ("nofirstlanguage",_("if audio isn't first language")), ("notanylanguage",_("if no prefered audio language")), ("always",_("always"))]
	[SUBTITLE_ENABLE_SAVED, SUBTITLE_ENABLE_DEFAULT, SUBTITLE_ENABLE_FORCED, SUBTITLE_ENABLE_NOTFIRSTLANG, SUBTITLE_ENABLE_NOTANYLANG, SUBTITLE_ENABLE_ALWAYS] = [x[0] for x in subtitle_enable_choices]

	handle_services_choices = [("servicegst",_("Media Files")), ("servicedvb",_("TV Services")), ("servicedvd",_("DVD"))]
	[SERVICE_GST, SERVICE_DVB, SERVICE_DVD] = [x[0] for x in handle_services_choices]

	services_dict = { eServiceReference.idDVB: SERVICE_DVB, 0x1001: SERVICE_GST, 0x1111: SERVICE_DVD }

	def __init__(self):
		from Screens.AudioSelection import AUDIO_FORMATS, SUB_FORMATS, GST_SUB_FORMATS

		self.iso639 = Autoselect639Language()
		(self.language_dict, self.language_choices, self.language_defaults) = self.iso639.getTranslatedChoicesDictAndSortedListAndDefaults()
		self.language_comparison_dict = {}

		self.audio_format_choices = []
		self.sub_format_choices = []

		self.audio_format_dict = {}
		for idx, (short, text, rank) in sorted(list(AUDIO_FORMATS.items()), key=lambda x: x[1][2]):
			if rank > 0:
				self.audio_format_choices.append((short, text))
				self.audio_format_dict[idx] = short

		self.sub_format_dict = {}
		self.gstsub_format_dict= {}
		for idx, (short, text, rank) in sorted(list(SUB_FORMATS.items()), key=lambda x: x[1][2]):
			if rank > 0:
				self.sub_format_choices.append((short, text))
				self.sub_format_dict[idx] = short
		for idx, (short, text, rank) in sorted(list(GST_SUB_FORMATS.items()), key=lambda x: x[1][2]):
			if rank > 0:
				self.sub_format_choices.append((short, short))
				self.gstsub_format_dict[idx] = short

		config.plugins.TrackAutoselect = ConfigSubsection()

		config.plugins.TrackAutoselect.audio_autoselect_enable = ConfigYesNo(default=True)
		config.plugins.TrackAutoselect.audio_parameter_order = ConfigSet(self.audio_order_choices, default=[x[0] for x in self.audio_order_choices[:-1]], resort=False)
		config.plugins.TrackAutoselect.audio_language_preference = ConfigSet(self.language_choices, default=self.language_defaults, resort=False)
		config.plugins.TrackAutoselect.audio_format_preference = ConfigSet(self.audio_format_choices, default=[x[0] for x in self.audio_format_choices], resort=False)
		#config.plugins.TrackAutoselect.audio_description_preference = ConfigSet(self.audio_format_choices, default=[x[0] for x in self.audio_description_choices], resort=False)

		config.plugins.TrackAutoselect.subtitle_autoselect_enable = ConfigYesNo(default=True)
		config.plugins.TrackAutoselect.subtitle_enable_conditions = ConfigSet(self.subtitle_enable_choices, default=[x[0] for x in self.subtitle_enable_choices[:3]], resort=False)
		config.plugins.TrackAutoselect.subtitle_parameter_order = ConfigSet(self.subtitle_order_choices, default=[x[0] for x in self.subtitle_order_choices], resort=False)
		config.plugins.TrackAutoselect.subtitle_language_preference = ConfigSet(self.language_choices, default=self.language_defaults, resort=False)
		config.plugins.TrackAutoselect.subtitle_format_preference = ConfigSet(self.sub_format_choices, default=[x[0] for x in self.sub_format_choices], resort=False)

		config.plugins.TrackAutoselect.handle_services = ConfigSet(self.handle_services_choices, default=[x[0] for x in self.handle_services_choices[:2]], resort=False)
		config.plugins.TrackAutoselect.same_languages = ConfigYesNo(default=False)
		config.plugins.TrackAutoselect.wait_for_eit = ConfigInteger(default=1500, limits = (0, 99999))

		config.plugins.TrackAutoselect.audio_language_preference.addNotifier(self.updateLanguageComparisonDict, initial_call=True)
		config.plugins.TrackAutoselect.subtitle_language_preference.addNotifier(self.updateLanguageComparisonDict, initial_call=True)

	def updateLanguageComparisonDict(self, config_element):
		id_list = config_element.getValue()
		for shortid in id_list:
			name = self.iso639.name_by_shortid[shortid]
			for identry in self.iso639.idlist_by_name[name]:
				self.language_comparison_dict[identry] = shortid

	def getAvailableChoicesAndPreferenceTuplelist(self, category, preference_list):
		#print "[TrackAutoselectConfig] getAvailableChoices for category", category, "minus preference_list", preference_list
		preference_tuplelist = []
		choicelist = []
		choicedict = {}
		if category in [self.CATEGORY_AUDIO_LANGUAGE, self.CATEGORY_SUBTITLE_LANGUAGE]:
			choicelist = self.language_choices
			choicedict = self.language_dict.copy()
		else:
			if category == self.CATEGORY_AUDIO_FORMAT:
				choicelist = self.audio_format_choices
			elif category == self.CATEGORY_SUBTITLE_FORMAT:
				choicelist = self.sub_format_choices
			elif category == self.CATEGORY_AUDIO_ORDER:
				choicelist = self.audio_order_choices
			elif category == self.CATEGORY_SUBTITLE_ORDER:
				choicelist = self.subtitle_order_choices
			elif category == self.CATEGORY_SUBTITLE_ENABLE:
				choicelist = self.subtitle_enable_choices
			elif category == self.CATEGORY_HANDLE_SERVICES:
				choicelist = self.handle_services_choices
			choicedict = dict(choicelist)

		choicelist = [tuple(reversed(x)) for x in choicelist]

		for key in preference_list:
			try:
				value = choicedict[key]
				preference_tuplelist.append((key, value))
				choicelist.remove((value, key))
			except KeyError as e:
				print("[TrackAutoselectConfig] getAvailableChoicesAndPreferenceTuplelist Error in settings! couldn't find key '%s'" % e)

		return (choicelist, preference_tuplelist)

