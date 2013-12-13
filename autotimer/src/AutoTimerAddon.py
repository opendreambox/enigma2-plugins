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
ataddonXMLtypes = {AT_EXCLUDE: "addon_exclude", AT_INCLUDE: "addon_include", AT_EXTENSION: "addon_extension"}
atdefaultFilters = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}

#Plugin- keys, that are ignored when writing the XML for the addins, as they are stored differently
ataddonSeriesDomain = "SeriesPlugin"
ataddonSeriesRename = "rename"
ataddonSeriesRenameKey = ataddonSeriesDomain + "." + ataddonSeriesRename
ataddonXMLignoreKeys = ["AutoTimer.title", "AutoTimer.shortdescription", "AutoTimer.description", "AutoTimer.dayofweek", ataddonSeriesRenameKey]

#New Plugin- Descriptor- value
WHERE_AUTOTIMERFILTERINCLUDE = 0xA0001
WHERE_AUTOTIMERFILTEREXCLUDE = 0xA0002
WHERE_AUTOTIMEREXTENSION = 0xA0003

atdescriptors = {WHERE_AUTOTIMERFILTERINCLUDE: AT_INCLUDE, WHERE_AUTOTIMERFILTEREXCLUDE: AT_EXCLUDE, WHERE_AUTOTIMEREXTENSION: AT_EXTENSION}

try:
    from Plugins.Extensions.SeriesPlugin.plugin import renameTimer
except ImportError as ie:
    renameTimer = None

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

class AutoTimerAddonEntry:
    """Specific entry in an autotimer based on an AutoTimerAddonDefinition. User fills values for all parameters and saves it in the AutoTimer.xml"""
    def __init__( self, addonKey = "AutoTimer.title", addonType=AT_EXCLUDE, description='', paramValues=None  ):
        self.addonKey = addonKey #Key to find the AddonDefinition in the list of definitions
        self.addonDefinition = addonDefinitions.addons[addonType][self.addonKey] #AddonDefinition for this Entry
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
            try:
                value
                valueFound=True
            except NameError:
                valueFound=False
            if valueFound:       
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

class AutoTimerAddonParamDefinition:
    """Parameter definitions for each AutoTimer Addon. Used to define the parameters the user can fill out if this filter is used"""
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

class AutoTimerAddonDefiniton():
    """Defines an addon with domain, name, called function and parameters The parameters are a list of AutoTimerAddonParamDefinition"""
    def __init__(self, domain, name, description, fnc, fncParams):
        self.domain = domain
        self.name = name
        addDomain = "." if self.domain else ""
        self.addonKey = self.domain + addDomain + self.name
        self.description = description
        self.fnc = fnc
        self.fncParams = fncParams

