#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import xml.etree.ElementTree as ET
import json
import re
import unicodedata
import requests

INPUT_FILE = "epg.xml.gz"
OUTPUT_FILE = "channels.json"

ICON_MAP_FILE = "icon_map.json"
ALIAS_FILE = "alias_map.json"

EPG_INDEX_URL = "https://raw.githubusercontent.com/taksssss/tv/refs/heads/main/ku9/epg_data.json"


# ===================== EPG ===================== #
def load_epg():
    try:
        with gzip.open(INPUT_FILE, "rb") as f:
            return ET.parse(f).getroot()
    except Exception as e:
        print("[WARN] EPG加载失败:", e)
        return None


# ===================== 远程索引 ===================== #
def load_remote_index():
    try:
        r = requests.get(EPG_INDEX_URL, timeout=20)
        data = r.json()

        index = {}

        for item in data.get("epgs", []):
            logo = item.get("logo", "")
            names = item.get("name", "").split(",")

            for n in names:
                n = n.strip()
                if n:
                    index[normalize(n)] = logo

        print("[OK] 远程索引:", len(index))
        return index

    except Exception as e:
        print("[WARN] 远程索引失败:", e)
        return {}


# ===================== ICON ===================== #
def load_icon_map():
    try:
        with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


# ===================== ALIAS ===================== #
def load_alias():
    try:
        with open(ALIAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"exact": {}}


# ===================== normalize ===================== #
def normalize(name):
    if not name:
        return ""

    name = unicodedata.normalize("NFKC", name)
    name = name.upper()
    name = re.sub(r"[\s\-\_\(\)（）·\.／\/]", "", name)

    return name


# ===================== 主逻辑 ===================== #
def main():

    root = load_epg()
    icon_map = load_icon_map()
    alias_raw = load_alias()
    remote_index = load_remote_index()

    alias_exact = alias_raw.get("exact", {})
    norm_icon_map = {normalize(k): v for k, v in icon_map.items()}

    channels = {}

    if root is None:
        root = ET.Element("tv")

    # ===================== 解析频道 ===================== #
    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")
        if not cid:
            continue

        names = [n.text.strip() for n in ch.findall("display-name") if n.text]

        if not names:
            names = [cid]

        if cid not in channels:
            channels[cid] = {
                "names": [],
                "logo": ""
            }

        # ===== EPG原始名 ===== #
        for n in names:
            if n not in channels[cid]["names"]:
                channels[cid]["names"].append(n)

        # ===== alias补充 ===== #
        if cid in alias_exact:
            for a in alias_exact[cid]:
                if a not in channels[cid]["names"]:
                    channels[cid]["names"].append(a)

        # ===== 去重 ===== #
        seen = set()
        clean = []

        for n in channels[cid]["names"]:
            nn = normalize(n)
            if nn not in seen:
                clean.append(n)
                seen.add(nn)

        channels[cid]["names"] = clean

        # ===== logo匹配 ===== #
        logo = ""

        for n in clean:
            nn = normalize(n)

            # 本地优先
            if nn in norm_icon_map:
                logo = norm_icon_map[nn]
                break

            # 远程兜底
            if nn in remote_index:
                logo = remote_index[nn]
                break

        channels[cid]["logo"] = logo

    # ===================== 输出 ===================== #
    final = {}

    for cid, data in channels.items():

        final[cid] = {
            "epgid": cid,  # ✅ 永远用cid（核心修复）
            "name": ",".join(data["names"]),
            "logo": data["logo"]
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print("✅ DONE:", len(final))


if __name__ == "__main__":
    main()
