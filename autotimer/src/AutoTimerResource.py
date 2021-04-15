# -*- coding: UTF-8 -*-
from AutoTimer import AutoTimer
from AutoTimerConfiguration import CURRENT_CONFIG_VERSION
from RecordTimer import AFTEREVENT
from twisted.internet import reactor
from twisted.web import http, resource, server
import threading
try:
	from urllib import unquote
except ImportError as ie:
	from urllib.parse import unquote
from ServiceReference import ServiceReference
from Tools.XMLTools import stringToXML
from enigma import eServiceReference
from . import config, iteritems, plugin
from plugin import autotimer, AUTOTIMER_VERSION

API_VERSION = "1.6"


class AutoTimerBaseResource(resource.Resource):
	def returnResult(self, req, state, statetext):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2simplexmlresult>
	<e2state>%s</e2state>
	<e2statetext>%s</e2statetext>
</e2simplexmlresult>""" % ('True' if state else 'False', statetext)


class AutoTimerBackgroundThread(threading.Thread):
	def __init__(self, req, fnc):
		threading.Thread.__init__(self)
		self._req = req
		if hasattr(req, 'notifyFinish'):
			req.notifyFinish().addErrback(self.connectionLost)
		self._stillAlive = True
		self._fnc = fnc
		self.start()

	def connectionLost(self, err):
		self._stillAlive = False

	def run(self):
		req = self._req
		code = http.OK
		try:
			ret = self._fnc(req)
		except Exception as e:
			ret = str(e)
			code = http.INTERNAL_SERVER_ERROR

		def finishRequest():
			req.setResponseCode(code)
			if code == http.OK:
				req.setHeader('Content-type', 'application/xhtml+xml')
			req.setHeader('charset', 'UTF-8')
			req.write(ret)
			req.finish()
		if self._stillAlive:
			reactor.callFromThread(finishRequest)


class AutoTimerBackgroundingResource(AutoTimerBaseResource, threading.Thread):
	def render(self, req):
		AutoTimerBackgroundThread(req, self.renderBackground)
		return server.NOT_DONE_YET

	def renderBackground(self, req):
		pass


class AutoTimerDoParseResource(AutoTimerBaseResource):
	def render(self, req):
		self._req = req
		self._stillAlive = True
		if hasattr(req, 'notifyFinish'):
			req.notifyFinish().addErrback(self.connectionLost)

		d = autotimer.parseEPGAsync().addCallback(self.epgCallback).addErrback(self.epgErrback)

		def timeout():
			if not d.called and self._stillAlive:
				reactor.callFromThread(lambda: req.write("<ignore />"))
				reactor.callLater(50, timeout)
		reactor.callLater(50, timeout)

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		req.write("""<?xml version=\"1.0\" encoding=\"UTF-8\" ?><e2simplexmlresult>""")
		return server.NOT_DONE_YET

	def connectionLost(self, err):
		self._stillAlive = False

	def epgCallback(self, ret):
		if self._stillAlive:
			ret = """<e2state>True</e2state>
	<e2statetext>""" + \
	_("Found a total of %(matches)d matching Events.\n%(timer)d Timer were added and\n%(modified)d modified,\n%(conflicts)d conflicts encountered,\n%(similars)d similars added.") % \
	{"matches": ret[0], "timer": ret[1], "modified": ret[2], "conflicts": len(ret[4]), "similars": len(ret[5])} \
	+ "</e2statetext></e2simplexmlresult>"

			def finishRequest():
				self._req.write(ret)
				self._req.finish()
			reactor.callFromThread(finishRequest)

	def epgErrback(self, failure):
		if self._stillAlive:
			ret = """<e2state>False</e2state>
	<e2statetext>""" + _("AutoTimer failed with error %s") % (str(failure),) + "</e2statetext></e2simplexmlresult>"

			def finishRequest():
				self._req.write(ret)
				self._req.finish()
			reactor.callFromThread(finishRequest)


