from __future__ import absolute_import
import sys
sys.argv = ["enigma2"] #HACKFIX FOR argparse reading sys.argv[0] wihtout checking sys.argc

from . import TwitchChannelListServiceProvider