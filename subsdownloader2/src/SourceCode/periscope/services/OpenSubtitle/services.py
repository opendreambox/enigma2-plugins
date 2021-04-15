# -*- coding: utf-8 -*-

#   This file is part of periscope.
#
#    periscope is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    periscope is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with periscope; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import socket # For timeout purposes
from Plugins.Extensions.SubsDownloader2.SourceCode import xmlrpclib
import os
import struct
import commands
import traceback
import logging

#from Screens.MessageBox import MessageBox
#from Screens.Screen import Screen

#try:
#	import gzip
#except:
#	from Plugins.Extensions.SubsDownloader2.SourceCode import gzip
import gzip
from Plugins.Extensions.SubsDownloader2.SourceCode.periscope import SubtitleDatabase

#from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.utilities import toOpenSubtitles_two
from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.utilities import LANGUAGES, languageTranslate

"""OS_LANGS ={ "en": "eng",
            "fr" : "fre",
            "hu": "hun",
            "cs": "cze",
            "pl" : "pol",
            "sk" : "slo",
            "pt" : "por",
            "pb" : "pob",  # this was added by me
            "pt-br" : "pob",
            "es" : "spa",
            "el" : "ell",
            "ar":"ara",
            'sq':'alb',
            "hy":"arm",
            "ay":"ass",
            "bs":"bos",
            "bg":"bul",
            "ca":"cat",
            "zh":"chi",
            "hr":"hrv",
            "da":"dan",
            "nl":"dut",
            "eo":"epo",
            "et":"est",
            "fi":"fin",
            "gl":"glg",
            "ka":"geo",
            "de":"ger",
            "he":"heb",
            "hi":"hin",
            "is":"ice",
            "id":"ind",
            "it":"ita",
            "ja":"jpn",
            "kk":"kaz",
            "ko":"kor",
            "lv":"lav",
            "lt":"lit",
            "lb":"ltz",
            "mk":"mac",
            "ms":"may",
            "no":"nor",
            "oc":"oci",
            "fa":"per",
            "ro":"rum",
            "ru":"rus",
            "sr":"scc",
            "sl":"slv",
            "sv":"swe",
            "th":"tha",
            "tr":"tur",
            "uk":"ukr",
            "vi":"vie"}"""

OS_LANGS = {}
for x in LANGUAGES:
  #languageTranslate(x[0], 0, 2)
  #languageTranslate(x[0], 0, 3)
  OS_LANGS.update({languageTranslate(x[0], 0, 2): languageTranslate(x[0], 0, 3)})


class OpenSubtitle(SubtitleDatabase.SubtitleDB):
    url = "http://www.opensubtitles.org/"
    site_name = "OpenSubtitles"

    def __init__(self, config, cache_folder_path):
        super(OpenSubtitle, self).__init__(OS_LANGS)
        self.server_url = 'http://api.opensubtitles.org/xml-rpc'
        self.revertlangs = dict(map(lambda item: (item[1], item[0]), self.langs.items()))

    def process(self, filepath, langs):
        ''' main method to call on the plugin, pass the filename and the wished
        languages and it will query OpenSubtitles.org '''

         #Convert subtitle language to plugin requirements
        temp_lang = []
        for x in langs:
            if x == "All":
                temp_lang = []
                break
            elif x == "None":
                pass
            else:
                #temp_lang.append(toOpenSubtitles_two(str(x)))
                temp_lang.append(languageTranslate(x, 0, 2))
        langs = temp_lang
        #Convert subtitle language to plugin requirements

        if os.path.isfile(filepath):
            filehash = self.hashFile(filepath)
            size = os.path.getsize(filepath)
            fname = self.getFileName(filepath)
            return self.query(moviehash=filehash, langs=langs, bytesize=size, filename=fname)
        else:
            fname = self.getFileName(filepath)
            return self.query(langs=langs, filename=fname)

#    def createFile(self, subtitle):
    def createFile(self, subtitle, filename):
        '''pass the URL of the sub and the file it matches, will unzip it
        and return the path to the created file'''
        suburl = subtitle["link"]
        #videofilename = subtitle["filename"]
        videofilename = filename
        srtbasefilename = videofilename.rsplit(".", 1)[0]
        self.downloadFile(suburl, srtbasefilename + ".srt.gz")
#        try:
        f = gzip.open(srtbasefilename + ".srt.gz")
        dump = open(srtbasefilename + ".srt", "wb")
        dump.write(f.read())
        dump.close()
        f.close()
        os.remove(srtbasefilename + ".srt.gz")
        return srtbasefilename + ".srt"
