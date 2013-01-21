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

atextensiontypes = {AT_EXCLUDE: _("Exclude"), AT_INCLUDE: _("Include"), AT_EXTENSION: _("Extension")}

#New Plugin- Descriptor- value
WHERE_AUTOTIMERFILTERINCLUDE = 0xA0001
WHERE_AUTOTIMERFILTEREXCLUDE = 0xA0002
WHERE_AUTOTIMERFILTEREXTENSION = 0xA0003

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

class AutoTimerFilterParam:
    def __init__( self, name='', description='', configtype='ConfigText', choices=None, default='', useasfilterlabel=False ):
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
        self.useasfilterlabel = useasfilterlabel

class AutoTimerFilterEntry:
    def __init__( self, filterKey = "AutoTimer.title", filterType=AT_EXCLUDE, description='', paramValues=None  ):
        self.filterKey = filterKey
        self.filterDefinition = filterDefinitions.filters[self.filterKey]
        self.filterName = self.filterDefinition.name
        self.filterDomain = self.filterDefinition.domain
        self.filterDescription = self.filterDefinition.description if self.filterDefinition.description else self.filterName 
        self.filterType = filterType
        self.paramValues = paramValues if paramValues else {}
        atLog( ATLOG_DEBUG, "FilterEntry: paramValues= ", self.paramValues )
        if description and description != "-":
            self.description = description
        else:
            self.getDescription()
        atLog( ATLOG_DEBUG, "FilterEntry: description=", self.description )
        
    def getDescription(self):
        atLog( ATLOG_DEBUG, "FilterEntry, getDescription: Description was empty. Try to build it" )

        self.description = ""
        filterParams = self.filterDefinition.fncParams
        firstValue = None
        descriptionCount = 0
        for name,value in iteritems(self.paramValues):
            atLog( ATLOG_DEBUG, "FilterEntry, getDescription: Reading parameter name=%s, value=%s" % (name,value) )
            if value:    
                if name in filterParams.keys():
                    atLog( ATLOG_DEBUG, "FilterEntry, getDescription: Name is in keys" )
                    useasfilterlabel = filterParams[name].useasfilterlabel
                    atLog( ATLOG_DEBUG, "FilterEntry, getDescription: useasfilterlabel=", useasfilterlabel )
                else:
                    useasfilterlabel = False
                if useasfilterlabel:
                    if descriptionCount == 0:
                        self.description = value
                    else:
                        self.description += " " + value
                    descriptionCount += 1
                if not firstValue:
                    atLog( ATLOG_DEBUG, "FilterEntry, getDescription: first found value= %s" %(value) )
                    firstValue = value

        if self.description == "":
            atLog( ATLOG_DEBUG, "FilterEntry, getDescription: No description found, falling back to default entry %s" %(firstValue) )
            self.description = firstValue if firstValue else "-"

class AutoTimerFilterDefiniton():
    def __init__(self, domain, name, description, fnc, fncParams):
        self.domain = domain
        self.name = name
        addDomain = "." if self.domain else ""
        self.filterKey = self.domain + addDomain + self.name
        self.description = description
        self.fnc = fnc
        self.fncParams = fncParams

