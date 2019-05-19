from __future__ import print_function
import sqlite3

SI_DATABASE_PATH = '/etc/enigma2/SkipIntro.db'
SI_DATABASE_VERSION = '1.0'

class SIDatabase:
	def __init__(self):
		self._dbfilepath = SI_DATABASE_PATH
		self._srDBConn = None
		self.connect()

	def __del__(self):
		self.close()

	def connect(self):
		self._srDBConn = sqlite3.connect(self._dbfilepath)
		self._srDBConn.isolation_level = None
		self._srDBConn.text_factory = lambda x: str(x.decode("utf-8"))

	def close(self):
		if self._srDBConn:
			self._srDBConn.close()
			self._srDBConn = None

	def initialize(self):
		cur = self._srDBConn.cursor()
		cur.execute("CREATE TABLE IF NOT EXISTS dbInfo ("
					"Key TEXT NOT NULL UNIQUE, "
					"Value TEXT NOT NULL DEFAULT '')")
		cur.execute("INSERT OR IGNORE INTO dbInfo (Key, Value) VALUES ('Version', ?)", [SI_DATABASE_VERSION])

		cur.execute("CREATE TABLE IF NOT EXISTS 'skipTimes' ("
					"'name' TEXT UNIQUE, "
					"'skipTime' INTEGER)")

		cur.close()

	def beginTransaction(self):
		cur = self._srDBConn.cursor()
		cur.execute("BEGIN TRANSACTION")
		cur.close()

	def commit(self):
		cur = self._srDBConn.cursor()
		cur.execute("COMMIT")
		cur.close()

	def rollback(self):
		cur = self._srDBConn.cursor()
		cur.execute("ROLLBACK")
		cur.close()

	def getVersion(self):
		dbVersion = None
		try:
			cur = self._srDBConn.cursor()
			cur.execute("SELECT Value FROM dbInfo WHERE Key='Version'")
			row = cur.fetchone()
			if row:
				(dbVersion,) = row
			cur.close()
		except:
			pass

		return dbVersion

	def hasSkipTime(self, name):
		cur = self._srDBConn.cursor()
		cur.execute("SELECT COUNT(*) FROM skipTimes WHERE name LIKE ?", [name + '%'])
		result = (cur.fetchone()[0] > 0)
		cur.close()
		return result

	def setSkipTime(self, name, skipTime):
		cur = self._srDBConn.cursor()
		cur.execute("REPLACE INTO skipTimes (name, skipTime) VALUES (?, ?)", (name, skipTime))
		cur.close()

	def getSkipTime(self, name, season):
		print("=== getSkipTime", name, season)
		skipTime = 0
		dbname = ""
		cur = self._srDBConn.cursor()
		cur.execute("SELECT skipTime, name FROM skipTimes WHERE name = ?", [name + season])
		row = cur.fetchone()
		if row:
			(skipTime, dbname, ) = row
		else:
			cur.execute("SELECT skipTime, name FROM skipTimes WHERE name LIKE ? order by name COLLATE NOCASE", [name + "%"])
			row = cur.fetchone()
			if row:
				(skipTime, dbname, ) = row
		cur.close()
		return int(skipTime), dbname

	def renameSeries(self, oldname, newname):
		cur = self._srDBConn.cursor()
		cur.execute("UPDATE skipTimes SET name = ? WHERE name = ?", (newname, oldname))
		cur.close()

	def removeSkipTime(self, name):
		cur = self._srDBConn.cursor()
		cur.execute("DELETE FROM skipTimes WHERE name = ?", [name])
		cur.close()

	def getAllSkipTimes(self):
		cur = self._srDBConn.cursor()
		cur.execute("SELECT * FROM skipTimes order by name COLLATE NOCASE")
		entries = cur.fetchall()
		cur.close()
		return entries
