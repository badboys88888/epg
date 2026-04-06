#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import xml.etree.ElementTree as ET
import json
import os
import re
import unicodedata

INPUT_FILE = "epg.xml.gz"
OUTPUT_FILE = "channels.json"
ICON_MAP_FILE = "icon_map.json"
ALIAS_FILE = "alias_map.json"


def load_epg():
    with gzip.open(INPUT_FILE, "rb") as f:
        return ET.parse(f).getroot()


def load_icon_map():
    try:
        with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def load_alias():
    try:
        with open(ALIAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"exact": {}}


def normalize(name):
    if not name:
        return ""
    name = unicodedata.normalize("NFKC", name)
    name = name.upper()
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"[-_()（）·\.]", "", name)
    return name


def main():

    root = load_epg()
    icon_map = load_icon_map()
    alias_raw = load_alias()

    alias_exact = alias_raw.get("exact", {})
    norm_icon_map = {normalize(k): v for k, v in icon_map.items()}

    channels = {}

    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")
        if not cid:
            continue

        names = [n.text.strip() for n in ch.findall("display-name") if n.text]

        if not names:
            names = [cid]

        if cid not in channels:
            channels[cid] = {
                "epgid": cid,
                "names": [],
                "logo": ""
            }

        # EPG names
        for n in names:
            if n not in channels[cid]["names"]:
                channels[cid]["names"].append(n)

        # alias
        if cid in alias_exact:
            for a in alias_exact[cid]:
                if a not in channels[cid]["names"]:
                    channels[cid]["names"].append(a)

        # 去重（normalize）
        seen = set()
        clean = []

        for n in channels[cid]["names"]:
            nn = normalize(n)
            if nn not in seen:
                clean.append(n)
                seen.add(nn)

        channels[cid]["names"] = clean

        # logo
        logo = ""
        for n in clean:
            if normalize(n) in norm_icon_map:
                logo = norm_icon_map[normalize(n)]
                break

        channels[cid]["logo"] = logo

    # ================= OUTPUT（重点改这里） ================= #
    final = {}

    for cid, data in channels.items():
        final[cid] = {
            "epgid": cid,
            "name": ",".join(data["names"]),
            "logo": data["logo"]
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print("✅ DONE:", len(final))


if __name__ == "__main__":
    main()
