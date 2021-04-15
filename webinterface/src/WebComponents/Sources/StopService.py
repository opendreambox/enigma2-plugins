from Components.Sources.Source import Source


class StopService(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def pipAvailable(self):
		# pip isn't available in every state of e2
		try:
			self.session.pipshown
			pipavailable = True
		except:
			pipavailable = False
		return pipavailable

	def command(self):
		currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if currentServiceRef is not None:
			text = currentServiceRef.toString()
		else:
			text = "N/A"

		self.session.nav.stopService()
		if self.pipAvailable():
			if self.session.pipshown: # try to disable pip
				self.session.pipshown = False
				self.session.deleteDialog(self.session.pip)
				del self.session.pip

		return text

	text = property(command)
