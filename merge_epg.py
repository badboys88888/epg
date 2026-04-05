import requests
import gzip
import xml.etree.ElementTree as ET
import json

SOURCE_FILE = "epg_sources.txt"
XML_OUTPUT = "e.xml.gz"
JSON_OUTPUT = "epg_data.json"
ICON_BASE = "https://gcore.jsdelivr.net/gh/taksssss/tv/icon/"

# ========== 读取EPG源 ==========
def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

# ========== 自动识别 XML / GZ ==========
def load_xml(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    content = r.content

    # gzip 自动识别（关键）
    if content[:2] == b'\x1f\x8b':
        content = gzip.decompress(content)

    return ET.fromstring(content)

channels = {}
programmes = []
seen = set()

# ========== 合并EPG ==========
for url in load_sources():
    try:
        root = load_xml(url)

        # channel 去重
        for ch in root.findall("channel"):
            cid = ch.get("id")
            if cid and cid not in channels:
                channels[cid] = ch

        # programme 去重
        for p in root.findall("programme"):
            key = (p.get("channel"), p.get("start"), p.get("stop"))
            if key not in seen:
                seen.add(key)
                programmes.append(p)

        print("OK:", url)

    except Exception as e:
        print("FAIL:", url, e)

# ========== 输出 e.xml.gz ==========
tv = ET.Element("tv")

for ch in channels.values():
    tv.append(ch)

for p in programmes:
    tv.append(p)

tree = ET.ElementTree(tv)

with gzip.open(XML_OUTPUT, "wt", encoding="utf-8") as f:
    tree.write(f, encoding="unicode", xml_declaration=True)

print("DONE XML ->", XML_OUTPUT)

# ========== 输出 epg_data.json ==========
epg_list = []

for cid in channels.keys():
    epg_list.append({
        "epgid": cid,
        "logo": ICON_BASE + cid + ".png",
        "name": cid + ","
    })

with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(epg_list, f, ensure_ascii=False, indent=2)

print("DONE JSON ->", JSON_OUTPUT)
