from Components.config import config, ConfigSubsection, ConfigYesNo, ConfigSelectionNumber, ConfigSelection
import json
import os.path

#######################################################
# Initialize Configuration
config.plugins.skipintro = ConfigSubsection()

default_title_pattern = "(.*?)\s-\s(S\d+)E(.+)\s-\s(.*)"
pattern_config_file_path = "/etc/enigma2/SkipIntro.pattern.json"

if not os.path.exists(pattern_config_file_path):
	without_title_pattern = "(.*?)\s-\s(S\d+)E(.+)"
	title_pattern_choices = [
			("Off", _("Disabled")),
			(default_title_pattern, "Series - S01E01 - Title"),
			(without_title_pattern, "Series - S01E01")
		]

	with open(pattern_config_file_path, "w") as write_file:
		json.dump(dict(title_pattern_choices), write_file, ensure_ascii=False, indent=4)

with open(pattern_config_file_path, "r") as read_file:
    data = json.load(read_file)
title_pattern_choices = list(data.items())

config.plugins.skipintro.show_skipmsg = ConfigYesNo(default = True)
config.plugins.skipintro.show_videostartmsg = ConfigYesNo(default = False)
config.plugins.skipintro.skiptime_decrease = ConfigSelectionNumber(0, 5, 1, default = 0)
config.plugins.skipintro.title_pattern = ConfigSelection(choices = title_pattern_choices, default = default_title_pattern)
#config.plugins.skipintro.save_season = ConfigYesNo(default = False)