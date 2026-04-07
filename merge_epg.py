#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import gzip
import xml.etree.ElementTree as ET
import json
import os

EPG_SOURCES_FILE = "epg_sources.txt"
OUTPUT_XML_GZ = "epg.xml.gz"
OUTPUT_CHANNELS_JSON = "channels.json"


# ===================== XML 美化 ===================== #
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# ===================== 下载 ===================== #
def fetch_epg(url):
    print(f"[FETCH] {url}")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://epg.iill.top/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 403:
            print("[WARN] 403 -> curl fallback")
            return fetch_with_curl(url)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print("[ERROR requests]", e)
        return fetch_with_curl(url)


def fetch_with_curl(url):
    tmp = "tmp.gz"
    os.system(f'curl -L -A "Mozilla/5.0" -o {tmp} "{url}"')

    with open(tmp, "rb") as f:
        data = f.read()

    os.remove(tmp)
    return data


# ===================== 解析 ===================== #
def parse_epg(content):
    if content[:2] == b'\x1f\x8b':
        content = gzip.decompress(content)
    return ET.fromstring(content)


# ===================== 主合并 ===================== #
def merge_roots(roots):
    tv = ET.Element("tv")

    channel_map = {}
    seen_prog = set()

    # ---------- CHANNEL ----------
    for root, region in roots:
        for ch in root.findall("channel"):
            cid = ch.attrib.get("id")
            if not cid:
                continue

            if cid not in channel_map:
                channel_map[cid] = set()

            for dn in ch.findall("display-name"):
                if dn.text:
                    channel_map[cid].add(dn.text.strip())

    # 写 channel
    for cid, names in channel_map.items():
        ch = ET.SubElement(tv, "channel", {"id": cid})
        for name in names:
            dn = ET.SubElement(ch, "display-name")
            dn.text = name

    # ---------- PROGRAMME ----------
    for root, region in roots:
        for prog in root.findall("programme"):
            cid = prog.attrib.get("channel")
            start = prog.attrib.get("start")
            stop = prog.attrib.get("stop")

            title = ""
            t = prog.find("title")
            if t is not None and t.text:
                title = t.text.strip()

            # 👉 去重（包含 region）
            key = (cid, start, stop, title, region)
            if key in seen_prog:
                continue
            seen_prog.add(key)

            new_prog = ET.SubElement(tv, "programme", prog.attrib)

            # 复制子节点
            for child in prog:
                new_child = ET.SubElement(new_prog, child.tag)
                new_child.text = child.text

            # 👉 防止重复 category
            has_region = False
            for c in prog.findall("category"):
                if c.text and c.text.upper() == region:
                    has_region = True

            if not has_region:
                ET.SubElement(new_prog, "category").text = region

    return tv, channel_map


# ===================== 写 XML ===================== #
def write_gz_xml(root):
    indent(root)

    xml_str = ET.tostring(root, encoding="utf-8")

    with gzip.open(OUTPUT_XML_GZ, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(b'<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
        f.write(xml_str)

    print("[OK] epg.xml.gz saved")


# ===================== 写 JSON ===================== #
def write_channels_json(channel_map):
    data = {}

    for cid, names in channel_map.items():
        data[cid] = {
            "epgid": cid,
            "logo": "",
            "name": ",".join(names)
        }

    with open(OUTPUT_CHANNELS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("[OK] channels.json saved")


# ===================== 主流程 ===================== #
def main():
    roots = []

    with open(EPG_SOURCES_FILE, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f if x.strip()]

    for line in lines:
        try:
            # 👉 解析 region
            if "|" in line:
                url, region = line.split("|", 1)
                region = region.strip().upper()
            else:
                url = line
                region = "UNKNOWN"

            content = fetch_epg(url.strip())
            root = parse_epg(content)

            roots.append((root, region))

        except Exception as e:
            print(f"[ERROR] {line} -> {e}")

    tv, channel_map = merge_roots(roots)

    write_gz_xml(tv)
    write_channels_json(channel_map)


if __name__ == "__main__":
    main()
