import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

SOURCE_FILE = "epg_sources.txt"


def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f.readlines() if x.strip()]


def download(url):
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    data = r.content

    if url.endswith(".gz"):
        try:
            data = gzip.decompress(data)
        except:
            pass

    return data


def match_channel(name):
    if not name:
        return None

    n = name.lower()

    if "cctv" in n or "央视" in n:
        return "cctv"

    if "bbc" in n:
        return "bbc"

    if "tvb" in n or "jade" in n:
        return "tvb"

    if "hbo" in n:
        return "hbo"

    return None


def main():

    sources = load_sources()

    tv = ET.Element("tv")
    seen = set()

    print("sources:", len(sources))

    for url in sources:

        try:
            data = download(url)
            root = ET.fromstring(data)

            print("OK:", url)

            for prog in root.findall("programme"):

                ch = prog.attrib.get("channel", "")
                cid = match_channel(ch)

                if not cid:
                    continue

                title = prog.find("title")
                title = title.text if title is not None else ""

                start = prog.attrib.get("start", "")

                key = cid + start + title
                if key in seen:
                    continue
                seen.add(key)

                p = ET.SubElement(tv, "programme", {
                    "channel": cid,
                    "start": start,
                    "stop": prog.attrib.get("stop", "")
                })

                t = ET.SubElement(p, "title")
                t.text = title

        except Exception as e:
            print("FAIL:", url, e)

    xml = ET.tostring(tv, encoding="utf-8")

    with gzip.open("epg.xml.gz", "wb") as f:
        f.write(xml)

    print("DONE → epg.xml.gz")


if __name__ == "__main__":
    main()
