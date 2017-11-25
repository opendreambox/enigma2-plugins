#
#  fstabeditor
#
#  $Id$
#
#  Coded by dre (c) 2010 - 2017
#  Coding idea and design by dre
#  dirselect by DarkVolli
#  design by Vali
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Property GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from Components.config import config, ConfigText, ConfigNumber, ConfigSelection, NoSave, getConfigListEntry
from Components.ActionMap import *
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists
from dirSelect import dirSelectDlg
from enigma import RT_HALIGN_LEFT, RT_HALIGN_RIGHT, eListboxPythonMultiContent, gFont
import os
from skin import TemplatedListFonts, componentSizes

#global vars
entryList = []
lengthList = [0,0,0,0]

def main(session,**kwargs):
    session.open(fstabViewerScreen)
	
class fstabMenuList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.BIG), tlf.size(tlf.BIG)))
		self.l.setFont(1, gFont(tlf.face(tlf.SMALL), tlf.size(tlf.SMALL)))
		
def fstabMenuListEntry(devicename, mountpoint,fstype, options, dumpfreq, passnum):
	res = [ (devicename, mountpoint,fstype, options, dumpfreq, passnum) ]
	res.append(MultiContentEntryText(pos=(270,15),size=(800,30), font=0, text=devicename))
	res.append(MultiContentEntryText(pos=(270,60),size=(800,30), font=0, text=mountpoint))
	res.append(MultiContentEntryText(pos=(270,90),size=(800,30), font=0, text=fstype))
	res.append(MultiContentEntryText(pos=(270,120),size=(800,30), font=0, text=options))
	res.append(MultiContentEntryText(pos=(270,150),size=(800,30), font=0, text=dumpfreq))
	res.append(MultiContentEntryText(pos=(270,180),size=(800,30), font=0, text=passnum))
	res.append(MultiContentEntryText(pos=(0,17),size=(250,30), font=1, flags=RT_HALIGN_RIGHT, text="Device name:"))
	res.append(MultiContentEntryText(pos=(0,62),size=(250,30), font=1, flags=RT_HALIGN_RIGHT, text="Mount point:"))
	res.append(MultiContentEntryText(pos=(0,92),size=(250,30), font=1, flags=RT_HALIGN_RIGHT, text="File system type:"))
	res.append(MultiContentEntryText(pos=(0,122),size=(250,30), font=1, flags=RT_HALIGN_RIGHT, text="Options:"))
	res.append(MultiContentEntryText(pos=(0,152),size=(250,30), font=1, flags=RT_HALIGN_RIGHT, text="Dump frequency:"))
	res.append(MultiContentEntryText(pos=(0,182),size=(250,30), font=1, flags=RT_HALIGN_RIGHT, text="Pass number:"))
	return res
	
	
