DEVELOPER_KEY = "AIzaSyDUp-wKizINw0m6n_7_DInK6A4qKnMaKFU"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

from apiclient.discovery import build

def buildYoutube():
	return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)