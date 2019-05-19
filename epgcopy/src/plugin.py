# -*- coding: utf-8 -*-
#=========================================================================================
#
# All Files of this Software are licensed under the Creative Commons 
# Attribution-NonCommercial-ShareAlike 3.0 Unported 
# License if not stated otherwise in a Files Head. To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
# Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
# Alternatively, this plugin may be distributed and executed on hardware which
# is licensed by Dream Property GmbH.
#
# This plugin is NOT free software. It is open source, you are allowed to
# modify it (if you keep the license), but it may not be commercially 
# distributed other than under the conditions noted above.
#
# Copyright (C) 2015 by nixkoenner@newnigma2.to
# http://newnigma2.to
#
# License: GPL
#
#=========================================================================================
from __future__ import print_function
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen

from enigma import eEPGCache, getDesktop, eTimer
from Plugins.Plugin import PluginDescriptor

import ftplib
from os import path, remove
from shutil import move
from Components.config import getConfigListEntry, config, \
    ConfigSubsection, ConfigText, ConfigIP, ConfigYesNo, \
    ConfigPassword, ConfigNumber, KEY_LEFT, KEY_RIGHT, KEY_0, ConfigClock
    

from time import time, strftime, mktime, localtime
now = localtime()
autoCopy = mktime((
        now.tm_year, now.tm_mon, now.tm_mday, 0o6, 00, \
        0, now.tm_wday, now.tm_yday, now.tm_isdst)
)

config.plugins.epgCopy = ConfigSubsection()
config.plugins.epgCopy.username = ConfigText(default = "root", fixed_size = False)
config.plugins.epgCopy.password = ConfigPassword(default = "", fixed_size = False)
config.plugins.epgCopy.ip = ConfigIP(default = [0, 0, 0, 0])
config.plugins.epgCopy.copytime = ConfigClock(default = int(autoCopy))

def myPrint(txt, prefix = None):
    print(("\033[91m[EPGCopy] %s\033[m " % txt))
    
def myFtp(): 
    directory_local='/tmp/' 
    directory = '/etc/enigma2/' 
    fileQuelle='epg.db'
    fileZiel='epgSync.db'
    
    if path.isfile(directory_local+fileZiel):
        try:
            remove(directory_local+fileZiel)
            myPrint ("deleted pre-existing " + fileZiel)
        except OSError:
            myPrint ("could not remove pre-existing " + fileZiel)
        
    remoteip = "%d.%d.%d.%d" % tuple(config.plugins.epgCopy.ip.value)
    f = ftplib.FTP(remoteip) 
    f.login(config.plugins.epgCopy.username.value, config.plugins.epgCopy.password.value)
    f.cwd(directory)
    #f.retrlines('LIST')
    file = open(directory_local+fileZiel, 'wb')
    f.retrbinary('RETR '+ fileQuelle, file.write)
    file.close()
    f.quit()
    if path.isfile(directory+fileQuelle):
        remove(directory+fileQuelle)
    move(directory_local+fileZiel,directory+fileQuelle)
    myPrint("epg.db was successfully transferred")

class copyEveryDay(Screen):
    instance = None

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        copyEveryDay.instance = self
        self.timer = eTimer()
        self.timer_conn = self.timer.timeout.connect(self.__doCopy)
        self.configChange()
    
    def configChange(self, configElement = None):   
        if self.timer.isActive(): # stop timer if running
            self.timer.stop()
        now = localtime()
        begin = int(mktime(
            (now.tm_year, now.tm_mon, now.tm_mday,
            config.plugins.epgCopy.copytime.value[0],
            config.plugins.epgCopy.copytime.value[1],
            now.tm_sec, now.tm_wday, now.tm_yday, now.tm_isdst)
        ))
        if begin < time():
            begin += 86400
        next = int(abs(time() - begin))
        myPrint("[copyEveryDay] next reset: %s" % strftime("%c", localtime(time()+ next)))
        self.timer.startLongTimer(next)
        
    def __doCopy(self):
        if config.plugins.epgCopy.copytime.value:
            myPrint("[__doCopy] do reset: %s" % strftime("%c", localtime(time())))
            ftpOK = False
            myEpg = None
            myEpg = eEPGCache.getInstance()
            try:
                myFtp()
                ftpOK = True
            except:
                ftpOK = False
            if ftpOK:
                myEpg.load()
                myPrint ("epg was loaded into memory")
            else:
                myPrint("an error occurred while transferring the epg")
        self.configChange()

