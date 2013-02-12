# -*- coding: UTF-8 -*-
# for localized messages
from . import _, iteritems

# Logging
from AutoTimerLogger import atLog, ATLOG_DEBUG, ATLOG_INFO, ATLOG_WARN, ATLOG_ERROR

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

#Plugin Descriptor
from Plugins.Plugin import PluginDescriptor
from Components.PluginComponent import plugins
from Components.config import getConfigListEntry, ConfigEnableDisable, \
    ConfigYesNo, ConfigText, ConfigClock, ConfigNumber, ConfigSelection, \
    ConfigDateTime, config, NoSave

# regular expression
from re import compile as re_compile

# Weekdays
weekdays = [
    ("0", _("Monday")),
    ("1", _("Tuesday")),
    ("2", _("Wednesday")),
    ("3", _("Thursday")),
    ("4", _("Friday")),
    ("5", _("Saturday")),
    ("6", _("Sunday")),
    ("weekend", _("Weekend")),
    ("weekday", _("Weekday"))
]

AT_EXCLUDE = 0
AT_INCLUDE = 1
AT_EXTENSION = 2

ataddontypes = {AT_EXCLUDE: _("Exclude"), AT_INCLUDE: _("Include"), AT_EXTENSION: _("Extension")}
ataddonXMLtypes = {AT_EXCLUDE: "exclude", AT_INCLUDE: "include", AT_EXTENSION: "extension"}
atdefaultFilters = {"title": 0, "short": 1, "desc": 2, "day": 3}

#New Plugin- Descriptor- value
WHERE_AUTOTIMERFILTERINCLUDE = 0xA0001
WHERE_AUTOTIMERFILTEREXCLUDE = 0xA0002
WHERE_AUTOTIMEREXTENSION = 0xA0003

atdescriptors = {WHERE_AUTOTIMERFILTERINCLUDE: AT_INCLUDE, WHERE_AUTOTIMERFILTEREXCLUDE: AT_EXCLUDE, WHERE_AUTOTIMEREXTENSION: AT_EXTENSION}

class ExtendedConfigText(ConfigText):
    def __init__(self, default = "", fixed_size = True, visible_width = False):
        ConfigText.__init__(self, default = default, fixed_size = fixed_size, visible_width = visible_width)

        # Workaround some characters currently not "typeable" using NumericalTextInput
        mapping = self.mapping
        if mapping:
            if "&" not in mapping[0]:
                mapping[0] += "&"
            if ";" not in mapping[0]:
                mapping[0] += ";"
            if "%" not in mapping[0]:
                mapping[0] += "%"

class AutoTimerAddonParam:
    def __init__( self, name='', description='', configtype='ConfigText', choices=None, default='', useasaddonlabel=False ):
        self.name = name
        self.description = description if description else name
        self.configtype = configtype
        if isinstance(choices, list):
            self.choices = {}
            for curChoice in choices:
                if isinstance(curChoice, tuple):
                    curKey = str(curChoice[0])
                    curVal = curChoice[1] if len(curChoice)>1 else curKey
                else:
                    curKey = str(curChoice)
                    curVal = curKey
                self.choices[curKey] = curVal 
        elif isinstance(choices, dict):
            self.choices = choices
        elif choices:
            self.choices = {}
            self.choices[str(choices)] = str(choices)
        else:
            self.choices = None
        self.default = default
        self.useasaddonlabel = useasaddonlabel

