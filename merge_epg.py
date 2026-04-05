import requests
import gzip
import xml.etree.ElementTree as ET
import json
import os

SOURCE_FILE = "epg_sources.txt"

XML_GZ = "e.xml.gz"
JSON_OUTPUT = "epg_data.json"

ICON_BASE = "https://raw.githubusercontent.com/badboys88888/scmobilemulticast/main/icons/"

# ========= 读取源 =========
def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

# ========= 自动处理 xml / gz =========
def fetch_xml(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.content

    # gzip 自动识别
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)

    return ET.fromstring(data)

channels = {}
programmes = []
seen = set()

# ========= 合并 =========
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

# ========= 输出 XML =========
tv = ET.Element("tv")

for ch in channels.values():
    tv.append(ch)

for p in programmes:
    tv.append(p)

tree = ET.ElementTree(tv)

with gzip.open(XML_GZ, "wt", encoding="utf-8") as f:
    tree.write(f, encoding="unicode", xml_declaration=True)

print("DONE XML ->", XML_GZ)

# ========= 输出 JSON =========
epg_list = []
for cid in channels.keys():
    epg_list.append({
        "epgid": cid,
        "logo": ICON_BASE + cid + ".png",
        "name": cid
    })

with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(epg_list, f, ensure_ascii=False, indent=2)

print("DONE JSON ->", JSON_OUTPUT)

# ========= 自动返回文件列表（关键防错） =========
print("FILES:", os.listdir("."))
