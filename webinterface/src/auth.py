# Password verfication stuff
from crypt import crypt
from pwd import getpwnam
from spwd import getspnam

def check_passwd(name, passwd):
	cryptedpass = None
	try:
		cryptedpass = getpwnam(name)[1]
	except:
		return False

	#shadowed or not, that's the questions here
	if cryptedpass == 'x' or cryptedpass == '*':
		try:
			cryptedpass = getspnam(name)[1]
		except:
			return False

	if cryptedpass == '':
		return True

	return crypt(passwd, cryptedpass) == cryptedpass