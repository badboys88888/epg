import requests
import gzip
import xml.etree.ElementTree as ET
import json

SOURCE_FILE = "epg_sources.txt"
XML_OUTPUT = "e.xml"
JSON_OUTPUT = "epg_data.json"
ICON_BASE = "https://gcore.jsdelivr.net/gh/taksssss/tv/icon/"

def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

def load_xml(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()

    content = r.content
    if content[:2] == b'\x1f\x8b':
        content = gzip.decompress(content)

    return ET.fromstring(content)

channels = {}
programmes = []
seen = set()

# ================== 合并 EPG ================== #
for url in load_sources():
    try:
        root = load_xml(url)

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

# ================== 输出 e.xml ================== #
tv = ET.Element("tv")

for ch in channels.values():
    tv.append(ch)

for p in programmes:
    tv.append(p)

ET.ElementTree(tv).write(XML_OUTPUT, encoding="utf-8", xml_declaration=True)

print("DONE XML ->", XML_OUTPUT)

# ================== 生成 epg_data.json ================== #
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
