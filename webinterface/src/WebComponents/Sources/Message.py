from Components.Sources.Source import Source
from Screens.MessageBox import MessageBox
from os import unlink
from os.path import isfile


class Message(Source):
	PRINT = 0
	ANSWER = 1
	#TODO FIXME - this could be done with an on-going request that finishes when the answer has been given
	yesnoFile = "/tmp/yesno"

	def __init__(self, session, func=PRINT):
		self.cmd = []
		self.session = session

		self.func = func
		Source.__init__(self)
		error = _("unknown command (%s)") % func
		self.res = (False, error)

	def handleCommand(self, cmd):
		self.cmd = cmd
		if self.func is self.PRINT:
			self.res = self.printMessage(cmd)
		elif self.func is self.ANSWER:
			self.res = self.getYesNoAnswer(cmd)

	def printMessage(self, param):
		print "printMessage"

		if self.cmd['text'] == "" or self.cmd['text'] is None:
			return (False, _("No Messagetext given"))
		else:
			mtext = self.cmd['text']

		try:
			typeint = int(self.cmd['type'])
		except (ValueError, TypeError):
			return (False, _("type %s is not a number") % self.cmd['type'])

		sel = True
		if self.cmd['default'] is not None and self.cmd['default'] == "no":
			sel = False

		if typeint == MessageBox.TYPE_YESNO:
			#dont know how to give the result to the webif back
			mtype = MessageBox.TYPE_YESNO
		elif typeint == MessageBox.TYPE_INFO:
			mtype = MessageBox.TYPE_INFO
		elif typeint == MessageBox.TYPE_WARNING:
			mtype = MessageBox.TYPE_WARNING
		elif typeint == MessageBox.TYPE_ERROR:
			mtype = MessageBox.TYPE_ERROR
		else:
			return (False, _("Unsupported Messagetype %s") % self.cmd['type'])

		try:
			mtimeout = int(self.cmd['timeout'])
		except (ValueError, TypeError):
			mtimeout = -1

		if typeint == MessageBox.TYPE_YESNO:
			self.session.openWithCallback(self.yesNoAnswer, MessageBox, mtext, type=mtype, timeout=mtimeout, default=sel)
		else:
			self.session.open(MessageBox, mtext, type=mtype, timeout=mtimeout)

		return (True, _("Message sent successfully!"))

	def yesNoAnswer(self, confirmed):
		print "yesNoAnswer", confirmed
		#self.session.messageboxanswer = confirmed

		with open(self.yesnoFile, 'w') as f:
			f.write(['no', 'yes'][confirmed])

	def getYesNoAnswer(self, param):
		print "getYesNoAnswer"#,self.session.messageboxanswer
		if isfile(self.yesnoFile) == True:
			with open(self.yesnoFile, 'r') as f:
				data = f.read()
			unlink(self.yesnoFile)
			print "Answer: (%s)" % data
			if data == "yes":
				return (True, "Answer is YES!")
			else:
				return (True, "Answer is NO!")
		else:
			return (False, "No answer in time")

	result = property(lambda self: self.res)
