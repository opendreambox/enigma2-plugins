# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2022 Andreas Oberritter
# SPDX-License-Identifier: MIT
#

import hashlib
import sqlite3
import struct
from datetime import datetime

class EpgDatabase:
    def __init__(self, path):
        try:
            self._con = sqlite3.connect(path)
        except sqlite3.OperationalError as exc:
            raise ValueError("Can't access database at {}".format(path))

    def commit(self):
        self._con.commit()

    def cursor(self):
        return self._con.cursor()

    def hash(self, text):
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        integer, = struct.unpack("!i", digest[:4])
        return integer

    def add_unique_service(self, sid, tsid, onid, dvbnamespace):
        """
        CREATE TABLE T_Service (id INTEGER PRIMARY KEY, sid INTEGER NOT NULL, tsid INTEGER, onid INTEGER, dvbnamespace INTEGER, changed DATETIME NOT NULL DEFAULT current_timestamp);
        """
        cur = self.cursor()
        for (_id,) in cur.execute(
            "SELECT id FROM T_Service WHERE sid=? AND tsid=? AND onid=? AND dvbnamespace=? LIMIT 1",
            (sid, tsid, onid, dvbnamespace),
        ):
            return _id
        cur.execute(
            "INSERT INTO T_Service (sid, tsid, onid, dvbnamespace, changed) VALUES (?, ?, ?, ?, ?)",
            (sid, tsid, onid, dvbnamespace, datetime.utcnow()),
        )
        return cur.lastrowid

    def add_unique_source(self, source_name):
        """
        CREATE TABLE T_Source (id INTEGER PRIMARY KEY, source_name TEXT NOT NULL, priority INTEGER NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp);
        """
        cur = self.cursor()
        for (_id,) in cur.execute(
            "SELECT id FROM T_Source WHERE source_name=? LIMIT 1", (source_name,)
        ):
            return _id
        cur.execute(
            "INSERT INTO T_Source (source_name, priority, changed) VALUES (?, 1, ?)",
            (source_name, datetime.utcnow()),
        )
        return cur.lastrowid

    def add_unique_title(self, title):
        """
        CREATE TABLE T_Title (id INTEGER PRIMARY KEY, hash INTEGER NOT NULL UNIQUE, title TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp);
        """
        cur = self.cursor()
        _hash = self.hash(title)
        for _id, old_title in cur.execute(
            "SELECT id, title FROM T_Title WHERE hash=? LIMIT 1", (_hash,)
        ):
            if title != old_title:
                cur.execute("UPDATE T_Title SET title=? WHERE id=?", (title, _id))
            return _id
        cur.execute(
            "INSERT INTO T_Title (hash, title, changed) VALUES (?, ?, ?)",
            (_hash, title, datetime.utcnow()),
        )
        return cur.lastrowid

    def add_unique_short_description(self, short_description):
        """
        CREATE TABLE T_Short_Description (id INTEGER PRIMARY KEY, hash INTEGER NOT NULL UNIQUE, short_description TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp);
        """
        cur = self.cursor()
        _hash = self.hash(short_description)
        for _id, old_short_description in cur.execute(
            "SELECT id, short_description FROM T_Short_Description WHERE hash=? LIMIT 1", (_hash,)
        ):
            if short_description != old_short_description:
                cur.execute(
                    "UPDATE T_Short_Description SET short_description=? WHERE id=?",
                    (short_description, _id),
                )
            return _id
        cur.execute(
            "INSERT INTO T_Short_Description (hash, short_description, changed) VALUES (?, ?, ?)",
            (_hash, short_description, datetime.utcnow()),
        )
        return cur.lastrowid

    def add_unique_extended_description(self, extended_description):
        """
        CREATE TABLE T_Extended_Description (id INTEGER PRIMARY KEY, hash INTEGER NOT NULL UNIQUE, extended_description TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp);
        """
        cur = self.cursor()
        _hash = self.hash(extended_description)
        for _id, old_extended_description in cur.execute(
            "SELECT id, extended_description FROM T_Extended_Description WHERE hash=? LIMIT 1",
            (_hash,),
        ):
            if extended_description != old_extended_description:
                cur.execute(
                    "UPDATE T_Extended_Description SET extended_description=? WHERE id=?",
                    (extended_description, _id),
                )
            return _id
        cur.execute(
            "INSERT INTO T_Extended_Description (hash, extended_description, changed) VALUES (?, ?, ?)",
            (_hash, extended_description, datetime.utcnow()),
        )
        return cur.lastrowid

    def add_unique_event(self, service_id, begin_time, duration, source_id, dvb_event_id):
        """
        CREATE TABLE T_Event (id INTEGER PRIMARY KEY, service_id INTEGER NOT NULL, begin_time INTEGER NOT NULL, duration INTEGER NOT NULL, source_id INTEGER NOT NULL, dvb_event_id INTEGER, changed DATETIME NOT NULL DEFAULT current_timestamp);
        """
        cur = self.cursor()
        for _id, old_begin_time, old_duration in cur.execute(
            "SELECT id, begin_time, duration FROM T_Event WHERE service_id=? AND source_id=? AND dvb_event_id=? LIMIT 1",
            (service_id, source_id, dvb_event_id),
        ):
            if (begin_time, duration) != (old_begin_time, old_duration):
                cur.execute(
                    "UPDATE T_Event SET begin_time=?, duration=? WHERE id=?",
                    (begin_time, duration, _id),
                )
            return _id
        cur.execute(
            "INSERT INTO T_Event (service_id, begin_time, duration, source_id, dvb_event_id, changed) VALUES (?, ?, ?, ?, ?, ?)",
            (service_id, begin_time, duration, source_id, dvb_event_id, datetime.utcnow()),
        )
        return cur.lastrowid

    def add_unique_data(
        self,
        event_id,
        title_id,
        short_description_id,
        extended_description_id,
        iso_639_language_code,
    ):
        """
        CREATE TABLE T_Data (event_id INTEGER NOT NULL, title_id INTEGER, short_description_id INTEGER, extended_description_id INTEGER, iso_639_language_code TEXT NOT NULL, changed DATETIME NOT NULL DEFAULT current_timestamp);
        """
        cur = self.cursor()
        for _ in cur.execute(
            "SELECT event_id FROM T_Data WHERE event_id=? AND title_id=? AND short_description_id=? AND extended_description_id=? AND iso_639_language_code=? LIMIT 1",
            (
                event_id,
                title_id,
                short_description_id,
                extended_description_id,
                iso_639_language_code,
            ),
        ):
            return

        for old_title_id, old_short_description_id, old_extended_description_id in cur.execute(
            "SELECT title_id, short_description_id, extended_description_id FROM T_Data WHERE event_id=? LIMIT 1",
            (event_id,),
        ):
            cur.execute(
                "UPDATE T_Data SET title_id=?, short_description_id=?, extended_description_id=?, iso_639_language_code=? WHERE event_id=?",
                (
                    title_id,
                    short_description_id,
                    extended_description_id,
                    iso_639_language_code,
                    event_id,
                ),
            )
            if title_id != old_title_id:
                cur.execute("DELETE FROM T_Title WHERE id=?", (old_title_id,))
            if short_description_id != old_short_description_id:
                cur.execute(
                    "DELETE FROM T_Short_Description WHERE id=?", (old_short_description_id,)
                )
            if extended_description_id != old_extended_description_id:
                cur.execute(
                    "DELETE FROM T_Extended_Description WHERE id=?", (old_extended_description_id,)
                )
            return

        cur.execute(
            "INSERT INTO T_Data (event_id, title_id, short_description_id, extended_description_id, iso_639_language_code, changed) VALUES (?, ?, ?, ?, ?, ?)",
            (
                event_id,
                title_id,
                short_description_id,
                extended_description_id,
                iso_639_language_code,
                datetime.utcnow(),
            ),
        )
