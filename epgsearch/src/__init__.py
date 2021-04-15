# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigText, ConfigNumber, ConfigYesNo, ConfigSelection
from collections import OrderedDict


class SearchType:
	ASK = "ask"
	EXACT_TITLE = "exact_title"
	TITLE = "title"
	TITLE_DESCRIPTION = "title_description"

	CHOICES = OrderedDict()
	CHOICES[ASK] = _("Ask user")
	CHOICES[EXACT_TITLE] = _("Exact match of title")
	CHOICES[TITLE] = _("Partial match of title")
	CHOICES[TITLE_DESCRIPTION] = _("Partial match of title or description")

	BUTTON_CHOICES = [("none", _("none")), ("red", _("Channellist red")), ("blue", _("EPG Single/Eventview blue")), ("all", _("all"))]


config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.history = ConfigSet(choices=[])
config.plugins.epgsearch.history_length = ConfigNumber(default=10)
config.plugins.epgsearch.add_history_onOpen = ConfigYesNo(default=True)
config.plugins.epgsearch.search_type = ConfigSelection(choices=SearchType.CHOICES, default=SearchType.ASK)
config.plugins.epgsearch.search_scope = ConfigText(default="all", fixed_size=False)
config.plugins.epgsearch.show_shortdesc = ConfigYesNo(default=False)
config.plugins.epgsearch.show_events = ConfigSelection(choices=[("all", _("all")), ("current", _("current")), ("future", _("future")), ("current_future", _("current & future"))], default="all")
config.plugins.epgsearch.show_sname_in_title = ConfigYesNo(default=False)
config.plugins.epgsearch.show_picon = ConfigYesNo(default=False)
config.plugins.epgsearch.blue_function = ConfigSelection(choices=[("combi", _("Text search history with search filters")), ("ask", _("Ask user")), ("searchlist", _("Search filter list")), ("history", _("Text search history"))], default="combi")

config.plugins.epgsearch.searchEPG_menu = ConfigSelection(choices=SearchType.BUTTON_CHOICES, default="all")
config.plugins.epgsearch.openSearchFilter_menu = ConfigSelection(choices=SearchType.BUTTON_CHOICES, default="all")
config.plugins.epgsearch.addSearchFilter_menu = ConfigSelection(choices=SearchType.BUTTON_CHOICES, default="all")
