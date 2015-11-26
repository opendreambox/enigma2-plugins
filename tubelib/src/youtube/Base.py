DEVELOPER_KEY = "AIzaSyDUp-wKizINw0m6n_7_DInK6A4qKnMaKFU"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

from apiclient.discovery import build
from oauth2client.file import Storage

import httplib2

def loadCredentials(credentials_file):
	credentials = None
	storage = Storage(credentials_file)
	credentials = storage.get()
	return credentials

def saveCredentials(credentials_file, credentials):
	try:
		storage = Storage(credentials_file)
		storage.put(credentials)
		return True
	except:
		return False

def buildYoutube(credentials=None):
	if credentials:
		return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY, http=credentials.authorize(httplib2.Http()))
	else:
		return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)