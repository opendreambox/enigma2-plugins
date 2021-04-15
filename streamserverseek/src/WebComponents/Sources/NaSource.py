from Components.Sources.Source import Source


class NaSource(Source):
	na = ""

	def __init__(self, na):
		Source.__init__(self)
		self.na = na
		
	def handleCommand(self, params):
		return
	
	def getResult(self):
		return (False, self.na)

	result = property(getResult)
