# -*- coding: utf-8 -*-
# for localized messages
#from __init__ import _
from enigma import eConsoleAppContainer, eEnv, eNetworkManager, eTimer
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.Network import iNetworkInfo, NetworkInterface
from Components.config import getConfigListEntry, ConfigIP
from Components.ConfigList import ConfigListScreen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from Tools.Log import Log
from cPickle import dump, load
from os import path as os_path, stat, mkdir, remove
from time import time
from stat import ST_MTIME
from netaddr import IPNetwork
from nfsutils import showmount
from nmb.NetBIOS import NetBIOS
from smb.base import SharedDevice
from smb.SMBConnection import SMBConnection

import rpcinfo
import socket
from MountManager import AutoMountManager
from AutoMount import iAutoMount
from MountEdit import AutoMountEdit
from UserDialog import UserDialog

from twisted.internet import reactor, threads

def write_cache(cache_file, cache_data):
	#Does a cPickle dump
	if not os_path.isdir( os_path.dirname(cache_file) ):
		try:
			mkdir( os_path.dirname(cache_file) )
		except OSError:
			print os_path.dirname(cache_file), '[Networkbrowser] is a file'
	fd = open(cache_file, 'w')
	dump(cache_data, fd, -1)
	fd.close()

def valid_cache(cache_file, cache_ttl):
	#See if the cache file exists and is still living
	try:
		mtime = stat(cache_file)[ST_MTIME]
	except:
		return 0
	curr_time = time()
	if (curr_time - mtime) > cache_ttl:
		return 0
	else:
		return 1

def load_cache(cache_file):
	#Does a cPickle load
	fd = open(cache_file)
	cache_data = load(fd)
	fd.close()
	return cache_data

class NetworkDescriptor:
	def __init__(self, name = "NetworkServer", description = ""):
		self.name = name
		self.description = description

