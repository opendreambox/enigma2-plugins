from . import _, ATLOG_LIST
from Components.config import config

ATLOG_DEBUG = "1"
ATLOG_INFO = "2"
ATLOG_WARN = "3"
ATLOG_ERROR = "4"

ATLOG_MESSAGES = {"1": "DEBUG",
                  "2": "INFO ",
                  "3": "WARN ",
                  "4": "ERROR"}

def atLog(logLevel, *args):
    cfgLogLevel = config.plugins.autotimer.loglevel.value
    if logLevel >= cfgLogLevel:
        strargs = ""
        logLevelText = ATLOG_MESSAGES[logLevel] if logLevel in ATLOG_MESSAGES.keys() else "?????"
        for arg in args:
            if strargs: strargs += " "
            strargs += str(arg)
        print "[AutoTimer " + logLevelText + "] " + strargs
        
        if config.plugins.autotimer.logwrite.value:
            strargs += "\n"
            
            # Append to file
            f = None
            try:
                f = open(config.plugins.autotimer.logfile.value, 'a')
                f.write("[" + logLevelText + "] " + strargs)
            except Exception, e:
                print "[AutoTimer] atLog exception " + str(e)
            finally:
                if f:
                    f.close()