from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSet, ConfigElement
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.Boolean import Boolean
from Components.ServiceEventTracker import ServiceEventTracker
from Components.SortableList import SortableListScreen
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Tools.BoundFunction import boundFunction

class TrackAutoselectSetup(Screen, ConfigListScreen):
	skin = """
		<screen name="TrackAutoselectSetup" position="center,120" size="820,520" title="Track Autoselect configuration">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
			<widget source="button_yellow" render="Pixmap" position="410,5" size="200,40" pixmap="skin_default/buttons/yellow.png" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on"/>
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
			<widget name="config" position="10,60" size="800,390" enableWrapAround="1" scrollbarMode="showOnDemand"/>
		</screen>"""

	def __init__(self, session, track_autoselect_config):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [], session=session)
		self.track_autoselect_config = track_autoselect_config

		self["button_yellow"] = Boolean(False)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label("")
		self["key_blue"] = Label(_("Edit"))

		self["SetupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"save": self.keySave,
			"cancel": self.keyCancel,
			"ok": self.modifyEntry,
			"blue": self.modifyEntry,
			"yellow": self.keyYellow
		}, -3)
		self.onLayoutFinish.append(self.__layoutFinished)
		self.onClose.append(self.removeNotifiers)

	def __layoutFinished(self):
		cptas = config.plugins.TrackAutoselect
		for element in [cptas.audio_autoselect_enable, cptas.audio_parameter_order, cptas.subtitle_autoselect_enable, cptas.subtitle_parameter_order]:
			element.addNotifier(self.fillList, initial_call=False)
		self.fillList()

	def fillList(self, element=None):
		C = self.track_autoselect_config
		cptas = config.plugins.TrackAutoselect
		conflist = []
		conflist.append(getConfigListEntry(_("Enable automatic selection of audio tracks"), config.plugins.TrackAutoselect.audio_autoselect_enable))
		if cptas.audio_autoselect_enable.getValue():
			conflist.append(getConfigListEntry(C.CATEGORY_AUDIO_ORDER, cptas.audio_parameter_order))
			for parameter in cptas.audio_parameter_order.getValue():
				if parameter == C.AUDIO_ORDER_FORMAT:
					conflist.append(getConfigListEntry(C.CATEGORY_AUDIO_FORMAT, cptas.audio_format_preference))
				if parameter == C.AUDIO_ORDER_LANGUAGE:
					conflist.append(getConfigListEntry(C.CATEGORY_AUDIO_LANGUAGE, cptas.audio_language_preference))
				#if parameter == C.AUDIO_ORDER_DESCRIPTION:
					#conflist.append(getConfigListEntry(C.CATEGORY_AUDIO_DESCRIPTION, cptas.audio_description_preference))

		conflist.append(getConfigListEntry(_("Enable automatic selection of subtitle tracks"), cptas.subtitle_autoselect_enable))
		if cptas.subtitle_autoselect_enable.getValue():
			conflist.append(getConfigListEntry(C.CATEGORY_SUBTITLE_ENABLE, cptas.subtitle_enable_conditions))
			conflist.append(getConfigListEntry(C.CATEGORY_SUBTITLE_ORDER, cptas.subtitle_parameter_order))
			for parameter in cptas.subtitle_parameter_order.getValue():
				if parameter == C.SUBTITLE_ORDER_LANGUAGE:
					conflist.append(getConfigListEntry(C.CATEGORY_SUBTITLE_LANGUAGE, cptas.subtitle_language_preference))
				if parameter == C.SUBTITLE_ORDER_FORMAT:
					conflist.append(getConfigListEntry(C.CATEGORY_SUBTITLE_FORMAT, cptas.subtitle_format_preference))

		conflist.append(getConfigListEntry(C.CATEGORY_HANDLE_SERVICES, cptas.handle_services))
		conflist.append(getConfigListEntry(_("subtitle and audio language may be the same"), cptas.same_languages))
		conflist.append(getConfigListEntry(_("EIT wait timeout (ms) before auto selection"), cptas.wait_for_eit))
		self["config"].l.setList(conflist)
		self["config"].list = conflist

	def removeNotifiers(self):
		cptas = config.plugins.TrackAutoselect
		for element in [cptas.audio_autoselect_enable, cptas.audio_parameter_order, cptas.subtitle_autoselect_enable, cptas.subtitle_parameter_order]:
			element.clearNotifiers()

	def keySave(self):
		#print "[TrackAutoselectSetup] keySave"
		ConfigListScreen.keySave(self)

	def keyCancel(self):
		#print "[TrackAutoselectSetup] keyCancel"
		ConfigListScreen.keyCancel(self)

	def keyYellow(self):
		print "[TrackAutoselectSetup] keyYellow"

	def modifyEntry(self):
		cur = self["config"].getCurrent()
		if isinstance(cur, tuple) and isinstance(cur[1], ConfigSet):
			preference_list = cur[1].getValue()
			category = cur[0]
			(available_choices, preference_tuplelist) = self.track_autoselect_config.getAvailableChoicesAndPreferenceTuplelist(category, preference_list)
			self.session.openWithCallback(boundFunction(self.preferencesSetCB, cur[1]), TrackAutoselectPreferenceListScreen, category, available_choices, preference_tuplelist)
		else:
			ConfigListScreen.keyRight(self)

	def preferencesSetCB(self, config_item, preference_tuplelist):
		if isinstance(preference_tuplelist, list) and isinstance(config_item, ConfigElement):
			new_value = [entry[0] for entry in preference_tuplelist]
			if new_value != config_item.getValue():
				#print "[TrackAutoselectSetup]:preferencesSetCB old value", config_item.getValue()
				config_item.value = [entry[0] for entry in preference_tuplelist]
				#print "[TrackAutoselectSetup]:preferencesSetCB new value", config_item.getValue()

	def close(self):
		Screen.close(self)

