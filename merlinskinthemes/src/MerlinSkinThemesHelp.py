from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Screens.Screen import Screen

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_HALIGN_RIGHT, RT_VALIGN_CENTER
from skin import TemplatedListFonts, componentSizes


class MerlinSkinThemesHelpList(MenuList):
	SKIN_COMPONENT_KEY = "MerlinSkinThemesHelpList"
	SKIN_COMPONENT_KEY_WIDTH = "keyWidth"
	SKIN_COMPONENT_DESCR_WIDTH = "descrWidth"
	SKIN_COMPONENT_ITEM_HEIGHT = "itemHeight"

	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		
		sizes = componentSizes[MerlinSkinThemesHelpList.SKIN_COMPONENT_KEY]
		self.componentItemHeight = sizes.get(MerlinSkinThemesHelpList.SKIN_COMPONENT_ITEM_HEIGHT, 40)
		self.keyWidth = sizes.get(MerlinSkinThemesHelpList.SKIN_COMPONENT_KEY_WIDTH, 250)
		self.descrWidth = sizes.get(MerlinSkinThemesHelpList.SKIN_COMPONENT_DESCR_WIDTH, 750)
		
		tlf = TemplatedListFonts()
		self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		self.l.setItemHeight(self.componentItemHeight)
		self.l.setBuildFunc(self.buildEntry)
		
	def buildEntry(self, keyText, descriptionText):
		res = [(keyText, descriptionText),
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, self.keyWidth, self.componentItemHeight, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, keyText),
			(eListboxPythonMultiContent.TYPE_TEXT, 5 + self.keyWidth, 0, self.descrWidth, self.componentItemHeight, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, descriptionText)
				]
		return res


class MerlinSkinThemesHelp(Screen):
	skin = """
		<screen position="center,center" size="1000,400" title="MerlinSkinThemes - Help" backgroundColor="#00303030" >
			<widget name="help" position="0,0" size="1000,360" scrollbarMode="showNever" transparent="1" zPosition="2"/>
		</screen>"""
		
	def __init__(self, session, helpType="skin"):
		Screen.__init__(self, session)
		
		self["OkCancelActions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self.close,
		}, -1)
		
		self.setTitle(_("MerlinSkinThemes - Help"))
		
		helpKeyDescriptionList = [
		("OK", _("Switch to themes/designs config screen for selected skin")),
		("Exit", _("Close the plugin without saving changes")),
		(_("Menu"), _("Open context menu to access functionality like help and settings")),
		(_("Red"), _("Close the plugin without saving changes")),
		(_("Green"), _("Activate selected skin")),
		(_("Yellow"), _("Create themes.xml for selected skin")),
		(_("Blue"), _("Open context menu to access functionality like help and settings"))
		]
		
		helpKeyDescriptionList2 = [
		("OK", _("Switch to themes/designs config screen for selected skin")),
		("Exit", _("Close the plugin without saving changes")),
		(_("Menu"), _("Open context menu to access functionality like help and settings")),
		(_("Info"), _("Display an information about impact of setting")),
		(_("Red"), _("Close the plugin without saving changes")),
		(_("Green"), _("Apply selected theme")),
		(_("Yellow"), _("Save configuration as design / Delete design")),
		(_("Blue"), _("Open context menu to access functionality like help and settings"))		
		]
		
		self["help"] = MerlinSkinThemesHelpList([])
		
		if helpType == "SkinsList":
			self["help"].l.setList(helpKeyDescriptionList)
		else:
			self["help"].l.setList(helpKeyDescriptionList2)
