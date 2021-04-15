# -*- coding: UTF-8 -*-

# Attention this is a Frankenstein Monster. Patched from other pieces of code,
# ugly and may not work at all. Feel free to improve, change anything.
# I do not know how to code, especially in Python, at all.
# Credits to amet, Guilherme Jardim, and many more.
# mrto

import urllib2
import re
import string
import sys
import os
#, xbmc
from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.utilities import log, twotofull
from Plugins.Extensions.SubsDownloader2.SourceCode.archives_extractor import zip_extractor
from Screens.MessageBox import MessageBox

#_ = sys.modules[ "__main__" ].__language__

main_url = "http://napisy.me/search.php?str="
down_url = "http://napisy.me/download/sr/"

subtitle_pattern = 'alt="(.+?)" border="0" />[\r\n\t ]+?</div>[\r\n\t ]+?<div class="title">[\r\n\t ]+?<a href="javascript:void\(0\);" onclick="javascript:pobierzNapis\(\'(.+?)\'\);" title="Wydanie: (.+?)" class="vtip">[ \r\n]*?                                (.+?)[ \r\n]*?</a>'


def getallsubs(content, title, subtitles_list, file_original_path):
    for matches in re.finditer(subtitle_pattern, content):
      jezyk, numer_napisu, wydanie, tytul = matches.groups()
      if 'other' in jezyk:
          continue
      else:
          jezyk = jezyk
      link = "%s%s/" % (down_url, numer_napisu)
      log(__name__, "Subtitles found: %s %s (link=%s)" % (tytul, wydanie, link))
      obraz_flagi = "flags/%s.gif" % (jezyk)
      lang = twotofull(jezyk)
      tytul_pelny = '%s %s' % (tytul, wydanie)
      wydanie_sclean = wydanie.replace(" ", "")
      wydanie_clean = wydanie_sclean.replace(",", ";")
      wydanie_srednik = '%s;' % (wydanie_clean)
      for wydania in re.finditer('(.+?);', wydanie_srednik):
          wydania = wydania.group()
      wydania_clean = wydania.replace(";", "")
      wydania_upper = wydania_clean.upper()
      filepatch_upper = file_original_path.upper()
      if wydania_upper in filepatch_upper:
        sync_value = True
      else:
        sync_value = False
      subtitles_list.append({'filename': tytul_pelny, 'sync': sync_value, 'link': link, 'language_flag': obraz_flagi, 'language_name': lang, 'rating': ""})

#def search_subtitles( file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack ): #standard input


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack, screen_sessiom): #standard input
    subtitles_list = []
    msg = ""
    if len(tvshow) > 0:
      for rok in re.finditer(' \(\d\d\d\d\)', tvshow):
          rok = rok.group()
          if len(rok) > 0:
              tvshow = tvshow.replace(rok, "")
          else:
              continue
      tvshow_plus = tvshow.replace(" ", "+")
      if len(str(season)) < 2:
        season_full = '0%s' % (season)
      else:
        season_full = str(season)
      if len(str(episode)) < 2:
        episode_full = '0%s' % (episode)
      else:
        episode_full = str(episode)
      url = '%s%s+%sx%s' % (main_url, tvshow_plus, season_full, episode_full)
    else:
      original_title = title #xbmc.getInfoLabel("VideoPlayer.OriginalTitle")
      log(__name__, "Original title: [%s]" % (original_title))
      movie_title_plus = original_title.replace(" ", "+")
      url = '%s%s' % (main_url, movie_title_plus)
    log(__name__, "Pobieram z [ %s ]" % (url))
    response = urllib2.urlopen(url)
    content = response.read()
    getallsubs(content, title, subtitles_list, file_original_path)
    return subtitles_list, "", "" #standard output

#def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id): #standard input


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id, screen_session):  #standard input
    import urllib
    f = urllib.urlopen(subtitles_list[pos]["link"])
    language = subtitles_list[pos]["language_name"]

    local_tmp_file = os.path.join(tmp_sub_dir, "zipsubs.zip")
    log(__name__, "Saving subtitles to '%s'" % (local_tmp_file))

    local_file = open(zip_subs, "w" + "b")
    local_file.write(f.read())
    local_file.close()
    zipped_file = zip_extractor(zip_subs, destination_dir=tmp_sub_dir)
    subs_file = zipped_file.extract_zipped_file()
    os.remove(zip_subs)
    return True, language, subs_file #standard output
