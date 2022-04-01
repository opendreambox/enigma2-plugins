# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2022 Andreas Oberritter
# SPDX-License-Identifier: MIT
#

import filecmp
import hashlib
import json
import logging
import os
import struct
import tempfile
from datetime import datetime, timedelta, tzinfo
from distutils.version import LooseVersion
from xml.etree import ElementTree

import requests
from enigma import eDVBDB, eServiceReference, getEnigmaVersionString

import epgdb

known_modes = {
    1: {
        "name": "TV",
        "types": ("dash", "hls", "slides", "video"),
        "formats": ("dash", "hls", "webm"),
    },
    2: {
        "name": "Radio",
        "types": ("audio", "music"),
        "formats": ("hls", "mp3", "opus"),
    },
}

sysconfdir = "/etc"
pkgsysconfdir = os.path.join(sysconfdir, "enigma2")


def c3voc_title():
    return "c3voc"


def name_line(text):
    assert "\n" not in text
    return "#NAME {}\n".format(text)


def description_line(text):
    assert "\n" not in text
    return "#DESCRIPTION {}\n".format(text)


def service_line(ref):
    return "#SERVICE {}\n".format(ref.toString())


def bouquet_id(name):
    return "".join([c.lower() if c.isalnum() else "_" for c in name])


def create_name(obj, attr, idx, title=None):
    name = obj.get(attr)
    if not name:
        if not title:
            title = attr.title()
        name = "{} #{}".format(title, idx + 1)

    return name


def fetch_uri(uri):
    ca_bundle = os.path.join(sysconfdir, "ssl/certs/ca-certificates.crt")
    if os.path.exists(ca_bundle):
        verify = ca_bundle
    else:
        verify = True

    try:
        r = requests.get(uri, timeout=3, verify=verify)
    except requests.exceptions.RequestException as exc:
        logging.error(exc)
    else:
        return r


def fetch_json(uri):
    if uri.startswith("file://"):
        filename = uri[7:]
        with open(filename, "r") as fp:
            return json.load(fp)

    r = fetch_uri(uri)
    if not r:
        return []

    try:
        data = r.json()
    except ValueError as exc:
        logging.error(exc)
        return []

    return data


def fetch_xml(uri):
    if uri.startswith("file://"):
        filename = uri[7:]
        return ElementTree.parse(filename).getroot()

    r = fetch_uri(uri)
    if not r:
        return None

    try:
        data = ElementTree.fromstring(r.content)
    except ElementTree.ParseError as exc:
        logging.error(exc)
    else:
        return data


def create_service_ids(name):
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    sid, tsid, onid, namespace = struct.unpack("!HHHi", digest[:10])
    return sid, tsid, onid, namespace


