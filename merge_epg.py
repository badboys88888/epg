#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import gzip
import xml.etree.ElementTree as ET
import json
import os
import re

EPG_SOURCES_FILE = "epg_sources.txt"
OUTPUT_XML_GZ = "epg.xml.gz"
OUTPUT_CHANNELS_JSON = "channels.json"


# ===================== 格式化XML ===================== #
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


# ===================== 名字归一化（去重核心） ===================== #
def normalize_name(name):
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"[ \-_]", "", name)
    return name


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
        print("[OK] download")
        return r.content

    except Exception as e:
        print("[ERROR requests]", e)
        return fetch_with_curl(url)


def fetch_with_curl(url):
    tmp = "tmp.gz"
    cmd = f'curl -L -A "Mozilla/5.0" -o {tmp} "{url}"'
    os.system(cmd)

    if not os.path.exists(tmp):
        raise Exception("curl failed")

    with open(tmp, "rb") as f:
        data = f.read()

    os.remove(tmp)
    return data


# ===================== 解析 ===================== #
def parse_epg(content):
    try:
        if content[:2] == b'\x1f\x8b':
            content = gzip.decompress(content)

        root = ET.fromstring(content)
        print("[OK] parsed")
        return root

    except Exception as e:
        print("[ERROR parse]", e)
        return None


# ===================== 合并 ===================== #
def merge_roots(roots):
    tv = ET.Element("tv")

    channel_map = {}
    seen_prog = set()

    total_prog = 0
    kept_prog = 0

    # ---------- CHANNEL ----------
    for root in roots:
        for ch in root.findall("channel"):
            cid = ch.get("id")
            if not cid:
                continue

            if cid not in channel_map:
                channel_map[cid] = {}

            for dn in ch.findall("display-name"):
                if dn.text:
                    raw = dn.text.strip()
                    key = normalize_name(raw)

                    # 👉 去重（民视 / 民視）
                    if key not in channel_map[cid]:
                        channel_map[cid][key] = raw

    print(f"[INFO] channels collected: {len(channel_map)}")

    # 写入 channel
    for cid, name_dict in channel_map.items():
        ch = ET.SubElement(tv, "channel", {"id": cid})

        for name in name_dict.values():
            dn = ET.SubElement(ch, "display-name")
            dn.text = name

    # ---------- PROGRAMME ----------
    for root in roots:
        for prog in root.findall("programme"):
            total_prog += 1

            cid = prog.get("channel")
            start = prog.get("start")
            stop = prog.get("stop")

            if not cid or not start:
                continue

            key = (cid, start, stop)

            # 👉 去重节目
            if key in seen_prog:
                continue

            seen_prog.add(key)
            kept_prog += 1

            new_prog = ET.SubElement(tv, "programme", prog.attrib)

            for child in prog:
                c = ET.SubElement(new_prog, child.tag)
                c.text = child.text

    print(f"[INFO] programmes: {total_prog} -> {kept_prog}")

    return tv, channel_map


# ===================== 写 XML ===================== #
def write_gz_xml(root):
    indent(root)  # 👈 美化XML

    xml_str = ET.tostring(root, encoding="utf-8")

    with gzip.open(OUTPUT_XML_GZ, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(xml_str)

    size = os.path.getsize(OUTPUT_XML_GZ) / 1024
    print(f"[OK] saved epg.xml.gz ({size:.1f} KB)")


# ===================== 写 JSON ===================== #
def write_channels_json(channel_map):
    data = {}

    for cid, names in channel_map.items():
        if not names:
            continue

        data[cid] = {
            "epgid": cid,
            "logo": "",
            "name": ",".join(names.values())
        }

    with open(OUTPUT_CHANNELS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] channels.json ({len(data)})")


# ===================== 主流程 ===================== #
def main():
    roots = []

    with open(EPG_SOURCES_FILE, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip()]

    print(f"[INFO] total sources: {len(urls)}")

    for url in urls:
        try:
            content = fetch_epg(url)
            root = parse_epg(content)
            if root:
                roots.append(root)
        except Exception as e:
            print(f"[FAIL] {url} -> {e}")

    print(f"[INFO] valid sources: {len(roots)}")

    tv, channel_map = merge_roots(roots)

    write_gz_xml(tv)
    write_channels_json(channel_map)


if __name__ == "__main__":
    main()
