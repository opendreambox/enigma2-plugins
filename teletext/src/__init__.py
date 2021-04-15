def _log(message):
  print "[TeleText]", message
  

def _debug(message):
  d = open("/tmp/dbttcp.log", "a")
  d.write("[TeleText] %s\n" % message)
  d.close()
