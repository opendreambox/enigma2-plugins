#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Property GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Property GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Property GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Components.Sources.Source import Source
from Plugins.Extensions.InternetRadio.InternetRadioFavoriteConfig import InternetRadioFavoriteConfig


class InternetRadioWebFavoriteList(Source):
	def __init__(self):
		Source.__init__(self)

	def getFavoritesList(self):
		favoriteConfig = InternetRadioFavoriteConfig()
		return favoriteConfig.getFavoriteList(html=True)

	def handleCommand(self, cmd):
		self.getFavoritesList()

	list = property(getFavoritesList)
	lut = {"Name": 0, "Text": 1, "Type": 2, "Tags": 3, "Country": 4, "Homepage": 5}
