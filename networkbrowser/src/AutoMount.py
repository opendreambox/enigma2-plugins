# -*- coding: utf-8 -*-
from re import compile as re_compile
from os import path as os_path, symlink, listdir, unlink, readlink, remove
from copy import deepcopy

from enigma import eTimer, eEnv
from Components.Console import Console
from Components.Harddisk import harddiskmanager, Util
from Tools.Directories import isMount, removeDir, createDir, pathExists
from Tools.Log import Log

from xml.etree.cElementTree import parse as cet_parse

XML_FSTAB = eEnv.resolve("${sysconfdir}/enigma2/automounts.xml")

class AutoMount():
	MOUNT_BASE = '/media/'
	DEFAULT_OPTIONS_NFS = { 'isMounted': False, 'active': False, 'ip': '192.168.0.1', 'sharename': 'Sharename', 'sharedir': "/export/hdd", 'username': "", \
							'password': "", 'mounttype' : 'nfs', 'options' : "rw,nolock,udp", 'hdd_replacement' : False }
	DEFAULT_OPTIONS_CIFS = { 'isMounted': False, 'active': False, 'ip': '192.168.0.1', 'sharename': 'Sharename', 'sharedir': "/export/hdd", 'username': "", \
							'password': "", 'mounttype' : 'cifs', 'options' : "rw", 'hdd_replacement' : False }

	"""Manages Mounts declared in a XML-Document."""
	def __init__(self):
		self._mounts = {}
		self._console = Console()
		self._numActive = 0
		self.reload()

	def _getAutoMounts(self):
		return self._mounts

	def _setAutoMounts(self, automounts):
		self._mounts = automounts

	mounts = property(_getAutoMounts)#, _setAutoMounts)

	def _parse(self, tree, types, defaults):
		def setFromTag(parent, key, data, bool=False):
			elements = parent.findall(key)
			if len(elements):
					val = elements[0].text
					if bool:
						val = val == "True"
					if val != None:
						data[key] = val

		keys = ['active', 'hdd_replacement', 'ip', 'sharedir', 'sharename', 'options', 'username', 'password']
		bool_keys = ['active', 'hdd_replacement']
		for i in range(0, len(types)):
			mounttype = types[i]
			for parent in tree.findall(mounttype):
				for mount in parent.findall("mount"):
					data = deepcopy(defaults[i])
					try:
						for key in keys:
							setFromTag(mount, key, data, key in bool_keys)
						Log.d("%s share %s" %(mounttype.upper(), data,))
						if data["active"]:
							self._numActive += 1
						self._mounts[data['sharename']] = data
					except Exception, e:
						Log.w("Error reading %s share: %s" %(mounttype.upper(), e))

	def reload(self, callback=None):
		Log.i()
		# Initialize mounts to empty list
		automounts = []
		self._mounts = {}
		self._numActive = 0

		if not pathExists(XML_FSTAB):
			return
		tree = cet_parse(XML_FSTAB).getroot()
		self._parse(tree, ['nfs', 'cifs'], [AutoMount.DEFAULT_OPTIONS_NFS, AutoMount.DEFAULT_OPTIONS_CIFS])

		if len(self._mounts):
			for sharename, sharedata in self._mounts.items():
				self._applyShare(sharedata, callback)
			self._reloadSystemd(callback=self._onSharesApplied)
		else:
			Log.i("self._mounts without mounts %s" %(self._mounts,))
			if callback is not None:
				callback(True)

	def sanitizeOptions(self, options, cifs=False):
		self._ensureOption(options, 'x-systemd.automount')
		self._ensureOption(options, 'rsize', 'rsize=8192')
		self._ensureOption(options, 'wsize', 'wsize=8192')
		self._ensureOption(options, 'x-systemd.device-timeout', 'x-systemd.device-timeout=2')
		self._ensureOption(options, 'x-systemd.idle-timeout', 'x-systemd.idle-timeout=60')
		self._ensureOption(options, 'soft')
		if not cifs:
			self._ensureOption(options, 'retry', 'retry=0')
			self._ensureOption(options, 'retrans', 'retrans=1')
			self._ensureOption(options, 'timeo', 'timeo=2')
			if not 'tcp' not in options and 'udp' not in options:
				options.append('udp')

		return options

	def _ensureOption(self, options, key, default=None):
		if default is None:
			default = key
		for option in options:
			if option.startswith(key):
				return
		options.append(default)

	def _applyShare(self, data, callback):
		if data['active']:
			mountpoint = AutoMount.MOUNT_BASE + data['sharename']
			Log.d("mountpoint: %s" %(mountpoint,))
			createDir(mountpoint)
			tmpsharedir = data['sharedir'].replace(" ", "\\ ").replace("$", "\\$")

			if data['mounttype'] == 'nfs':
				opts = self.sanitizeOptions(data['options'].split(','))
				remote = '%s:/%s' % (data['ip'], tmpsharedir)
				harddiskmanager.modifyFstabEntry(remote, mountpoint, mode="add_deactivated", extopts=opts, fstype="nfs")

			elif data['mounttype'] == 'cifs':
				opts = self.sanitizeOptions(data['options'].split(','), cifs=True)
				password = data['password']
				username = data['username'].replace(" ", "\\ ")
				if password:
					username = data['username'].replace(" ", "\\ ")
					opts.extend([
						'username=%s' % (data['username']),
						'password=%s' % (data['password']),
						])
				else:
					opts.extend(['guest'])
				opts.extend(['sec=ntlmv2'])
				remote = "//%s/%s" % (data['ip'], tmpsharedir)
				harddiskmanager.modifyFstabEntry(remote, mountpoint, mode="add_deactivated", extopts=opts, fstype="cifs")
		else:
			mountpoint = AutoMount.MOUNT_BASE + data['sharename']
			self.removeMount(mountpoint)
		if callback:
			callback(True)

	def _onSharesApplied(self):
		Log.d()
		for sharename, data in self._mounts.items():
			mountpoint = AutoMount.MOUNT_BASE + sharename
			Log.d("mountpoint: %s" %(mountpoint,))
			if isMount(mountpoint):
				Log.i("'%s' is mounted" %(mountpoint,))
				data['isMounted'] = True
				desc = data['sharename']
				if data['hdd_replacement']: #hdd replacement hack
					self._linkAsHdd(mountpoint)
				harddiskmanager.addMountedPartition(mountpoint, desc)
			else:
				Log.w("'%s' is NOT mounted" %(mountpoint,))
				sharename = self._mounts.get(data['sharename'], None)
				if sharename:
					data['isMounted'] = False
				if pathExists(mountpoint):
					if not isMount(mountpoint):
						removeDir(mountpoint)
						harddiskmanager.removeMountedPartition(mountpoint)

	def _linkAsHdd(self, path):
		hdd_dir = '/media/hdd'
		Log.i("symlink %s %s" % (path, hdd_dir))
		if os_path.islink(hdd_dir):
			if readlink(hdd_dir) != path:
				remove(hdd_dir)
				symlink(path, hdd_dir)
		elif not isMount(hdd_dir):
			if os_path.isdir(hdd_dir):
				removeDir(hdd_dir)
		try:
			symlink(path, hdd_dir)
		except OSError:
			Log.i("adding symlink failed!")
		if pathExists(hdd_dir + '/movie') is False:
			createDir(hdd_dir + '/movie')

	def getMounts(self):
		return self._mounts

	def getMountsAttribute(self, mountpoint, attribute):
		if self._mounts.has_key(mountpoint):
			if self._mounts[mountpoint].has_key(attribute):
				return self._mounts[mountpoint][attribute]
		return None

	def setMountAttributes(self, mountpoint, attributes):
		mount = self._mounts.get(mountpoint, None)
		Log.w("before: %s" %(mount,))
		if mount:
			mount.update(attributes)
		Log.w("after: %s" %(mount,))

	def save(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" encoding="UTF-8"?>\n<mountmanager>\n']

		for sharename, sharedata in self._mounts.items():
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
			Log.w("Error Saving Mounts List: %s" %e)
		finally:
			if file is not None:
				file.close()

	def removeMount(self, mountpoint, callback=None):
		res = False
		entry = Util.findInFstab(src=None, dst=mountpoint)
		if entry:
			sharename=os_path.basename(mountpoint)
			if sharename in self._mounts:
				del self._mounts[sharename]
			self._unmount(mountpoint)
			harddiskmanager.modifyFstabEntry(entry['src'], entry['dst'], mode="remove")
			harddiskmanager.removeMountedPartition(mountpoint)
			res = True
		if callback is not None:
			callback(res)

	def _unmount(self, mountpoint):
		if isMount(mountpoint):
			self._console.ePopen('umount -fl %s' %mountpoint, self._onConsoleFinished)

	def _reloadSystemd(self, **kwargs):
		self._console.ePopen('systemctl daemon-reload && systemctl restart remote-fs.target', self._onConsoleFinished, kwargs)

	def _onConsoleFinished(self, *args):
		kwargs = {}
		if len(args) > 2:
			kw = args[2]
			if isinstance(kw, dict):
				kwargs = kw
		Log.d("args=%s\nkwargs=%s" %(args, kwargs))
		callback = kwargs.get('callback', None)
		if callback:
			args = kwargs.get('args', [])
			callback(*args)

iAutoMount = AutoMount()