class AutoTimerAddonEntry:
    def __init__( self, addonKey = "AutoTimer.title", addonType=AT_EXCLUDE, description='', paramValues=None  ):
        self.addonKey = addonKey
        self.addonDefinition = addonDefinitions.addons[addonType][self.addonKey]
        self.addonName = self.addonDefinition.name
        self.addonDomain = self.addonDefinition.domain
        self.addonDescription = self.addonDefinition.description if self.addonDefinition.description else self.addonName 
        self.addonType = addonType
        self.paramValues = paramValues if paramValues else {}
        atLog( ATLOG_DEBUG, "AddonEntry: paramValues= ", self.paramValues )
        if description and description != "-":
            self.description = description
        else:
            self.getDescription()
        atLog( ATLOG_DEBUG, "AddonEntry: description=", self.description )
        
    def getDescription(self):
        atLog( ATLOG_DEBUG, "AddonEntry, getDescription: Description was empty. Try to build it" )

        self.description = ""
        addonParams = self.addonDefinition.fncParams
        firstValue = None
        descriptionCount = 0
        for name,value in iteritems(self.paramValues):
            atLog( ATLOG_DEBUG, "AddonEntry, getDescription: Reading parameter name=%s, value=%s" % (name,value) )
            if value:    
                if name in addonParams.keys():
                    atLog( ATLOG_DEBUG, "AddonEntry, getDescription: Name is in keys" )
                    useasaddonlabel = addonParams[name].useasaddonlabel
                    atLog( ATLOG_DEBUG, "AddonEntry, getDescription: useasaddonlabel=", useasaddonlabel )
                else:
                    useasaddonlabel = False
                if useasaddonlabel:
                    if descriptionCount == 0:
                        self.description = value
                    else:
                        self.description += " " + value
                    descriptionCount += 1
                if not firstValue:
                    atLog( ATLOG_DEBUG, "AddonEntry, getDescription: first found value= %s" %(value) )
                    firstValue = value

        if self.description == "":
            atLog( ATLOG_DEBUG, "AddonEntry, getDescription: No description found, falling back to default entry %s" %(firstValue) )
            self.description = firstValue if firstValue else "-"

class AutoTimerAddonDefiniton():
    def __init__(self, domain, name, description, fnc, fncParams):
        self.domain = domain
        self.name = name
        addDomain = "." if self.domain else ""
        self.addonKey = self.domain + addDomain + self.name
        self.description = description
        self.fnc = fnc
        self.fncParams = fncParams

