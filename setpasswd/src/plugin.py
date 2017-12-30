from enigma import eConsoleAppContainer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Screens.Setup import SetupSummary
from Components.ConfigList import ConfigList
from Components.config import config, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigText

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from enigma import getDesktop

import string
import sys 
import time
from random import Random 

setpasswd_title=_("Change Root Password")

sz_w = getDesktop(0).size().width()  

class ChangePasswdScreen(Screen):
	if sz_w == 1920:  
		skin = """
		<screen name="ChangePasswdScreen" position="center,center" size="1200,150" title="Change Root Password">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="295,70" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="305,5" size="295,70" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="600,5" size="295,70" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="895,5" size="295,70" />
			<widget backgroundColor="#9f1313" font="Regular;30" halign="center" position="10,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_red" transparent="1" valign="center" zPosition="1" />
			<widget backgroundColor="#1f771f" font="Regular;30" halign="center" position="305,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_green" transparent="1" valign="center" zPosition="1" />
			<widget backgroundColor="#a08500" font="Regular;30" halign="center" position="600,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_yellow" transparent="1" valign="center" zPosition="1" />
			<widget backgroundColor="#18188b" font="Regular;30" halign="center" position="895,5" render="Label" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="295,70" source="key_blue" transparent="1" valign="center" zPosition="1" />
			<eLabel backgroundColor="grey" position="10,80" size="1180,1" />
			<widget name="passwd" position="10,90" size="1180,45" />
		</screen>"""
	else:
		skin="""
		<screen name="ChangePasswdScreen" position="center,center" size="820,100" title="Change Root Password" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on" />
			<widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2" />
			<eLabel position="10,50" size="800,1" backgroundColor="grey" />
			<widget name="passwd" position="10,60" size="800,45" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args = 0):
		Screen.__init__(self, session)
		self.skin = ChangePasswdScreen.skin

		self.user="root"
		self.output_line = ""
		self.list = []

		self.onShown.append(self.setWindowTitle)
		
		self["passwd"] = ConfigList(self.list)
		self["key_red"] = StaticText(_("Password")+" "+_("delete").lower())
		self["key_green"] = StaticText(_("Set Password"))
		self["key_yellow"] = StaticText(_("new Random"))
		self["key_blue"] = StaticText(_("virt. Keyboard"))

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
				{
						"exit": self.close,
						"red": self.emptyPasswd,
						"green": self.SetPasswd,
						"yellow": self.newRandom,
						"blue": self.bluePressed,
						"cancel": self.close
				}, -1)
	
		self.buildList(self.GeneratePassword())

	def setWindowTitle(self):
		if config.usage.setup_level.value != "expert":
			p=open("/etc/shadow","r")
			rp=p.readline()
			p.close()
			if not rp.startswith("root::"): # root password already set but not expert ...
				message=_("Unable to change/reset password for %s user") % self.user
				type=MessageBox.TYPE_ERROR
				self.session.open(MessageBox, message , type)
				self.close()
		else:
			self.setTitle(setpasswd_title)

	def newRandom(self):
		self.buildList(self.GeneratePassword())
	
	def buildList(self, password):
		self.password=password
		self.list = []
		self.list.append(getConfigListEntry(_('Enter new Password'), ConfigText(default = self.password, fixed_size = False)))
		self["passwd"].setList(self.list)
		
	def GeneratePassword(self): 
		passwdChars = string.letters + string.digits
		passwdLength = 8
		return ''.join(Random().sample(passwdChars, passwdLength)) 

	def SetPasswd(self):
		print "Changing password for %s to %s" % (self.user,self.password) 
		self.container = eConsoleAppContainer()
		self.appClosed_conn = self.container.appClosed.connect(self.runFinished)
		self.container.execute("echo \"%s:%s\" | chpasswd" % (self.user,self.password))

	def emptyPasswd(self):
		print "Emptying password for %s" % (self.user) 
		self.password=_("empty")
		self.container = eConsoleAppContainer()
		self.appClosed_conn = self.container.appClosed.connect(self.runFinished)
		self.container.execute("passwd -d %s" % self.user)

	def runFinished(self,retval):
		if retval==0:
			message=_("Sucessfully changed password for %s user to: %s") % (self.user, self.password)
			type=MessageBox.TYPE_INFO
		else:
			message=_("Unable to change/reset password for %s user") % self.user
			type=MessageBox.TYPE_ERROR
		self.session.open(MessageBox, message , type)
		del self.container
		self.close()
		
	def bluePressed(self):
		self.session.openWithCallback(self.VirtualKeyBoardTextEntry, VirtualKeyBoard, title = (_("Enter your password here:")), text = self.password)
	
	def VirtualKeyBoardTextEntry(self, callback = None):
		if callback is not None and len(callback):
			self.buildList(callback)

def startChange(menuid):
	if menuid != "system": 
		return [ ]
	return [(setpasswd_title, main, "change_root_passwd", 50)]

def main(session, **kwargs):
	session.open(ChangePasswdScreen)

def Plugins(**kwargs):
	return PluginDescriptor(
		name=setpasswd_title,  
		description=_("Change or reset the root password of your dreambox"),
		where = [PluginDescriptor.WHERE_MENU], fnc = startChange)
	