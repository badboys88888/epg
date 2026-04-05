#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import gzip
import xml.etree.ElementTree as ET
import json
import re
from opencc import OpenCC

# ===================== 配置 =====================
SOURCE_FILE = "epg_sources.txt"

XML_OUTPUT = "e.xml.gz"
JSON_OUTPUT = "epg_data.json"
INDEX_OUTPUT = "index.json"

ICON_MAP_URL = "https://raw.githubusercontent.com/badboys88888/epg/main/icon_map.json"

# ===================== 初始化 =====================
cc = OpenCC('t2s')

# ===================== 加载icon =====================
try:
    icon_map = requests.get(ICON_MAP_URL, timeout=30).json()
except:
    icon_map = {}
    print("⚠️ icon_map 加载失败")

# ===================== 名字清洗 =====================
def normalize(name):
    name = name.strip()
    name = cc.convert(name)

    name = re.sub(r'\s+', '', name)
    name = name.replace("-", "")
    name = name.replace("高清", "")
    name = name.replace("HD", "")
    name = name.replace("频道", "")
    name = name.replace("台", "")
    name = name.replace("4K", "")

    return name.lower()

# ===================== 索引规则 =====================
INDEX_RULES = {

    # ===== CCTV（精准）=====
    "CCTV1": ["cctv1"],
    "CCTV2": ["cctv2"],
    "CCTV3": ["cctv3"],
    "CCTV4": ["cctv4"],
    "CCTV5": ["cctv5"],
    "CCTV6": ["cctv6"],
    "CCTV7": ["cctv7"],
    "CCTV8": ["cctv8"],
    "CCTV9": ["cctv9"],
    "CCTV10": ["cctv10"],
    "CCTV11": ["cctv11"],
    "CCTV12": ["cctv12"],
    "CCTV13": ["cctv13"],
    "CCTV14": ["cctv14"],
    "CCTV15": ["cctv15"],
    "CCTV16": ["cctv16"],
    "CCTV17": ["cctv17"],

    # ===== 分类 =====
    "电影": ["1905", "电影", "影院"],
    "体育": ["体育", "sport", "espn"],
    "新闻": ["新闻", "news", "cnn", "bbc"],
    "少儿": ["少儿", "动漫"],

    # ===== 地区 =====
    "黑龙江": ["黑龙江"],
    "湖南": ["湖南"],
    "广东": ["广东"],
    "北京": ["北京"],
    "上海": ["东方", "新视觉"],
}

# ===================== 匹配索引 =====================
def match_index(name):
    n = normalize(name)

    for key, aliases in INDEX_RULES.items():
        for a in aliases:

            # CCTV保护
            if key.startswith("CCTV") and "cctv" not in n:
                continue

            if a in n:
                return key

    return name

# ===================== icon匹配 =====================
def get_icon(key):
    k = normalize(key)

    if k in icon_map:
        return icon_map[k]

    for i, v in icon_map.items():
        if normalize(i) == k:
            return v

    return ""

# ===================== 读取源 =====================
def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

# ===================== 获取XML =====================
def fetch_xml(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.content

    # 自动判断 gzip
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)

    return ET.fromstring(data)

# ===================== 主流程 =====================
channels = {}
programmes = []
seen_programmes = set()

print("🚀 开始合并EPG...")

for url in load_sources():
    try:
        root = fetch_xml(url)

        # 频道
        for ch in root.findall("channel"):
            cid = ch.get("id")
            if cid and cid not in channels:
                channels[cid] = ch

        # 节目
        for p in root.findall("programme"):
            key = (p.get("channel"), p.get("start"), p.get("stop"))
            if key not in seen_programmes:
                seen_programmes.add(key)
                programmes.append(p)

        print("✅ OK:", url)

    except Exception as e:
        print("❌ FAIL:", url, e)

print("📊 频道数:", len(channels))
print("📊 节目数:", len(programmes))

# ===================== 输出XML =====================
tv = ET.Element("tv")

for ch in channels.values():
    tv.append(ch)

for p in programmes:
    tv.append(p)

tree = ET.ElementTree(tv)

with gzip.open(XML_OUTPUT, "wt", encoding="utf-8") as f:
    tree.write(f, encoding="unicode", xml_declaration=True)

print("✅ XML 输出完成")

# ===================== 生成 JSON + INDEX =====================
epg_list = []
index_output = {}

for cid, ch in channels.items():

    name = None
    for n in ch.findall("display-name"):
        if n.text:
            name = n.text.strip()
            break

    if not name:
        name = cid

    group = match_index(name)

    # epg数据
    epg_list.append({
        "epgid": group,
        "name": name,
        "logo": get_icon(group)
    })

    # index（只记录归一的）
    if group != name:
        if group not in index_output:
            index_output[group] = []

        if name not in index_output[group]:
            index_output[group].append(name)

# 去重
for k in index_output:
    index_output[k] = list(set(index_output[k]))

# ===================== 写文件 =====================
with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(epg_list, f, ensure_ascii=False, indent=2)

with open(INDEX_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(index_output, f, ensure_ascii=False, indent=2)

print("✅ JSON 输出完成")
print("🎉 全部完成")
