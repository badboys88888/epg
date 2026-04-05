import requests
import gzip
import xml.etree.ElementTree as ET

SOURCE_FILE = "epg_sources.txt"
OUTPUT_FILE = "merged_epg.xml"

def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

def load_xml(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    if url.endswith(".gz"):
        data = gzip.decompress(r.content)
    else:
        data = r.content

    return ET.fromstring(data)

channels = {}
programmes = []
seen = set()

for url in load_sources():
    try:
        root = load_xml(url)

        for ch in root.findall("channel"):
            cid = ch.get("id")
            if cid not in channels:
                channels[cid] = ch

        for p in root.findall("programme"):
            key = (p.get("channel"), p.get("start"), p.get("stop"))
            if key not in seen:
                seen.add(key)
                programmes.append(p)

        print("OK:", url)

    except Exception as e:
        print("FAIL:", url, e)

tv = ET.Element("tv")

for ch in channels.values():
    tv.append(ch)

for p in programmes:
    tv.append(p)

tree = ET.ElementTree(tv)
tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

print("DONE ->", OUTPUT_FILE)