class AutoTimerAddonDefinitions():
    """List of all Addon Definitions: The 'default' ones (Title Filter, Short- Description Filter, Description Filter and day Filter, rename_series- Extension, if installed) 
    and all other plugins that use the AT- Plugin descriptors"""
    def __init__(self):
        self.addonDefinitionsRead = False
    
    @property
    def addons(self):        
        if not self.addonDefinitionsRead:
            self.readAddonDefinitions()
        return self._addons
    
    @property
    def addonSelection(self):
        if not self.addonDefinitionsRead:
            self.readAddonDefinitions()
        return self._addonSelection
        
    def readAddonDefinitions(self):
        atLog( ATLOG_INFO, "Reading Addon definitions")
        self.addonDefinitionsRead = True
        defaultAutoTimerParam = AutoTimerAddonParamDefinition(name='searchstring', description=_("Search for"), configtype='ConfigText', useasaddonlabel=True)
        defaultParams = (self.checkDefaultFilter, {'searchstring':defaultAutoTimerParam} )
        dayAutoTimerParam = AutoTimerAddonParamDefinition(name='searchstring', description=_("Search for"), configtype='ConfigSelection', choices = weekdays, useasaddonlabel=True)
        dayParams = (self.checkDefaultFilter, {'searchstring':dayAutoTimerParam} )

        titleAddon = AutoTimerAddonDefiniton( "AutoTimer", "title", _("in Title"), *defaultParams )
        shortAddon = AutoTimerAddonDefiniton( "AutoTimer", "shortdescription", _("in Shortdescription"), *defaultParams )
        descAddon = AutoTimerAddonDefiniton( "AutoTimer", "description", _("in Description"), *defaultParams )
        dayAddon = AutoTimerAddonDefiniton( "AutoTimer", "dayofweek", _("on Weekday"), *dayParams )
        
        self.defaultAddons = {    "AutoTimer.title": titleAddon, 
                            "AutoTimer.shortdescription": shortAddon,
                            "AutoTimer.description": descAddon,
                            "AutoTimer.dayofweek": dayAddon}
        
        self._addons = {}
        self._addons[AT_INCLUDE] = self.defaultAddons
        self._addons[AT_EXCLUDE] = self.defaultAddons

        # _addonSelection is a dictionary of Addons that can be selected from the Addon- Dialog. The key is the AddonDomain + AddonName, the value is the description
        self._addonSelection = {}
        self._addonSelection[AT_INCLUDE] = []
        self._addonSelection[AT_EXCLUDE] = []
        for defaultKey, defaultDefinition in iteritems(self.defaultAddons):
            self._addonSelection[AT_INCLUDE].append((defaultKey, defaultDefinition.description))
            self._addonSelection[AT_EXCLUDE].append((defaultKey, defaultDefinition.description))
                
        for pluginDescriptor,addonType in iteritems(atdescriptors):                
            curAddons = self._addons.get(addonType, {})
            curAddonSelection = self._addonSelection.get(addonType, [])
            atLog( ATLOG_DEBUG, "AddonDefinitions: Searching for Plugins for descriptor", pluginDescriptor )
            for p in plugins.getPlugins(pluginDescriptor):
                if not hasattr(p, "addonDomain"):
                    atLog( ATLOG_WARN, "Plugin does not have a domain specified: Not a valid AutoTimer Addon:", p.name)
                    continue
                else:
                    domain = p.addonDomain + "." if p.addonDomain else ""
                addonKey = domain + p.name
                atLog( ATLOG_DEBUG, "   >>>found Plugin ", addonKey )
                pluginAddon =  AutoTimerAddonDefiniton( p.addonDomain, p.name, p.description, p, p.fncParams)
                curAddons[addonKey] = pluginAddon
                curAddonSelection.append((addonKey, pluginAddon.description))
            self._addons[addonType] = curAddons
            self._addonSelection[addonType] = curAddonSelection
        
        # Add old series- plugin to addons, but only if not already done by newer version of series Plugin
        if renameTimer is not None:            
            seriesAutoTimerParam = AutoTimerAddonParamDefinition(name='enabled', description=_("Enabled"), configtype='ConfigYesNo', useasaddonlabel=True)
            seriesParams = (self.renameSeries, {'enabled': seriesAutoTimerParam} )
            seriesAddon = AutoTimerAddonDefiniton( ataddonSeriesDomain, ataddonSeriesRename, _("Label Series"), *seriesParams )
            execAddons = self._addons.get(AT_EXTENSION, {})
            execAddonSelection = self._addonSelection.get(AT_EXTENSION, [])
            if not ataddonSeriesRenameKey in execAddons:
                execAddons[ataddonSeriesRenameKey] = seriesAddon
                execAddonSelection.append((ataddonSeriesRenameKey, seriesAddon.description))
                self._addons[AT_EXTENSION] = execAddons

    def executeAddons(self, addonType, autotimer, timer, title, short, extended, dayofweek, serviceref, eit, begin, duration):
        """Called from autotimer on execution of autotimer. Returns if an exclude / include filter matches or TRUE, if just an Extension was run"""
        if not self.addonDefinitionsRead:
            self.readAddonDefinitions()
        atLog( ATLOG_INFO, "executeAddons: Start execute Addons of type %s" % (ataddonXMLtypes[addonType]) )
        addonTypeEntries = autotimer.addonEntries.get(addonType, {}) 
        if addonType == AT_EXCLUDE:
            defaultReturn = False
        elif addonType == AT_INCLUDE:
            defaultReturn = len(addonTypeEntries) == 0 # Return a Filter match, if the include filter is empty, else check filters...
        else:
            defaultReturn = True # Extensions return True by default

        if not addonTypeEntries:
            atLog( ATLOG_INFO, "executeAddons: No addons for this type in this autotimer" )
            return defaultReturn
        else:
            atLog( ATLOG_INFO, "executeAddons: found addons:", len(addonTypeEntries) )

        for addonKey,addonKeyEntries in iteritems(addonTypeEntries):
            atLog( ATLOG_DEBUG, "executeAddons: addonKey=", addonKey )
            for addonEntry in addonKeyEntries:
                if addonKey in self._addons[addonType].keys():
                    atLog( ATLOG_DEBUG, "executeAddons: addonDefinition found" )
                    addonDefinition = self._addons[addonType][addonKey]
                    addonName = addonDefinition.name
                    fnc = addonDefinition.fnc
                    if fnc:
                        try:
                            atLog( ATLOG_DEBUG, "executeAddons: calling addonFnc=", fnc.__name__ )
                            checkResult = fnc( addonName=addonName, autotimer=autotimer, timer=timer, title=title, short=short, extended=extended, \
                                           dayofweek=dayofweek, eit=eit, begin=begin, duration=duration, **addonEntry.paramValues )
                            if checkResult:
                                atLog( ATLOG_INFO, "executeAddons: addon %s returned TRUE" % (addonName) )
                                return True
                        except Exception, e:
                            atLog( ATLOG_ERROR, "executeAddons: addon error in addon %s: %s" %(addonKey, e) )           
                    else:
                        atLog( ATLOG_ERROR, "executeAddons: addon error in addon %s: No fnc given" %addonKey )
        atLog( ATLOG_INFO, "executeAddons: No match. returning:", defaultReturn )
        return defaultReturn
