from enigma import eServiceReference, iPlayableServicePtr
from Components.Sources.Source import Source
from Components.Converter import ServiceName
from Components.config import config
from Screens.InfoBar import InfoBar, MoviePlayer

from Tools.Log import Log


class SwitchService(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session
		self.info = None
		self.res = (False, _("Obligatory parameter sRef is missing"))

	def handleCommand(self, cmd):
		self.res = self.switchService(cmd)

	def playService(self, ref, root=None):
		from Screens.InfoBar import InfoBar
		if root and InfoBar.instance:
			try:
				InfoBar.instance.servicelist.zap(ref, root)
				return
			except:
				try:
					from types import MethodType

					def zap(self, nref=None, root=None):
						self.revertMode = None
						ref = self.session.nav.getCurrentlyPlayingServiceReference()
						if not nref:
							nref = self.getCurrentSelection()
						if root:
							if not self.preEnterPath(root):
								self.clearPath()
								self.enterPath(eServiceReference(root))
						if ref is None or ref != nref:
							self.new_service_played = True
							self.session.nav.playService(nref)
							self.saveRoot()
							self.saveChannel(nref)
							config.servicelist.lastmode.save()
							self.addToHistory(nref)
					InfoBar.instance.servicelist.zap = MethodType(zap, InfoBar.instance.servicelist)
					InfoBar.instance.servicelist.zap(ref, root)
					return
				except:
					Log.w("Patch failed! Will fallback primitive zap")
					pass
		self.session.nav.playService(ref)

	def switchService(self, cmd):
		print "[SwitchService] ref=%s, root=%s" % (cmd["sRef"], cmd["root"])
		root = cmd["root"]
		if config.plugins.Webinterface.allowzapping.value:
			from Screens.Standby import inStandby
			if inStandby == None:
				if cmd["sRef"]:
					pc = config.ParentalControl.configured.value
					if pc:
						config.ParentalControl.configured.value = False

					eref = eServiceReference(cmd["sRef"])
					if cmd["title"]:
						eref.setName(cmd["title"])

					isRec = eref.getPath()
					isRec = isRec and isRec.startswith("/")
					if not isRec:
						# if this is not a recording and the movie player is open, close it
						if isinstance(self.session.current_dialog, MoviePlayer):
							self.session.current_dialog.lastservice = eref
							self.session.current_dialog.close()
						self.playService(eref, root)
					elif isRec:
						# if this is a recording and the infobar is shown, open the movie player
						if isinstance(self.session.current_dialog, InfoBar):
							self.session.open(MoviePlayer, eref)
						# otherwise just play it with no regard for the context
						else:
							self.playService(eref, root)

					if pc:
						config.ParentalControl.configured.value = pc

					name = cmd["sRef"]
					if cmd["title"] is None:
						service = self.session.nav.getCurrentService()
						info = None
						if isinstance(service, iPlayableServicePtr):
							info = service and service.info()
							ref = None

						if info != None:
							name = ref and info.getName(ref)
							if name is None:
								name = info.getName()
							name.replace('\xc2\x86', '').replace('\xc2\x87', '')
					elif eref.getName() != "":
						name = eref.getName()

					return (True, _("Active service is now '%s'") % name)
				else:
					return (False, _("Obligatory parameter 'sRef' is missing"))
			else:
				return (False, _("Cannot zap while device is in Standby"))
		else:
			return (False, _("Zapping is disabled in WebInterface Configuration"))

	result = property(lambda self: self.res)