class fstabViewerScreen(Screen,HelpableScreen):
	skin = """
		<screen position="center,center" size="820,340" title="fstab-Editor">
		<widget name="ButtonRed" pixmap="skin_default/buttons/red.png" position="10,0" size="200,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,0" size="200,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,0" size="200,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,0" size="200,50" alphatest="on" />
		<widget name="ButtonRedText" position="10,0" size="200,50" zPosition="1" valign="center" halign="center" backgroundColor="#9f1313" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel text="Add entry" position="210,0" size="200,50" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel text="Run mount -a" position="410,0" size="200,50" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel text="Restore fstab.backup" position="610,0" size="200,50" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<eLabel position="10,55" size="800,1" backgroundColor="grey" />
		<widget name="menulist" itemHeight="220" position="10,67" size="800,220" enableWrapAround="1" scrollbarMode="showNever" />
		<eLabel position="10,300" size="800,1" backgroundColor="grey" />
		<widget name="entryinfo" position="10,310" size="800,25" font="Regular;22" halign="center" />
		</screen>"""
		
	def __init__(self, session, args = 0):
		self.skin = fstabViewerScreen.skin
		self.session = session
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.hideDelete = False
		
		self["ButtonRed"] = Pixmap()
		self["ButtonRedText"] = Label(_("Remove entry"))

		self["entryinfo"] = Label()
		self["menulist"] = fstabMenuList([])
		self.fstabEntryList = []

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.removeEntry, _("Remove entry")),
			"green": (self.addEntry, _("Add entry")),
			"yellow": (self.restoreBackUp, _("Restore back up of fstab")),
			"blue":	(self.mountall, _("Run mount -a")),
		}, -1)
		
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel":	(self.close, _("Close plugin")),
			"ok":		(self.openEditScreen, _("Open editor")),
		}, -1)

		self.buildScreen()
		
		self["menulist"].onSelectionChanged.append(self.selectionChanged)

	def openEditScreen(self):
		self.selectedEntry = self["menulist"].getSelectedIndex()
		self.session.openWithCallback(self.writeFile, fstabEditorScreen, self.selectedEntry, self.hideDelete)
	
	def buildScreen(self):
		self.fstabEntryList = []
		if fileExists("/etc/fstab"):
			fstabFile = open("/etc/fstab" ,"r")
			global entryList
			entryList = []
			self.counter = 0
			for line in fstabFile:
				if line[0] != "\n" and line[0] != "#":
					entry = line.split()
					entryList.append(entry)
					global lenghtList
					if len(entry[0]) > lengthList[0]:
						lengthList[0] = len(entry[0])
					if len(entry[1]) > lengthList[1]:
						lengthList[1] = len(entry[1])
					if len(entry[2]) > lengthList[2]:
						lengthList[2] = len(entry[2])					
					if len(entry[3]) > lengthList[3]:
						lengthList[3] = len(entry[3])
					self.fstabEntryList.append(fstabMenuListEntry(entry[0],entry[1],entry[2],entry[3],entry[4],entry[5]))
					self.counter = self.counter+1
			fstabFile.close()
			
		self["menulist"].l.setList(self.fstabEntryList)
		self["entryinfo"].setText("%d / %d" %(self["menulist"].getSelectedIndex()+1, self.counter))
		if entryList[0][0] in ("rootfs", "proc", "sysfs", "devpts", "tmpfs"):
			self["ButtonRed"].hide()
			self["ButtonRedText"].hide()
			self.hideDelete = True		
	
	def writeFile(self, returnvalue):
		if returnvalue != 0:
			os.system("cp /etc/fstab /etc/fstab.backup")
			configFile = open('/etc/fstab', 'w')
			for i in range(len(entryList)):
				line = "%*s %*s %*s %*s %s %s\n" %(int(lengthList[0])*-1, entryList[i][0], int(lengthList[1])*-1, entryList[i][1], int(lengthList[2])*-1, entryList[i][2], int(lengthList[3])*-1, entryList[i][3],str(entryList[i][4]), str(entryList[i][5]))
				configFile.write(line)
			configFile.close()
			self.buildScreen()
			
	def selectionChanged(self):
		self["entryinfo"].setText("%d / %d" %(self["menulist"].getSelectedIndex()+1, self.counter))
		if entryList[self["menulist"].getSelectedIndex()][0] in ("rootfs", "proc", "sysfs", "devpts", "tmpfs"):
			self["ButtonRed"].hide()
			self["ButtonRedText"].hide()
			self.hideDelete = True
		else:
			self["ButtonRed"].show()
			self["ButtonRedText"].show()			
			self.hideDelete = False
		
	def mountall(self):
		os.system("mount -a")

	def removeEntry(self):
		global entryList
		if entryList[self["menulist"].getSelectedIndex()][0] in ("rootfs", "proc", "sysfs", "devpts", "tmpfs"):
			msg = self.session.open(MessageBox, _("Entry is required for Dreambox to work. Delete is not allowed"), MessageBox.TYPE_ERROR, timeout=5)
		else:
			del entryList[self["menulist"].getSelectedIndex()]
			self.writeFile(1)
			
	def addEntry(self):
		self.session.openWithCallback(self.writeFile, fstabEditorScreen, None, addEntry=True)
		
	def restoreBackUp(self):
		os.system("rm -f /etc/fstab")
		os.system("cp /etc/fstab.backup /etc/fstab")
		self.buildScreen()
		
