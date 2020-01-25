from __future__ import print_function
from __future__ import absolute_import
Version = '$Header$';

from enigma import eConsoleAppContainer
from Plugins.Plugin import PluginDescriptor

from Components.config import config, ConfigBoolean, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, ConfigOnOff
from Components.Network import iNetworkInfo
from Screens.MessageBox import MessageBox
from .WebIfConfig import WebIfConfigScreen
from .WebChilds.Toplevel import getToplevel
from Tools.HardwareInfo import HardwareInfo

from Tools.Directories import copyfile, resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG
from Tools.IO import saveFile
from Tools.Log import Log

from twisted.internet import reactor, ssl
from twisted.internet.error import CannotListenError
from twisted.web import server, http, util, static, resource

from socket import gethostname as socket_gethostname
from OpenSSL import SSL, crypto
from time import gmtime
from os.path import isfile as os_isfile, exists as os_exists

from .__init__ import __version__

import random, uuid, time, hashlib

from ipaddress import ip_address, ip_interface
import six

hw = HardwareInfo()
#CONFIG INIT

#init the config
config.plugins.Webinterface = ConfigSubsection()
config.plugins.Webinterface.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.show_in_extensionsmenu = ConfigYesNo(default = False)
config.plugins.Webinterface.allowzapping = ConfigYesNo(default=True)
config.plugins.Webinterface.includemedia = ConfigYesNo(default=False)
config.plugins.Webinterface.autowritetimer = ConfigYesNo(default=False)
config.plugins.Webinterface.loadmovielength = ConfigYesNo(default=True)
config.plugins.Webinterface.version = ConfigText(__version__) # used to make the versioninfo accessible enigma2-wide, not confgurable in GUI.

config.plugins.Webinterface.http = ConfigSubsection()
config.plugins.Webinterface.http.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.http.port = ConfigInteger(default = 80, limits=(1, 65535) )
config.plugins.Webinterface.http.auth = ConfigYesNo(default=True)

config.plugins.Webinterface.https = ConfigSubsection()
config.plugins.Webinterface.https.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.https.port = ConfigInteger(default = 443, limits=(1, 65535) )
config.plugins.Webinterface.https.auth = ConfigYesNo(default=True)

config.plugins.Webinterface.streamauth = ConfigYesNo(default=False)
config.plugins.Webinterface.localauth = ConfigOnOff(default=False)

config.plugins.Webinterface.anti_hijack = ConfigOnOff(default=True)
config.plugins.Webinterface.extended_security = ConfigOnOff(default=True)

global running_defered, waiting_shutdown, toplevel

running_defered = []
waiting_shutdown = 0
toplevel = None
server.VERSION = "Enigma2 WebInterface Server $Revision$".replace("$Revi", "").replace("sion: ", "").replace("$", "")

KEY_FILE = resolveFilename(SCOPE_CONFIG, "key.pem")
CERT_FILE = resolveFilename(SCOPE_CONFIG, "cert.pem")

#===============================================================================
# Helperclass to close running Instances of the Webinterface
#===============================================================================
class Closer:
	counter = 0
	def __init__(self, session, callback=None):
		self.callback = callback
		self.session = session
#===============================================================================
# Closes all running Instances of the Webinterface
#===============================================================================
	def stop(self):
		global running_defered
		for d in running_defered:
			print("[Webinterface] stopping interface on ", d.interface, " with port", d.port)
			x = d.stopListening()

			try:
				x.addCallback(self.isDown)
				self.counter += 1
			except AttributeError:
				pass
		running_defered = []
		if self.counter < 1:
			if self.callback is not None:
				self.callback(self.session)

#===============================================================================
# #Is it already down?
#===============================================================================
	def isDown(self, s):
		self.counter -= 1
		if self.counter < 1:
			if self.callback is not None:
				self.callback(self.session)

