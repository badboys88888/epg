import requests
import gzip
import xml.etree.ElementTree as ET
import json
import re

SOURCE_FILE = "epg_sources.txt"

EPG_XML_GZ = "e.xml.gz"
EPG_JSON = "epg_data.json"
INDEX_FILE = "index.json"

ICON_MAP_URL = "https://raw.githubusercontent.com/badboys88888/epg/main/icon_map.json"


# ===================== 远程icon =====================
icon_map = requests.get(ICON_MAP_URL, timeout=30).json()


# ===================== 基础清洗 =====================
def normalize(name):
    name = name.strip()
    name = re.sub(r'\s+', '', name)
    name = name.replace("-", "")
    name = name.replace("高清", "")
    name = name.replace("HD", "")
    name = name.replace("4K", "")
    return name.lower()


# ===================== 索引库（核心） =====================
INDEX_RULES = {
    "CCTV1": ["cctv1", "cctv-1", "cctv 1", "综合"],
    "CCTV5": ["cctv5", "cctv-5", "体育"],
    "电影": ["1905", "电影", "影院", "CCTV6"],
    "4K": ["4k", "uhd", "超高清"],
}


# ===================== 生成索引 =====================
def match_index(name):
    n = normalize(name)

    for key, aliases in INDEX_RULES.items():
        for a in aliases:
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


# ===================== XML解析 =====================
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


# ===================== 输出 XML =====================
tv = ET.Element("tv")

for ch in channels.values():
    tv.append(ch)

for p in programmes:
    tv.append(p)

tree = ET.ElementTree(tv)

with gzip.open(EPG_XML_GZ, "wt", encoding="utf-8") as f:
    tree.write(f, encoding="unicode", xml_declaration=True)

print("XML DONE")


# ===================== 生成 index + epg =====================
index_output = {}
epg_list = []

for cid, ch in channels.items():

    name = None
    for n in ch.findall("display-name"):
        if n.text:
            name = n.text.strip()
            break

    if not name:
        name = cid

    group = match_index(name)

    # index归类
    if group not in index_output:
        index_output[group] = []

    index_output[group].append(name)

    epg_list.append({
        "epgid": group,
        "name": name,
        "logo": get_icon(group)
    })


# ===================== 写 index.json =====================
with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index_output, f, ensure_ascii=False, indent=2)

print("INDEX DONE")


# ===================== 写 epg.json =====================
with open(EPG_JSON, "w", encoding="utf-8") as f:
    json.dump(epg_list, f, ensure_ascii=False, indent=2)

print("EPG DONE")
