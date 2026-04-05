#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import gzip
import requests
from opencc import OpenCC
from rapidfuzz import fuzz

# ===================== 配置区 ===================== #

INPUT_SOURCES = [
    {"type": "m3u", "path": "input.m3u"},
    # {"type": "json", "path": "channels.json"},
    # {"type": "api", "url": "http://127.0.0.1/api"}
]

EPG_SOURCE_FILE = "epg.txt"
ICON_MAP_URL = "https://raw.githubusercontent.com/badboys88888/epg/main/icon_map.json"

OUT_M3U = "output.m3u"
OUT_JSON = "epg_data.json"
OUT_XMLGZ = "e.xml.gz"

cc = OpenCC("t2s")

# ===================== 基础工具 ===================== #

def norm(name: str):
    name = cc.convert(name)
    name = name.lower().strip()
    name = re.sub(r'[\s\-\_\[\]\(\)\.\|]+', '', name)
    name = name.replace("hd", "").replace("4k", "")
    return name


def load_icon_map():
    try:
        return requests.get(ICON_MAP_URL, timeout=10).json()
    except:
        return {}


# ===================== 多轨索引（核心） ===================== #

def build_keys(name: str):
    keys = set()

    base = norm(name)
    simp = cc.convert(name)

    keys.add(name)
    keys.add(base)
    keys.add(simp)

    # CCTV规则（正则核心）
    m = re.search(r'cctv[- ]*(\d{1,2})', base)
    if m:
        keys.add(f"cctv{m.group(1)}")
        keys.add("cctv")

    # 卫视规则
    if "hunan" in base or "湖南" in name:
        keys.add("hunan")
    if "dongfang" in base or "东方" in name:
        keys.add("dongfang")
    if "guangdong" in base or "广东" in name:
        keys.add("guangdong")

    # 港台
    if "tvb" in base:
        keys.add("tvb")

    return list(keys)


# ===================== EPG加载 ===================== #

def load_epg():
    epg_list = []

    try:
        with open(EPG_SOURCE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "|" not in line:
                    continue

                name = line.split("|")[0].strip()
                epg_list.append({
                    "name": name,
                    "norm": norm(name),
                    "keys": build_keys(name)
                })
    except:
        pass

    return epg_list


# ===================== 输入适配层 ===================== #

def parse_m3u(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            name = lines[i].split(",")[-1].strip()
            url = lines[i + 1].strip()

            items.append({
                "name": name,
                "url": url
            })

    return items


def load_channels():
    result = []

    for src in INPUT_SOURCES:

        if src["type"] == "m3u":
            result += parse_m3u(src["path"])

    return result


# ===================== 匹配引擎 ===================== #

def match_channel(ch, epg_list):

    ch_keys = build_keys(ch["name"])
    ch_norm = norm(ch["name"])

    best = None
    best_score = 0

    for e in epg_list:

        # 1. 精确匹配（多轨）
        if set(ch_keys) & set(e["keys"]):
            return e

        # 2. fuzzy
        score = fuzz.ratio(ch_norm, e["norm"])
        if score > best_score:
            best_score = score
            best = e

    if best_score >= 85:
        return best

    return None


# ===================== 输出EPG XML ===================== #

def build_xml(epg_list):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv>']

    for e in epg_list:
        cid = norm(e["name"])

        xml.append(f'<channel id="{cid}">')
        xml.append(f'<display-name>{e["name"]}</display-name>')
        xml.append('</channel>')

    xml.append('</tv>')
    return "\n".join(xml)


def save_gz(xml_str):
    with gzip.open(OUT_XMLGZ, "wb") as f:
        f.write(xml_str.encode("utf-8"))


# ===================== 主流程 ===================== #

def main():

    icon_map = load_icon_map()
    epg_list = load_epg()
    channels = load_channels()

    out_m3u = []
    out_json = []

    for ch in channels:

        epg = match_channel(ch, epg_list)

        if epg:

            tvg_id = norm(epg["name"])
            tvg_name = epg["name"]
            tvg_logo = icon_map.get(tvg_id, "")

            out_m3u.append(
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}" tvg-logo="{tvg_logo}",{tvg_name}\n{ch["url"]}'
            )

            out_json.append({
                "channel": ch["name"],
                "epg": epg["name"],
                "tvg_id": tvg_id
            })

        else:
            out_m3u.append(
                f'#EXTINF:-1,{ch["name"]}\n{ch["url"]}'
            )

    # ===== 输出 M3U ===== #
    with open(OUT_M3U, "w", encoding="utf-8") as f:
        f.write("\n".join(out_m3u))

    # ===== 输出 JSON ===== #
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out_json, f, ensure_ascii=False, indent=2)

    # ===== 输出 XML ===== #
    xml = build_xml(epg_list)
    save_gz(xml)

    print("✅ v3 AI引擎执行完成")


if __name__ == "__main__":
    main()