def parse_schedule_xml(root):
    """
    Schemas: https://github.com/voc/schedule/tree/master/validator/xsd
    """
    try:
        db = epgdb.EpgDatabase(os.path.join(pkgsysconfdir, "epg.db"))
    except ValueError as exc:
        logging.error(exc)
        return False

    for tag in ("acronym", "title"):
        source_name = root.find("conference/{}".format(tag))
        if source_name is not None and source_name.text:
            source_name = source_name.text
            break
    else:
        source_name = c3voc_title()

    source_id = db.add_unique_source(source_name)

    class FixedOffset(tzinfo):
        def __init__(self, offset):
            self._utcoffset = timedelta(seconds=offset)
            self._dst = timedelta(0)

        def utcoffset(self, dt):
            return self._utcoffset

        def dst(self, dt):
            return self._dst

        def tzname(self, dt):
            return None

    epoch = datetime(1970, 1, 1, tzinfo=FixedOffset(0))

    room_ids = {}
    for day in root.findall("day"):
        for room in day.findall("room"):
            room_name = room.attrib.get("name")
            if not room_name:
                continue

            sid, tsid, onid, namespace = create_service_ids(room_name)
            service_id = db.add_unique_service(sid, tsid, onid, namespace)

            for event in room.findall("event"):
                start = event.find("date")
                if start is None or not start.text:
                    logging.warning("No start time found")
                    continue

                date = start.text
                if date.endswith("Z"):
                    date = date[:-1] + "+00:00"

                sign = date[-6]
                if sign not in ("+", "-") or date[-3] != ":":
                    logger.warning("Unexpected date format")
                    continue

                hours, minutes = map(int, date[-5:].split(":"))
                offset = timedelta(hours=hours, minutes=minutes).total_seconds()
                if sign == "-":
                    offset = -offset

                dt = datetime.strptime(date[:-6], "%Y-%m-%dT%H:%M:%S").replace(
                    tzinfo=FixedOffset(offset)
                )
                begin_time = dt - epoch

                _id = event.attrib.get("id")
                if not _id:
                    logging.warning("No event ID found")
                    continue

                if _id.isdigit() and int(_id) < 0x10000:
                    dvb_event_id = int(_id)
                else:
                    digest = hashlib.sha256(_id.encode("utf-8")).digest()
                    (dvb_event_id,) = struct.unpack("!H", digest[:2])

                duration = event.find("duration")
                if duration is None or not duration.text:
                    logging.warning("No duration found")
                    continue

                hours, minutes = map(int, duration.text.split(":"))
                duration = timedelta(hours=hours, minutes=minutes)

                title = event.find("title")
                if title is None or not title.text:
                    logging.warning("No title found")
                    continue
                title = title.text

                language = event.find("language")
                if language is None or not language.text:
                    content_locale = "de"
                else:
                    content_locale = language.text

                title_id = db.add_unique_title(title)

                abstract = event.find("abstract")
                if abstract is None or not abstract.text:
                    short_description_id = None
                else:
                    short_description_id = db.add_unique_short_description(abstract.text)

                description = event.find("description")
                if description is None or not description.text:
                    extended_description_id = None
                else:
                    extended_description_id = db.add_unique_extended_description(description.text)

                event_id = db.add_unique_event(
                    service_id,
                    begin_time.total_seconds(),
                    duration.total_seconds(),
                    source_id,
                    dvb_event_id,
                )

                db.add_unique_data(
                    event_id,
                    title_id,
                    short_description_id,
                    extended_description_id,
                    content_locale,
                )

    db.commit()
    return True


def fetch_and_parse_schedules(data):
    changed = False

    for event in data:
        schedule_url = event.get("schedule")
        if not schedule_url:
            continue
        if schedule_url.startswith("https://") and schedule_url.endswith(".xml"):
            logging.debug(
                "Fetching schedule URL for event {}: {}".format(
                    event.get("conference"), schedule_url
                )
            )
            root = fetch_xml(schedule_url)
            if root is not None and root.tag == "schedule":
                if parse_schedule_xml(root):
                    changed = True
        else:
            logging.warning(
                "Ignoring unsafe schedule URL for event {}: {}".format(
                    event.get("conference"), schedule_url
                )
            )

    return changed


