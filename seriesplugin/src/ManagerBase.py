# by betonme @2012

from Tools.BoundFunction import boundFunction

from ModuleBase import ModuleBase


class ManagerBase(ModuleBase):
	def __init__(self):
		ModuleBase.__init__(self)


	################################################
	# Service prototypes
	def getState(self, callback, show_name, season, episode):
		# True: Episode is marked as seen
		# False: Episode is not marked as seen
		callback( False )

	def setState(self, callback, show_name, season, episode, state):
		# state = True: Mark episode as seen
		# state = False: Mark episode as not seen
		callback()