class AutoTimerAddonDefinitions():
    def __init__(self):
        defaultAutoTimerParam = AutoTimerAddonParam(name='searchstring', description=_("Search for"), configtype='ConfigText', useasaddonlabel=True)
        defaultParams = (self.checkDefaultFilter, {'searchstring':defaultAutoTimerParam} )
        dayAutoTimerParam = AutoTimerAddonParam(name='searchstring', description=_("Search for"), configtype='ConfigSelection', choices = weekdays, useasaddonlabel=True)
        dayParams = (self.checkDefaultFilter, {'searchstring':dayAutoTimerParam} )

        titleAddon = AutoTimerAddonDefiniton( "AutoTimer", "title", _("in Title"), *defaultParams )
        shortAddon = AutoTimerAddonDefiniton( "AutoTimer", "short", _("in Shortdescription"), *defaultParams )
        descAddon = AutoTimerAddonDefiniton( "AutoTimer", "desc", _("in Description"), *defaultParams )
        dayAddon = AutoTimerAddonDefiniton( "AutoTimer", "day", _("on Weekday"), *dayParams )
        
        self.defaultAddons = {    "AutoTimer.title": titleAddon, 
                            "AutoTimer.short": shortAddon,
                            "AutoTimer.desc": descAddon,
                            "AutoTimer.day": dayAddon}
        
        self.addons = {}
        self.addons[AT_INCLUDE] = self.defaultAddons
        self.addons[AT_EXCLUDE] = self.defaultAddons

        self.addonSelection = {}
        self.addonSelection[AT_INCLUDE] = []
        self.addonSelection[AT_EXCLUDE] = []
        for defaultKey, defaultDefinition in iteritems(self.defaultAddons):
            self.addonSelection[AT_INCLUDE].append((defaultKey, defaultDefinition.description))
            self.addonSelection[AT_EXCLUDE].append((defaultKey, defaultDefinition.description))
                
        for pluginDescriptor,addonType in iteritems(atdescriptors):                
            curAddons = self.addons.get(addonType, {})
            curAddonSelection = self.addonSelection.get(addonType, [])
            for p in plugins.getPlugins(pluginDescriptor):
                domain = p.addondomain + "." if p.addondomain else ""
                addonKey = domain + p.name
                pluginAddon =  AutoTimerAddonDefiniton( p.addondomain, p.name, p.description, p, p.fncParams)
                curAddons[addonKey] = pluginAddon
                curAddonSelection.append((addonKey, pluginAddon.description))
            self.addons[addonType] = curAddons
            self.addonSelection[addonType] = curAddonSelection
    
    def executeAddon(self, addonType, autotimer, timer, title, short, extended, dayofweek, serviceref, eit, begin, duration):
        atLog( ATLOG_INFO, "executeAddon: Start execute Addons of type %s" % (ataddontypes[addonType]) )
        if not addonType in autotimer.addons:
            atLog( ATLOG_INFO, "executeAddon: No addons for this type in this autotimer" )
            return False
        addonEntries = autotimer.addons[addonType]
        if addonType == AT_EXCLUDE:
            defaultReturn = False
        elif addonType == AT_INCLUDE:
            defaultReturn = len(addonEntries) == 0 # Return a Filter match, if the include filter is empty, else check filters...
        else:
            defaultReturn = True # Extensions return True by default

        for addon in addonEntries:
            addonKey = addon.addonKey
            
            atLog( ATLOG_DEBUG, "executeAddon: addonKey=", addonKey )
            if addonKey in self.addons[addonType].keys():
                atLog( ATLOG_DEBUG, "executeAddon: addonDefinition found" )
                addonDefinition = self.addons[addonType][addonKey]
                addonName = addonDefinition.name
                fnc = addonDefinition.fnc
                if fnc:
                    try:
                        atLog( ATLOG_DEBUG, "executeAddon: calling addonFnc=", fnc.__name__ )
                        checkResult = fnc( addonName=addonName, autotimer=autotimer, timer=timer, title=title, short=short, extended=extended, \
                                       dayofweek=dayofweek, eit=eit, begin=begin, duration=duration, **addon.paramValues )
                        if checkResult:
                            atLog( ATLOG_INFO, "executeAddon: addon %s returned TRUE" % (addonName) )
                            return True
                    except Exception, e:
                        atLog( ATLOG_ERROR, "executeAddon: addon error in addon %s: %s" %(addonKey, e) )           
                else:
                    atLog( ATLOG_ERROR, "executeAddon: addon error in addon %s: No fnc given" %addonKey )
        atLog( ATLOG_INFO, "executeAddon: No match. returning:", defaultReturn )
        return defaultReturn

    def advertiseAddon(self, addonType):
        atLog(ATLOG_DEBUG, "advertiseAddon: Advertising Addons of type", ataddontypes[addonType])
        assert(addonType == AT_EXTENSION, "addonType must be AT_EXTENSION")
        if addonType not in self.addons:
            atLog( ATLOG_INFO, "advertiseAddon: Nothing to advertise")
            return ()

        return [x.name for x in self.addons[addonType]]

    def checkDefaultFilter(self, filterName='title', title='', short='', extended='', dayofweek='', searchstring='', **kwargs):
        atLog( ATLOG_DEBUG, "checkDefaultFilter: Checking filterName=%s, title=%s, short=%s, extended=%s, dayofweek=%s, searchstring=%s" \
               %(filterName, title, short, extended, dayofweek, searchstring) )

        if not searchstring:
            atLog( ATLOG_WARN, "checkDefaultFilter: No searchstring given: break" )
            return False
        if filterName=='day':
            if dayofweek:
                list = [ searchstring ]
                if dayofweek in list:
                    atLog( ATLOG_INFO, "checkDefaultFilter: Found %s in %s" %(dayofweek, list) )
                    return True
                if "weekend" in list and dayofweek in ("5", "6"):
                    atLog( ATLOG_INFO, "checkDefaultFilter: Found %s in weekend" %dayofweek )
                    return True
                if "weekday" in list and dayofweek in ("0", "1", "2", "3", "4"):
                    atLog( ATLOG_INFO, "checkDefaultFilter: Found %s in weekdays" %dayofweek )
                    return True
        else:            
            searchRegEx = re_compile(searchstring.lower())
            if filterName == "title":
                searchIn = title
            elif filterName =="short":
                searchIn = short
            else:
                searchIn = extended
            searchIn = searchIn.lower()
            atLog( ATLOG_DEBUG, "checkDefaultFilter: Searching for %s in %s" %(searchstring, filterName) )    
            if searchRegEx.search(searchIn):
                atLog( ATLOG_INFO, "checkDefaultFilter: Found %s in %s" %(searchstring, filterName) )
                return True
        return False
        