def parse_streams_v2(
    data,
    service_type,
    stream_formats={},
    stream_types={},
):
    """
    API Docs:
    https://github.com/voc/streaming-website/blob/master/view/streams-json-v2.php
    """
    all_types = set()
    included_types = set()
    all_formats = set()
    included_formats = set()
    lines = []

    for enr, event in enumerate(data):
        event_name = create_name(event, "conference", enr)

        for gnr, group in enumerate(event.get("groups", [])):
            group_name = create_name(group, "group", gnr)

            for rnr, room in enumerate(group.get("rooms", [])):
                room_name = create_name(room, "display", rnr, title="Room")

                # Derive IDs from schedule name, so we can match EPG entries
                schedule_name = room.get("schedulename")
                if schedule_name:
                    sid, tsid, onid, namespace = create_service_ids(schedule_name)
                else:
                    sid, tsid, onid, namespace = (0, 0, 0, 0)

                stream_lines = []
                for snr, stream in enumerate(room.get("streams", [])):
                    stream_name = create_name(stream, "display", snr, title="Stream")
                    stream_type = stream.get("type")
                    skip_type = stream_types and stream_type not in stream_types
                    all_types.add(stream_type)

                    for stream_format, url_data in stream.get("urls", {}).items():
                        all_formats.add(stream_format)
                        if skip_type:
                            continue
                        if stream_formats and stream_format not in stream_formats:
                            continue

                        url = url_data.get("url")
                        if url:
                            format_name = url_data.get("display", stream_format)
                            name = "{} ({})".format(stream_name, format_name)
                            ref = eServiceReference(
                                service_type, eServiceReference.isLive, url.encode("utf-8")
                            )
                            ref.setData(1, sid)
                            ref.setData(2, tsid)
                            ref.setData(3, onid)
                            ref.setData(4, namespace)
                            ref.setName(name.encode("utf-8"))

                            stream_lines.append(service_line(ref))
                            stream_lines.append(description_line(name))

                        included_types.add(stream_type)
                        included_formats.add(stream_format)

                if stream_lines:
                    name = " - ".join([room_name, group_name, event_name])
                    ref = eServiceReference(
                        eServiceReference.idDVB, eServiceReference.isMarker, b""
                    )
                    ref.setName(name.encode("utf-8"))

                    lines.append(service_line(ref))
                    lines.append(description_line(name))
                    lines += stream_lines

    included_types &= all_types
    included_formats &= all_formats
    excluded_types = all_types ^ included_types
    excluded_formats = all_formats ^ included_formats

    logging.debug("Included stream types: {}".format(sorted(included_types)))
    logging.debug("Excluded stream types: {}".format(sorted(excluded_types)))
    logging.debug("Included stream formats: {}".format(sorted(included_formats)))
    logging.debug("Excluded stream formats: {}".format(sorted(excluded_formats)))

    return lines


def service_type_for_enigma_version(dvb_service_type):
    if dvb_service_type == 1:  # TV
        version = LooseVersion(getEnigmaVersionString())
        if version >= LooseVersion("4.5"):
            return eServiceReference.idStream

    return eServiceReference.idGST


def update_streams_v2(url="https://streaming.media.ccc.de/streams/v2.json"):
    streams = fetch_json(url)
    if not streams:
        return False

    changed = fetch_and_parse_schedules(streams)

    for dvb_service_type, mode in known_modes.items():
        lines = parse_streams_v2(
            streams,
            service_type=service_type_for_enigma_version(dvb_service_type),
            stream_formats=mode["formats"],
            stream_types=mode["types"],
        )
        if not lines:
            continue

        mode_name = mode["name"]
        bouquet_title = "{} ({})".format(c3voc_title(), mode_name)
        bouquet_filename = "userbouquet.{}.{}".format(bouquet_id(bouquet_title), mode_name.lower())
        bouquet_path = os.path.join(pkgsysconfdir, bouquet_filename)

        try:
            fp = tempfile.NamedTemporaryFile(mode="w", dir=pkgsysconfdir, delete=False)
        except OSError as exc:
            logging.error(exc)
            continue

        with fp:
            fp.write(name_line(bouquet_title))
            fp.writelines(lines)

        try:
            same = filecmp.cmp(fp.name, bouquet_path)
        except OSError:
            same = False

        if same:
            try:
                os.unlink(fp.name)
            except OSError as exc:
                logging.error(exc)
        else:
            try:
                os.rename(fp.name, bouquet_path)
            except OSError as exc:
                logging.error(exc)
            else:
                logging.info("Wrote bouquet '{}' to '{}'.".format(bouquet_title, bouquet_path))
                changed = True

        bouquets_tv_path = os.path.join(pkgsysconfdir, "bouquets.{}".format(mode_name.lower()))
        try:
            fp = open(bouquets_tv_path, "a+")
        except OSError as exc:
            logging.error(exc)
            continue

        path = 'FROM BOUQUET "{}" ORDER BY bouquet'.format(bouquet_filename)
        ref = eServiceReference(
            eServiceReference.idDVB, eServiceReference.flagDirectory, path.encode("utf-8")
        )
        ref.setData(0, dvb_service_type)
        line = service_line(ref)

        with fp:
            fp.seek(0)
            if line not in fp:
                fp.write(line)
                logging.info("Added bouquet '{}' to '{}'.".format(c3voc_title(), bouquets_tv_path))
                changed = True

        if changed:
            eDVBDB.getInstance().reloadBouquets()
            logging.info("Reloaded bouquets")

    return changed
