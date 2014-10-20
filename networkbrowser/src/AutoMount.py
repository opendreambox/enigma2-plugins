# -*- coding: utf-8 -*-
# for localized messages
#from __init__ import _
from re import compile as re_compile
from os import path as os_path, symlink, listdir, unlink, readlink, remove

from enigma import eTimer, eEnv
from Components.Console import Console
from Components.Harddisk import harddiskmanager #global harddiskmanager
from Tools.Directories import isMount, removeDir, createDir

from xml.etree.cElementTree import parse as cet_parse

XML_FSTAB = eEnv.resolve("${sysconfdir}/enigma2/automounts.xml")

class AutoMount():
	MOUNT_BASE = '/media/'
	"""Manages Mounts declared in a XML-Document."""
	def __init__(self):
		self.automounts = {}
		self.MountConsole = Console()
		self.removeConsole = Console()
		self.activeMountsCounter = 0
		# Initialize Timer
		self.callback = None
		self.timer = eTimer()
		self.timer_conn = self.timer.timeout.connect(self.mountTimeout)

		self.getAutoMountPoints()

	def getAutoMountPoints(self, callback = None):
		# Initialize mounts to empty list
		automounts = []
		self.automounts = {}
		self.activeMountsCounter = 0

		if not os_path.exists(XML_FSTAB):
			return
		tree = cet_parse(XML_FSTAB).getroot()

		def getValue(definitions, default):
			# Initialize Output
			ret = ""
			# How many definitions are present
			Len = len(definitions)
			return Len > 0 and definitions[Len-1].text or default
		# Config is stored in "mountmanager" element
		# Read out NFS Mounts
		for nfs in tree.findall("nfs"):
			for mount in nfs.findall("mount"):
				data = { 'isMounted': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, \
							'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
				try:
					data['mounttype'] = 'nfs'.encode("UTF-8")
					data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
					if data["active"] == 'True' or data["active"] == True:
						self.activeMountsCounter +=1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
					data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
					data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
					data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
					data['options'] = getValue(mount.findall("options"), "rw,nolock,tcp").encode("UTF-8")
					print "NFSMOUNT",data
					self.automounts[data['sharename']] = data
				except Exception, e:
					print "[MountManager] Error reading Mounts:", e
			# Read out CIFS Mounts
		for nfs in tree.findall("cifs"):
			for mount in nfs.findall("mount"):
				data = { 'isMounted': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, \
							'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
				try:
					data['mounttype'] = 'cifs'.encode("UTF-8")
					data['active'] = getValue(mount.findall("active"), False).encode("UTF-8")
					if data["active"] == 'True' or data["active"] == True:
						self.activeMountsCounter +=1
					data['hdd_replacement'] = getValue(mount.findall("hdd_replacement"), "False").encode("UTF-8")
					data['ip'] = getValue(mount.findall("ip"), "192.168.0.0").encode("UTF-8")
					data['sharedir'] = getValue(mount.findall("sharedir"), "/exports/").encode("UTF-8")
					data['sharename'] = getValue(mount.findall("sharename"), "MEDIA").encode("UTF-8")
					data['options'] = getValue(mount.findall("options"), "rw,nolock").encode("UTF-8")
					data['username'] = getValue(mount.findall("username"), "guest").encode("UTF-8")
					data['password'] = getValue(mount.findall("password"), "").encode("UTF-8")
					print "CIFSMOUNT",data
					self.automounts[data['sharename']] = data
				except Exception, e:
					print "[MountManager] Error reading Mounts:", e

		print "[AutoMount.py] -getAutoMountPoints:self.automounts -->",self.automounts
		if len(self.automounts) == 0:
			print "[AutoMount.py] self.automounts without mounts",self.automounts
			if callback is not None:
				callback(True)
		else:
			for sharename, sharedata in self.automounts.items():
				self.CheckMountPoint(sharedata, callback)

	def sanitizeOptions(self, origOptions, cifs=False):
		options = origOptions.strip()
		if not options:
			options = 'rsize=8192,wsize=8192'
			if not cifs:
				options += ',tcp'
		else:
			if 'rsize' not in options:
				options += ',rsize=8192'
			if 'wsize' not in options:
				options += ',wsize=8192'
			if not cifs and 'tcp' not in options and 'udp' not in options:
				options += ',tcp'
		return options

	def CheckMountPoint(self, data, callback):
		print "[AutoMount.py] CheckMountPoint"
		print "[AutoMount.py] activeMounts:--->",self.activeMountsCounter
		if not self.MountConsole:
			self.MountConsole = Console()

		self.command = None
		if self.activeMountsCounter == 0:
			print "self.automounts without active mounts",self.automounts
			if data['active'] == 'False' or data['active'] is False:
				path = AutoMount.MOUNT_BASE + data['sharename']
				umountcmd = 'umount -fl '+ path
				print "[AutoMount.py] UMOUNT-CMD--->",umountcmd
				self.MountConsole.ePopen(umountcmd, self.CheckMountPointFinished, [data, callback])
		else:
			if data['active'] == 'False' or data['active'] is False:
				path = AutoMount.MOUNT_BASE + data['sharename']
				self.command = 'umount -fl '+ path

			elif data['active'] == 'True' or data['active'] is True:
				path = AutoMount.MOUNT_BASE + data['sharename']
				if os_path.exists(path) is False:
					createDir(path)
				tmpsharedir = data['sharedir'].replace(" ", "\\ ")
				if tmpsharedir[-1:] == "$":
					tmpdir = tmpsharedir.replace("$", "\\$")
					tmpsharedir = tmpdir

				if data['mounttype'] == 'nfs':
					if not os_path.ismount(path):
						tmpcmd = 'mount -t nfs -o '+ self.sanitizeOptions(data['options']) + ' ' + data['ip'] + ':/' + tmpsharedir + ' ' + path
						self.command = tmpcmd.encode("UTF-8")

				elif data['mounttype'] == 'cifs':
					if not os_path.ismount(path):
						tmpusername = data['username'].replace(" ", "\\ ")
						tmpcmd = 'mount -t cifs -o '+ self.sanitizeOptions(data['options'], cifs=True) +',iocharset=utf8,username='+ tmpusername + ',password='+ data['password'] + ' //' + data['ip'] + '/' + tmpsharedir + ' ' + path
						self.command = tmpcmd.encode("UTF-8")

			if self.command is not None:
				print "[AutoMount.py] U/MOUNTCMD--->",self.command
				self.MountConsole.ePopen(self.command, self.CheckMountPointFinished, [data, callback])
			else:
				self.CheckMountPointFinished(None,None, [data, callback])

	def CheckMountPointFinished(self, result, retval, extra_args):
		print "[AutoMount.py] CheckMountPointFinished"
		print "[AutoMount.py] result",result
		print "[AutoMount.py] retval",retval
		(data, callback ) = extra_args
		print "LEN",len(self.MountConsole.appContainers)
		path = AutoMount.MOUNT_BASE + data['sharename']
		print "PATH im CheckMountPointFinished",path
		if os_path.exists(path):
			if os_path.ismount(path):
				if self.automounts.has_key(data['sharename']):
					self.automounts[data['sharename']]['isMounted'] = True
					desc = data['sharename']
					if self.automounts[data['sharename']]['hdd_replacement'] == 'True': #hdd replacement hack
						self.makeHDDlink(path)
					harddiskmanager.addMountedPartition(path, desc)
			else:
				if self.automounts.has_key(data['sharename']):
					self.automounts[data['sharename']]['isMounted'] = False
				if os_path.exists(path):
					if not os_path.ismount(path):
						removeDir(path)
						harddiskmanager.removeMountedPartition(path)

		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(10)

	def makeHDDlink(self, path):
		hdd_dir = '/media/hdd'
		print "[AutoMount.py] symlink %s %s" % (path, hdd_dir)
		if os_path.islink(hdd_dir):
			if readlink(hdd_dir) != path:
				remove(hdd_dir)
				symlink(path, hdd_dir)
		elif isMount(hdd_dir) is False:
			if os_path.isdir(hdd_dir):
				self.rm_rf(hdd_dir)
		try:
			symlink(path, hdd_dir)
		except OSError:
			print "[AutoMount.py] add symlink fails!"
		if os_path.exists(hdd_dir + '/movie') is False:
			createDir(hdd_dir + '/movie')

	def rm_rf(self, d): # only for removing the ipkg stuff from /media/hdd subdirs
		for path in (os_path.join(d,f) for f in listdir(d)):
			if os_path.isdir(path):
				self.rm_rf(path)
			else:
				unlink(path)
		removeDir(d)

	def mountTimeout(self):
		self.timer.stop()
		if self.MountConsole:
			if len(self.MountConsole.appContainers) == 0:
				print "self.automounts after mounting",self.automounts
				if self.callback is not None:
					self.callback(True)

	def getMountsList(self):
		return self.automounts

	def getMountsAttribute(self, mountpoint, attribute):
		if self.automounts.has_key(mountpoint):
			if self.automounts[mountpoint].has_key(attribute):
				return self.automounts[mountpoint][attribute]
		return None

	def setMountsAttribute(self, mountpoint, attribute, value):
		print "setting for mountpoint", mountpoint, "attribute", attribute, " to value", value
		if self.automounts.has_key(mountpoint):
			self.automounts[mountpoint][attribute] = value

	def writeMountsConfig(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<mountmanager>\n']

		for sharename, sharedata in self.automounts.items():
			if sharedata['mounttype'] == 'nfs':
				list.append('<nfs>\n')
				list.append(' <mount>\n')
				list.append(''.join(["  <active>", str(sharedata['active']), "</active>\n"]))
				list.append(''.join(["  <hdd_replacement>", str(sharedata['hdd_replacement']), "</hdd_replacement>\n"]))
				list.append(''.join(["  <ip>", sharedata['ip'], "</ip>\n"]))
				list.append(''.join(["  <sharename>", sharedata['sharename'], "</sharename>\n"]))
				list.append(''.join(["  <sharedir>", sharedata['sharedir'], "</sharedir>\n"]))
				list.append(''.join(["  <options>", sharedata['options'], "</options>\n"]))
				list.append(' </mount>\n')
				list.append('</nfs>\n')

			if sharedata['mounttype'] == 'cifs':
				list.append('<cifs>\n')
				list.append(' <mount>\n')
				list.append(''.join(["  <active>", str(sharedata['active']), "</active>\n"]))
				list.append(''.join(["  <hdd_replacement>", str(sharedata['hdd_replacement']), "</hdd_replacement>\n"]))
				list.append(''.join(["  <ip>", sharedata['ip'], "</ip>\n"]))
				list.append(''.join(["  <sharename>", sharedata['sharename'], "</sharename>\n"]))
				list.append(''.join(["  <sharedir>", sharedata['sharedir'], "</sharedir>\n"]))
				list.append(''.join(["  <options>", sharedata['options'], "</options>\n"]))
				list.append(''.join(["  <username>", sharedata['username'], "</username>\n"]))
				list.append(''.join(["  <password>", sharedata['password'], "</password>\n"]))
				list.append(' </mount>\n')
				list.append('</cifs>\n')

		# Close Mountmanager Tag
		list.append('</mountmanager>\n')

		# Try Saving to Flash
		file = None
		try:
			file = open(XML_FSTAB, "w")
			file.writelines(list)
		except Exception, e:
			print "[AutoMount.py] Error Saving Mounts List:", e
		finally:
			if file is not None:
				file.close()

	def stopMountConsole(self):
		if self.MountConsole is not None:
			self.MountConsole = None

	def removeMount(self, mountpoint, callback = None):
		print "[AutoMount.py] removing mount: ",mountpoint
		self.newautomounts = {}
		for sharename, sharedata in self.automounts.items():
			if sharename is not mountpoint.strip():
				self.newautomounts[sharename] = sharedata
		self.automounts.clear()
		self.automounts = self.newautomounts
		if not self.removeConsole:
			self.removeConsole = Console()
		path = AutoMount.MOUNT_BASE + mountpoint
		umountcmd = 'umount -fl '+ path
		print "[AutoMount.py] UMOUNT-CMD--->",umountcmd
		self.removeConsole.ePopen(umountcmd, self.removeMountPointFinished, [path, callback])

	def removeMountPointFinished(self, result, retval, extra_args):
		print "[AutoMount.py] removeMountPointFinished"
		print "[AutoMount.py] result",result
		print "[AutoMount.py] retval",retval
		(path, callback ) = extra_args
		if os_path.exists(path):
			if not os_path.ismount(path):
				removeDir(path)
				harddiskmanager.removeMountedPartition(path)

		if self.removeConsole:
			if len(self.removeConsole.appContainers) == 0:
				if callback is not None:
					self.callback = callback
					self.timer.startLongTimer(10)

iAutoMount = AutoMount()