class AutoTimerFilterDefinitions():
    def __init__(self):
        defaultAutoTimerParam = AutoTimerFilterParam(name='searchstring', description=_("Search for"), configtype='ConfigText', useasfilterlabel=True)
        defaultParams = (self.checkDefaultFilter, {'searchstring':defaultAutoTimerParam} )
        dayAutoTimerParam = AutoTimerFilterParam(name='searchstring', description=_("Search for"), configtype='ConfigSelection', choices = weekdays, useasfilterlabel=True)
        dayParams = (self.checkDefaultFilter, {'searchstring':dayAutoTimerParam} )

        titleFilter = AutoTimerFilterDefiniton( "AutoTimer", "title", _("in Title"), *defaultParams )
        shortFilter = AutoTimerFilterDefiniton( "AutoTimer", "short", _("in Shortdescription"), *defaultParams )
        descFilter = AutoTimerFilterDefiniton( "AutoTimer", "desc", _("in Description"), *defaultParams )
        dayFilter = AutoTimerFilterDefiniton( "AutoTimer", "day", _("on Weekday"), *dayParams )
        
        self.filters = {    "AutoTimer.title": titleFilter, 
                            "AutoTimer.short": shortFilter,
                            "AutoTimer.desc": descFilter,
                            "AutoTimer.day": dayFilter}
        
        for p in plugins.getPlugins([WHERE_AUTOTIMERFILTEREXCLUDE, WHERE_AUTOTIMERFILTERINCLUDE, WHERE_AUTOTIMERFILTEREXTENSION]):
            domain = p.filterdomain + "." if p.filterdomain else ""
            filterKey = domain + p.name
            pluginFilter =  AutoTimerFilterDefiniton( p.filterdomain, p.name, p.description, p, p.fncParams)
            self.filters[filterKey] = pluginFilter
            # ToDo: Create Lists for each WHERE and only show filters in the right places...

        self.filterSelection = []
        
        for filterKey, filterParams in iteritems( self.filters ):
            self.filterSelection.append((filterKey, filterParams.description))
    
    def checkFilter(self, filterType, timer, title, short, extended, dayofweek, serviceref, eit, begin, duration):
        atLog( ATLOG_INFO, "checkFilter: Start checking filters of type %s" % (atextensiontypes[filterType]) )
        if filterType == AT_EXCLUDE:
            filterEntries = timer.exclude 
            defaultReturn = False
        elif filterType == AT_INCLUDE:
            filterEntries = timer.include
            defaultReturn = len(filterEntries) == 0 # Return a Filter match, if the include filter is empty, else check filters...
        else:
            filterEntries = timer.extension
            defaultReturn = True # Extensions return True by default

        for filter in filterEntries:
            filterKey = filter.filterKey
            
            atLog( ATLOG_DEBUG, "checkFilter: filterKey=", filterKey )
            if filterKey in self.filters.keys():
                atLog( ATLOG_DEBUG, "checkFilter: filterDefinition found" )
                filterDefinition = self.filters[filterKey]
                filterName = filterDefinition.name
                fnc = filterDefinition.fnc
                if fnc:
                    try:
                        atLog( ATLOG_DEBUG, "checkFilter: calling filterFnc=", fnc.__name__ )
                        checkResult = fnc( filterName=filterName, timer=timer, title=title, short=short, extended=extended, \
                                       dayofweek=dayofweek, eit=eit, begin=begin, duration=duration, **filter.paramValues )
                        if checkResult:
                            atLog( ATLOG_INFO, "checkFilter: Filter %s returned TRUE" % (filterName) )
                            return True
                    except Exception, e:
                        atLog( ATLOG_ERROR, "checkFilter: Filter error in filter %s: %s" %(filterKey, e) )           
                else:
                    atLog( ATLOG_ERROR, "checkFilter: Filter error in filter %s: No fnc given" %filterKey )
        atLog( ATLOG_INFO, "checkFilter: No match. returning:", defaultReturn )
        return defaultReturn
    
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
        
filterDefinitions = AutoTimerFilterDefinitions()
    