<<<<<<< HEAD
    
    def checkDefaultFilter(self, addonName='title', title='', short='', extended='', dayofweek='', searchstring='', **kwargs):
        """replaces the default filter checks for title, short, extended and dayofweek. Used as fnc for default filters"""
        if not self.addonDefinitionsRead:
            self.readAddonDefinitions()
        atLog( ATLOG_DEBUG, "checkDefaultFilter: Checking addonName=%s, title=%s, short=%s, extended=%s, dayofweek=%s, searchstring=%s" \
               %(addonName, title, short, extended, dayofweek, searchstring) )
=======

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
>>>>>>> branch 'AutoTimer-IgnoreEvents' of git+ssh://tode@scm.schwerkraft.elitedvb.net/scmrepos/git/enigma2-plugins/enigma2-plugins.git

        if not searchstring:
            atLog( ATLOG_WARN, "checkDefaultFilter: No searchstring given: break" )
            return False
        if addonName=='dayofweek':
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
            if addonName == "title":
                searchIn = title
            elif addonName =="shortdescription":
                searchIn = short
            else:
                searchIn = extended
            searchIn = searchIn.lower()
            atLog( ATLOG_DEBUG, "checkDefaultFilter: Searching for %s in %s" %(searchstring, addonName) )    
            if searchRegEx.search(searchIn):
                atLog( ATLOG_INFO, "checkDefaultFilter: Found %s in %s" %(searchstring, addonName) )
                return True
        return False
    
    def renameSeries(self, addonName='rename', autotimer=None, timer=None, title='', short='', extended='', \
                        eit=None, begin=0, duration=0, **kwargs):
        atLog( ATLOG_DEBUG, "renameSeries: Running renameTimer with parameters title=%s, short=%s, extended=%s" %(title, short, extended) )    
        if renameTimer is not None:
            renameTimer(timer, title, begin, begin + duration )
        return True

