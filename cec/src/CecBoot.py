from enigma import eEnv

from Tools.Log import Log
from Tools.Directories import fileExists, pathExists

from os import remove
import subprocess

class CecBoot(object):
	UBOOT_SCRIPT_DIR = eEnv.resolve("${sysconfdir}/u-boot.scr.d")
	UBOOT_SCRIPT_FILE = "{0}/001_cec.scr".format(UBOOT_SCRIPT_DIR)
	UBOOT_SCRIPT = "setenv cec_on_cmd={command}; setenv cec_on_flags={reason};"
	CEC_COMMAND = "dm_cec init; dm_cec active_source {logical} {physical}; dm_cec image_view_on {logical}"
	# available bootloader reasons are: Button IR Reset RTC WOL and BTLE
	CEC_REASON = "Button IR RESET BTLE n/a"
	UPDATE_AUTOEXEC = "/usr/sbin/update-autoexec"

	@staticmethod
	def check():
		return pathExists(CecBoot.UBOOT_SCRIPT_DIR)

	@staticmethod
	def install(logical, physical):
		if not CecBoot.check():
			Log.w("No bootloader scriptdir found! Not installing cec boot script!")
			return
		Log.i("physical address: %s | logical address: %s" %(physical, logical))
		try:
			command = CecBoot.CEC_COMMAND.format(logical=logical, physical=physical)
			script = CecBoot.UBOOT_SCRIPT.format(command=command, reason=CecBoot.CEC_REASON)
			if fileExists(CecBoot.UBOOT_SCRIPT_FILE):
				with open(CecBoot.UBOOT_SCRIPT_FILE, "r") as f:
					oldScript = f.readlines()
					if oldScript and oldScript[0] == script:
						Log.i("Identical cec-script already in place! skipping installation!")
						return

			with open(CecBoot.UBOOT_SCRIPT_FILE, "w") as f:
				f.write(script)
				Log.i(script)
			CecBoot.updateAutoexec()
		except:
			Log.w("Could not write bootloader script!")

	@staticmethod
	def uninstall():
		if not CecBoot.check():
			Log.w("No bootloader scriptdir found! Not installing cec boot script!")
			return
		if fileExists(CecBoot.UBOOT_SCRIPT_FILE):
			Log.i("Removing cec boot script!")
			try:
				remove(CecBoot.UBOOT_SCRIPT_FILE)
				CecBoot.updateAutoexec()
			except:
				Log.w("Could not delete CeC u-boot script")

	@staticmethod
	def updateAutoexec():
		Log.i()
		if fileExists(CecBoot.UPDATE_AUTOEXEC):
			ret = subprocess.call(CecBoot.UPDATE_AUTOEXEC)
			if ret != 0:
				Log.w("update-autoexec failed!")
