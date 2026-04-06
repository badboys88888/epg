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


# ===================== 下载EPG（核心增强版） ===================== #
def fetch_epg(url):
    print(f"[FETCH] {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://epg.iill.top/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=30)

        # ❌ 403 自动 fallback curl
        if r.status_code == 403:
            print("[WARN] 403 detected, switching to curl...")

            return fetch_with_curl(url)

        r.raise_for_status()
        return r.content

    except Exception as e:
        print("[ERROR requests]", e)
        return fetch_with_curl(url)


# ===================== curl fallback ===================== #
def fetch_with_curl(url):
    tmp_file = "temp_epg.gz"

    cmd = f'curl -L -A "Mozilla/5.0" -e "https://epg.iill.top/" -o {tmp_file} "{url}"'
    os.system(cmd)

    if not os.path.exists(tmp_file):
        raise Exception("curl download failed")

    with open(tmp_file, "rb") as f:
        data = f.read()

    os.remove(tmp_file)
    return data


# ===================== 解析EPG ===================== #
def parse_epg(content):
    if content[:2] == b'\x1f\x8b':
        content = gzip.decompress(content)

    return ET.fromstring(content)


# ===================== 合并 ===================== #
def merge_roots(roots):
    tv = ET.Element("tv")

    channel_map = {}
    seen_prog = set()

    # ---------- CHANNEL ----------
    for root in roots:
        for ch in root.findall("channel"):
            cid = ch.attrib.get("id")
            if not cid:
                continue

            if cid not in channel_map:
                channel_map[cid] = []

            for dn in ch.findall("display-name"):
                if dn.text:
                    name = dn.text.strip()
                    if name not in channel_map[cid]:
                        channel_map[cid].append(name)

    # 写入 channel
    for cid, names in channel_map.items():
        ch = ET.SubElement(tv, "channel", {"id": cid})

        for n in names:
            dn = ET.SubElement(ch, "display-name")
            dn.text = n

    # ---------- PROGRAMME ----------
    for root in roots:
        for prog in root.findall("programme"):
            cid = prog.attrib.get("channel")
            start = prog.attrib.get("start")
            stop = prog.attrib.get("stop")

            key = (cid, start, stop)
            if key in seen_prog:
                continue
            seen_prog.add(key)

            new_prog = ET.SubElement(tv, "programme", prog.attrib)

            for child in prog:
                new_child = ET.SubElement(new_prog, child.tag)
                new_child.text = child.text

    return tv, channel_map


# ===================== 写 XML ===================== #
def write_gz_xml(root):
    xml_str = ET.tostring(root, encoding="utf-8")

    with gzip.open(OUTPUT_XML_GZ, "wb") as f:
        f.write(xml_str)

    print("[OK] epg.xml.gz saved")


# ===================== 写 JSON ===================== #
def write_channels_json(channel_map):
    data = {}

    for cid, names in channel_map.items():
        if not names:
            continue

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
