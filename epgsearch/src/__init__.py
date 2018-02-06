# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigText, ConfigNumber, ConfigYesNo, ConfigSelection

class SearchType:
	ASK = "ask"
	TITLE = "title"
	TITLE_DESCRIPTION = "title_description"
	CHOICES = {
		ASK : _("Always Ask"),
		TITLE : _("Title only"),
		TITLE_DESCRIPTION : _("Title and Description"),
	}

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.history = ConfigSet(choices = [])
config.plugins.epgsearch.history_length = ConfigNumber(default = 10)
config.plugins.epgsearch.add_search_to_epg = ConfigYesNo(default = True)
config.plugins.epgsearch.search_type = ConfigSelection(choices=SearchType.CHOICES, default=SearchType.ASK)
