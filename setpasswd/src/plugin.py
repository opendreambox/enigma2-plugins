from enigma import eConsoleAppContainer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox
from Tools.Log import Log

from Plugins.Plugin import PluginDescriptor

import string
from random import Random 


class ChangePasswordScreen(ChoiceBox):
	WINDOW_TITLE = _("Change Password")
	KEY_SET = "set"
	KEY_RANDOM = "random"
	KEY_LOCK = "lock"
	KEY_REMOVE = "remove"

	def __init__(self, session, user="root"):
		options = [
				(_("Enter a new password"), self.KEY_SET),
				(_("Generate a random password"), self.KEY_RANDOM),
				(_("Disable password-based login"), self.KEY_LOCK),
				(_("Remove password protection (DANGEROUS!)"), self.KEY_REMOVE),
			]
		ChoiceBox.__init__(self, session, title=_("If you want to login to your Dreambox using SSH, FTP or a remote web browser, you need to configure a password first.\nThe username will be '%s'.") % (user), list=options, windowTitle=ChangePasswordScreen.WINDOW_TITLE)
		self._user = user
		self._password = ""
		self._wasLocked = False
		self._container = eConsoleAppContainer()
		self.__appClosed_conn = self._container.appClosed.connect(self._commandFinished)

	def go(self):
		selected = self["list"].l.getCurrentSelection()
		Log.w(selected)
		selected = selected and selected[0]
		if not selected:
			return
		selected = selected[1]
		if selected == self.KEY_SET:
			self.session.openWithCallback(self._onPasswordInputFinished, InputBox, title=_("Please enter a new password for %s") % (self._user), windowTitle=_("New Password"), text=self._getRandom())
			return
		elif selected == self.KEY_RANDOM:
			self._apply(self._getRandom())
		elif selected == self.KEY_LOCK:
			self._lock()
		elif selected == self.KEY_REMOVE:
			self._apply("")

	def _apply(self, password):
		Log.w("Changing password for %s" % (self._user,))
		self._password = password
		if password:
			self._container.execute("echo \"%s:%s\" | chpasswd" % (self._user, password))
		else:
			self._container.execute("passwd -d %s" % self._user)

	def _getRandom(self):
		passwdChars = string.letters + string.digits
		passwdLength = 10
		return ''.join(Random().sample(passwdChars, passwdLength)) 

	def _lock(self):
		Log.w("Removing password for %s" % (self._user))
		self._password = ""
		self._wasLocked = True
		self._container.execute("passwd -l %s" % self._user)

	def _commandFinished(self,retval):
		if retval == 0:
			type = MessageBox.TYPE_INFO
			windowTitle = _("Password changed")
			if self._password:
				message = _("The password for '%s' was successfully changed to:\n\n%s") % (self._user, self._password)
			else:
				type = MessageBox.TYPE_WARNING
				if self._wasLocked:
					windowTitle = _("Password locked")
					message = _("The password for '%s' is now disabled!") % (self._user,)
				else:
					windowTitle = _("Password removed")
					message = _("The password protection for '%s' was removed!") % (self._user,)
		else:
			windowTitle = _("Password change failed!")
			message = _("Unable to set new password for '%s'") % self._user
			type = MessageBox.TYPE_ERROR
		self.session.open(MessageBox, message, type, windowTitle=windowTitle)
		self.close()

	def _onPasswordInputFinished(self, password):
		if password:
			self._apply(password)

def startChange(menuid):
	if menuid != "system": 
		return []
	return [(_("Password"), main, "change_root_passwd", 50)]

def main(session, **kwargs):
	session.open(ChangePasswordScreen)

def Plugins(**kwargs):
	return PluginDescriptor(
		name=ChangePasswordScreen.WINDOW_TITLE,
		description=_("Change or reset the root password of your dreambox"),
		where=[PluginDescriptor.WHERE_MENU], fnc=startChange)