#Global variable with ALL definitions that are available. Singleton      
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

    def __init__(self, session, addonsEnabled, addonEntriesTimer, excludesTimer, includesTimer, seriesLabelingTimer):
        Screen.__init__(self, session)

        # Summary
        self.setup_title = _("AutoTimer Addons")
        self.onChangedEntry = []

        self.enabled = addonsEnabled

        self.editPos = -1
        self.excludes = excludesTimer
        self.includes = includesTimer
        self.series_labeling = seriesLabelingTimer
        
        # Add the default filters first
        self.addonEntriesFlat = {}
        self.getAddonsForFilter(self.excludes, AT_EXCLUDE)
        self.getAddonsForFilter(self.includes, AT_INCLUDE)
        
        # Now add all other addons
        for addonType,addonTypeList in iteritems(addonEntriesTimer):
            for addonKey,addonKeyList in iteritems(addonTypeList):     
                atLog( ATLOG_DEBUG, "AddonList: Check addons for addonKey %s" %(addonKey) )                        
                if not addonKey in ataddonXMLignoreKeys:
                    atLog( ATLOG_DEBUG, "AddonList: Not a default key -> Add entry" %(addonKey) )
                    if addonType in self.addonEntriesFlat:
                        self.addonEntriesFlat[addonType].extend(addonKeyList)
                    else:
                        self.addonEntriesFlat[addonType] = addonKeyList
                    
        self.addonLenList = {}

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
        """Get the addons from the 'classic' filters"""
        atLog( ATLOG_DEBUG, "AddonList, getAddonsForFilter: Create addons for filterType %s" %(ataddonXMLtypes[filterType]) )                        
        defaultType = -1
        self.addonEntriesFlat[filterType] = []
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
                    self.addonEntriesFlat[filterType].append(curAddon)
                    
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
        self.addonEntries = {}
        self.excludes = ([], [], [], [])
        self.includes = ([], [], [], [])
        
        # Warning, accessing a ConfigListEntry directly might be considered evil!

        for item in self["config"].getList()[:]:
            # Skip empty entries
            if item[1].value == "":
                continue
            else:
                addonEntry = item[2]
                addonType = addonEntry.addonType
                addonDomain = addonEntry.addonDomain
                addonName = addonEntry.addonName
                addonKey = addonDomain + "." + addonName
                atLog( ATLOG_DEBUG, "AddonList, saveCurrent: Adding addon of type %s with name %s for domain %s" %( ataddonXMLtypes[addonType], addonName, addonDomain ) )                        
                if addonType in self.addonEntries:
                    if addonKey in self.addonEntries[addonType]:
                        self.addonEntries[addonType][addonKey].append(addonEntry)
                    else:
                        self.addonEntries[addonType][addonKey] = [addonEntry]
                else:
                    self.addonEntries[addonType] = {addonKey: [addonEntry]}
                
                # Add old legacy entries, as they are, what will be saved in XML
                # ... for SeriesPlugin
                if addonKey == ataddonSeriesRenameKey:
                    self.series_labeling = addonEntry.paramValues["enabled"]

                #... and default filters
                if addonDomain == "AutoTimer":
                    atLog( ATLOG_DEBUG, "AddonList, saveCurrent: Adding default filter of type %s with name %s" %( ataddonXMLtypes[addonType], addonName ) )                        
                    addonNr = atdefaultFilters[addonName]
                    if addonType == AT_EXCLUDE:
                        atLog( ATLOG_DEBUG, "   >>>Add Exclude to list %d" %(addonNr) )                        
                        self.excludes[addonNr].append(addonEntry.paramValues["searchstring"])
                    elif addonType == AT_INCLUDE:
                        atLog( ATLOG_DEBUG, "   >>>Add Include to list %d" %(addonNr) )                        
                        self.includes[addonNr].append(addonEntry.paramValues["searchstring"])

    def refresh(self, *args, **kwargs):
        self.saveCurrent()

        self.reloadList()
        self["config"].setList(self.list)

    def reloadList(self):
        self.list = []
        self.enabled = False
        for addonType,addonList in iteritems(self.addonEntriesFlat):
            if addonList:
                self.enabled = True
                self.addonLenList[addonType] = len(addonList)
                self.list.extend([
                    self.getConfigForAddonEntry(addonEntry)
                        for addonEntry in addonList
                ])

    def remove(self):
        idx = self["config"].getCurrentIndex()
        if idx and idx >= 0:
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
                    self.addonLenList[myAddon.addonType] += 1
                else:
                    self.addonLenList[myAddon.addonType] = 1
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
            self.enabled,
            self.addonEntries,
            self.excludes,
            self.includes,
            self.series_labeling
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
            atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: item=", item)
            idx += 1
            curValue = item[1].value
            atLog( ATLOG_INFO, "AddonEditorAdvanced, ok: curValue="+ str(curValue) )
            curParam = item[2]
            atLog( ATLOG_INFO, "AddonEditorAdvanced, ok: curParam=", curParam )
            
            curChoices = {curValue: curValue}
            if hasattr(item[1], "choices"):
                if item[1].choices:
                    curChoices = item[1].choices 
            atLog( ATLOG_DEBUG, "AddonEditorAdvanced, ok: curChoices=", curChoices )

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
                        self.curAddon.description = curValue
                        firstParam = curParam
                        firstValue = curValue
                    else:
                        self.curAddon.description += ", " + curParam + ": " + curValue
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
        if fncParams:
            for name,param in iteritems( fncParams ):
                descriptor.fncParams[name] = param if isinstance(param, AutoTimerAddonParamDefinition) else AutoTimerAddonParamDefinition( name=str(param) )
    else:
        atLog( ATLOG_ERROR, "getAutoTimerPluginDescriptor: mandatory Parameters missing, ignoring request")
        descriptor = None
    return descriptor

