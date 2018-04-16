from DreamboxServerProtocol import DreamboxServerProtocol

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource

class DreamboxWebSocketServer():
	def __init__(self):
		self.session = None
		self._sessions = set()
		self._factory = WebSocketServerFactory(url=None, debug=False, debugCodePaths=False)
		self._factory.setProtocolOptions(autoPingInterval=15, autoPingTimeout=3)
		self._factory.protocol = DreamboxServerProtocol
		self.root = WebSocketResource(self._factory)
		DreamboxServerProtocol.server = None

	def addSession(self, session):
		self._sessions.add(session)

	def removeSession(self, session):
		self._sessions.remove(session)

	def checkSession(self, session):
		return session in self._sessions

	def start(self, session):
		self._session = session
		#protocol
		DreamboxServerProtocol.server = self
		DreamboxServerProtocol.session = session

webSocketServer = DreamboxWebSocketServer()