class NetworkBrowser(Screen):
	skin = """
		<screen name="NetworkBrowser" position="center,120" size="820,520" title="Network Neighbourhood">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on"/>
		<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on"/>
		<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		<eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		<widget source="infotext" render="Label" position="10,55" size="800,420" zPosition="1" font="Regular;22" halign="center" valign="center"/>
		<widget source="list" render="Listbox" position="10,55" size="800,420" zPosition="2" enableWrapAround="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
				MultiContentEntryPixmapAlphaTest(pos = (10,5),size = (50,50),png = 1),# index 1 is the expandable/expanded/verticalline icon
				MultiContentEntryText(pos = (70,4),size = (700,26),font=2,flags = RT_HALIGN_LEFT,text = 2),# index 2 is the Hostname
				MultiContentEntryText(pos = (180,5),size = (610,25),font=0,flags = RT_HALIGN_LEFT,text = 3),# index 3 is the sharename
				MultiContentEntryText(pos = (180,26),size = (610,18),font=1,flags = RT_HALIGN_LEFT,text = 4),# index 4 is the sharedescription
				MultiContentEntryPixmapAlphaTest(pos = (65,5),size = (50,50),png = 5),# index 5 is the nfs/cifs icon
				MultiContentEntryPixmapAlphaTest(pos = (125,5),size = (50,50),png = 6),# index 6 is the isMounted icon
				],
				"fonts": [gFont("Regular",22),gFont("Regular",18),gFont("Regular",24)],
				"itemHeight": 60
				}
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session, iface,plugin_path):
		Screen.__init__(self, session)
		self.skin_path = plugin_path
		self.session = session
		self.iface = iface or 'eth0'
		for service in eNetworkManager.getInstance().getServices():
			key = self.getServiceIF(service)
			if key:
				self.iface = key
				break
		self.networklist = []
		self.expanded = []
		self.cache_ttl = 604800 #Seconds cache is considered valid, 7 Days should be ok
		self.cache_file = eEnv.resolve("${sysconfdir}/enigma2/networkbrowser.cache") #Path to cache directory
		self._nrthreads = 0
		self._netbios = NetBIOS(broadcast=False)
		self._ipv4 = iNetworkInfo.getConfiguredInterfaces()[self.iface].ipv4
		self._myhostname = self._lookupHostname(self._ipv4.address, local=True)

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Mounts"))
		self["key_yellow"] = StaticText(_("Rescan"))
		self["key_blue"] = StaticText(_("Expert"))
		self["infotext"] = StaticText(_("Press OK to mount!"))
		
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.go,
			"back": self.close,
			"red": self.close,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
		})

		self.list = []
		self.statuslist = []
		self.listindex = 0
		self["list"] = List(self.list)
		self["list"].onSelectionChanged.append(self.selectionChanged)

		self.onLayoutFinish.append(self.startRun)
		self.onShown.append(self.setWindowTitle)
		self.onClose.append(self.cleanup)
		self.Timer = eTimer()
		self.Timer_conn = self.Timer.timeout.connect(self.TimerFire)

	def getServiceIF(self, service):
		key = None
		if service.state() == eNetworkManager.STATE_ONLINE:
			iface = NetworkInterface(service)
			key = iface.ethernet.interface
		return key

	def cleanup(self):
		del self.Timer

	def startRun(self):
		self.expanded = []
		self.setStatus('update')
		self["infotext"].setText("")
		self.vc = valid_cache(self.cache_file, self.cache_ttl)
		if self.cache_ttl > 0 and self.vc != 0:
			self.process_NetworkIPs()
		else:
			self.Timer.start(3000)

	def TimerFire(self):
		self.Timer.stop()
		self.process_NetworkIPs()

	def setWindowTitle(self):
		self.setTitle(_("Browse network neighbourhood"))

	def keyGreen(self):
		self.session.open(AutoMountManager, None, self.skin_path)

	def keyYellow(self):
		if (os_path.exists(self.cache_file) == True):
			remove(self.cache_file)
		self.startRun()

	def keyBlue(self):
		self.session.openWithCallback(self.scanIPclosed,ScanIP)

	def scanIPclosed(self,result):
		if result[0]:
			# scan subnet outside ipv4.address/24
			if result[1] == "address":
				print "[Networkbrowser] got IP:",result[0]
				self.setStatus('update')
				net = IPNetwork('%s/24' % result[0])
				localnet = IPNetwork('%s/%s' % (self._ipv4.address, self._ipv4.netmask))
				if localnet.__contains__(net):
					self._startScan(self.iface, net.cidr)
				else:
					for host in net.iter_hosts():
						self._nrthreads += 1
						reactor.callInThread(self.getNetworkIPs, str(host))
			# add offline host
			elif result[1] == "nfs":
				self.networklist.append(['host', result[0], result[0] , '00:00:00:00:00:00', result[0], 'Master Browser'])
				write_cache(self.cache_file, self.networklist)
				self.updateHostsList()

	def setStatus(self,status = None):
		if status:
			self.statuslist = []
			if status == 'update':
				statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/update.png"))
				self.statuslist.append(( ['info'], statuspng, _("Searching your network. Please wait..."), None, None, None, None ))
				self['list'].setList(self.statuslist)
			elif status == 'error':
				statuspng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/error.png"))
				self.statuslist.append(( ['info'], statuspng, _("No network devices found!"), None, None, None, None ))
				self['list'].setList(self.statuslist)

	def process_NetworkIPs(self):
		self.inv_cache = 0
		self.vc = valid_cache(self.cache_file, self.cache_ttl)
		if self.cache_ttl > 0 and self.vc != 0:
			Log.i('Loading network cache from %s' %(self.cache_file))
			try:
				self.networklist = load_cache(self.cache_file)
				if len(self.networklist) > 0:
					self.updateHostsList()
				else:
					self.setStatus('error')
			except:
				self.inv_cache = 1
		if self.cache_ttl == 0 or self.inv_cache == 1 or self.vc == 0:
			Log.i('Getting fresh network list')

			net = IPNetwork('%s/%s' % (self._ipv4.address, self._ipv4.netmask))
			if net.prefixlen < 24:
				net.prefixlen = 24

			self.networklist = []
			self._startScan(self.iface, net.cidr)

	def _startScan(self, iface, cidr):
			cmd = "arp-scan -gqNx --retry=1 --interface=%s %s" % (iface, cidr)
			Log.i("Command: %s" % cmd)
			self._arpscan_container = eConsoleAppContainer()
			self._arpscan_appClosed_conn = self._arpscan_container.appClosed.connect(self._onArpScanClosed)
			self._arpscan_dataAvail_conn = self._arpscan_container.dataAvail.connect(self._onArpScanData)

			self._arpscan_hosts = []
			self._arpscan_container.execute(cmd)

	def _onArpScanData(self, data):
		for line in data.splitlines():
			try:
				(address, mac) = line.split()
			except:
				Log.w('Unexpected line: %s' % line)
			else:
				self._arpscan_hosts.append(address)

	def _onArpScanClosed(self, retval):
		Log.i("arp-scan closed, retval=%d" % retval)
		for host in self._arpscan_hosts:
			self._nrthreads += 1
			reactor.callInThread(self.getNetworkIPs, host)

	def _probeTcpPort(self, host, port):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(1)
		try:
			sock.connect((host, port))
		except:
			Log.w("Connection to %s:%d failed" % (host, port))
			found = False
		else:
			Log.i("Detected service on %s:%d" % (host, port))
			found = True
		sock.close()
		return found

	def getNetworkIPs(self, host):
		Log.i("Detecting availablility of NFS or SMB services on host %s" % host)
		info = []
		services = []

		if self._probeTcpPort(host, 445) or self._probeTcpPort(host, 139):
			Log.i("Found SMB server on %s" % host)
			services.append("smb")

		if rpcinfo.progping('udp', host, 'nfs') or rpcinfo.progping('tcp', host, 'nfs'):
			Log.i("Found NFS server on %s" % host)
			services.append("nfs")

		if services:
			hostname = self._lookupHostname(host)
			info.append(['host', hostname, host, '00:00:00:00:00:00', host, 'Master Browser', services])

		Log.i(info)
		reactor.callFromThread(self._onNetworkIPsReady, info)

	def _onNetworkIPsReady(self, info):
		self.networklist += info
		self._nrthreads -= 1
		Log.i("Waiting for %d more threads" % self._nrthreads)
		if self._nrthreads == 0:
			write_cache(self.cache_file, self.networklist)
			if len(self.networklist) > 0:
				self.updateHostsList()
			else:
				self.setStatus('error')

	def _onError(self, *args, **kwargs):
		Log.w()

	def _lookupHostname(self, addr, local=False):
		names = self._netbios.queryIPForName(addr, timeout=1)
		if names:
			return sorted(names)[0]

		try:
			fqdn = socket.getnameinfo((addr, 0), socket.NI_NAMEREQD)[0]
		except:
			pass
		else:
			hostname = fqdn.split('.', 1)[0]
			if hostname:
				return hostname

		if local:
			hostname = socket.gethostname()
			if hostname:
				return hostname

		return addr

	def getNetworkShares(self, hostip, hostname):
		sharelist = []
		self.sharecache_file = None
		self.sharecache_file = eEnv.resolve("${sysconfdir}/enigma2/") + hostname.strip() + '.cache' #Path to cache directory

		username = "guest"
		password = ""
		if os_path.exists(self.sharecache_file):
			print '[Networkbrowser] Loading userinfo from ',self.sharecache_file
			try:
				self.hostdata = load_cache(self.sharecache_file)
				username = self.hostdata['username']
				password = self.hostdata['password']
			except:
				pass

		for port in (445, 139):
			smbconn = SMBConnection(username, password, self._myhostname, hostname, is_direct_tcp=(port == 445))
			if smbconn.connect(hostip, port=port, timeout=1):
				print '[Networkbrowser] established SMB connection to %s:%d' % (hostip, port)
				for share in smbconn.listShares(timeout=1):
					if share.type == SharedDevice.DISK_TREE and not share.isSpecial:
						sharelist.append(['smbShare', hostname, hostip, share.name.encode('utf-8'), 'Disk', share.comments.encode('utf-8')])
				smbconn.close()
				break

		try:
			exports = showmount(hostip)
		except IOError as e:
			print '[Networkbrowser] showmount: ' + str(e)
		else:
			for ex in exports:
				sharelist.append(['nfsShare', os_path.basename(ex['dir']), hostip, ','.join(ex['groups']), ex['dir'], ''])

		return sharelist

	def updateHostsList(self):
		Log.i()
		self.list = []
		network = {}
		for x in self.networklist:
			if not network.has_key(x[2]):
				network[x[2]] = []
			network[x[2]].append((NetworkDescriptor(name = x[1], description = x[2]), x))
		
		for x in network.keys():
			hostentry = network[x][0][1]
			name = hostentry[2] + " ( " +hostentry[1].strip() + " )"
			expandableIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/host.png"))
			self.list.append(( hostentry, expandableIcon, name, None, None, None, None ))

		if len(self.list):
			for entry in self.list:
				entry[0][2]= "%3s.%3s.%3s.%3s" % tuple(entry[0][2].split("."))
			self.list.sort(key=lambda x: x[0][2])
			for entry in self.list:
				entry[0][2]= entry[0][2].replace(" ", "")
		self["list"].setList(self.list)
		self["list"].setIndex(self.listindex)

	def updateNetworkList(self):
		Log.i()
		self.list = []
		network = {}
		for x in self.networklist:
			if not network.has_key(x[2]):
				network[x[2]] = []
			network[x[2]].append((NetworkDescriptor(name = x[1], description = x[2]), x))
		for x in sorted(network.keys()):
			if x in self.expanded:
				networkshares = self.getNetworkShares(x, network[x][0][1][1].strip())
				hostentry = network[x][0][1]
				name = hostentry[2] + " ( " +hostentry[1].strip() + " )"
				expandedIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/host.png"))
				self.list.append(( hostentry, expandedIcon, name, None, None, None, None ))
				for share in networkshares:
					self.list.append(self.BuildNetworkShareEntry(share))
			else: # HOSTLIST - VIEW
				hostentry = network[x][0][1]
				name = hostentry[2] + " ( " +hostentry[1].strip() + " )"
				expandableIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/host.png"))
				self.list.append(( hostentry, expandableIcon, name, None, None, None, None ))
		if len(self.list):
			for entry in self.list:
				entry[0][2]= "%3s.%3s.%3s.%3s" % tuple(entry[0][2].split("."))
			self.list.sort(key=lambda x: x[0][2])
			for entry in self.list:
				entry[0][2]= entry[0][2].replace(" ", "")
		self["list"].setList(self.list)
		self["list"].setIndex(self.listindex)

	def BuildNetworkShareEntry(self,share):
		verticallineIcon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/verticalLine.png"))
		sharetype = share[0]
		localsharename = share[1]
		sharehost = share[2]

		if sharetype == 'smbShare':
			sharedir = share[3]
			sharedescription = share[5]
		else:
			sharedir = share[4]
			sharedescription = share[3]

		if sharetype == 'nfsShare':
			newpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-nfs.png"))
		else:
			newpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-smb.png"))

		self.isMounted = False
		mounts = iAutoMount.getMounts()
		for sharename, sharedata in mounts.items():
			if sharedata['ip'] == sharehost:
				if sharetype == 'nfsShare' and sharedata['mounttype'] == 'nfs':
					if sharedir == sharedata['sharedir']:
						if sharedata["isMounted"] is True:
							self.isMounted = True
				if sharetype == 'smbShare' and sharedata['mounttype'] == 'cifs':
					if sharedir == sharedata['sharedir']:
						if sharedata["isMounted"] is True:
							self.isMounted = True
		if self.isMounted is True:
			isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/ok.png"))
		else:
			isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/cancel.png"))

		return((share, verticallineIcon, None, sharedir, sharedescription, newpng, isMountedpng))

	def selectionChanged(self):
		current = self["list"].getCurrent()
		self.listindex = self["list"].getIndex()
		if current:
			if len(current[0]) >= 2:
				if current[0][0] in ("nfsShare", "smbShare"):
					self["infotext"].setText(_("Press OK to mount this share!"))
				else:
					selectedhost = current[0][2]
					if selectedhost in self.expanded:
						self["infotext"].setText(_("Press OK to collapse this host"))
					else:
						self["infotext"].setText(_("Press OK to expand this host"))

	def go(self):
		sel = self["list"].getCurrent()
		if sel is None:
			return
		if len(sel[0]) <= 1:
			return
		selectedhost = sel[0][2]
		selectedhostname = sel[0][1]

		self.hostcache_file = None
		if sel[0][0] == 'host': # host entry selected
			if selectedhost in self.expanded:
				self.expanded.remove(selectedhost)
				self.updateNetworkList()
				return
			else:
				self.hostcache_file = None
				self.hostcache_file = eEnv.resolve("${sysconfdir}/enigma2/") + selectedhostname.strip() + '.cache' #Path to cache directory
				if os_path.exists(self.hostcache_file):
					print '[Networkbrowser] Loading userinfo cache from ',self.hostcache_file
					try:
						self.hostdata = load_cache(self.hostcache_file)
						self.passwordQuestion(False)
						return
					except:
						pass
			if len(sel[0]) < 7 or "smb" in sel[0][6]:
				self.session.openWithCallback(self.passwordQuestion, MessageBox, text=_("Do you want to enter a username and password for this host?\n"), default=False )
			else:
				self.passwordQuestion(False)

		if sel[0][0] == 'nfsShare': # share entry selected
			print '[Networkbrowser] sel nfsShare'
			self.openMountEdit(sel[0])
			return

		if sel[0][0] == 'smbShare': # share entry selected
			print '[Networkbrowser] sel cifsShare'
			self.hostcache_file = None
			self.hostcache_file = eEnv.resolve("${sysconfdir}/enigma2/") + selectedhostname.strip() + '.cache' #Path to cache directory
			if os_path.exists(self.hostcache_file):
				print '[Networkbrowser] userinfo found from ',self.sharecache_file
				self.openMountEdit(sel[0])
				return

	def passwordQuestion(self, ret = False):
		sel = self["list"].getCurrent()
		selectedhost = sel[0][2]
		selectedhostname = sel[0][1]
		if (ret == True):
			self.session.openWithCallback(self.UserDialogClosed, UserDialog, self.skin_path, selectedhostname.strip())
		else:
			if sel[0][0] == 'host': # host entry selected
				if selectedhost in self.expanded:
					self.expanded.remove(selectedhost)
				else:
					self.expanded.append(selectedhost)
				self.updateNetworkList()
			if sel[0][0] == 'nfsShare': # share entry selected
				self.openMountEdit(sel[0])
			if sel[0][0] == 'smbShare': # share entry selected
				self.openMountEdit(sel[0])

	def UserDialogClosed(self, *ret):
		if ret is not None and len(ret):
			self.go()

	def openMountEdit(self, selection):
		if selection:
			mounts = iAutoMount.getMounts()
			if selection[0] == 'nfsShare': # share entry selected
				#Initialize blank mount enty
				data = iAutoMount.DEFAULT_OPTIONS_NFS
				# add data
				data['active'] = True
				data['ip'] = selection[2]
				data['sharename'] = selection[1]
				data['sharedir'] = selection[4]

				for sharename, sharedata in mounts.items():
					if sharedata['ip'] == selection[2] and sharedata['sharedir'] == selection[4]:
						data = sharedata
				self.session.openWithCallback(self.MountEditClosed,AutoMountEdit, self.skin_path, data)
			if selection[0] == 'smbShare': # share entry selected
				#Initialize blank mount enty
				data = iAutoMount.DEFAULT_OPTIONS_CIFS
				# add data
				data['active'] = True
				data['ip'] = selection[2]
				data['sharename'] = selection[1]
				data['sharedir'] = selection[3]
				self.sharecache_file = None
				self.sharecache_file = eEnv.resolve("${sysconfdir}/enigma2/") + selection[1].strip() + '.cache' #Path to cache directory
				if os_path.exists(self.sharecache_file):
					print '[Networkbrowser] Loading userinfo from ',self.sharecache_file
					try:
						self.hostdata = load_cache(self.sharecache_file)
						data['username'] = self.hostdata['username']
						data['password'] = self.hostdata['password']
					except:
						pass

				for sharename, sharedata in mounts.items():
					if sharedata['ip'] == selection[2].strip() and sharedata['sharedir'] == selection[3].strip():
						data = sharedata
				self.session.openWithCallback(self.MountEditClosed,AutoMountEdit, self.skin_path, data)

	def MountEditClosed(self, returnValue = None):
		if returnValue == None:
			self.updateNetworkList()

class ScanIP(Screen, ConfigListScreen):
	skin = """
		<screen name="ScanIP" position="center,center" size="770,110" title="Scan IP">
		<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="250,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="260,5" size="250,50" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="510,5" size="250,50" alphatest="on" />
		<widget source="key_red" render="Label" position="10,5" size="250,50" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_green" render="Label" position="260,5" size="250,50" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
		<widget source="key_yellow" render="Label" position="510,5" size="250,50" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1"  shadowColor="black" shadowOffset="-2,-2" />
		<widget name="config" position="10,65" size="750,30"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Scan NFS share"))
		self["key_yellow"] = StaticText(_("Scan range"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"back": self.exit,
			"red": self.exit,
			"cancel": self.exit,
			"green": self.goNfs,
			"yellow": self.goAddress,
		}, -1)
		
		self.ipAddress = ConfigIP(default=[0,0,0,0])
		
		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("IP Address"), self.ipAddress),
		], self.session)

		self.onLayoutFinish.append(self.layoutFinished)

	def exit(self):
		self.close((None,None))

	def layoutFinished(self):
		self.setWindowTitle()

	def setWindowTitle(self):
		self.setTitle(_("Enter IP to scan..."))

	def goAddress(self):
		if self.ipAddress.getText() != "0.0.0.0":
			self.close((self.ipAddress.getText(), "address"))
		else:
			self.exit

	def goNfs(self):
		if self.ipAddress.getText() != "0.0.0.0":
			self.close((self.ipAddress.getText(), "nfs"))
		else:
			self.exit