class fstabEditorScreen(Screen,ConfigListScreen,HelpableScreen):
	skin = """
		<screen position="center,center" size="820,640" title="fstab-Editor" >
		<widget name="ButtonRed" pixmap="skin_default/buttons/red.png" position="10,0" size="200,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,0" size="200,50" alphatest="on" />
		<widget name="ButtonYellow" pixmap="skin_default/buttons/yellow.png" position="410,0" size="200,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,0" size="200,50" alphatest="on" />
		<widget name="ButtonRedText" position="10,0" size="200,50" zPosition="1" valign="center" halign="center" backgroundColor="#9f1313" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<eLabel text="Save" position="210,0" size="200,50" zPosition="1" valign="center" halign="center" backgroundColor="#1f771f" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="ButtonYellowText" position="410,0" size="200,50" zPosition="1" valign="center" halign="center" backgroundColor="#18188b" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="ButtonBlueText" position="610,0" size="200,50" zPosition="1" valign="center" halign="center" backgroundColor="#18188b" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<eLabel position="10,55" size="800,1" backgroundColor="grey" />
		<widget name="config" position="10,60" size="800,570" enableWrapAround="1" scrollbarMode="showOnDemand" />
		</screen>"""
		
	def __init__(self, session, selectedEntry, addEntry=False, hideDelete=False):
		self.skin = fstabEditorScreen.skin
		self.session = session
		self.selectedEntry = selectedEntry
		self.addEntry = addEntry
		self.hideDelete = hideDelete
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self["ButtonRed"] = Pixmap()
		self["ButtonRedText"] = Label(_("Remove entry"))

		if self.hideDelete:
			self["ButtonRed"].hide()
			self["ButtonRedText"].hide()

		self["ButtonBlue"] = Pixmap()
		self["ButtonBlueText"] = Label(_("Add option"))
		self["ButtonYellow"] = Pixmap()
		self["ButtonYellowText"] = Label(_("Remove option"))
		
		if self.addEntry:
			self["ButtonRed"].hide()
			self["ButtonRedText"].hide()
			
		self["ButtonYellow"].hide()
		self["ButtonYellowText"].hide()
		
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"red": (self.removeEntry, _("Remove entry")),
			"green":	(self.checkEntry, _("Return with saving")),
			"blue":		(self.addOption, _("Add option")),
			"yellow":	(self.removeOption, _("Remove option")),
		}, -1)
		
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel":	(self.cancelEntry, _("Return without saving")),
			"ok":		(self.ok, _("Open selector")),
		}, -1)	
		
		self.list = []
		ConfigListScreen.__init__(self, self.list)
		
		self.createConfig()
		
		self["config"].onSelectionChanged.append(self.selectionChanged)
		
	def selectionChanged(self):
		self.selectedOptionEntry = self["config"].getCurrentIndex()
		if self.selectedOptionEntry > 3 and self.selectedOptionEntry < len(self.list)-2:
			self["ButtonYellow"].show()
			self["ButtonYellowText"].show()
		else:
			self["ButtonYellow"].hide()
			self["ButtonYellowText"].hide()

	def createConfig(self):
		self.list = []
		self.optionList = []
				
		if 	self.addEntry:
			self.devicename = NoSave(ConfigText(default = ""))
			self.mountpoint = NoSave(ConfigText(default = ""))
			self.fstype = NoSave(ConfigSelection([("auto","auto"),("ext2","ext2"),("ext3","ext3"),("ext4","ext4"),("swap","swap"),("tmpfs","tmpfs"),("proc","proc"),("cifs","cifs"),("nfs","nfs"),("jffs2","jffs2"),("usbfs","usbfs"),("devpts","devpts"),("vfat","vfat"),("fat","fat"),("ntfs","ntfs"),("noauto", "no auto"), ("xfs", "xfs")], default = "auto"))
			self.optionList.append(NoSave(ConfigText(default = "defaults")))
			
			self.dumpfreq = NoSave(ConfigNumber(default = 0))
			self.passnum = NoSave(ConfigSelection([("0","0"),("1","1"),("2","2")], default = "0"))			
		else:
			self.devicename = NoSave(ConfigText(default = entryList[self.selectedEntry][0]))
			self.mountpoint = NoSave(ConfigText(default = entryList[self.selectedEntry][1]))
			self.fstype = NoSave(ConfigSelection([("auto","auto"),("ext2","ext2"),("ext3","ext3"),("ext4","ext4"),("swap","swap"),("tmpfs","tmpfs"),("proc","proc"),("cifs","cifs"),("nfs","nfs"),("jffs2","jffs2"),("usbfs","usbfs"),("devpts","devpts"),("vfat","vfat"),("fat","fat"),("ntfs","ntfs"),("noauto", "no auto"), ("xfs", "xfs"), ("rootfs","rootfs"),("sysfs","sysfs")], default = entryList[self.selectedEntry][2]))
			splitoptions = entryList[self.selectedEntry][3].split(",")
			for option in splitoptions:
				self.optionList.append(NoSave(ConfigText(default=option)))
			self.dumpfreq = NoSave(ConfigNumber(default = int(entryList[self.selectedEntry][4])))
			self.passnum = NoSave(ConfigSelection([("0","0"),("1","1"),("2","2")], default = entryList[self.selectedEntry][5]))
		
		self.list.append(getConfigListEntry(_("device name: "), self.devicename))
		self.list.append(getConfigListEntry(_("mount point: "), self.mountpoint))
		self.list.append(getConfigListEntry(_("file system type: "), self.fstype))
		self.list.append((_("options: "),))
		i = 1
		for entry in self.optionList:
			self.list.append(getConfigListEntry(_("option %d: ") %(i), entry))
			i += 1
		self.list.append(getConfigListEntry(_("dump frequency (in days): "), self.dumpfreq))
		self.list.append(getConfigListEntry(_("pass num: "), self.passnum))

		self["config"].setList(self.list)
	
	def checkEntry(self):
		if self.devicename.value == "" or self.mountpoint.value == "":
			error = self.session.open(MessageBox, _("Please enter a value for every input field"), MessageBox.TYPE_ERROR, timeout=10)
		else:
			self.saveEntry()
	
	def saveEntry(self):
		global entryList, lengthList
		
		optionsString = ""
		for entry in self.optionList:
			if entry.value == "":
				continue
			if optionsString == "":
				optionsString = entry.value
			else:
				optionsString += ",%s" %(entry.value)

		# keep the print for debug purpose in case problems occur				
		print "optionsString", optionsString
		
		#check if new entry is longer than the currently longest
		if len(self.devicename.value) > lengthList[0]:
			lengthList[0] = len(self.devicename.value)
		if len(self.mountpoint.value) > lengthList[1]:
			lengthList[1] = len(self.mountpoint.value)
		if len(self.fstype.value) > lengthList[2]:
			lengthList[2] = len(self.fstype.value)
		if len(optionsString) > lengthList[3]:
			lengthList[3] = len(optionsString)
		if self.addEntry:
			entryList.append([self.devicename.value, self.mountpoint.value, self.fstype.value, optionsString, str(self.dumpfreq.value), self.passnum.value])
		else:
			entryList[self.selectedEntry] = [self.devicename.value, self.mountpoint.value, self.fstype.value, optionsString, str(self.dumpfreq.value), self.passnum.value]
		self.close(1)
		
	def cancelEntry(self):
		self.close(0)
	
	def ok(self):
		self.selectedOptionEntry = self["config"].getCurrentIndex()
		if self.selectedOptionEntry == 1:
			self.session.openWithCallback(self.dirSelectDlgClosed, dirSelectDlg, "/media/dummy/", False)  # just add any (not even existing) subdir to start in /media
		elif self.selectedOptionEntry == 0:
			self.session.openWithCallback(self.dirSelectDlgClosed, dirSelectDlg, "/dev/disk/dummy/", True) # just add any (not even existing) subdir to start in /dev
		elif self.selectedOptionEntry > 3 and self.selectedOptionEntry < len(self.list)-2:
			self.session.openWithCallback(self.updateSelectedOption, optionSelector, self.list[self.selectedOptionEntry][1].value)
			
	def updateSelectedOption(self, returnValue=""):
		print returnValue
		self.list[self.selectedOptionEntry][1].value=returnValue
		self.optionList[self.selectedOptionEntry-4].value = returnValue
	
	def dirSelectDlgClosed(self, mountpoint):
		#use print to see in crashlog what's been selected
		print "mountpoint: ", mountpoint
		if mountpoint != False:
			if self.selectedOptionEntry == 1:
				self.mountpoint.value = mountpoint
			elif self.selectedOptionEntry == 0:
				self.devicename.value = mountpoint

	def removeEntry(self):
		if not self.hideDelete:
			global entryList
			if entryList[self.selectedEntry][0] in ("rootfs", "proc", "sysfs", "devpts", "tmpfs"):
				msg = self.session.open(MessageBox, _("Entry is required for Dreambox to work. Delete is not allowed"), MessageBox.TYPE_ERROR, timeout=5)
				returnvalue = 0
			else:		
				del entryList[self.selectedEntry]
				returnvalue = 1
			self.close(returnvalue)
				
	def addOption(self):
		self.optionList.append(NoSave(ConfigText(default="")))
		self.list.insert(len(self.list)-2, getConfigListEntry(_("new option: "), NoSave(ConfigText(default=""))))
		self["config"].setList(self.list)
		
	def removeOption(self):
		self.selectedOptionEntry = self["config"].getCurrentIndex()
		if len(self.optionList) > 1:
			if self.selectedOptionEntry > 3 and self.selectedOptionEntry < len(self.list)-2:
				del self.list[self.selectedOptionEntry]
				del self.optionList[self.selectedOptionEntry-4]
			else:
				self.session.open(MessageBox, _("Cannot remove option. At least one option is required. Option will be set to defaults"), MessageBox.TYPE_ERROR, timeout=5)
				self.list[self.selectedOptionEntry][1].value = "defaults"
				self.optionList[0].value = "defaults"
			self["config"].setList(self.list)

