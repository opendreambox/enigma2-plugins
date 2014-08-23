# -*- coding: UTF-8 -*-

from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox

from Components.config import config
from enigma import eEPGCache
from enigma import eTimer
from Tools import Notifications

from . import _

# Error-print
from EPGBackupTools import debugOut, EPGBACKUP_NOTIFICATIONDOMAIN
from traceback import format_exc

# SH-Script
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
import os
SH_EXEC_FILE = resolveFilename(SCOPE_PLUGINS, "Extensions/EPGBackup/EPGBackup.sh")
SH_TMP_OUTPUT="/tmp/.EPGBackup.sh.output"
BOOTCOUNTERFILE="/tmp/.EPGBackup.boot.counter"

FORCERESTORENOFILES="FORCEBACKUP_NOFILES"
FORCERESTORECANCEL="FORCEBACKUP_CANCEL"
EPGBACKUP_SHELL_CONSTANTS = { 'INSTALL': 'install',
		'UNINSTALL': 'uninstall',
		'FORCERESTORE': 'restore',
		'MAKEBACKUP': 'backup',
		'GETLASTFILE': 'getlastfile',
		'SETFORCERESTORE': 'setforcefile',
		'EPGINFO': 'epginfo',
		'EPGINFOSORTSIZE': 'bySize',
		'STRINGBIGGEST': 'biggest',
		'STRINGYOUNGEST': 'youngest',
		'STRINGFORCED': 'force',
}
class EPGBackupSupport:
	"""Class for the Backup-Functionality"""
	epgrefresh_instance = None

	def __init__(self, session):
		# Initialize
		self.session = session
		
		self.backuptimer = eTimer()
		self.backuptimer.callback.append(self.makeBackup)
		
		config.plugins.epgbackup.backup_enabled.addNotifier(self.autoinstall, initial_call = False, immediate_feedback = True)

		config.plugins.epgbackup.backupSaveInterval.addNotifier(self.startStopBackupTimer, initial_call = False, immediate_feedback = True)
		try:
			from Plugins.Extensions.EPGRefresh.EPGRefresh import epgrefresh
			self.epgrefresh_instance = epgrefresh
			config.plugins.epgbackup.callAfterEPGRefresh.addNotifier(self.enableBackupAfterEPGRefresh, initial_call = True, immediate_feedback = True)
		except:
			debugOut("EPGRefresh not installed!", forced=True)
			debugOut("Debug: EPGRefresh-Import-Error:\n" + str(format_exc()))
		
		self.notifyBootCount()

	def notifyBootCount(self):
		try:
			if os.path.exists(BOOTCOUNTERFILE):
				bootCount = ""
				fo=open(BOOTCOUNTERFILE)
				line = fo.readline()
				while (line):
					bootCount = line
					line = fo.readline()
				fo.close
				
				# We have succesfully booted, so delete the counter-File
				os.remove(BOOTCOUNTERFILE)
				
				bootCount= int(bootCount)
				if bootCount > int(config.plugins.epgbackup.max_boot_count.value):
					backupedFile = self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["GETLASTFILE"], "backup", getoutput = True)
					Notifications.AddNotificationWithCallback(self.askDeleteBadBackupCB, MessageBox, \
						text = _("The EPG-Backup was not performed, because there were %d unsuccessfully boot-attempts!\nThe last restored backup-file was \"%s\".\nDo you want to delete the file?") \
						% (bootCount, backupedFile), type = MessageBox.TYPE_YESNO, \
						timeout = 10, domain = EPGBACKUP_NOTIFICATIONDOMAIN)
		except:
			debugOut("checkBootCount-Error:\n" + str(format_exc()), forced=True)
	
	def askDeleteBadBackupCB(self, deleteIt):
		try:
			if deleteIt:
				backupedFile = self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["GETLASTFILE"], "backup", getoutput = True)
				if backupedFile != "":
					debugOut("Deleting file \"%s\"..." % (backupedFile))
					os.system("rm -f %s" % (backupedFile))
		except:
				debugOut("askDeleteBadBackupCB-Error:\n" + str(format_exc()), forced=True)

	def enableBackupAfterEPGRefresh(self, configentry):
		try:
			if self.epgrefresh_instance:
				debugOut("addEPGRefresh-Notifier: " + str(configentry.value))
				if configentry.value:
					self.epgrefresh_instance.addFinishNotifier(self.makeBackup)
				else:
					self.epgrefresh_instance.removeFinishNotifier(self.makeBackup)
		except:
			debugOut("enableBackupAfterEPGRefresh-Error, maybe wrong Versoin of epgrefresh?:\n" + str(format_exc()), forced=True)

	def startStopBackupTimer(self, configentry = None):
		try:
			if configentry == None:
				configentry = config.plugins.epgbackup.backupSaveInterval
			self.timerInterval = int(configentry.value) * 60 # minutes
			if self.timerInterval > 0:
				debugOut("backuptimer-Interval: " + str(self.timerInterval) + " seconds")
				self.backuptimer.startLongTimer(self.timerInterval)
			else:
				debugOut("backuptimer stopped!")
				self.backuptimer.stop()
		except:
			debugOut("startStopBackupTimer-Error:\n" + str(format_exc()), forced=True)

	def makeBackup(self, interactive = False):
		try:
			debugOut("making a backup!")
			eEPGCache.getInstance().Lock()
			eEPGCache.getInstance().save()
			eEPGCache.getInstance().Unlock()
			self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["MAKEBACKUP"])
			self.startStopBackupTimer()
			if interactive or config.plugins.epgbackup.show_messages_background.value:
				backupedFile = self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["GETLASTFILE"], "backup", getoutput = True)
				if backupedFile != "":
					Notifications.AddPopup(
						_("Backup \"%s\" successfully created!") % (backupedFile), \
						MessageBox.TYPE_INFO, 10, domain = EPGBACKUP_NOTIFICATIONDOMAIN)
				else:
					Notifications.AddPopup(
						_("Couldn't create a backup, see logfile for more details!"), \
						MessageBox.TYPE_ERROR, 30, domain = EPGBACKUP_NOTIFICATIONDOMAIN)
		except:
			debugOut("makeBackup-Error:\n" + str(format_exc()), forced=True)
	
	def forceDefaultRestore(self):
		self._defaultRestore(self.__forceRestoreCB, \
			_("Select a file to force a restore"))

	def forceRestore(self):
		self._forceRestore(self.__forceRestoreCB, _("Select a file to force a restore"))
		
	def forceRestoreBySize(self):
		self._forceRestore(self.__forceRestoreCB, _("Select a file to force a restore"), \
			sortMode = EPGBACKUP_SHELL_CONSTANTS["EPGINFOSORTSIZE"])
	
	def setNextBootRestore(self):
		self._defaultRestore(self.__setNextBootRestoreCB, \
			_("Select a file to force a restore on next boot"))

	def _defaultRestore(self, callback, boxTitle):
		if config.plugins.epgbackup.backup_strategy.getValue() in ("biggest_before_youngest", "biggest"):
			self._forceRestore(callback, boxTitle, sortMode = EPGBACKUP_SHELL_CONSTANTS["EPGINFOSORTSIZE"])
		else:
			self._forceRestore(callback, boxTitle)
	
	def _forceRestore(self, callback, boxTitle, sortMode = ""):
		backupList = self._getBackupFiles(sortMode)
		if len(backupList) == 0:
			backupList.append((_("No Backupfiles found"), FORCERESTORENOFILES))
		backupList.insert(0, (_("Cancel"), FORCERESTORECANCEL))
		self.session.openWithCallback(callback,
			ChoiceBox, boxTitle, backupList)
	
	def __forceRestoreCB(self, backupinfo):
		try:
			if backupinfo is None:
				return
			else:
				backupfile = backupinfo [1].rstrip()
				if FORCERESTORECANCEL != backupfile and FORCERESTORENOFILES != backupfile:
					self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["FORCERESTORE"], backupfile)
					restoredFile = self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["GETLASTFILE"], "restore", getoutput = True)
					if restoredFile != "":
						eEPGCache.getInstance().Lock()
						eEPGCache.getInstance().load()
						eEPGCache.getInstance().Unlock()
						self.session.open(MessageBox, \
							_("Backup-file \"%s\" successfully loaded!") % (restoredFile), \
							type = MessageBox.TYPE_INFO)
					else:
						self.session.open(MessageBox, \
							_("Couldn't load backup-file, see logfile for more details!"), \
							type = MessageBox.TYPE_ERROR)
		except:
			debugOut("__forceRestoreCB-Error:\n" + str(format_exc()), forced=True)

	def __setNextBootRestoreCB(self, backupinfo):
		if backupinfo is None:
			return
		else:
			backupfile = backupinfo [1].rstrip()
			if FORCERESTORECANCEL != backupfile and FORCERESTORENOFILES != backupfile:
				self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["SETFORCERESTORE"], backupfile)
				self.session.open(MessageBox, \
					_("Backup-file \"%s\" will be loaded on next boot!") % (backupfile), \
					type = MessageBox.TYPE_INFO)

	def _getBackupFiles(self, sortMode):
		try:
			backupList = []
			backupStrList = self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["EPGINFO"], sortMode, True)
			if backupStrList:
				backupfiles = backupStrList.split("\n")
			if backupfiles:
				for backupfile in backupfiles:
					if backupfile:
						backupfile = backupfile.replace(EPGBACKUP_SHELL_CONSTANTS["STRINGBIGGEST"], _("FILELIST_BIGGEST"))
						backupfile = backupfile.replace(EPGBACKUP_SHELL_CONSTANTS["STRINGYOUNGEST"], _("FILELIST_YOUNGEST"))
						backupfile = backupfile.replace(EPGBACKUP_SHELL_CONSTANTS["STRINGFORCED"], _("FILELIST_FORCED"))
						backupList.append(( backupfile, backupfile.split(" ")[0] ))
		except:
			debugOut("getBackupFiles-Error:\n" + str(format_exc()), forced=True)
		return backupList
	
	def autoinstall(self, configentry):
		if configentry.value:
			self.install()
		else:
			self.uninstall()
	
	def install(self):
		self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["INSTALL"], \
			config.plugins.epgbackup.showin_usr_scripts.value)
	
	def uninstall(self):
		self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["UNINSTALL"])

	def executeShScript(self, sh_action, param1 = "", getoutput = False):
		outtext = ""
		if getoutput:
			os.system(SH_EXEC_FILE + " %s %s > %s" %(sh_action, param1, str(SH_TMP_OUTPUT)))
			fo=open(str(SH_TMP_OUTPUT))
			line = fo.readline()
			while (line):
				outtext += line
				line = fo.readline()
			fo.close
		else:
			debugOut("EPGBackup.sh execute wiht params %s %s" %(sh_action, param1))
			os.system(SH_EXEC_FILE + " %s %s" %(sh_action, param1))
		return outtext



