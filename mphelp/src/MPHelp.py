from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText


class HelpPage:
	def __init__(self, title, text):
		self.__title = title
		self.__text = text

	def getTitle(self):
		return self.__title

	def getText(self):
		return self.__text

	def __getitem__(self, item):
		if item == 0:
			return self.getTitle()
		elif item == 1:
			return self.getText()
		raise IndexError("no more items")


class MPHelp(Screen):
	skin = """
		<screen name="MPHelp" title="MPHelp" position="center,120" size="820,520">
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,5" size="200,40" alphatest="on"/>
		    <ePixmap pixmap="skin_default/buttons/green.png" position="210,5" size="200,40" alphatest="on"/>
		    <ePixmap pixmap="skin_default/buttons/yellow.png" position="410,5" size="200,40" alphatest="on"/>
		    <ePixmap pixmap="skin_default/buttons/blue.png" position="610,5" size="200,40" alphatest="on"/>
		    <widget source="key_red" render="Label" position="10,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		    <widget source="key_green" render="Label" position="210,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		    <widget source="key_yellow" render="Label" position="410,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		    <widget source="key_blue" render="Label" position="610,5" size="200,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" shadowColor="black" shadowOffset="-2,-2"/>
		    <eLabel	position="10,50" size="800,1" backgroundColor="grey"/>
		    <widget render="Label" source="title" position="10,60" size="800,30" font="Regular;26"/>
		    <widget name="detailtext" position="10,120" size="800,390" font="Regular;21"/>
		</screen>"""

	def __init__(self, session, pages, title="", additionalSkin=""):
		Screen.__init__(self, session)
		if additionalSkin:
			self.skinName = [additionalSkin, "MPHelp"]
		self.designatedTitle = title

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText("")
		if len(pages) > 1:
			self["key_blue"] = StaticText(">>")
		else:
			self["key_blue"] = StaticText("")
		self["title"] = StaticText()
		self["detailtext"] = ScrollLabel()

		self.pages = pages
		self.curPage = 0

		self["actions"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"back": self.close,
			"red": self.close,
			"up": self.pageUp,
			"down": self.pageDown,
			"left": self.pageUp,
			"right": self.pageDown,
			"yellow": self.prevPage,
			"blue": self.nextPage,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if self.designatedTitle:
			self.setTitle(self.designatedTitle)
		self.setPage(0)

	def setPage(self, newPage):
		try:
			title, text = self.pages[newPage]
		except IndexError:
			title = "Invalid Help Page"
			text = "You managed to jump to an invalid page. Stop it :-)"
			newPage = self.curPage
		self["Title"].text = title.encode('utf-8', 'ignore')
		self["detailtext"].setText(text.encode('utf-8', 'ignore'))
		self.curPage = newPage

	def pageUp(self):
		self["detailtext"].pageUp()

	def pageDown(self):
		self["detailtext"].pageDown()

	def prevPage(self):
		curPage = self.curPage
		if curPage > 0:
			self.setPage(curPage - 1)

		self["key_blue"].setText(">>")
		if self.curPage > 0:
			self["key_yellow"].setText("<<")
		else:
			self["key_yellow"].setText("")

	def nextPage(self):
		curPage = self.curPage
		Len = len(self.pages) - 1
		if curPage < Len:
			self.setPage(curPage + 1)

		self["key_yellow"].setText("<<")
		if self.curPage < Len:
			self["key_blue"].setText(">>")
		else:
			self["key_blue"].setText("")


__all__ = ['HelpPage', 'MPHelp']
