# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

import os, sys, traceback

from Tools.Directories import resolveFilename, SCOPE_PLUGINS

# Plugin framework
import imp, inspect

from PluginBase import PluginBase

# Constants
IBTS_PLUGINS_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/InfoBarTunerState/Handler/" )


class InfoBarTunerStatePlugins(object):

	def __init__(self):
		self.__plugins = {}
		self.loadPlugins(IBTS_PLUGINS_PATH, PluginBase)
		print "[IBTS Plugins]: " + str(self.__plugins)

	#######################################################
	# Module functions
	def loadPlugins(self, path, base):
		self.__plugins = {}
		
		if not os.path.exists(path):
			print "[IBTS Plugins]: Error: Path doesn't exist: " + path
			return
		
		# Import all subfolders to allow relative imports
		for root, dirs, files in os.walk(path):
			if root not in sys.path:
				sys.path.append(root)
		
		# List files
		files = [fname[:-3] for fname in os.listdir(path) if fname.endswith(".py") and not fname.startswith("__")]
		if not files:
			files = [fname[:-4] for fname in os.listdir(path) if fname.endswith(".pyo")]
		print "[IBTS Plugins]: Files: " + str(files)
		
		# Import Plugins
		for name in files:
			module = None
			
			if name == "__init__":
				continue
			
			try:
				fp, pathname, description = imp.find_module(name, [path])
			except Exception as e:
				print "[IBTS Plugins] Find module exception: " + str(e)
				fp = None
			
			if not fp:
				print "[IBTS Plugins] No module found: " + str(name)
				continue
			
			try:
				module = imp.load_module( name, fp, pathname, description)
			except Exception as e:
				print "[IBTS Plugins] Load exception: " + str(e)
			finally:
				# Since we may exit via an exception, close fp explicitly.
				if fp: fp.close()
			
			if not module:
				print "[IBTS Plugins] No module available: " + str(name)
				continue
			
			# Continue only if the attribute is available
			if not hasattr(module, name):
				print "[IBTS Plugins] Warning attribute not available: " + str(name)
				continue
			
			# Continue only if attr is a class
			attr = getattr(module, name)
			if not inspect.isclass(attr):
				print "[IBTS Plugins] Warning no class definition: " + str(name)
				continue
			
			# Continue only if the class is a subclass of the corresponding base class
			if not issubclass( attr, base):
				print "[IBTS Plugins] Warning no subclass of base: " + str(name)
				continue
			
			# Instantiate module and add it to the module list
			instance = self.instantiatePlugin(attr)
			if instance:
				self.__plugins[name] = instance
	
	def isPlugin(self, name):
		return name in self.__plugins
	
	def getPlugin(self, name):
		return self.__plugins[name]

	def getPlugins(self):
		return sorted( self.__plugins.values(), key=lambda x: (x.getType()), reverse=True )

	def instantiatePlugin(self, module):
		if module and callable(module):
			# Create instance
			try:
				return module()
			except Exception as e:
				print "[IBTS] Instantiate exception: " + str(module) + "\n" + str(e)
				if sys.exc_info()[0]:
					print "Unexpected error: " + str(sys.exc_info()[0])
					traceback.print_exc(file=sys.stdout)
					return None
		else:
			print "[IBTS] Module is not callable: " + str(module.getClass())
			return None