class AutoTimerSimulateBackgroundThread(AutoTimerBackgroundThread):
	def run(self):
		req = self._req
		if self._stillAlive:
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'application/xhtml+xml')
			req.setHeader('charset', 'UTF-8')
			reactor.callFromThread(lambda: req.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<e2autotimersimulate api_version=\"" + str(API_VERSION) + "\">\n"))

		def finishRequest():
			req.write('</e2autotimersimulate>')
			req.finish()

		try:
			autotimer.parseEPG(simulateOnly=True, callback=self.intermediateWrite)
		except Exception as e:
			def finishRequest():
				req.write('<exception>' + str(e) + '</exception><|PURPOSEFULLYBROKENXML<')
				req.finish()

		if self._stillAlive:
			reactor.callFromThread(finishRequest)

	def intermediateWrite(self, timers, conflicting, similar, skipped):
		returnlist = []
		extend = returnlist.extend

		for (name, begin, end, serviceref, autotimername, message) in timers:
			ref = ServiceReference(str(serviceref))
			extend((
				'<e2simulatedtimer>\n'
				'   <e2servicereference>', stringToXML(serviceref), '</e2servicereference>\n',
				'   <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
				'   <e2name>', stringToXML(name), '</e2name>\n',
				'   <e2timebegin>', str(begin), '</e2timebegin>\n',
				'   <e2timeend>', str(end), '</e2timeend>\n',
				'   <e2autotimername>', stringToXML(autotimername), '</e2autotimername>\n'
				'</e2simulatedtimer>\n'
			))

		if self._stillAlive:
			reactor.callFromThread(lambda: self._req.write(''.join(returnlist)))


class AutoTimerTestBackgroundThread(AutoTimerBackgroundThread):
	def run(self):
		req = self._req
		if self._stillAlive:
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'application/xhtml+xml')
			req.setHeader('charset', 'UTF-8')
			reactor.callFromThread(lambda: req.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<e2autotimersimulate api_version=\"" + str(API_VERSION) + "\">\n"))

		def finishRequest():
			req.write('</e2autotimersimulate>')
			req.finish()

		id = req.args.get("id")
		if id:
			self.id = int(id[0])
		else:
			self.id = None
		
		try:
			autotimer.parseEPG(simulateOnly=True, uniqueId=self.id, callback=self.intermediateWrite)
		except Exception as e:
			def finishRequest():
				req.write('<exception>' + str(e) + '</exception><|PURPOSEFULLYBROKENXML<')
				req.finish()

		if self._stillAlive:
			reactor.callFromThread(finishRequest)

	def intermediateWrite(self, timers, conflicting, similar, skipped):
		returnlist = []
		extend = returnlist.extend

		for (name, begin, end, serviceref, autotimername, message) in timers:
			ref = ServiceReference(str(serviceref))
			extend((
				'<e2simulatedtimer>\n'
				'   <e2servicereference>', stringToXML(serviceref), '</e2servicereference>\n',
				'   <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
				'   <e2name>', stringToXML(name), '</e2name>\n',
				'   <e2timebegin>', str(begin), '</e2timebegin>\n',
				'   <e2timeend>', str(end), '</e2timeend>\n',
				'   <e2autotimername>', stringToXML(autotimername), '</e2autotimername>\n',
				'   <e2state>OK</e2state>\n'
				'   <e2message>', stringToXML(message), '</e2message>\n'
				'</e2simulatedtimer>\n'
			))

		if skipped:
			for (name, begin, end, serviceref, autotimername, message) in skipped:
				ref = ServiceReference(str(serviceref))
				extend((
					'<e2simulatedtimer>\n'
					'   <e2servicereference>', stringToXML(serviceref), '</e2servicereference>\n',
					'   <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
					'   <e2name>', stringToXML(name), '</e2name>\n',
					'   <e2timebegin>', str(begin), '</e2timebegin>\n',
					'   <e2timeend>', str(end), '</e2timeend>\n',
					'   <e2autotimername>', stringToXML(autotimername), '</e2autotimername>\n',
					'   <e2state>Skip</e2state>\n'
					'   <e2message>', stringToXML(message), '</e2message>\n'
					'</e2simulatedtimer>\n'
				))
		
		if self._stillAlive:
			reactor.callFromThread(lambda: self._req.write(''.join(returnlist)))


