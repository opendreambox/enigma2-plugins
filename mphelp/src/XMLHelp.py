from MPHelp import HelpPage
from xml.etree.cElementTree import parse as cet_parse

class XMLHelpPage(HelpPage):
	def __init__(self, node, translate=_):
		# calling HelpPage.__init__ is not required
		self.node = node
		self.__translate = translate

	def getText(self):
		node = self.node.find('text')
		if node is not None:
			return self.__translate(node.get('value', ''))
		return ""

	def getTitle(self):
		return self.__translate(self.node.get('title', ''))

class XMLHelpReader:
	def __init__(self, filename, translate=_):
		# this may raise an exception, it is up to the caller to handle that
		self.__dom = cet_parse(filename).getroot()
		self.__translate = translate

	def __getitem__(self, index):
		if self.__dom:
			if index == 0:
				_ = self.__translate
				caption = self.__dom.get('caption', '')
				return lambda: _(caption)
			elif index == 1:
				_ = self.__translate
				return lambda: [XMLHelpPage(x, _) for x in self.__dom.findall('page')]
			elif index == 2:
				return self.__dom.get('skin', "") # additional skin name
			raise IndexError('no more indices')
		raise RuntimeError('no valid dom')

__all__ = ['XMLHelpReader']