def installCertificates(session):
	if not os_exists(CERT_FILE) \
			or not os_exists(KEY_FILE):
		print("[Webinterface].installCertificates :: Generating SSL key pair and CACert")
		# create a key pair
		k = crypto.PKey()
		k.generate_key(crypto.TYPE_RSA, 2048)

		# create a self-signed cert
		cert = crypto.X509()
		cert.get_subject().C = "DE"
		cert.get_subject().ST = "Home"
		cert.get_subject().L = "Home"
		cert.get_subject().O = "Dreambox"
		cert.get_subject().OU = "STB"
		cert.get_subject().CN = socket_gethostname()
		cert.set_serial_number(random.randint(1000000,1000000000))
		cert.set_notBefore(b"20120101000000Z");
		cert.set_notAfter(b"20301231235900Z")
		cert.set_issuer(cert.get_subject())
		cert.set_pubkey(k)
		print("[Webinterface].installCertificates :: Signing SSL key pair with new CACert")
		cert.sign(k, 'sha256')

		try:
			print("[Webinterface].installCertificates ::  Installing newly generated certificate and key pair")
			saveFile(CERT_FILE, crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
			saveFile(KEY_FILE, crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
		except IOError as e:
			#Disable https
			config.plugins.Webinterface.https.enabled.value = False
			config.plugins.Webinterface.https.enabled.save()
			#Inform the user
			session.open(MessageBox, "Couldn't install generated SSL-Certifactes for https access\nHttps access is disabled!", MessageBox.TYPE_ERROR)


#===============================================================================
# restart the Webinterface for all configured Interfaces
#===============================================================================
def restartWebserver(session):
	try:
		del session.mediaplayer
		del session.messageboxanswer
	except NameError:
		pass
	except AttributeError:
		pass

	global running_defered
	if len(running_defered) > 0:
		Closer(session, startWebserver).stop()
	else:
		startWebserver(session)

#===============================================================================
# start the Webinterface for all configured Interfaces
#===============================================================================
def startWebserver(session):
	global running_defered
	global toplevel

	session.mediaplayer = None
	session.messageboxanswer = None
	if toplevel is None:
		toplevel = getToplevel(session)

	errors = ""

	if config.plugins.Webinterface.enabled.value is not True:
		print("[Webinterface] is disabled!")

	else:
		# IF SSL is enabled we need to check for the certs first
		# If they're not there we'll exit via return here
		# and get called after Certificates are installed properly
		if config.plugins.Webinterface.https.enabled.value:
			installCertificates(session)

		# Listen on all Interfaces

		#HTTP
		port = config.plugins.Webinterface.http.port.value
		auth = config.plugins.Webinterface.http.auth.value
		if config.plugins.Webinterface.http.enabled.value is True:
			ret = startServerInstance(session, port, useauth=auth)
			if not ret:
				errors = "%s port %i\n" %(errors, port)
			else:
				registerBonjourService('http', port)

		#Streaming requires listening on localhost:80 no matter what, ensure it its available
		if config.plugins.Webinterface.http.port.value != 80 or not config.plugins.Webinterface.http.enabled.value:
			#LOCAL HTTP Connections (Streamproxy)
			local4 = "127.0.0.1"
			local4mapped = "::ffff:127.0.0.1"
			local6 = "::1"

			ret = startServerInstance(session, 80, useauth=auth, ipaddress=local4)
			if not ret:
				errors = "%s%s:%i\n" %(errors, local4, 80)
			ret = startServerInstance(session, 80, useauth=auth, ipaddress=local4mapped, ipaddress2=local6)
			#ip6 is optional
#			if not ret:
#				errors = "%s%s/%s:%i\n" %(errors, local4mapped, local6, 80)

		#HTTPS
		if config.plugins.Webinterface.https.enabled.value is True:
			sport = config.plugins.Webinterface.https.port.value
			sauth = config.plugins.Webinterface.https.auth.value

			ret = startServerInstance(session, sport, useauth=sauth, usessl=True)
			if not ret:
				errors = "%s%s:%i\n" %(errors, "0.0.0.0 / ::", sport)
			else:
				registerBonjourService('https', sport)

		if errors:
			session.open(MessageBox, "Webinterface - Couldn't listen on:\n %s" % (errors), type=MessageBox.TYPE_ERROR, timeout=30)

#===============================================================================
# stop the Webinterface for all configured Interfaces
#===============================================================================
def stopWebserver(session):
	try:
		del session.mediaplayer
		del session.messageboxanswer
	except NameError:
		pass
	except AttributeError:
		pass

	global running_defered
	if len(running_defered) > 0:
		Closer(session).stop()

#===============================================================================
# startServerInstance
# Starts an Instance of the Webinterface
# on given ipaddress, port, w/o auth, w/o ssl
#===============================================================================
def startServerInstance(session, port, useauth=False, usessl=False, ipaddress="::", ipaddress2=None):
	if useauth:
# HTTPAuthResource handles the authentication for every Resource you want it to
		root = HTTPAuthResource(toplevel, "Enigma2 WebInterface")
		site = server.Site(root)
	else:
		root = HTTPRootResource(toplevel)
		site = server.Site(root)

	result = False

	def logFail(addr, exception=None):
		print("[Webinterface] FAILED to listen on %s:%i auth=%s ssl=%s" % (addr, port, useauth, usessl))
		if exception:
			print(exception)

	if usessl:
		ctx = ChainedOpenSSLContextFactory(KEY_FILE, CERT_FILE)
		try:
			d = reactor.listenSSL(port, site, ctx, interface=ipaddress)
			result = True
			running_defered.append(d)
		except CannotListenError as e:
			logFail(ipaddress, e)
		if ipaddress2:
			try:
				d = reactor.listenSSL(port, site, ctx, interface=ipaddress2)
				result = True
				running_defered.append(d)
			except CannotListenError as e:
				logFail(ipaddress2, e)
	else:
		try:
			d = reactor.listenTCP(port, site, interface=ipaddress)
			result = True
			running_defered.append(d)
		except CannotListenError as e:
			logFail(ipaddress, e)
		if ipaddress2:
			try:
				d = reactor.listenTCP(port, site, interface=ipaddress2)
				result = True
				running_defered.append(d)
			except CannotListenError as e:
				logFail(ipaddress2, e)
	
	print("[Webinterface] started on %s:%i auth=%s ssl=%s" % (ipaddress, port, useauth, usessl))
	return result

	#except Exception, e:
		#print "[Webinterface] starting FAILED on %s:%i!" % (ipaddress, port), e
		#return False

class ChainedOpenSSLContextFactory(ssl.DefaultOpenSSLContextFactory):
	def __init__(self, privateKeyFileName, certificateChainFileName, sslmethod=SSL.SSLv23_METHOD):
		self.privateKeyFileName = privateKeyFileName
		self.certificateChainFileName = certificateChainFileName
		self.sslmethod = sslmethod
		self.cacheContext()

	def cacheContext(self):
		ctx = SSL.Context(self.sslmethod)
		ctx.set_options(SSL.OP_NO_SSLv3|SSL.OP_NO_SSLv2)
		ctx.use_certificate_chain_file(self.certificateChainFileName)
		ctx.use_privatekey_file(self.privateKeyFileName)
		self._context = ctx

class SimpleSession(object):
	def __init__(self, expires=0):
		self._id = "0"
		self._expires = time.time() + expires if expires > 0 else 0

	def _generateId(self):
		if config.plugins.Webinterface.extended_security.value:
			self._id = str ( uuid.uuid4() )
		else:
			self._id = "0"

	def _getId(self):
		if self.expired():
			self._generateId()
		return self._id

	def expired(self):
		expired = False
		if config.plugins.Webinterface.extended_security.value:
			expired = self._expires > 0 and self._expires < time.time()
			expired = expired or self._id == "0"
		else:
			expired = self._id != "0"
		return expired

	id = property(_getId)

#Every request made will pass this Resource (as it is the root resource)
#Any "global" checks should be done here
class HTTPRootResource(resource.Resource):
	SESSION_PROTECTED_PATHS = [b'/web/', b'/opkg', b'/ipkg']
	SESSION_EXCEPTIONS = [
		b'/web/epgsearch.rss', b'/web/movielist.m3u', b'/web/movielist.rss', b'/web/services.m3u', b'/web/session',
		b'/web/stream.m3u', b'/web/stream', b'/web/streamcurrent.m3u', b'/web/strings.js', b'/web/ts.m3u']

	def __init__(self, res):
		print("[HTTPRootResource}.__init__")
		resource.Resource.__init__(self)
		self.resource = res
		self.sessionInvalidResource = resource.ErrorPage(http.PRECONDITION_FAILED, "Precondition failed!", "sessionid is missing, invalid or expired!")
		self._sessions = {}

	def getClientToken(self, request):
		ip = request.getClientIP()
		ua = request.getHeader("User-Agent") or "Default UA"
		return hashlib.sha1(six.ensure_binary("%s/%s" %(ip, ua))).hexdigest()

	def isSessionValid(self, request):
		session = self._sessions.get( self.getClientToken(request), None )
		if session is None or session.expired():
			session = SimpleSession()
			key = self.getClientToken(request)
			print("[HTTPRootResource].isSessionValid :: created session with id '%s' for client with token '%s'" %(session.id, key))
			self._sessions[ key ] = session

		request.enigma2_session = session

		if config.plugins.Webinterface.extended_security.value and not request.path in self.SESSION_EXCEPTIONS:
			protected = False
			for path in self.SESSION_PROTECTED_PATHS:
				if request.path.startswith(path):
					protected = True

			if protected:
				rsid = request.args.get('sessionid', None)
				if rsid:
					rsid = rsid[0]
				return session and session.id == rsid

		return True

	def render(self, request):
		#enable SAMEORIGIN policy for iframes
		if config.plugins.Webinterface.anti_hijack.value:
			request.setHeader("X-Frame-Options", "SAMEORIGIN")

		if self.isSessionValid(request):
			return self.resource.render(request)
		else:
			return self.sessionInvalidResource.render(request)

	def getChildWithDefault(self, path, request):
		#enable SAMEORIGIN policy for iframes
		if config.plugins.Webinterface.anti_hijack.value:
			request.setHeader("X-Frame-Options", "SAMEORIGIN")

		if self.isSessionValid(request):
			return self.resource.getChildWithDefault(path, request)
		else:
			print("[Webinterface.HTTPRootResource.render] !!! session invalid !!!")
			return self.sessionInvalidResource

#===============================================================================
# HTTPAuthResource
# Handles HTTP Authorization for a given Resource
#===============================================================================
class HTTPAuthResource(HTTPRootResource):
	def __init__(self, res, realm):
		HTTPRootResource.__init__(self, res)
		self.realm = realm
		self.authorized = False
		self.unauthorizedResource = resource.ErrorPage(http.UNAUTHORIZED, "Access denied", "Authentication credentials invalid!")
		self._interfaces = []

	def _addInterface(self, address, netmask):
		iface = ip_interface(u"%s/%s" % (address, netmask))
		self._interfaces.append(iface)

	def _assignLocalNetworks(self, ifaces):
		if self._interfaces:
			return
		self._interfaces = []
		#LAN
		for key, iface in six.iteritems(ifaces):
			if iface.ipv4.address != "0.0.0.0":
				self._addInterface(iface.ipv4.address, iface.ipv4.netmask)
			if iface.ipv6.address != "::":
				self._addInterface(iface.ipv6.address, iface.ipv6.netmask)
		Log.w(self._interfaces)

	def unauthorized(self, request):
		request.setHeader('WWW-authenticate', 'Basic realm="%s"' % self.realm)
		request.setResponseCode(http.UNAUTHORIZED)
		return self.unauthorizedResource

	def _isLocalClient(self, ip):
		if ip.is_loopback:
			return True

		for iface in self._interfaces:
			if ip in iface.network:
				return True
		return False

	def isAuthenticated(self, request):
		self._assignLocalNetworks(iNetworkInfo.getConfiguredInterfaces())
		if request.transport:
			#If streamauth is disabled allow all acces from localhost
			try:
				ip = ip_address(request.transport.getPeer().host.decode('utf-8'))
			except ValueError:
				pass
			else:
				# You may get an ipv6 noted ipv4 address like "::ffff:192.168.0.2"
				# In that case it won't match the ipv4 local network so we have to try converting it to plain ipv4
				if ip.version == 6 and ip.ipv4_mapped:
					ip = ip.ipv4_mapped

				if not config.plugins.Webinterface.streamauth.value and ip.is_loopback:
					Log.i("Streaming auth is disabled - Bypassing Authcheck because host '%s' is local!" % str(ip))
					return True
				if not config.plugins.Webinterface.localauth.value and self._isLocalClient(ip):
					Log.i("Local auth is disabled - Bypassing Authcheck because host '%s' is local!" % str(ip))
					return True

		# get the Session from the Request
		http_session = request.getSession().sessionNamespaces

		# if the auth-information has not yet been stored to the http_session
		if 'authenticated' not in http_session:
			if request.getUser() and request.getPassword():
				http_session['authenticated'] = check_passwd(request.getUser(), request.getPassword())
			else:
				http_session['authenticated'] = False

		#if the auth-information already is in the http_session
		else:
			if http_session['authenticated'] is False:
				http_session['authenticated'] = check_passwd(request.getUser(), request.getPassword() )

		#return the current authentication status
		return http_session['authenticated']

#===============================================================================
# Call render of self.resource (if authenticated)
#===============================================================================
	def render(self, request):
		if self.isAuthenticated(request) is True:
			return HTTPRootResource.render(self, request)
		else:
			print("[Webinterface.HTTPAuthResource.render] !!! unauthorized !!!")
			return self.unauthorized(request).render(request)

#===============================================================================
# Override to call getChildWithDefault of self.resource (if authenticated)
#===============================================================================
	def getChildWithDefault(self, path, request):
		if self.isAuthenticated(request) is True:
			return HTTPRootResource.getChildWithDefault(self, path, request)
		else:
			print("[Webinterface.HTTPAuthResource.getChildWithDefault] !!! unauthorized !!!")
			return self.unauthorized(request)

from .auth import check_passwd

global_session = None

#===============================================================================
# sessionstart
# Actions to take place on Session start
#===============================================================================
def sessionstart(reason, session):
	global global_session
	global_session = session
	networkstart(True, session)


def registerBonjourService(protocol, port):
	try:
		from Plugins.Extensions.Bonjour.Bonjour import bonjour

		service = bonjour.buildService(protocol, port)
		bonjour.registerService(service, True)
		print("[WebInterface.registerBonjourService] Service for protocol '%s' with port '%i' registered!" %(protocol, port))
		return True

	except ImportError as e:
		print("[WebInterface.registerBonjourService] %s" %e)
		return False

def unregisterBonjourService(protocol):
	try:
		from Plugins.Extensions.Bonjour.Bonjour import bonjour

		bonjour.unregisterService(protocol)
		print("[WebInterface.unregisterBonjourService] Service for protocol '%s' unregistered!" %(protocol))
		return True

	except ImportError as e:
		print("[WebInterface.unregisterBonjourService] %s" %e)
		return False

def checkBonjour():
	if ( not config.plugins.Webinterface.http.enabled.value ) or ( not config.plugins.Webinterface.enabled.value ):
		unregisterBonjourService('http')
	if ( not config.plugins.Webinterface.https.enabled.value ) or ( not config.plugins.Webinterface.enabled.value ):
		unregisterBonjourService('https')

#===============================================================================
# networkstart
# Actions to take place after Network is up (startup the Webserver)
#===============================================================================
#def networkstart(reason, **kwargs):
def networkstart(reason, session):
	if reason is True:
		startWebserver(session)
		checkBonjour()

	elif reason is False:
		stopWebserver(session)
		checkBonjour()

def openconfig(session, **kwargs):
	session.openWithCallback(configCB, WebIfConfigScreen)

def menu_config(menuid, **kwargs):
	if menuid == "network":
		return [(_("Webinterface"), openconfig, "webif", 60)]
	else:
		return []

def configCB(result, session):
	if result:
		print("[WebIf] config changed")
		restartWebserver(session)
		checkBonjour()
	else:
		print("[WebIf] config not changed")

def Plugins(**kwargs):
	p = PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart)
	p.weight = 100 #webif should start as last plugin
	list = [p,
#			PluginDescriptor(where=[PluginDescriptor.WHERE_NETWORKCONFIG_READ], fnc=networkstart),
			PluginDescriptor(name=_("Webinterface"), description=_("Configuration for the Webinterface"),
							where=PluginDescriptor.WHERE_MENU, icon="plugin.png", fnc=menu_config)]
	if config.plugins.Webinterface.show_in_extensionsmenu.value:
		list.append(PluginDescriptor(name="Webinterface", description=_("Configuration for the Webinterface"),
			where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon="plugin.png", fnc=openconfig))
	return list