#        except:
#            return "None"

    def hashFile(self, name):
        '''
        Calculates the Hash à-la Media Player Classic as it is the hash used by OpenSubtitles.
        By the way, this is not a very robust hash code.
        '''

        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat)

        f = open(name, "rb")
        filesize = os.path.getsize(name)
        hash = filesize

        if filesize < 65536 * 2:
            logging.error("File %s is too small (SizeError < 2**16)" % name)
            return []

        for x in range(65536 / bytesize):
            buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number

        f.seek(max(0, filesize - 65536), 0)
        for x in range(65536 / bytesize):
            buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF

        f.close()
        returnedhash = "%016x" % hash
        return returnedhash

    def query(self, filename, imdbID=None, moviehash=None, bytesize=None, langs=None):
        ''' Makes a query on opensubtitles and returns info about found subtitles.
            Note: if using moviehash, bytesize is required.    '''

        #Prepare the search
        search = {}
        sublinks = []
        if moviehash:
          search['moviehash'] = moviehash
        if imdbID:
          search['imdbid'] = imdbID
        if bytesize:
          search['moviebytesize'] = str(bytesize)
        if langs:
          search['sublanguageid'] = ",".join([self.getLanguage(lang) for lang in langs])
        if len(search) == 0:
            logging.debug("No search term, we'll use the filename")
            # Let's try to guess what to search:
            guessed_data = self.guessFileData(filename)
            search['query'] = guessed_data['name']
            logging.debug(search['query'])

        #Login
        self.server = xmlrpclib.Server(self.server_url)
        socket.setdefaulttimeout(10)
        try:
            log_result = self.server.LogIn("", "", "eng", "periscope")
            logging.debug(log_result)
            token = log_result["token"]
        except Exception:
            logging.error("Open subtitles could not be contacted for login")
            token = None
            socket.setdefaulttimeout(None)
            return []
        if not token:
            logging.error("Open subtitles did not return a token after logging in.")
            token = None
            return []

        # Search
        self.filename = filename #Used to order the results
        sublinks += self.get_results(token, search)

        # Logout
        try:
            self.server.LogOut(token)
        except:
            logging.error("Open subtitles could not be contacted for logout")
        socket.setdefaulttimeout(None)
        return sublinks

    def get_results(self, token, search):
        logging.debug("query: token='%s', search='%s'" % (token, search))
        try:
            if search:
                results = self.server.SearchSubtitles(token, [search])
        except Exception, e:
            logging.error("Could not query the server OpenSubtitles")
            logging.debug(e)
            return []
        logging.debug("Result: %s" % str(results))

        sublinks = []
        if results['data']:
            logging.debug(results['data'])
            # OpenSubtitles hash function is not robust ... We'll use the MovieReleaseName to help us select the best candidate
            for r in sorted(results['data'], self.sort_by_moviereleasename):
                # Only added if the MovieReleaseName matches the file
                result = {}
                result["release"] = r['SubFileName']
                result["link"] = r['SubDownloadLink']
                result["page"] = r['SubDownloadLink']
                result["lang"] = self.getLG(r['SubLanguageID'])
                if search.has_key("query"): #We are using the guessed file name, let's remove some results
                    if r["MovieReleaseName"].startswith(self.filename):
                        sublinks.append(result)
                    else:
                        logging.debug("Removing %s because release '%s' has not right start %s" % (result["release"], r["MovieReleaseName"], self.filename))
                else:
                    sublinks.append(result)
        return sublinks

    def sort_by_moviereleasename(self, x, y):
        ''' sorts based on the movierelease name tag. More matching, returns 1'''
        #TODO add also support for subtitles release
        xmatch = x['MovieReleaseName'] and (x['MovieReleaseName'].find(self.filename) > -1 or self.filename.find(x['MovieReleaseName']) > -1)
        ymatch = y['MovieReleaseName'] and (y['MovieReleaseName'].find(self.filename) > -1 or self.filename.find(y['MovieReleaseName']) > -1)
        #print "analyzing %s and %s = %s and %s" %(x['MovieReleaseName'], y['MovieReleaseName'], xmatch, ymatch)
        if xmatch and ymatch:
            if x['MovieReleaseName'] == self.filename or x['MovieReleaseName'].startswith(self.filename):
                return -1
            return 0
        if not xmatch and not ymatch:
            return 0
        if xmatch and not ymatch:
            return -1
        if not xmatch and ymatch:
            return 1
        return 0