class AutoTimerFilterList(Screen, ConfigListScreen):
    """Edit AutoTimer Filter"""

    skin = """<screen name="AutoTimerFilterList" title="Edit AutoTimer Filters" position="center,center" size="565,280">
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

    def __init__(self, session, filterset, excludes, includes, extensions):
        Screen.__init__(self, session)

        # Summary
        self.setup_title = _("AutoTimer Filters")
        self.onChangedEntry = []

        self.enabled = NoSave(ConfigEnableDisable(default = filterset))

        self.lenExcludes = 0
        self.lenIncludes = 0
        self.editPos = -1
        self.excludes = excludes
        self.includes = includes
        self.extensions = extensions

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

    def changed(self):
        for changeFnc in self.onChangedEntry:
            try:
                changeFnc()
            except Exception:
                pass

    def setCustomTitle(self):
        self.setTitle(_("Edit AutoTimer filters"))

    def getCurrentEntry(self):
        return self["config"].getCurrent()[0]

    def getCurrentValue(self):
        return str(self["config"].getCurrent()[1].getText())

    def createSummary(self):
        return SetupSummary

    def saveCurrent(self):
        self.excludes = []
        self.includes = []
        self.extensions = []
        
        # Warning, accessing a ConfigListEntry directly might be considered evil!

        idx = -1
        for item in self["config"].getList()[:]:
            idx += 1
            # Skip empty entries (and those which are no filters)
            if item[1].value == "" or idx < 1:
                continue
            elif idx < self.lenExcludes:
                self.excludes.append(item[2])
            elif idx < self.lenIncludes:
                self.includes.append(item[2])
            else:
                self.extensions.append(item[2])

    def refresh(self, *args, **kwargs):
        self.saveCurrent()

        self.reloadList()
        self["config"].setList(self.list)

    def reloadList(self):
        self.list = [
            getConfigListEntry(_("Enable Filtering"), self.enabled),
        ]

        if self.enabled.value:
            if self.excludes:
                self.list.extend([
                    self.getConfigForFilterEntry(x)
                        for x in self.excludes
            ])
     
            self.lenExcludes = len(self.list)
            if self.includes:
                self.list.extend([
                    self.getConfigForFilterEntry(x)
                        for x in self.includes
            ])
                
            self.lenIncludes = len(self.list)
            if self.extensions:
                self.list.extend([
                    self.getConfigForFilterEntry(x)
                        for x in self.extensions
            ])
            

    def remove(self):
        idx = self["config"].getCurrentIndex()
        if idx and idx > 0:
            if idx < self.lenExcludes:
                self.lenExcludes -= 1
                self.lenIncludes -= 1
            elif idx < self.lenIncludes:
                self.lenIncludes -= 1

            list = self["config"].getList()
            list.remove(self["config"].getCurrent())
            self["config"].setList(list)

    def new(self):
        self.editPos = -1
        newFilter = AutoTimerFilterEntry()
        self.session.openWithCallback(
            self.filterEditorCallback,
            AutoTimerFilterEditorAdvanced,
            newFilter 
        )

    def keyOK(self):
        idx = self["config"].getCurrentIndex()
        atLog( ATLOG_DEBUG, "FilterList, keyOK: idx= " + str(idx) )
        if idx and idx > 0:
            atLog( ATLOG_DEBUG, "FilterList, keyOK: current selected: ", self["config"].getCurrent()[2] )
            self.editPos = idx
            self.session.openWithCallback(
                self.filterEditorCallback,
                AutoTimerFilterEditorAdvanced,
                self["config"].getCurrent()[2]
        )

    def filterEditorCallback(self, ret):
        if ret is not None:
            myList = self["config"].getList()

            myFilter = ret
            entry = self.getConfigForFilterEntry(myFilter)
            
            if self.editPos == -1: # New?
                if myFilter.filterType == AT_EXCLUDE:
                    pos = self.lenExcludes
                    self.lenExcludes += 1
                    self.lenIncludes += 1
                elif myFilter.filterType == AT_INCLUDE:
                    pos = self.lenIncludes
                    self.lenIncludes += 1
                else:
                    pos = len(self.list)               
                myList.insert(pos, entry)
            else:
                pos = self.editPos
                myList[pos] = entry
                
            self["config"].setList(myList)

    def getConfigForFilterEntry(self, curFilter):
        filterType = curFilter.filterType
        entryType = atextensiontypes[filterType] + " " + curFilter.filterDescription
        
        filterEntryDescription = curFilter.description
        
        entry = getConfigListEntry(entryType, NoSave(ConfigSelection(choices = [(filterEntryDescription, filterEntryDescription)], default = filterEntryDescription)), curFilter)
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
            self.excludes,
            self.includes,
            self.extensions
        ))
class AutoTimerFilterEditorAdvanced(Screen, ConfigListScreen):
    """Edit AutoTimer Filter"""

    skin = """<screen name="AutoTimerFilterEditorAdvanced" title="Edit AutoTimer Filter" position="center,center" size="565,280">
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

    def __init__(self, session, curFilter):
        Screen.__init__(self, session)

        # Summary
        self.setup_title = _("AutoTimer Filter")  
        self.onChangedEntry = []
        self.curFilter = curFilter        
        self.filterType = NoSave(ConfigSelection(choices = [(AT_EXCLUDE, _("Exclude")),(AT_INCLUDE, _("Include"))], default = self.curFilter.filterType))         
        self.filterSelection = NoSave(ConfigSelection(choices = filterDefinitions.filterSelection, default = self.curFilter.filterKey))
        
        self.filterSelection.addNotifier(self.refresh, initial_call = False)
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
        self.setTitle(_("Edit AutoTimer"))
        
    def refresh(self, *args, **kwargs):
        self.reloadList()
        self["config"].setList(self.list) 
    
    def reloadList(self):
        self.list = [
            getConfigListEntry(_("Type of Filter"), self.filterType, "filterType"),
            getConfigListEntry(_("Filter"), self.filterSelection, "filterName")
        ]

        self.descriptionIndices = []
        #Get the filter- definition for the selected filter
        filterDefinition = filterDefinitions.filters[self.filterSelection.getValue()]

        idx = len(self.list)
        for paramName,filterParam in iteritems( filterDefinition.fncParams ):
            paramValue = self.curFilter.paramValues[filterParam.name] if filterParam.name in self.curFilter.paramValues else filterParam.default
            paramDescription = filterParam.description
            paramConfigType = filterParam.configtype
            idx += 1
            if filterParam.useasfilterlabel:
                atLog( ATLOG_DEBUG, "FilterEditorAdvanced, reloadList: found label parameter= ", paramDescription)
                self.descriptionIndices.append(idx)
            if paramConfigType == "ConfigText":
                newEntry = getConfigListEntry( paramDescription, NoSave(ExtendedConfigText(fixed_size = False, default=paramValue)), paramName)
            elif paramConfigType == "ConfigSelection":
                paramChoices = filterParam.choices
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
            
            atLog( ATLOG_DEBUG, "FilterEditorAdvanced, reloadList: newEntry=", newEntry)
            self.list.append(newEntry)   
            atLog( ATLOG_DEBUG, "FilterEditorAdvanced, reloadList: list=", self.list)

    def ok(self):
        self.curFilter.paramValues = {}
        self.curFilter.description = ""
        idx = 0
        descValues = 0
        firstValue = ""
        firstParam = ""
        atLog( ATLOG_DEBUG, "FilterEditorAdvanced, ok: configList=", self["config"].getList())
        for item in self["config"].getList()[:]:
            atLog( ATLOG_DEBUG, "FilterEditorAdvanced, ok: item= ", item)
            idx += 1
            curValue = item[1].value
            atLog( ATLOG_INFO, "FilterEditorAdvanced, ok: curValue= "+ str(curValue) )
            curParam = item[2]
            atLog( ATLOG_INFO, "FilterEditorAdvanced, ok: curParam: ", curParam )
            
            curChoices = {curValue: curValue}
            if hasattr(item[1], "choices"):
                if item[1].choices:
                    curChoices = item[1].choices 
            atLog( ATLOG_DEBUG, "FilterEditorAdvanced, ok: curChoices: ", curChoices )

            # Skip empty entries (and those which are no filters)
            if idx == 1:
                self.curFilter.filterType = curValue
            elif idx == 2:
                self.curFilter.filterKey = curValue
            elif curValue == "":
                continue
            else:
                atLog( ATLOG_DEBUG, "FilterEditorAdvanced, ok: descriptionIndices= ", self.descriptionIndices)
                atLog( ATLOG_DEBUG, "FilterEditorAdvanced, ok: idx= ", idx)
                if idx in self.descriptionIndices:
                    atLog( ATLOG_DEBUG, "FilterEditorAdvanced, ok: descriptionParam found with idx=", str(idx) )

                    descValues += 1
                    if descValues == 1:
                        self.curFilter.description = curChoices[curValue]
                        firstParam = curParam
                        firstValue = curChoices[curValue]
                    else:
                        self.curFilter.description += ", " + curParam + ": " + curChoices[curValue]
                    if descValues == 2: # Only add Parametername, if there is more than one param to return, was omitted in descValues == 1
                        self.curFilter.description = firstParam + ": " + self.curFilter.description  
                self.curFilter.paramValues[curParam] = curValue

        if self.curFilter.description == "":
            self.curFilter.description = firstValue if firstValue else "-"
        
        self.close(self.curFilter)
        
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
            
def getAutoTimerPluginDescriptor( filterDomain, name, description, where, fnc, fncParams ):
    if not fnc == None:
        descriptor = PluginDescriptor( name=name, description=description, where=where, fnc=fnc )
        descriptor.filterDomain = filterDomain
        descriptor.fncParams = {}
        for name,param in iteritems( fncParams.iteritems ):
            descriptor.fncParams[name] = param if isinstance(param, AutoTimerFilterParam) else AutoTimerFilterParam( name=str(param) )
    else:
        descriptor = None
    return descriptor

       