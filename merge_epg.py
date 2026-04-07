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


# ===================== 下载EPG ===================== #
def fetch_epg(url):
    print(f"[FETCH] {url}")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Referer": "https://epg.iill.top/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=30)

        if r.status_code == 403:
            print("[WARN] 403 → curl fallback")
            return fetch_with_curl(url)

        r.raise_for_status()
        return r.content

    except Exception as e:
        print(f"[ERROR requests] {e}")
        return fetch_with_curl(url)


# ===================== curl fallback ===================== #
def fetch_with_curl(url):
    tmp_file = "temp_epg.gz"

    cmd = f'curl -L -A "Mozilla/5.0" -o {tmp_file} "{url}"'
    os.system(cmd)

    if not os.path.exists(tmp_file):
        raise Exception("curl failed")

    with open(tmp_file, "rb") as f:
        data = f.read()

    os.remove(tmp_file)
    return data


# ===================== 解析 ===================== #
def parse_epg(content):
    if content[:2] == b'\x1f\x8b':
        content = gzip.decompress(content)

    return ET.fromstring(content)


# ===================== 简单标准化（用于去重） ===================== #
def normalize_text(text):
    if not text:
        return ""
    return text.strip().replace(" ", "").replace("-", "").lower()


# ===================== 合并 ===================== #
def merge_roots(roots):
    tv = ET.Element("tv")

    channel_map = {}
    seen_prog = set()

    total_channels = 0
    total_programs = 0

    # ---------- CHANNEL ----------
    for root in roots:
        for ch in root.findall("channel"):
            cid = ch.attrib.get("id")
            if not cid:
                continue

            total_channels += 1

            if cid not in channel_map:
                channel_map[cid] = []

            for dn in ch.findall("display-name"):
                if dn.text:
                    name = dn.text.strip()
                    if name not in channel_map[cid]:
                        channel_map[cid].append(name)

    print(f"[INFO] 收集频道: {len(channel_map)}")

    # 写入 channel
    for cid, names in channel_map.items():
        ch = ET.SubElement(tv, "channel", {"id": cid})

        for n in names:
            dn = ET.SubElement(ch, "display-name")
            dn.text = n

    # ---------- PROGRAMME ----------
    for root in roots:
        count = 0

        for prog in root.findall("programme"):
            cid = prog.attrib.get("channel")
            start = prog.attrib.get("start")
            stop = prog.attrib.get("stop")

            title_elem = prog.find("title")
            title = title_elem.text if title_elem is not None else ""

            # ✅ 更强去重（频道+时间+标题）
            key = (
                cid,
                start,
                stop,
                normalize_text(title)
            )

            if key in seen_prog:
                continue

            seen_prog.add(key)

            new_prog = ET.SubElement(tv, "programme", prog.attrib)

            for child in prog:
                new_child = ET.SubElement(new_prog, child.tag)
                new_child.text = child.text

            count += 1
            total_programs += 1

        print(f"[INFO] 本源节目: {count}")

    print(f"[INFO] 合并后节目总数: {total_programs}")

    return tv, channel_map


# ===================== 写 XML ===================== #
def write_gz_xml(root):
    xml_str = ET.tostring(root, encoding="utf-8")

    with gzip.open(OUTPUT_XML_GZ, "wb") as f:
        f.write(xml_str)

    size = os.path.getsize(OUTPUT_XML_GZ) / 1024
    print(f"[OK] epg.xml.gz saved ({size:.1f} KB)")


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

    print(f"[OK] channels.json saved ({len(data)} channels)")


# ===================== 主流程 ===================== #
def main():
    roots = []

    with open(EPG_SOURCES_FILE, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip()]

    print(f"[INFO] EPG源数量: {len(urls)}")

    for i, url in enumerate(urls, 1):
        try:
            print(f"\n[{i}/{len(urls)}]")
            content = fetch_epg(url)
            root = parse_epg(content)
            roots.append(root)
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")

    print("\n[INFO] 开始合并...")
    tv, channel_map = merge_roots(roots)

    write_gz_xml(tv)
    write_channels_json(channel_map)


if __name__ == "__main__":
    main()
