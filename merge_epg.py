#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import gzip
import requests
import xml.etree.ElementTree as ET
from opencc import OpenCC

EPG_SOURCE_FILE = "epg_sources.txt"

OUT_ENTITY = "epg_entities.json"
OUT_INDEX = "index.json"

cc = OpenCC("t2s")


# ===================== 标准化 ===================== #

def norm(name):
    if not name:
        return ""

    name = cc.convert(name)
    name = name.lower()
    name = re.sub(r'[\s\-\_\(\)\[\]\.]+', '', name)
    return name


# ===================== 读取源 ===================== #

def load_sources():
    with open(EPG_SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


# ===================== 下载 ===================== #

def fetch(url):
    r = requests.get(url, timeout=30)
    data = r.content
    if url.endswith(".gz"):
        data = gzip.decompress(data)
    return data


# ===================== XML解析 ===================== #

def parse_xml(data):

    root = ET.fromstring(data)

    epg = {}

    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")

        names = [n.text for n in ch.findall("display-name") if n.text]

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


# ===================== 合并 ===================== #

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

            if not name:
                continue

            index[norm(name)] = epgid
            index[name] = epgid

    return index


# ===================== 主流程 ===================== #

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

    # set → list（关键！结构固定）
    for k in epg_map:
        epg_map[k]["names"] = list(epg_map[k]["names"])

    index = build_index(epg_map)

    # ===================== 输出（固定结构） ===================== #

    with open(OUT_ENTITY, "w", encoding="utf-8") as f:
        json.dump(epg_map, f, ensure_ascii=False, indent=2)

    with open(OUT_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print("✅ entities:", len(epg_map))
    print("✅ index:", len(index))


if __name__ == "__main__":
    main()
