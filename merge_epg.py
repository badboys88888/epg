#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import gzip
import requests
import xml.etree.ElementTree as ET
from rules import make_epgid, norm

EPG_SOURCE_FILE = "epg_sources.txt"

OUT_ENTITIES = "epg_entities.json"
OUT_INDEX = "epg_index.json"
OUT_ALIAS = "epg_alias.json"


# ===================== sources ===================== #
def load_sources():
    with open(EPG_SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


# ===================== fetch ===================== #
def fetch(url):
    r = requests.get(url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0"
    })
    data = r.content
    if url.endswith(".gz"):
        data = gzip.decompress(data)
    return data


# ===================== parse ===================== #
def parse_xml(data):
    root = ET.fromstring(data)
    epg = {}

    for ch in root.findall("channel"):
        names = [n.text.strip() for n in ch.findall("display-name") if n.text]
        if not names:
            continue

        primary = names[0]
        cid = make_epgid(primary)

        icon = ch.find("icon")
        logo = icon.attrib.get("src") if icon is not None else ""

        if cid not in epg:
            epg[cid] = {
                "epgid": cid,
                "logo": logo,
                "names": set()
            }

        for n in names:
            epg[cid]["names"].add(n)

    return epg


# ===================== merge ===================== #
def merge(*sources):
    out = {}

    for src in sources:
        for k, v in src.items():
            if k not in out:
                out[k] = v
            else:
                out[k]["names"].update(v["names"])

    return out


# ===================== index ===================== #
def build_index(epg_map):
    index = {}

    for epgid, epg in epg_map.items():
        for name in epg["names"]:
            index[norm(name)] = epgid
            index[name] = epgid

    return index


# ===================== alias ===================== #
def build_alias(epg_map):
    alias = {}

    for epgid, epg in epg_map.items():
        alias[epgid] = list(epg["names"])

    return alias


# ===================== main ===================== #
def main():

    sources = load_sources()

    all_epg = []

    for url in sources:
        try:
            data = fetch(url)
            epg = parse_xml(data)
            all_epg.append(epg)
        except Exception as e:
            print("❌", url, e)

    epg_map = merge(*all_epg)

    # set → list
    for k in epg_map:
        epg_map[k]["names"] = list(epg_map[k]["names"])

    index = build_index(epg_map)
    alias = build_alias(epg_map)

    # ===================== output ===================== #
    with open(OUT_ENTITIES, "w", encoding="utf-8") as f:
        json.dump(epg_map, f, ensure_ascii=False, indent=2)

    with open(OUT_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    with open(OUT_ALIAS, "w", encoding="utf-8") as f:
        json.dump(alias, f, ensure_ascii=False, indent=2)

    print("✅ epg:", len(epg_map))
    print("✅ index:", len(index))


if __name__ == "__main__":
    main()