class TrackAutoselectPreferenceListScreen(Screen, SortableListScreen):
	skin = """
		<screen name="TrackAutoselectPreferenceListScreen" position="center,120" size="820,520">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
			<widget source="button_yellow" render="Pixmap" position="410,5" size="200,40" pixmap="skin_default/buttons/yellow.png" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget source="button_blue" render="Pixmap" position="610,5" size="200,40" pixmap="skin_default/buttons/blue.png" alphatest="on">
				<convert type="ConditionalShowHide" />
			</widget>
			<widget name="key_red" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_green" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_yellow" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<widget name="key_blue" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
			<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
			<widget name="list" position="10,60" size="800,390" enableWrapAround="1" scrollbarMode="showOnDemand"/>
			<eLabel	position="10,480" size="800,1" backgroundColor="grey"/>
			<widget name="info" position="10,488" size="800,25" font="Regular;22" halign="center" transparent="1"/>
		</screen>"""

	def __init__(self, session, category, available_choices, preference_tuplelist):
		Screen.__init__(self, session)

		self.category = category
		self.available_choices = available_choices

		SortableListScreen.__init__(self, session, preference_tuplelist)

		self["button_yellow"] = Boolean(True)
		self["button_blue"] = Boolean(True)
		self["key_yellow"] = Label(_("Add"))
		self["key_blue"] = Label(_("Remove"))
		self.setTitle(category)

		self["ColorActions"] = ActionMap(["ColorActions"],
		{
			"blue": self.keyBlue,
			"yellow": self.keyYellow
		}, -3)

	def keyYellow(self):
		#print "[TrackAutoselectPreferenceListScreen] keyYellow", self.available_choices
		if len(self.available_choices):
			self.session.openWithCallback(self.entryChosen, ChoiceBox, title=self.category, list=self.available_choices, keys=[str(x)[-1] for x in list(range(1,11))]+(len(self.available_choices)-10)*[False])

	def entryChosen(self, entry):
		#print "[TrackAutoselectPreferenceListScreen] entryChosen", entry, type(entry)
		if isinstance(entry, tuple):
			#print "[TrackAutoselectPreferenceListScreen] available_choices", self.available_choices, " -> entry", entry
			self.available_choices.remove(entry)
			self["list"].insertEntry(tuple(reversed(entry)))

	def keyBlue(self):
		cur = self["list"].getCurrent()
		#print "[TrackAutoselectPreferenceListScreen] keyBlue", cur
		if isinstance(cur, list):
			#print "[TrackAutoselectPreferenceListScreen] cur[0]", cur[0], "-> available_choices", self.available_choices
			self.available_choices.append(tuple(reversed(cur[0][:2])))
			self.available_choices.sort()
			#print "[TrackAutoselectPreferenceListScreen] new available_choices", self.available_choices
		self["list"].removeCurrentEntry()
