# -*- coding: utf-8 -*-
# for localized messages
#from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigIP, NoSave, ConfigText, ConfigOnOff, ConfigPassword, ConfigSelection, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import ePoint
from AutoMount import iAutoMount
from re import sub as re_sub

class AutoMountEdit(Screen, ConfigListScreen):
        skin = """
                <screen name="AutoMountEdit" position="center,center" size="560,450" title="MountEdit">
                        <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
                        <widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
                        <widget name="config" position="5,50" size="550,250" zPosition="1" scrollbarMode="showOnDemand" />
                        <ePixmap pixmap="skin_default/div-h.png" position="0,420" zPosition="1" size="560,2" />
                        <widget source="introduction" render="Label" position="10,430" size="540,21" zPosition="10" font="Regular;21" halign="center" valign="center" backgroundColor="#25062748" transparent="1"/>
                        <widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="10,430" zPosition="10" size="35,25" transparent="1" alphatest="on" />
                        <widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="160,350" zPosition="1" size="1,1" transparent="1" alphatest="on" />
                </screen>"""

        def __init__(self, session, plugin_path, mountinfo = None ):
                self.skin_path = plugin_path
                self.session = session
                Screen.__init__(self, self.session)
                ConfigListScreen.__init__(self, [],session = session)

                self.mountinfo = mountinfo
                if self.mountinfo is None:
                        #Initialize default mount data (using nfs default options)
                        self.mountinfo = iAutoMount.DEFAULT_OPTIONS_NFS

                self._applyConfigMsgBox = None
                self.updateConfigRef = None
                self.mounts = iAutoMount.getMounts()
                self.createConfig()

                self["actions"] = NumberActionMap(["SetupActions"],
                {
                        "ok": self.ok,
                        "back": self.close,
                        "cancel": self.close,
                        "red": self.close,
                }, -2)

                self["VirtualKB"] = ActionMap(["VirtualKeyboardActions"],
                {
                        "showVirtualKeyboard": self.KeyText,
                }, -2)

                self.createSetup()
                self.onLayoutFinish.append(self.layoutFinished)
                # Initialize Buttons
                self["VKeyIcon"] = Pixmap()
                self["HelpWindow"] = Pixmap()
                self["introduction"] = StaticText(_("Press OK to activate the settings."))
                self["key_red"] = StaticText(_("Cancel"))


        def layoutFinished(self):
                self.setTitle(_("Mounts editor"))
                self["VKeyIcon"].hide()
                self["VirtualKB"].setEnabled(False)
                self["HelpWindow"].hide()

        # helper function to convert ips from a sring to a list of ints
        def convertIP(self, ip):
                strIP = ip.split('.')
                ip = []
                for x in strIP:
                        ip.append(int(x))
                return ip

        def exit(self):
                self.close()

        def createConfig(self):
                self.sharetypelist = []
                self.sharetypelist.append(("nfs", _("NFS share")))
                self.sharetypelist.append(("cifs", _("CIFS share")))

                mounttype = self.mountinfo['mounttype']
                active = self.mountinfo['active']
                ip = self.convertIP(self.mountinfo['ip'])
                sharename = self.mountinfo['sharename']
                sharedir = self.mountinfo['sharedir']
                options = self.mountinfo['options']
                username = self.mountinfo['username']
                password = self.mountinfo['password']
                hdd_replacement = self.mountinfo['hdd_replacement']
                if mounttype == "nfs":
                        defaultOptions = iAutoMount.DEFAULT_OPTIONS_NFS['options']
                else:
                        defaultOptions = iAutoMount.DEFAULT_OPTIONS_CIFS['options']

                self._cfgActive = NoSave(ConfigOnOff(default = active))
                self._cfgIp = NoSave(ConfigIP(default = ip))
                self._cfgSharename = NoSave(ConfigText(default = sharename, visible_width = 50, fixed_size = False))
                self._cfgSharedir = NoSave(ConfigText(default = sharedir, visible_width = 50, fixed_size = False))
                self._cfgOptions = NoSave(ConfigText(default = defaultOptions, visible_width = 50, fixed_size = False))
                if options is not False:
                        self._cfgOptions.value = options
                self._cfgUsername = NoSave(ConfigText(default = username, visible_width = 50, fixed_size = False))
                self._cfgPassword = NoSave(ConfigPassword(default = password, visible_width = 50, fixed_size = False))
                self._cfgMounttype = NoSave(ConfigSelection(self.sharetypelist, default = mounttype ))
                self._cfgHddReplacement = NoSave(ConfigYesNo(default = hdd_replacement))

        def createSetup(self):
            if self._cfgOptions.value == self._cfgOptions.default:
                if self._cfgMounttype.value == "nfs":
                        self._cfgOptions = NoSave(ConfigText(default = iAutoMount.DEFAULT_OPTIONS_NFS['options'], visible_width = 50, fixed_size = False))
                else:
                        self._cfgOptions = NoSave(ConfigText(default = iAutoMount.DEFAULT_OPTIONS_CIFS['options'], visible_width = 50, fixed_size = False))
            optionsEntry = getConfigListEntry(_("Mount options"), self._cfgOptions)

            lst = [
                getConfigListEntry(_("Active"), self._cfgActive),
                getConfigListEntry(_("Local share name"), self._cfgSharename),
                getConfigListEntry(_("Mount type"), self._cfgMounttype),
                getConfigListEntry(_("Server IP"), self._cfgIp),
                getConfigListEntry(_("Server share"), self._cfgSharedir),
                getConfigListEntry(_("use as HDD replacement"), self._cfgHddReplacement),
                optionsEntry,
            ]
            if self._cfgMounttype.value == "cifs":
                lst.extend([
                    getConfigListEntry(_("Username"), self._cfgUsername),
                    getConfigListEntry(_("Password"), self._cfgPassword)
                ])
            self["config"].list = lst
            self["config"].onSelectionChanged.append(self.selectionChanged)

        def newConfig(self):
                if self["config"].getCurrent()[1] == self._cfgMounttype:
                        self.createSetup()

        def KeyText(self):
                current = self["config"].getCurrent()[1]
                if current == self._cfgSharename:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'sharename'), VirtualKeyBoard, title = (_("Enter share name:")), text = self._cfgSharename.value)
                elif current == self._cfgSharedir:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'sharedir'), VirtualKeyBoard, title = (_("Enter share directory:")), text = self._cfgSharedir.value)
                elif current == self._cfgOptions:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'options'), VirtualKeyBoard, title = (_("Enter options:")), text = self._cfgOptions.value)
                elif current == self._cfgUsername:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'username'), VirtualKeyBoard, title = (_("Enter username:")), text = self._cfgUsername.value)
                elif current == self._cfgPassword:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'password'), VirtualKeyBoard, title = (_("Enter password:")), text = self._cfgPassword.value)

        def VirtualKeyBoardCallback(self, callback = None, entry = None):
                if callback is not None and len(callback) and entry is not None and len(entry):
                        if entry == 'sharename':
                                self._cfgSharename.setValue(callback)
                                self["config"].invalidate(self._cfgSharename)
                        elif entry == 'sharedir':
                                self._cfgSharedir.setValue(callback)
                                self["config"].invalidate(self._cfgSharedir)
                        elif entry == 'options':
                                self._cfgOptions.setValue(callback)
                                self["config"].invalidate(self._cfgOptions)
                        elif entry == 'username':
                                self._cfgUsername.setValue(callback)
                                self["config"].invalidate(self._cfgUsername)
                        elif entry == 'password':
                                self._cfgPassword.setValue(callback)
                                self["config"].invalidate(self._cfgPassword)

        def keyLeft(self):
                ConfigListScreen.keyLeft(self)
                self.newConfig()

        def keyRight(self):
                ConfigListScreen.keyRight(self)
                self.newConfig()

        def selectionChanged(self):
                current = self["config"].getCurrent()[1]
                if current == self._cfgActive or current == self._cfgIp or current == self._cfgMounttype or current == self._cfgHddReplacement:
                        self["VKeyIcon"].hide()
                else:
                        self["VKeyIcon"].show()

        def ok(self):
                sharename = self._cfgSharename.value

                if self.mounts.has_key(sharename) is True:
                        self.session.openWithCallback(self.updateConfig, MessageBox, (_("A mount entry with this name already exists!\nUpdate existing entry and continue?\n") ) )
                else:
                        self.session.openWithCallback(self.applyConfig, MessageBox, (_("Are you sure you want to save this network mount?\n\n") ) )

        def updateConfig(self, ret = False):
                if ret == True:
                        sharedir = None
                        if self._cfgSharedir.value.startswith("/"):
                                sharedir = self._cfgSharedir.value[1:]
                        else:
                                sharedir = self._cfgSharedir.value
                        sharename = self._cfgSharename.value
                        iAutoMount.setMountAttributes(sharename, {
                            "sharename" : sharename,
                            "active" :  self._cfgActive.value,
                            "ip" :  self._cfgIp.getText(),
                            "sharedir" :  sharedir,
                            "mounttype" :  self._cfgMounttype.value,
                            "options" :  self._cfgOptions.value,
                            "username" :  self._cfgUsername.value,
                            "password" :  self._cfgPassword.value,
                            "hdd_replacement" :  self._cfgHddReplacement.value
                        })
                        self._applyConfigMsgBox = self.session.openWithCallback(self.applyConfigfinishedCB, MessageBox, _("Please wait while updating your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
                        iAutoMount.save()
                        iAutoMount.reload(self.applyConfigDataAvail)
                else:
                        self.close()

        def applyConfig(self, ret = False):
                if ret == True:
                        data = iAutoMount.DEFAULT_OPTIONS_NFS
                        data['active'] = self._cfgActive.value
                        data['ip'] = self._cfgIp.getText()
                        data['sharename'] = re_sub("\W", "", self._cfgSharename.value)
                        # "\W" matches everything that is "not numbers, letters, or underscores",where the alphabet defaults to ASCII.
                        if self._cfgSharedir.value.startswith("/"):
                                data['sharedir'] = self._cfgSharedir.value[1:]
                        else:
                                data['sharedir'] = self._cfgSharedir.value
                        data['options'] =  self._cfgOptions.value
                        data['mounttype'] = self._cfgMounttype.value
                        data['username'] = self._cfgUsername.value
                        data['password'] = self._cfgPassword.value
                        data['hdd_replacement'] = self._cfgHddReplacement.value
                        self._applyConfigMsgBox = self.session.openWithCallback(self.applyConfigfinishedCB, MessageBox, _("Please wait while I'm saving your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
                        iAutoMount.mounts[self._cfgSharename.value] = data
                        iAutoMount.save()
                        iAutoMount.reload(self.applyConfigDataAvail)
                else:
                        self.close()

        def applyConfigDataAvail(self, success):
                if success:
                        self._applyConfigMsgBox.close(True)

        def applyConfigfinishedCB(self,data):
                if data is True:
                        self.session.openWithCallback(self.applyfinished, MessageBox, _("Your network mount has been saved."), type = MessageBox.TYPE_INFO, timeout = 10)

        def applyfinished(self,data):
                if data is not None:
                        if data is True:
                                self.close()
