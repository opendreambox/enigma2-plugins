# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigText, ConfigNumber, ConfigYesNo, ConfigSelection
from collections import OrderedDict

class SearchType:
	ASK = "ask"
	EXAKT_TITLE = "exakt_title"
	TITLE = "title"
	TITLE_DESCRIPTION = "title_description"

	CHOICES = OrderedDict()
	CHOICES[ASK] = _("Ask user")
	CHOICES[EXAKT_TITLE] = _("exact Title-match")
	CHOICES[TITLE] = _("partial Title-match")
	CHOICES[TITLE_DESCRIPTION] = _("partial Title or Description")

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.history = ConfigSet(choices = [])
config.plugins.epgsearch.history_length = ConfigNumber(default = 10)
config.plugins.epgsearch.add_history_onOpen = ConfigYesNo(default = True)
config.plugins.epgsearch.add_search_to_epg = ConfigYesNo(default = True)
config.plugins.epgsearch.search_type = ConfigSelection(choices=SearchType.CHOICES, default=SearchType.ASK)
config.plugins.epgsearch.search_scope = ConfigText(default = "all", fixed_size = False)
config.plugins.epgsearch.show_shortdesc = ConfigYesNo(default = False)
config.plugins.epgsearch.show_events = ConfigSelection(choices=[("all",_("all")),("current",_("current")),("future",_("future")),("current_future",_("current & future"))], default="all")
config.plugins.epgsearch.show_sname_in_title = ConfigYesNo(default = False)
config.plugins.epgsearch.show_picon = ConfigYesNo(default = False)