class AutoTimerSimulateResource(AutoTimerBaseResource):
	def render(self, req):
		AutoTimerSimulateBackgroundThread(req, None)
		return server.NOT_DONE_YET


class AutoTimerTestResource(AutoTimerBaseResource):
	def render(self, req):
		AutoTimerTestBackgroundThread(req, None)
		return server.NOT_DONE_YET


class AutoTimerListAutoTimerResource(AutoTimerBaseResource):
	def render(self, req):
		# We re-read the config so we won't display empty or wrong information
		try:
			autotimer.readXml()
		except Exception as e:
			return self.returnResult(req, False, _("Couldn't load config file!") + '\n' + str(e))
		webif = True
		p = req.args.get('webif')
		if p:
			webif = not(p[0] == "false")
		# show xml
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return ''.join(autotimer.getXml(webif))


class AutoTimerRemoveAutoTimerResource(AutoTimerBaseResource):
	def render(self, req):
		id = req.args.get("id")
		if id:
			autotimer.remove(int(id[0]))
			
			# Save modified xml
			if config.plugins.autotimer.always_write_config.value:
				autotimer.writeXml()
			
			return self.returnResult(req, True, _("AutoTimer was removed"))
		else:
			return self.returnResult(req, False, _("missing parameter \"id\""))
			

