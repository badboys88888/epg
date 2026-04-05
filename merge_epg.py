#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
import json
from collections import defaultdict

# ===================== 配置 ===================== #
EPG_SOURCES_FILE = "epg_sources.txt"
OUTPUT_XML_GZ = "epg.xml.gz"
OUTPUT_CHANNELS_JSON = "channels.json"

# ===================== 下载EPG ===================== #
def fetch_epg(url):
    print(f"[FETCH] {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

# ===================== 解析EPG ===================== #
def parse_epg(content):
    if content[:2] == b'\x1f\x8b':  # gzip
        content = gzip.decompress(content)

    return ET.fromstring(content)

# ===================== 合并数据 ===================== #
def merge_roots(roots):
    tv = ET.Element("tv")

    channel_map = {}
    programme_seen = set()

    # ========== 1. 合并 channel ==========
    for root in roots:
        for ch in root.findall("channel"):
            cid = ch.attrib.get("id")
            name_node = ch.find("display-name")

            if cid and name_node is not None and name_node.text:
                name = name_node.text.strip()

                if cid not in channel_map:
                    channel_map[cid] = name

    # 写入 channel
    for cid, name in channel_map.items():
        ch = ET.SubElement(tv, "channel", {"id": cid})
        dn = ET.SubElement(ch, "display-name")
        dn.text = name

    # ========== 2. 合并 programme ==========
    for root in roots:
        for prog in root.findall("programme"):
            cid = prog.attrib.get("channel")
            start = prog.attrib.get("start")
            stop = prog.attrib.get("stop")

            key = (cid, start, stop)
            if key in programme_seen:
                continue
            programme_seen.add(key)

            new_prog = ET.SubElement(tv, "programme", prog.attrib)

            for child in prog:
                new_child = ET.SubElement(new_prog, child.tag)
                new_child.text = child.text

    return tv, channel_map

# ===================== 写 XML.gz ===================== #
def write_gz_xml(root):
    xml_str = ET.tostring(root, encoding="utf-8")

    with gzip.open(OUTPUT_XML_GZ, "wb") as f:
        f.write(xml_str)

    print(f"[OK] XML saved -> {OUTPUT_XML_GZ}")

# ===================== 写 channels.json ===================== #
def write_channels_json(channel_map):
    data = {}

    for cid, name in channel_map.items():
        data[cid] = {
            "epg_id": cid,
            "names": [name],
            "logo": ""
        }

    with open(OUTPUT_CHANNELS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] channels.json saved -> {OUTPUT_CHANNELS_JSON}")

# ===================== 主流程 ===================== #
def main():
    roots = []

    with open(EPG_SOURCES_FILE, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip()]

    for url in urls:
        try:
            content = fetch_epg(url)
            root = parse_epg(content)
            roots.append(root)
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")

    tv, channel_map = merge_roots(roots)

    write_gz_xml(tv)
    write_channels_json(channel_map)

if __name__ == "__main__":
    main()
