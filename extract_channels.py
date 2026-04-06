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


# ===================== EPG ===================== #
def load_epg():
    print("📦 EPG路径:", os.path.abspath(INPUT_FILE))
    with gzip.open(INPUT_FILE, "rb") as f:
        return ET.parse(f).getroot()


# ===================== ICON ===================== #
def load_icon_map():
    try:
        with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print("🖼️ logo_map加载:", len(data))
            return data
    except Exception as e:
        print("❌ logo_map加载失败:", e)
        return {}


# ===================== ALIAS ===================== #
def load_alias():
    try:
        with open(ALIAS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print("✅ alias加载成功")
            return data
    except Exception as e:
        print("❌ alias加载失败:", e)
        return {"exact": {}}


# ===================== normalize ===================== #
def normalize(name):
    if not name:
        return ""

    name = unicodedata.normalize("NFKC", name)
    name = name.upper()
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"[-_()（）·\.]", "", name)

    return name


# ===================== MAIN ===================== #
def main():

    print("🚀 RUNNING extract_channels FINAL (KEY=DISPLAY NAME)")

    root = load_epg()
    icon_map = load_icon_map()
    alias_raw = load_alias()

    alias_exact = alias_raw.get("exact", {})

    print("📊 alias_exact:", len(alias_exact))

    norm_icon_map = {normalize(k): v for k, v in icon_map.items()}

    # ===================== STEP 1: CID 聚合 ===================== #
    channels = {}

    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")
        if not cid:
            continue

        # display-name
        names = []
        for n in ch.findall("display-name"):
            if n.text:
                names.append(n.text.strip())

        if not names:
            names = [cid]

        # 初始化 CID bucket
        if cid not in channels:
            channels[cid] = {
                "epgid": cid,
                "names": [],
                "logo": ""
            }

        # 合并 EPG 名字
        for n in names:
            if n not in channels[cid]["names"]:
                channels[cid]["names"].append(n)

        # alias 追加（不覆盖）
        if cid in alias_exact:
            for a in alias_exact[cid]:
                if a not in channels[cid]["names"]:
                    channels[cid]["names"].append(a)

        # 去重（normalize级）
        seen = set()
        final_names = []

        for n in channels[cid]["names"]:
            nn = normalize(n)
            if nn not in seen:
                final_names.append(n)
                seen.add(nn)

        channels[cid]["names"] = final_names

        # logo匹配
        logo = ""
        for n in channels[cid]["names"]:
            nn = normalize(n)
            if nn in norm_icon_map:
                logo = norm_icon_map[nn]
                break

        channels[cid]["logo"] = logo

    # ===================== STEP 2: 输出结构转换 ===================== #
    final_channels = {}

    for cid, data in channels.items():

        if not data["names"]:
            continue

        # ✔ 第一个 display-name 作为 key（你要的）
        primary_name = data["names"][0].strip()

        final_channels[primary_name] = {
            "epgid": cid,
            "logo": data["logo"],
            "name": ",".join(data["names"])
        }

    # ===================== WRITE ===================== #
    print("\n📤 输出路径:", os.path.abspath(OUTPUT_FILE))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_channels, f, ensure_ascii=False, indent=2)

    print("✅ DONE:", len(final_channels))


if __name__ == "__main__":
    main()
