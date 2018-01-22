from Components.config import config, ConfigOnOff, ConfigSelectionNumber, ConfigSubsection

config.plugins.screensaver = ConfigSubsection()
config.plugins.screensaver.enabled = ConfigOnOff(default=True)
config.plugins.screensaver.delay = ConfigSelectionNumber(30, 120, 30, default=30, wraparound=True)
config.plugins.screensaver.photo = ConfigSubsection()
config.plugins.screensaver.photo.speed = ConfigSelectionNumber(1, 6, 1, default=3, wraparound=True)
config.plugins.screensaver.photo.retention = ConfigSelectionNumber(30, 120, 30, default=30, wraparound=True)
