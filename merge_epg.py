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


# ===================== XML缩进 ===================== #
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
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
    tmp = "tmp_epg.gz"
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

    # ---------------- CHANNEL ---------------- #
    channel_map = {}

    for root, region in roots:
        for ch in root.findall("channel"):
            cid = ch.attrib.get("id")
            if not cid:
                continue

            if cid not in channel_map:
                channel_map[cid] = {
                    "names": set(),
                    "icon": None,
                    "sources": set()
                }

            channel_map[cid]["sources"].add(region)

            # display-name
            for dn in ch.findall("display-name"):
                if dn.text:
                    channel_map[cid]["names"].add(dn.text.strip())

            # icon（只保留一个）
            icon = ch.find("icon")
            if icon is not None and icon.get("src"):
                if not channel_map[cid]["icon"]:
                    channel_map[cid]["icon"] = icon.get("src")

    # ---------------- PROGRAMME ---------------- #
    prog_map = {}

    for root, region in roots:
        for prog in root.findall("programme"):
            cid = prog.attrib.get("channel")
            start = prog.attrib.get("start")
            stop = prog.attrib.get("stop")

            title_node = prog.find("title")
            title = title_node.text.strip() if title_node is not None and title_node.text else ""

            # ✅ 关键：包含 title 做唯一去重
            key = (cid, start, stop, title)

            if key not in prog_map:
                prog_map[key] = {
                    "attrib": prog.attrib,
                    "title": title,
                    "regions": set()
                }

            prog_map[key]["regions"].add(region)

    # ---------------- 写 CHANNEL ---------------- #
    for cid, info in channel_map.items():
        ch = ET.SubElement(tv, "channel", {
            "id": cid,
            "source": ",".join(sorted(info["sources"]))
        })

        name = sorted(info["names"])[0] if info["names"] else cid

        ET.SubElement(ch, "display-name").text = name

        if info["icon"]:
            ET.SubElement(ch, "icon", {"src": info["icon"]})

    # ---------------- 写 PROGRAMME ---------------- #
    for (cid, start, stop, title), info in prog_map.items():

        prog = ET.SubElement(tv, "programme", {
            "channel": cid,
            "start": start,
            "stop": stop
        })

        ET.SubElement(prog, "title").text = title

        # 合并来源地区
        ET.SubElement(prog, "category").text = ",".join(sorted(info["regions"]))

    return tv, channel_map


# ===================== 写 XML ===================== #
def write_gz_xml(root):
    indent(root)

    xml_str = ET.tostring(root, encoding="utf-8")

    with gzip.open(OUTPUT_XML_GZ, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(xml_str)

    print("[OK] epg.xml.gz saved")


# ===================== 写 JSON ===================== #
def write_channels_json(channel_map):
    data = {}

    for cid, info in channel_map.items():
        data[cid] = {
            "epgid": cid,
            "name": ",".join(sorted(info["names"])),
            "logo": info["icon"] or "",
            "source": ",".join(sorted(info["sources"]))
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
