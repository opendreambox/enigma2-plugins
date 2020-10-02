from Tools.Log import Log
from Tools.Directories import fileExists

from os import remove

class CecBoot(object):
	UBOOT_SCRIPT_FILE = "/etc/u-boot.scr.d/001_cec.scr"
	UBOOT_SCRIPT = """dm_cec init
dm_cec active_source {logical} {physical}
dm_cec image_view_on {logical}
"""
	@staticmethod
	def install(logical, physical):
		Log.w("physical address: %s | logical address: %s" %(physical, logical))
		try:
			with open(CecBoot.UBOOT_SCRIPT_FILE, "w") as f:
				Log.w(CecBoot.UBOOT_SCRIPT.format(logical=logical, physical=physical))
				f.write(CecBoot.UBOOT_SCRIPT.format(logical=logical, physical=physical))
		except:
			Log.w("Could not write bootloader script!")

	@staticmethod
	def uninstall():
		if fileExists(CecBoot.UBOOT_SCRIPT_FILE):
			try:
				remove(CecBoot.UBOOT_SCRIPT_FILE)
			except:
				Log.w("Could not delete CeC u-boot script")