class epgCopyScreen(Screen, ConfigListScreen):
    if getDesktop(0).size().width() == 1280:
        skin = """
            <screen position="center,center" size="602,520" title="%s" >
            <widget name="config" position="center,center" size="580,435" scrollbarMode="showOnDemand" enableWrapAround="1"/>
            <ePixmap name="red" position="5,475" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
            <widget name="key_red" position="5,475" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <ePixmap name="green" position="150,475" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
            <widget name="key_green" position="150,475" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <ePixmap name="yellow" position="295,475" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
            <widget name="key_yellow" position="295,475" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />    
            </screen>"""% _("EPG Copy view 1280")
    else:
        skin = """
            <screen position="center,center" size="585,410" title="%s" >
            <widget name="config" position="center,center" size="580,335" scrollbarMode="showOnDemand" enableWrapAround="1"/>
            <ePixmap name="red" position="5,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
            <widget name="key_red" position="5,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <ePixmap name="green" position="150,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
            <widget name="key_green" position="150,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <ePixmap name="yellow" position="295,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
            <widget name="key_yellow" position="295,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />    
            </screen>"""% _("EPG Copy view")
            
    def __init__(self, session):
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.saveSettings,
            "yellow": self.startManually,
            "cancel": self.close,
        }, -1)
       
        self["key_green"] = Button(_("save"))
        self["key_yellow"] = Button(_("manually"))
        self["key_red"] = Button(_("cancel"))
        
        ConfigListScreen.__init__(self, [
            getConfigListEntry(_("EPG Copy - Source Network IP"), config.plugins.epgCopy.ip),
            getConfigListEntry(_("EPG Copy - Username"), config.plugins.epgCopy.username),
            getConfigListEntry(_("EPG Copy - Password"), config.plugins.epgCopy.password),
            getConfigListEntry(_("EPG Copy - Time to Copy"), config.plugins.epgCopy.copytime),
        ], session)
      
    def saveSettings(self):
          config.plugins.epgCopy.save()
          copyEveryDay.instance.configChange()
          self.close()
    
    def startManually(self):
        self.myStart()
        
    def myStart(self):
        ftpOK = False
        myEpg = None
        myEpg = eEPGCache.getInstance()
        try:
            myFtp()
            ftpOK = True
        except:
            ftpOK = False
        
        if ftpOK:
            myEpg.load()
            self.session.openWithCallback(self.epgLoadFinishedConfirm, MessageBox, _("Successfully transferred and loaded EPG"), MessageBox.TYPE_INFO, timeout=4)
            myPrint ("epg was loaded into memory")
        else:
            self.session.open(MessageBox,_("An error occurred while transferring the epg. Please check your ftp credentials."), MessageBox.TYPE_INFO, timeout=10)
            myPrint ("an error occurred while transferring the epg")
        
    def epgLoadFinishedConfirm(self, result):
        self.close()
        

def autoCpy(reason, **kwargs):
    if "session" in kwargs:
        global Session
        Session = kwargs["session"]
        Session.open(copyEveryDay)

def main(session, **kwargs):
    session.open(epgCopyScreen)

def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    return  [
             PluginDescriptor(name="epgCopy",description="copy epg.db", where = [ PluginDescriptor.WHERE_PLUGINMENU ], icon="epg.png", fnc = main),
             PluginDescriptor(name="epgCopy", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
             PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART,fnc = autoCpy)
             ]
      