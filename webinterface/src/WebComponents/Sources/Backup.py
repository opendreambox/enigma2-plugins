from Components.Sources.Source import Source
from Components.config import config, ConfigLocations
try:
	from Plugins.SystemPlugins.SoftwareManager import BackupRestore
except ImportError:
	from enigma import eEnv
	# defaults from BackupRestore
	backupdirs = ConfigLocations(default=[eEnv.resolve('${sysconfdir}/enigma2/'), '/etc/network/interfaces', '/etc/wpa_supplicant.conf', '/etc/wpa_supplicant.ath0.conf', '/etc/wpa_supplicant.wlan0.conf', '/etc/resolv.conf', '/etc/default_gw', '/etc/hostname'])
else:
	backupdirs = config.plugins.configurationbackup.backupdirs
from os import remove, path
from re import compile as re_compile
from subprocess import call

try:
	import tarfile
except ImportError:
	tarfile = None

class Backup(Source):
	BACKUP = 0
	RESTORE = 1

	BACKUP_PATH = "/tmp"
	BACKUP_FILENAME = "backup.tar" # XXX: better default name?

	def __init__(self, func=BACKUP):
		Source.__init__(self)
		self.func = func
		self.command = None
		self.result = ( False, _("Missing or Wrong Argument") )

	def handleCommand(self, cmd):
		if self.func is self.BACKUP:
			self.result = self.backupFiles(cmd)
		elif self.func is self.RESTORE:
			self.result = self.restoreFiles(cmd)
		else:
			self.result = ( False, "one two three four unknown command" )

	def getCompressionMode(self, tarname):
		"""
		  This basically guesses which compression to use.
		  No real intelligence here, just keeps some ugliness out of sight.
		"""
		isGz = tarname.endswith((".tar.gz", ".tgz"))
		isBz2 = tarname.endswith((".tar.bz2", ".tbz2"))
		if tarfile:
			return 'gz' if isGz else 'bz2' if isBz2 else ''
		else:
			return 'z' if isGz else 'j' if isBz2 else ''

	def writeTarFile(self, destfile, filenames):
		"""
		  Create a new tar file, either with the tarfile library module or using tar.
		"""
		compression = self.getCompressionMode(destfile)
		if tarfile:
			f = tarfile.open(destfile, 'w:%s' % compression)
			for sourcefile in filenames:
				if path.exists(sourcefile):
					f.add(sourcefile)
			f.close()
		else:
			call(['tar', '-cv%sf' % compression, destfile] + filenames)
		return (True, destfile)

	def backupFiles(self, filename):
		if not filename:
			filename = self.BACKUP_FILENAME
		invalidCharacters = re_compile(r'[^A-Za-z0-9_\. ]+|^\.|\.$|^ | $|^$')
		tarFilename = "%s.tar" % invalidCharacters.sub('_', filename)
		backupFilename = path.join(self.BACKUP_PATH, tarFilename)
		if path.exists(backupFilename):
			remove(backupFilename)

		return self.writeTarFile(backupFilename, backupdirs.value)

	def unpackTarFile(self, filename, destination="/"):
		"""
		  Unpack existing tar file to destination folder.
		"""
		compression = self.getCompressionMode(filename)
		if tarfile:
			f = tarfile.open(filename, 'r:%s' % compression)
			f.extractall(path=destination)
			f.close()
		else:
			call(['tar', '-xvf', filename, '-C', '/'])
		return (True, "Backup was successfully restored")

	def restoreFiles(self, filename):
		if not path.exists(filename):
			return (False, "Error, %s does not exists, restore is not possible..." % filename)

		ret = self.unpackTarFile(filename)
		if ret[0]:
			remove(filename)
		return ret
