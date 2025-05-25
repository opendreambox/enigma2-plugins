#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Property GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Property GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Property GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from twisted.internet import reactor
from twisted.web import client
from twisted.web.client import HTTPClientFactory
import urlparse

def url_parse(url, defaultPort=None):
	parsed = urlparse.urlparse(url)
	scheme = parsed[0]
	path = urlparse.urlunparse(('', '') + parsed[2:])
	if defaultPort is None:
		if scheme == 'https':
			defaultPort = 443
		else:
			defaultPort = 80
	host, port = parsed[1], defaultPort
	if ':' in host:
		host, port = host.split(':')
		port = int(port)
	return scheme, host, port, path

class InternetRadioHTTPClientFactory(HTTPClientFactory):
	def __init__(self, url, method='GET', postdata=None, headers=None,
	agent="Internet-Radio", timeout=0, cookies=None,
	followRedirect=1, lastModified=None, etag=None):
		HTTPClientFactory.__init__(self, url, method=method, postdata=postdata,
		headers=headers, agent=agent, timeout=timeout, cookies=cookies,followRedirect=followRedirect)

def sendUrlCommand(url, contextFactory=None, timeout=10, *args, **kwargs):
	scheme, host, port, path = url_parse(url)
	factory = InternetRadioHTTPClientFactory(url, *args, **kwargs)
	if scheme == 'https':
		from twisted.internet import ssl
		if contextFactory is None:
			contextFactory = ssl.ClientContextFactory()
		reactor.connectSSL(host, port, factory, contextFactory, timeout=timeout)
	else:
		reactor.connectTCP(host, port, factory, timeout=timeout)
	return factory.deferred