class optionSelector(Screen,ConfigListScreen,HelpableScreen):
	skin = """
		<screen position="center,center" size="820,280" title="Option Selector" >
		<ePixmap name ="ButtonRed" pixmap="skin_default/buttons/red.png" position="10,0" size="200,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,0" size="200,50" alphatest="on" />
		<eLabel text="Remove entry" position="10,0" size="200,50" zPosition="1" valign="center" halign="center" backgroundColor="#9f1313" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<eLabel text="Save" position="210,0" size="200,50" zPosition="1" valign="center" halign="center" backgroundColor="#1f771f" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<eLabel position="10,55" size="800,1" backgroundColor="grey" />
		<widget name="config" position="10,60" size="800,100" enableWrapAround="1" scrollbarMode="showOnDemand" />
		<widget name="description" position="10,170" size="800,100" zPosition="1" valign="top" halign="left" backgroundColor="#1f771f" font="Regular;18" transparent="1" foregroundColor="white" />
		</screen>"""
	def __init__(self, session, currentValue=""):
		self.skin = optionSelector.skin
		self.session = session
		self.currentOption = ""
		self.currentValue = ""
		currentValueSplit = currentValue.split("=")
		self.currentOption = currentValueSplit[0]
		if len(currentValueSplit) > 1:
			self.currentValue = currentValueSplit[1]
		print currentValueSplit
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		self["description"] = Label()

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"green":	(self.saveOption, _("Return with saving")),
			"red":		(self.removeOption, _("Remove entry")),
		}, -1)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
		{
			"cancel":	(self.closeScreen, _("Return without saving")),
		}, -1)	

		# this list contains all options that required a value
		self.needsValueList = ["retrans","wsize","rsize","x-systemd.idle-timeout","retry","timeo","x-systemd.device-timeout","mode","nfsvers","vers"]
		
		# this list contains many but not all possible options
		choices = ["defaults","atime","noatime","sync","async","user","nouser","users","auto","dev","exec","suid","rw","ro","relatime","nosuid","nodev","noexec","udp","tcp","x-systemd.automount","retrans","noauto","wsize","rsize","x-systemd.idle-timeout","retry","lock","nolock","timeo","x-systemd.device-timeout","soft","hard","nofail","mode","nfsvers","vers"]
		
		# this dictionary contains descriptions for options
		self.descriptionDict = {
		"async":_("All I/O to the filesystem should be done asynchronously."),
		"atime":_("Do not use the noatime feature, so the inode access time is controlled by kernel defaults."),
		"noatime":_("Do not update inode access times on this filesystem (e.g. for faster access on the news spool to speed up news servers). This works for all inode types (directories too), so it implies nodiratime."),
		"auto":_("Can be mounted with the -a option."),
		"noauto":_("Can only be mounted explicitly (i.e., the -a option will not cause the filesystem to be mounted)."),
		"defaults":_("Use the default options: rw, suid, dev, exec, auto, nouser, and async. Note that the real set of all default mount options depends on kernel and filesystem type."),
		"dev":_("Interpret character or block special devices on the filesystem."),
		"nodev":_("Do not interpret character or block special devices on the file system."),
		"diratime":_("Update directory inode access times on this filesystem. This is the default. (This option is ignored when noatime is set.)"),
		"nodiratime":_("Do not update directory inode access times on this filesystem. (This option is implied when noatime is set.)"),
		"dirsync":_("All directory updates within the filesystem should be done synchronously. This affects the following system calls: creat, link, unlink, symlink, mkdir, rmdir, mknod and rename."),
		"exec":_("Permit execution of binaries."),
		"noexec":_("Do not permit direct execution of any binaries on the mounted filesystem."),
		"group":_("Allow an ordinary user to mount the filesystem if one of that user's groups matches the group of the device. This option implies the options nosuid and nodev (unless overridden by subsequent options, as in the option line group,dev,suid)."),
		"iversion":_("Every time the inode is modified, the i_version field will be incremented."),
		"noiversion":_("Do not increment the i_version inode field."),
		"mand":_("Allow mandatory locks on this filesystem."),
		"nomand":_("Do not allow mandatory locks on this filesystem."),
		"nofail":_("Do not report errors for this device if it does not exist."),
		"relatime":_("Update inode access times relative to modify or change time. Access time is only updated if the previous access time was earlier than the current modify or change time. (Similar to noatime, but it doesn't break mutt or other applications that need to know if a file has been read since the last time it was modified.)"),
		"norelatime":_("Do not use the relatime feature."),
		"strictatime":_("Allows to explicitly request full atime updates. This makes it possible for the kernel to default to relatime or noatime but still allow userspace to override it."),
		"nostrictatime":_("Use the kernel's default behavior for inode access time updates."),
		"lazytime":_("Only update times (atime, mtime, ctime) on the in-memory version of the file inode."),
		"nolazytime":_("Do not use the lazytime feature."),
		"suid":_("Allow set-user-ID or set-group-ID bits to take effect."),
		"nosuid":_("Do not allow set-user-ID or set-group-ID bits to take effect."),
		"silent":_("Turn on the silent flag."),
		"loud":_("Turn off the silent flag."),
		"owner":_("Allow an ordinary user to mount the filesystem if that user is the owner of the device. This option implies the options nosuid and nodev (unless overridden by subsequent options, as in the option line owner,dev,suid)."),
		"ro":_("Mount the filesystem read-only."),
		"rw":_("Mount the filesystem read-write."),
		"sync":_("All I/O to the filesystem should be done synchronously. In the case of media with a limited number of write cycles (e.g. some flash drives), sync may cause life-cycle shortening."),
		"user":_("Allow an ordinary user to mount the filesystem. The name of the mounting user is written to the mtab file (or to the private libmount file in /run/mount on systems without a regular mtab) so that this same user can unmount the filesystem again. This option implies the options noexec, nosuid, and nodev (unless overridden by subsequent options, as in the option line user,exec,dev,suid)."),
		"nouser":_("Forbid an ordinary user to mount the filesystem. This is the default; it does not imply any other options."),
		"users":_("Allow any user to mount and to unmount the filesystem, even when some other ordinary user mounted it. This option implies the options noexec, nosuid, and nodev (unless overridden by subsequent options, as in the option line users,exec,dev,suid)."),
		"mode":_("Set the mode of all files to value & 0777 disregarding the original permissions. Add search permission to directories that have read permission. The value is given in octal."),
		"soft":_("Determines the recovery behavior of the NFS client after an NFS request times out. If neither option is specified (or if the hard option is specified), NFS requests are retried indefinitely. If the soft option is specified, then the NFS client fails an NFS request after retrans retransmissions have been sent, causing the NFS client to return an error to the calling application."),
		"hard":_("Determines the recovery behavior of the NFS client after an NFS request times out. If neither option is specified (or if the hard option is specified), NFS requests are retried indefinitely. If the soft option is specified, then the NFS client fails an NFS request after retrans retransmissions have been sent, causing the NFS client to return an error to the calling application."),
		"timeo":_("The time in deciseconds (tenths of a second) the NFS client waits for a response before it retries an NFS request."),
		"retrans":_("The number of times the NFS client retries a request before it attempts further recovery action. If the retrans option is not specified, the NFS client tries each request three times."),
		"rsize":_("The maximum number of bytes in each network READ request that the NFS client can receive when reading data from a file on an NFS server. The actual data payload size of each NFS READ request is equal to or smaller than the rsize setting. The largest read payload supported by the Linux NFS client is 1,048,576 bytes (one megabyte)."),
		"wsize":_("The maximum number of bytes per network WRITE request that the NFS client can send when writing data to a file on an NFS server. The actual data payload size of each NFS WRITE request is equal to or smaller than the wsize setting. The largest write payload supported by the Linux NFS client is 1,048,576 bytes (one megabyte)."),
		"retry":_("The number of minutes that the mount(8) command retries an NFS mount operation in the foreground or background before giving up. If this option is not specified, the default value for foreground mounts is 2 minutes, and the default value for background mounts is 10000 minutes (80 minutes shy of one week). If a value of zero is specified, the mount(8) command exits immediately after the first failure."),
		"udp":_("The udp option is an alternative to specifying proto=udp. It is included for compatibility with other operating systems."),
		"tcp":_("The tcp option is an alternative to specifying proto=tcp. It is included for compatibility with other operating systems."),
		"nfsvers":_("The NFS protocol version number used to contact the server's NFS service. If the server does not support the requested version, the mount request fails. If this option is not specified, the client negotiates a suitable version with the server, trying version 4 first, version 3 second, and version 2 last."),
		"vers":_("This option is an alternative to the nfsvers option. It is included for compatibility with other operating systems."),
		"lock":_("Selects whether to use the NLM sideband protocol to lock files on the server. If neither option is specified (or if lock is specified), NLM locking is used for this mount point. When using the nolock option, applications can lock files, but such locks provide exclusion only against other applications running on the same client. Remote applications are not affected by these locks."),
		"nolock":_("Selects whether to use the NLM sideband protocol to lock files on the server. If neither option is specified (or if lock is specified), NLM locking is used for this mount point. When using the nolock option, applications can lock files, but such locks provide exclusion only against other applications running on the same client. Remote applications are not affected by these locks."),
		"x-systemd.automount":_("An automount unit will be created for the file system."),
		"x-systemd.idle-timeout":_("Configures the idle timeout of the automount unit."),
		"x-systemd.device-timeout":_("Configure how long systemd should wait for a device to show up before giving up on an entry from /etc/fstab. Specify a time in seconds."),
		
		}
		
		self.list = []
		if self.currentOption != "":
			self.options = NoSave(ConfigSelection(choices, default=self.currentOption))
		else:
			self.options = NoSave(ConfigSelection(choices))
		self.list.append(getConfigListEntry(_("option: "), self.options))
		
		if self.currentValue != "":
			self.optionValue = NoSave(ConfigText(default=self.currentValue))
			self.list.append(getConfigListEntry(_("value: "), self.optionValue))
		
		ConfigListScreen.__init__(self, self.list)
		
	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self._onKeyEvent()
	
	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self._onKeyEvent()
	
	def _onKeyEvent(self):
		if self.options.value in self.needsValueList:
			if len(self.list) == 1:
				self.optionValue = NoSave(ConfigText(default=""))
				self.list.append(getConfigListEntry(_("value: "), self.optionValue))
		elif len(self.list) == 2:
			self.optionValue.value=""
			del self.list[1]
		self["description"].setText(self.descriptionDict.get(self.options.value, ""))
		self["config"].setList(self.list)
	
	def saveOption(self):
		if self.options.value in self.needsValueList:
			if self.optionValue.value != "":
				self.close("%s=%s" %(self.options.value, self.optionValue.value))
			else:
				self.session.open(MessageBox, _("A value is required for the selected option"), MessageBox.TYPE_ERROR, timeout=5)
		else:
			self.close(self.options.value)
		
	def removeOption(self):
		self.close()
	
	def closeScreen(self):
		if self.options.value in self.needsValueList:
			self.close("%s=%s" %(self.options.value, self.optionValue.value))
		else:
			self.close(self.options.value)
		
def Plugins(**kwargs):
	return [PluginDescriptor(name="fstab-Editor", description=_("Plugin to edit fstab"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon="fstabEditor.png", fnc=main)]
