# -*- coding: utf-8 -*-
# Config
from Components.config import config, ConfigSubsection, ConfigOnOff, \
	ConfigNumber, ConfigSelection, ConfigSelectionNumber, ConfigYesNo, ConfigText

config.plugins.autotimer = ConfigSubsection()
config.plugins.autotimer.autopoll = ConfigOnOff(default=False)
config.plugins.autotimer.delay = ConfigNumber(default=3)
config.plugins.autotimer.editdelay = ConfigNumber(default=3)
config.plugins.autotimer.interval = ConfigNumber(default=3)
config.plugins.autotimer.timeout = ConfigNumber(default=5)
config.plugins.autotimer.refresh = ConfigSelection(choices=[
		("none", _("None")),
		("auto", _("Only AutoTimers created during this session")),
		("all", _("All non-repeating timers"))
	], default="none"
)
config.plugins.autotimer.try_guessing = ConfigOnOff(default=True)
config.plugins.autotimer.editor = ConfigSelection(choices=[
		("plain", _("Classic")),
		("wizard", _("Wizard"))
	], default="wizard"
)
config.plugins.autotimer.addsimilar_on_conflict = ConfigOnOff(default=False)
config.plugins.autotimer.add_autotimer_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.add_name_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.disabled_on_conflict = ConfigOnOff(default=False)
config.plugins.autotimer.show_in_extensionsmenu = ConfigYesNo(default=False)
config.plugins.autotimer.fastscan = ConfigYesNo(default=False)
config.plugins.autotimer.notifconflict = ConfigYesNo(default=True)
config.plugins.autotimer.notifsimilar = ConfigYesNo(default=True)
config.plugins.autotimer.maxdaysinfuture = ConfigNumber(default=0)
config.plugins.autotimer.show_help = ConfigYesNo(default=True)
config.plugins.autotimer.skip_during_records = ConfigYesNo(default=False)
config.plugins.autotimer.skip_during_epgrefresh = ConfigYesNo(default=False)
config.plugins.autotimer.popup_timeout = ConfigNumber(default=5)
config.plugins.autotimer.check_eit_and_remove = ConfigOnOff(default=False)
config.plugins.autotimer.always_write_config = ConfigOnOff(default=False)

config.plugins.autotimer.log_shell = ConfigYesNo(default=False)
config.plugins.autotimer.log_write = ConfigYesNo(default=False)
config.plugins.autotimer.log_file = ConfigText(default="/tmp/autotimer.log", fixed_size=False)

config.plugins.autotimer.series_save_filter = ConfigYesNo(default=False)
config.plugins.autotimer.show_addto_in_filmmenu = ConfigYesNo(default=False)
config.plugins.autotimer.title_match_ratio = ConfigSelectionNumber(80, 100, 1, default=97)
config.plugins.autotimer.shortdesc_match_ratio = ConfigSelectionNumber(80, 100, 1, default=90)
config.plugins.autotimer.extdesc_match_ratio = ConfigSelectionNumber(80, 100, 1, default=90)
config.plugins.autotimer.searchlog_path = ConfigSelection(choices=[
		("?likeATlog?", _("like autotimer.log")),
		("/tmp", _("/tmp")),
		("/etc/enigma2", _("/etc/enigma2"))
	], default="?likeATlog?"
)
config.plugins.autotimer.searchlog_max = ConfigSelectionNumber(5, 20, 1, default=5)

try:
	xrange = xrange
	iteritems = lambda d: d.iteritems()
	itervalues = lambda d: d.itervalues()
except NameError:
	xrange = range
	iteritems = lambda d: d.items()
	itervalues = lambda d: d.values()

__all__ = ['config', 'iteritems', 'itervalues', 'xrange']
