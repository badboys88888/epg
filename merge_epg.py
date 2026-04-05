import requests
import gzip
import xml.etree.ElementTree as ET
import json
import re

SOURCE_FILE = "epg_sources.txt"

EPG_XML_GZ = "e.xml.gz"
EPG_JSON = "epg_data.json"

ICON_MAP_URL = "https://raw.githubusercontent.com/badboys88888/epg/main/icon_map.json"


# ===================== 读取源 =====================
def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


# ===================== 获取远程icon =====================
icon_map = requests.get(ICON_MAP_URL, timeout=30).json()


# ===================== 统一名称 =====================
def normalize(name):
    name = name.strip()
    name = re.sub(r'\s+', '', name)
    name = name.replace("高清", "")
    name = name.replace("HD", "")
    name = name.replace("4K", "")
    name = name.replace("-", "")
    return name.lower()


# ===================== icon匹配 =====================
def get_icon(name):
    key = normalize(name)

    # 1️⃣ 精确匹配
    if key in icon_map:
        return icon_map[key]

    # 2️⃣ 模糊匹配
    for k, v in icon_map.items():
        if normalize(k) == key:
            return v

    return ""


# ===================== 解析XML =====================
def fetch_xml(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.content

    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)

    return ET.fromstring(data)


channels = {}
programmes = []
seen = set()

# ===================== 合并EPG =====================
for url in load_sources():
    try:
        root = fetch_xml(url)

        for ch in root.findall("channel"):
            cid = ch.get("id")
            if cid and cid not in channels:
                channels[cid] = ch

        for p in root.findall("programme"):
            key = (p.get("channel"), p.get("start"), p.get("stop"))
            if key not in seen:
                seen.add(key)
                programmes.append(p)

        print("OK:", url)

    except Exception as e:
        print("FAIL:", url, e)


# ===================== XML输出 =====================
tv = ET.Element("tv")

for ch in channels.values():
    tv.append(ch)

for p in programmes:
    tv.append(p)

tree = ET.ElementTree(tv)

with gzip.open(EPG_XML_GZ, "wt", encoding="utf-8") as f:
    tree.write(f, encoding="unicode", xml_declaration=True)

print("DONE XML ->", EPG_XML_GZ)


# ===================== JSON输出 =====================
epg_list = []

for cid, ch in channels.items():

    # 取频道名
    name = None
    for n in ch.findall("display-name"):
        if n.text:
            name = n.text.strip()
            break

    if not name:
        name = cid

    epg_list.append({
        "epgid": cid,
        "name": name,
        "logo": get_icon(name)
    })

with open(EPG_JSON, "w", encoding="utf-8") as f:
    json.dump(epg_list, f, ensure_ascii=False, indent=2)

print("DONE JSON ->", EPG_JSON)