class AutoTimerAddXMLAutoTimerResource(AutoTimerBaseResource):
	def render_POST(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml;')
		req.setHeader('charset', 'UTF-8')
		autotimer.readXml() # read current timers to ensure autotimer.timers is populated with current autotimers
		autotimer.readXmlTimer(req.args['xml'][0])
		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()
		return self.returnResult(req, True, _("AutoTimer was added successfully"))
		

class AutoTimerUploadXMLConfigurationAutoTimerResource(AutoTimerBaseResource):
	def render_POST(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml;')
		req.setHeader('charset', 'UTF-8')	
		autotimer.readXml(xml_string=req.args['xml'][0])
		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()
		return self.returnResult(req, True, _("AutoTimers were changed successfully"))	


class AutoTimerAddOrEditAutoTimerResource(AutoTimerBaseResource):
	# TODO: recheck if we can modify regular config parser to work on this
	# TODO: allow to edit defaults?
	def render(self, req):
		def get(name, default=None):
			ret = req.args.get(name)
			return ret[0] if ret else default

		id = get("id")
		timer = None
		newTimer = True
		if id is None:
			id = autotimer.getUniqueId()
			timer = autotimer.defaultTimer.clone()
			timer.id = id
		else:
			id = int(id)
			for possibleMatch in autotimer.getTimerList():
				if possibleMatch.id == id:
					timer = possibleMatch
					newTimer = False
					break
			if timer is None:
				return self.returnResult(req, False, _("unable to find timer with id %i" % (id,)))

		if id != -1:
			# Match
			timer.match = unquote(get("match", timer.match))
			if not timer.match:
				return self.returnResult(req, False, _("autotimers need a match attribute"))

			# Name
			timer.name = unquote(get("name", timer.name)).strip()
			if not timer.name:
				timer.name = timer.match

			# Enabled
			enabled = get("enabled")
			if enabled is not None:
				try:
					enabled = int(enabled)
				except ValueError:
					enabled = enabled == "yes"
				timer.enabled = enabled

			# Timeframe
			before = get("before")
			after = get("after")
			if before and after:
				timer.timeframe = (int(after), int(before))
			elif before == '' or after == '':
				timer.timeframe = None

		# ...
		timer.searchType = get("searchType", timer.searchType)
		timer.searchCase = get("searchCase", timer.searchCase)

		# Alternatives
		timer.overrideAlternatives = int(get("overrideAlternatives", timer.overrideAlternatives))

		# Justplay
		justplay = get("justplay")
		if justplay is not None:
			try:
				justplay = int(justplay)
			except ValueError:
				justplay = justplay == "zap"
			timer.justplay = justplay
		setEndtime = get("setEndtime")
		if setEndtime is not None:
			timer.setEndtime = int(setEndtime)

		# Timespan
		start = get("timespanFrom")
		end = get("timespanTo")
		if start and end:
			start = [int(x) for x in start.split(':')]
			end = [int(x) for x in end.split(':')]
			timer.timespan = (start, end)
		elif start == '' and end == '':
			timer.timespan = None

		# Services
		servicelist = get("services")
		if servicelist is not None:
			servicelist = unquote(servicelist).split(',')
			appendlist = []
			for value in servicelist:
				myref = eServiceReference(str(value))
				if not (myref.flags & eServiceReference.isGroup):
					# strip all after last :
					pos = value.rfind(':')
					if pos != -1:
						if value[pos - 1] == ':':
							pos -= 1
						value = value[:pos + 1]

				if myref.valid():
					appendlist.append(value)
			timer.services = appendlist

		# Bouquets
		servicelist = get("bouquets")
		if servicelist is not None:
			servicelist = unquote(servicelist).split(',')
			while '' in servicelist:
				servicelist.remove('')
			timer.bouquets = servicelist

		# Offset
		offset = get("offset")
		if offset:
			offset = offset.split(',')
			if len(offset) == 1:
				before = after = int(offset[0] or 0) * 60
			else:
				before = int(offset[0] or 0) * 60
				after = int(offset[1] or 0) * 60
			timer.offset = (before, after)
		elif offset == '':
			timer.offset = None

		# AfterEvent
		afterevent = get("afterevent")
		if afterevent:
			if afterevent == "default":
				timer.afterevent = []
			else:
				try:
					afterevent = int(afterevent)
				except ValueError:
					afterevent = {
						"nothing": AFTEREVENT.NONE,
						"deepstandby": AFTEREVENT.DEEPSTANDBY,
						"standby": AFTEREVENT.STANDBY,
						"auto": AFTEREVENT.AUTO
					}.get(afterevent, AFTEREVENT.AUTO)
				start = get("aftereventFrom")
				end = get("aftereventTo")
				if start and end:
					start = [int(x) for x in start.split(':')]
					end = [int(x) for x in end.split(':')]
					timer.afterevent = [(afterevent, (start, end))]
				else:
					timer.afterevent = [(afterevent, None)]

		# Maxduration
		maxduration = get("maxduration")
		if maxduration:
			timer.maxduration = int(maxduration) * 60
		elif maxduration == '':
			timer.maxduration = None

		# Includes
		title = req.args.get("title")
		shortdescription = req.args.get("shortdescription")
		description = req.args.get("description")
		dayofweek = req.args.get("dayofweek")
		if title or shortdescription or description or dayofweek:
			includes = timer.include
			title = [unquote(x) for x in title] if title else includes[0]
			shortdescription = [unquote(x) for x in shortdescription] if shortdescription else includes[1]
			description = [unquote(x) for x in description] if description else includes[2]
			dayofweek = [unquote(x) for x in dayofweek] if dayofweek else includes[3]
			while '' in title:
				title.remove('')
			while '' in shortdescription:
				shortdescription.remove('')
			while '' in description:
				description.remove('')
			while '' in dayofweek:
				dayofweek.remove('')
			timer.include = (title, shortdescription, description, dayofweek)

		# Excludes
		title = req.args.get("!title")
		shortdescription = req.args.get("!shortdescription")
		description = req.args.get("!description")
		dayofweek = req.args.get("!dayofweek")
		if title or shortdescription or description or dayofweek:
			excludes = timer.exclude
			title = [unquote(x) for x in title] if title else excludes[0]
			shortdescription = [unquote(x) for x in shortdescription] if shortdescription else excludes[1]
			description = [unquote(x) for x in description] if description else excludes[2]
			dayofweek = [unquote(x) for x in dayofweek] if dayofweek else excludes[3]
			while '' in title:
				title.remove('')
			while '' in shortdescription:
				shortdescription.remove('')
			while '' in description:
				description.remove('')
			while '' in dayofweek:
				dayofweek.remove('')
			timer.exclude = (title, shortdescription, description, dayofweek)

		tags = req.args.get("tag")
		if tags:
			while '' in tags:
				tags.remove('')
			timer.tags = [unquote(x) for x in tags]

		timer.matchCount = int(get("counter", timer.matchCount))
		timer.matchFormatString = get("counterFormat", timer.matchFormatString)
		if id != -1:
			matchLeft = get("left")
			timer.matchLeft = int(matchLeft) if matchLeft else (timer.matchCount if newTimer else timer.matchLeft)
			timer.matchLimit = get("lastActivation", timer.matchLimit)
			timer.lastBegin = int(get("lastBegin", timer.lastBegin))

		timer.avoidDuplicateDescription = int(get("avoidDuplicateDescription", timer.avoidDuplicateDescription))
		timer.searchForDuplicateDescription = int(get("searchForDuplicateDescription", timer.searchForDuplicateDescription))
		timer.destination = get("location", timer.destination) or None

		# vps
		enabled = get("vps_enabled")
		if enabled is not None:
			try:
				enabled = int(enabled)
			except ValueError:
				enabled = enabled == "yes"
			timer.vps_enabled = enabled
		vps_overwrite = get("vps_overwrite")
		if vps_overwrite is not None:
			try:
				vps_overwrite = int(vps_overwrite)
			except ValueError:
				vps_overwrite = vps_overwrite == "yes"
			timer.vps_overwrite = vps_overwrite
		if not timer.vps_enabled and timer.vps_overwrite:
			timer.vps_overwrite = False

		# SeriesPlugin
		series_labeling = get("series_labeling")
		if series_labeling is not None:
			try:
				series_labeling = int(series_labeling)
			except ValueError:
				series_labeling = series_labeling == "yes"
			timer.series_labeling = series_labeling
		series_save_filter = get("series_save_filter")
		if series_save_filter is not None:
			try:
				series_save_filter = int(series_save_filter)
			except ValueError:
				series_save_filter = series_save_filter == "yes"
			timer.series_save_filter = series_save_filter
		if not timer.series_labeling and timer.series_save_filter:
			timer.series_save_filter = False

		if newTimer:
			autotimer.add(timer)
			message = _("AutoTimer was added successfully")
		else:
			message = _("AutoTimer was changed successfully")
		
		# Save modified xml
		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()

		return self.returnResult(req, True, message)


class AutoTimerChangeSettingsResource(AutoTimerBaseResource):
	def render(self, req):
		for key, value in iteritems(req.args):
			value = value[0]
			if key == "autopoll":
				config.plugins.autotimer.autopoll.value = True if value == "true" else False
			elif key == "interval":
				config.plugins.autotimer.interval.value = int(value)
			elif key == "refresh":
				config.plugins.autotimer.refresh.value = value
			elif key == "try_guessing":
				config.plugins.autotimer.try_guessing.value = True if value == "true" else False
			elif key == "editor":
				config.plugins.autotimer.editor.value = value
			elif key == "disabled_on_conflict":
				config.plugins.autotimer.disabled_on_conflict.value = True if value == "true" else False
			elif key == "addsimilar_on_conflict":
				config.plugins.autotimer.addsimilar_on_conflict.value = True if value == "true" else False
			elif key == "show_in_extensionsmenu":
				config.plugins.autotimer.show_in_extensionsmenu.value = True if value == "true" else False
			elif key == "fastscan":
				config.plugins.autotimer.fastscan.value = True if value == "true" else False
			elif key == "notifconflict":
				config.plugins.autotimer.notifconflict.value = True if value == "true" else False
			elif key == "notifsimilar":
				config.plugins.autotimer.notifsimilar.value = True if value == "true" else False
			elif key == "maxdaysinfuture":
				config.plugins.autotimer.maxdaysinfuture.value = int(value)
			elif key == "add_autotimer_to_tags":
				config.plugins.autotimer.add_autotimer_to_tags.value = True if value == "true" else False
			elif key == "add_name_to_tags":
				config.plugins.autotimer.add_name_to_tags.value = True if value == "true" else False
			elif key == "timeout":
				config.plugins.autotimer.timeout.value = int(value)
			elif key == "delay":
				config.plugins.autotimer.delay.value = int(value)
			elif key == "editdelay":
				config.plugins.autotimer.editdelay.value = int(value)
			elif key == "skip_during_records":
				config.plugins.autotimer.skip_during_records.value = True if value == "true" else False
			elif key == "skip_during_epgrefresh":
				config.plugins.autotimer.skip_during_epgrefresh.value = True if value == "true" else False

		if config.plugins.autotimer.autopoll.value:
			if plugin.autopoller is None:
				from AutoPoller import AutoPoller
				plugin.autopoller = AutoPoller()
			plugin.autopoller.start(initial=False)
		else:
			if plugin.autopoller is not None:
				plugin.autopoller.stop()
				plugin.autopoller = None

		return self.returnResult(req, True, _("config changed."))


class AutoTimerSettingsResource(resource.Resource):
	def render(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		try:
			from Plugins.SystemPlugins.vps import Vps
		except ImportError as ie:
			hasVps = False
		else:
			hasVps = True

		try:
			from Plugins.Extensions.SeriesPlugin.plugin import Plugins
		except ImportError as ie:
			hasSeriesPlugin = False
		else:
			hasSeriesPlugin = True

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2settings>
	<e2setting>
		<e2settingname>config.plugins.autotimer.autopoll</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.interval</e2settingname>
		<e2settingvalue>%d</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.refresh</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.try_guessing</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.editor</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.disabled_on_conflict</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.addsimilar_on_conflict</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.show_in_extensionsmenu</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.fastscan</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.notifconflict</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.notifsimilar</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.maxdaysinfuture</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.add_autotimer_to_tags</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.add_name_to_tags</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.timeout</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.delay</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.editdelay</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.skip_during_records</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.skip_during_epgrefresh</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>hasVps</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>hasSeriesPlugin</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>version</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>api_version</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>autotimer_version</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
</e2settings>""" % (
				config.plugins.autotimer.autopoll.value,
				config.plugins.autotimer.interval.value,
				config.plugins.autotimer.refresh.value,
				config.plugins.autotimer.try_guessing.value,
				config.plugins.autotimer.editor.value,
				config.plugins.autotimer.addsimilar_on_conflict.value,
				config.plugins.autotimer.disabled_on_conflict.value,
				config.plugins.autotimer.show_in_extensionsmenu.value,
				config.plugins.autotimer.fastscan.value,
				config.plugins.autotimer.notifconflict.value,
				config.plugins.autotimer.notifsimilar.value,
				config.plugins.autotimer.maxdaysinfuture.value,
				config.plugins.autotimer.add_autotimer_to_tags.value,
				config.plugins.autotimer.add_name_to_tags.value,
				config.plugins.autotimer.timeout.value,
				config.plugins.autotimer.delay.value,
				config.plugins.autotimer.editdelay.value,
				config.plugins.autotimer.skip_during_records.value,
				config.plugins.autotimer.skip_during_epgrefresh.value,
				hasVps,
				hasSeriesPlugin,
				CURRENT_CONFIG_VERSION,
				API_VERSION,
				AUTOTIMER_VERSION
			)
