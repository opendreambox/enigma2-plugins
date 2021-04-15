# -*- Python -*-
#
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

#
import string
import ircsupport
import e2chat
import dreamIRCTools
import dreamIRCSetup


class AccountManager:
	"""I am responsible for managing a user's accounts.

	That is, remembering what accounts are available, their settings,
	adding and removal of accounts, etc.

	@ivar accounts: A collection of available accounts.
	@type accounts: mapping of strings to L{Account<interfaces.IAccount>}s.
	"""

	def __init__(self, session):
		self.chatui = e2chat.ChatUI()
		self.config = dreamIRCSetup.dreamIRCConfig()
		self.accounts = self.config.load()
		self.pipe = dreamIRCTools.MessagePipe()

	def startConnect(self):
		if self.accounts == False:
			self.pipe.debug("You have defined no valid accounts.")
		else:
			for acct in self.accounts:
				acct.logOn(self.chatui)

	def getSnapShot(self):
		"""A snapshot of all the accounts and their status.

		@returns: A list of tuples, each of the form
			(string:accountName, boolean:isOnline,
			boolean:autoLogin, string:gatewayType)
		"""
		data = []
		for account in self.accounts:
			data.append((account.accountName, account.isOnline(), account.autoLogin, account.gatewayType))
		return data

	def isEmpty(self):
		return len(self.accounts) == 0

	def getConnectionInfo(self):
		if self.accounts == False:
			self.pipe.debug("You have defined no valid accounts.")
			return [0]
		else:
			connectioninfo = []
			for account in self.accounts:
				connectioninfo.append(account.isOnline())
			return connectioninfo

	def addAccount(self, account):
		self.accounts[account.accountName] = account

	def delAccount(self, accountName):
		del self.accounts[accountName]

	def connect(self, accountName, chatui):
		"""
		@returntype: Deferred L{interfaces.IClient}
		"""
		self.pipe.debug("connecting to : %s" % accountName)
		return self.accounts[accountName].logOn(chatui)

	def quit(self):
		pass