addonDefinitions = AutoTimerAddonDefinitions()
    
class AutoTimerAddonList(Screen, ConfigListScreen):
    """Edit AutoTimer Addons"""

    skin = """<screen name="AutoTimerAddonList" title="Edit AutoTimer Addons" position="center,center" size="565,280">
        <ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
        <ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
        <ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
        <ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
        <widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        <widget name="config" position="5,45" size="555,225" scrollbarMode="showOnDemand" />
    </screen>"""

    def __init__(self, session, addonsEnabled, addons, excludes, includes):
        Screen.__init__(self, session)

        # Summary
        self.setup_title = _("AutoTimer Addons")
        self.onChangedEntry = []

        self.enabled = NoSave(ConfigEnableDisable(default = addonsEnabled))

        self.editPos = -1
        self.excludes = excludes
        self.includes = includes
        
        # Add the default filters first
        self.addons = {}
        self.getAddonsForFilter(self.excludes, AT_EXCLUDE)
        self.getAddonsForFilter(self.includes, AT_INCLUDE)
        
        # Now add all other addons
        for addonType,addonList in addons:
            if addonType in self.addons:
                self.addons[addonType].extend(addonList)
            else:
                self.addons[addonType] = addonList
                
        self.addonLenList = {}

        self.enabled.addNotifier(self.refresh, initial_call = False)
        self.reloadList()
        
        ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

        # Initialize Buttons
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Save"))
        self["key_yellow"] = StaticText(_("delete"))
        self["key_blue"] = StaticText(_("New"))

        # Define Actions
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "ok": self.keyOK,
                "cancel": self.cancel,
                "save": self.save,
                "yellow": self.remove,
                "blue": self.new
            }
        )

        self.onLayoutFinish.append(self.setCustomTitle)

    def getAddonsForFilter(self, filterList, filterType):
        atLog( ATLOG_DEBUG, "AddonList, getAddonsForFilter: Create addons for filterType %s" %(filterType) )                        
        defaultType = -1
        self.addons[filterType] = []
        for filters in filterList:
            defaultType += 1
            if filters:
                atLog( ATLOG_DEBUG, "AddonList, getAddonsForFilter: Create addon config for filter nr %d" %(defaultType) )                        
                filterKey = next(key for key,nr in iteritems(atdefaultFilters) if nr==defaultType)
                atLog( ATLOG_DEBUG, "   >>> found filterKey %s" %(filterKey) )                        
                filterDomain = "AutoTimer"
                for filter in filters:
                    atLog( ATLOG_DEBUG, "   >>> Add Entry for %s" %(filter) )                        
                    curAddon = AutoTimerAddonEntry( addonKey = filterDomain + "." + filterKey, \
                                                    addonType=filterType, description=filter, paramValues={"searchstring": filter} )
                    self.addons[filterType].append(curAddon)
                    
    def changed(self):
        for changeFnc in self.onChangedEntry:
            try:
                changeFnc()
            except Exception:
                pass

    def setCustomTitle(self):
        self.setTitle(_("Edit AutoTimer addons"))

    def getCurrentEntry(self):
        return self["config"].getCurrent()[0]

    def getCurrentValue(self):
        return str(self["config"].getCurrent()[1].getText())

    def createSummary(self):
        return SetupSummary

    def saveCurrent(self):
        self.addons = {}
        self.excludes = ([], [], [], [])
        self.excludes = ([], [], [], [])
        
        # Warning, accessing a ConfigListEntry directly might be considered evil!

        idx = -1
        for item in self["config"].getList()[:]:
            idx += 1
            # Skip empty entries (and those which are no addons)
            if item[1].value == "" or idx < 1:
                continue
            else:
                addon = item[2]
                addonType = addon.addonType
                addonDomain = addon.addonDomain
                addonName = addon.addonName
                if addonDomain <> "AutoTimer":
                    atLog( ATLOG_DEBUG, "AddonList, saveCurrent: Adding addon of type %s with name %s for domain %s" %( addonType, addonName, addonDomain ) )                        
                    if addonType in self.addons:
                        self.addons[addonType].append(item[2])
                    else:
                        self.addons[addonType] = [item[2]]
                else: # Default filters
                    atLog( ATLOG_DEBUG, "AddonList, saveCurrent: Adding default filter of type %s with name %s" %( addonType, addonName ) )                        
                    addonNr = atdefaultFilters[addonName]
                    if addonType == AT_EXCLUDE:
                        atLog( ATLOG_DEBUG, "   >>>Add Exclude to list %d" %(addonNr) )                        
                        self.excludes[addonNr].append(addon.paramValues["searchstring"])
                    elif addonType == AT_INCLUDE:
                        atLog( ATLOG_DEBUG, "   >>>Add Include to list %d" %(addonNr) )                        
                        self.excludes[addonNr].append(addon.paramValues["searchstring"])

    def refresh(self, *args, **kwargs):
        self.saveCurrent()

        self.reloadList()
        self["config"].setList(self.list)

    def reloadList(self):
        self.list = [
            getConfigListEntry(_("Enable Addons"), self.enabled),
        ]

        for addonType,addonList in iteritems(self.addons):
            if addonList:
                self.addonLenList[addonType] = len(addonList)
                self.list.extend([
                    self.getConfigForAddonEntry(x)
                        for x in addonList
                ])

    def remove(self):
        idx = self["config"].getCurrentIndex()
        if idx and idx > 0:
            curEntry = self["config"].getCurrent()
            addonType = curEntry[2].addonType
            if addonType in self.addonLenList:
                self.addonLenList[addonType] -= 1
            
            list = self["config"].getList()
            list.remove(self["config"].getCurrent())
            self["config"].setList(list)

    def new(self):
        self.editPos = -1
        newAddon = AutoTimerAddonEntry()
        self.session.openWithCallback(
            self.addonEditorCallback,
            AutoTimerAddonEditorAdvanced,
            newAddon 
        )

    def keyOK(self):
        idx = self["config"].getCurrentIndex()
        atLog( ATLOG_DEBUG, "AddonList, keyOK: idx= " + str(idx) )
        if idx and idx > 0:
            curEntry = self["config"].getCurrent()[2]
            atLog( ATLOG_DEBUG, "AddonList, keyOK: current selected: ", curEntry )
            self.editPos = idx
            self.session.openWithCallback(
                self.addonEditorCallback,
                AutoTimerAddonEditorAdvanced,
                curEntry
        )

    def addonEditorCallback(self, ret):
        if ret is not None:
            myList = self["config"].getList()

            myAddon = ret
            entry = self.getConfigForAddonEntry(myAddon)

            if self.editPos == -1: # New?
                # Get the position for the new entry
                pos = 1
                for addonType,lenValue in iteritems(self.addonLenList):
                    if addonType <= myAddon.addonType:
                        pos += lenValue
                myList.insert(pos, entry)
                if myAddon.addonType in self.addonLenList:
                    self.addonLenList[addonType] += 1
                else:
                    self.addonLenList[addonType] = 1
            else:
                pos = self.editPos
                myList[pos] = entry
                
            self["config"].setList(myList)

    def getConfigForAddonEntry(self, curAddon):
        addonType = curAddon.addonType
        entryType = ataddontypes[addonType] + " " + curAddon.addonDescription
        
        addonEntryDescription = curAddon.description
        
        entry = getConfigListEntry(entryType, NoSave(ConfigSelection(choices = [(addonEntryDescription, addonEntryDescription)], default = addonEntryDescription)), curAddon)
        return entry

    def cancel(self):
        if self["config"].isChanged():
            self.session.openWithCallback(
                self.cancelConfirm,
                MessageBox,
                _("Really close without saving settings?")
            )
        else:
            self.close(None)

    def cancelConfirm(self, ret):
        if ret:
            self.close(None)

    def save(self):
        self.saveCurrent()

        self.close((
            self.enabled.value,
            self.addons,
            self.excludes,
            self.includes
        ))
class AutoTimerAddonEditorAdvanced(Screen, ConfigListScreen):
    """Edit AutoTimer Addon"""

    skin = """<screen name="AutoTimerAddonEditorAdvanced" title="Edit AutoTimer Addon" position="center,center" size="565,280">
            <ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
            <ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
            <ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
            <ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
            <widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <widget name="config" position="5,45" size="555,225" scrollbarMode="showOnDemand" />
            </screen>"""

    def __init__(self, session, curAddon):
        Screen.__init__(self, session)

        # Summary
        self.setup_title = _("AutoTimer Addon")  
        self.onChangedEntry = []
        self.curAddon = curAddon        
        self.addonType = NoSave(ConfigSelection(choices = ataddontypes, default = self.curAddon.addonType))         
        self.addonSelectionConfig = NoSave(ConfigSelection(choices = addonDefinitions.addonSelection[self.addonType.value], default = self.curAddon.addonKey))
        
        self.addonType.addNotifier(self.refresh, initial_call = False)
        self.addonSelectionConfig.addNotifier(self.refresh, initial_call = False)
        self.reloadList()
        
        ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

        # Initialize Buttons
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Ok"))
        self["key_yellow"] = StaticText("")
        self["key_blue"] = StaticText(_(""))

        # Define Actions
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.cancel,
                "green": self.ok,
                "red": self.cancel
            }
        )

        self.onLayoutFinish.append(self.setCustomTitle)

    def changed(self):
        for x in self.onChangedEntry:
            try:
                x()
            except Exception:
                pass

    def setCustomTitle(self):
        self.setTitle(_("Edit AutoTimer Addon"))
        
    def refresh(self, *args, **kwargs):
        self.reloadList()
        self["config"].setList(self.list) 
    
    def reloadList(self):
        self.list = [
            getConfigListEntry(_("Type of Addon"), self.addonType, "addonType")]
        
        if addonDefinitions.addonSelection[self.addonType.value]:
            self.addonSelectionConfig.setChoices(addonDefinitions.addonSelection[self.addonType.value])        
            self.list.append(getConfigListEntry(_("Addon"), self.addonSelectionConfig, "addonName"))
        
        if self.addonType.value in addonDefinitions.addons:
            # Is there an addon- definition for the current type (Exlude, include, ...)
            curAddonDefinitions = addonDefinitions.addons[self.addonType.value]
            if self.addonSelectionConfig.value in curAddonDefinitions:
                # is there a definition for the currently selected addon
                addonDefinition = curAddonDefinitions[self.addonSelectionConfig.value]
                
                self.descriptionIndices = []
                idx = len(self.list)
                for paramName,addonParam in iteritems( addonDefinition.fncParams ):
                    paramValue = self.curAddon.paramValues[addonParam.name] if addonParam.name in self.curAddon.paramValues else addonParam.default
                    paramDescription = addonParam.description
                    paramConfigType = addonParam.configtype
                    idx += 1
                    if addonParam.useasaddonlabel:
                        atLog( ATLOG_DEBUG, "AddonEditorAdvanced, reloadList: found label parameter= ", paramDescription)
                        self.descriptionIndices.append(idx)
                    if paramConfigType == "ConfigText":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ExtendedConfigText(fixed_size = False, default=paramValue)), paramName)
                    elif paramConfigType == "ConfigSelection":
                        paramChoices = addonParam.choices
                        defaultValue = paramValue if  paramValue in paramChoices.keys() else None
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigSelection(choices=paramChoices , default=defaultValue)), paramName)
                    elif paramConfigType == "ConfigInteger":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigInteger(default=paramValue)), paramName)
                    elif paramConfigType == "ConfigBoolean":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigBoolean(default=paramValue)), paramName)
                    elif paramConfigType == "ConfigYesNo":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigYesNo(default=paramValue)), paramName)
                    elif paramConfigType == "ConfigEnableDisable":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigEnableDisable(default=paramValue)), paramName)
                    elif paramConfigType == "ConfigDateTime":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigDateTime(default=paramValue)), paramName)
                    elif paramConfigType == "ConfigClock":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigClock(default=paramValue)), paramName)
                    elif paramConfigType == "ConfigDirectory":
                        newEntry = getConfigListEntry( paramDescription, NoSave(ConfigDirectory(default=paramValue)), paramName)
                    
                    self.list.append(newEntry)   

    def ok(self):
        self.curAddon.paramValues = {}
        self.curAddon.description = ""
        idx = 0
        descValues = 0
        firstValue = ""
        firstParam = ""
        for item in self["config"].getList()[:]:
            atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: item= ", item)
            idx += 1
            curValue = item[1].value
            atLog( ATLOG_INFO, "AddonEditorAdvanced, ok: curValue= "+ str(curValue) )
            curParam = item[2]
            atLog( ATLOG_INFO, "AddonEditorAdvanced, ok: curParam: ", curParam )
            
            curChoices = {curValue: curValue}
            if hasattr(item[1], "choices"):
                if item[1].choices:
                    curChoices = item[1].choices 
            atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: curChoices: ", curChoices )

            # Skip empty entries (and those which are no addons)
            if idx == 1:
                atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: set addonType to", curValue )                
                self.curAddon.addonType = curValue
            elif idx == 2:
                atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: set addonKey to", curValue )                
                self.curAddon.addonKey = curValue
                curAddonDefinition = addonDefinitions.addons[self.curAddon.addonType][curValue]
                self.curAddon.addonDescription = curAddonDefinition.description
                self.curAddon.addonName = curAddonDefinition.name
                self.curAddon.addonDomain = curAddonDefinition.domain
            elif curValue == "":
                continue
            else:
                atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: descriptionIndices= ", self.descriptionIndices)
                atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: idx= ", idx)
                if idx in self.descriptionIndices:
                    atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: descriptionParam found with idx=", str(idx) )

                    descValues += 1
                    if descValues == 1:
                        self.curAddon.description = curChoices[curValue]
                        firstParam = curParam
                        firstValue = curChoices[curValue]
                    else:
                        self.curAddon.description += ", " + curParam + ": " + curChoices[curValue]
                    if descValues == 2: # Only add Parametername, if there is more than one param to return, was omitted in descValues == 1
                        self.curAddon.description = firstParam + ": " + self.curAddon.description  
                self.curAddon.paramValues[curParam] = curValue

        if self.curAddon.description == "":
            self.curAddon.description = firstValue if firstValue else "-"
        
        self.close(self.curAddon)
        
    def cancel(self):
        if self["config"].isChanged():
            self.session.openWithCallback(
                self.cancelConfirm,
                MessageBox,
                _("Really close without saving settings?")
            )
        else:
            self.close(None)

    def cancelConfirm(self, ret):
        if ret:
            self.close(None)
            
def getAutoTimerPluginDescriptor( addonDomain, name, description, where, fnc, fncParams ):
    if addonDomain and name and where and fnc:
        descriptor = PluginDescriptor( name=name, description=description, where=where, fnc=fnc )
        descriptor.addonDomain = addonDomain
        descriptor.fncParams = {}
        for name,param in iteritems( fncParams.iteritems ):
            descriptor.fncParams[name] = param if isinstance(param, AutoTimerAddonParam) else AutoTimerAddonParam( name=str(param) )
    else:
        atLog( ATLOG_ERROR, "getAutoTimerPluginDescriptor: mandatory Parameters missing, ignoring request")
        descriptor = None
    return descriptor

