import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

SOURCE_FILE = "epg_sources.txt"
OUTPUT_FILE = "epg.xml.gz"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===================== 读取源 ===================== #
def load_sources():
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


# ===================== 下载 ===================== #
def download(url):
    r = requests.get(url, timeout=30, headers=HEADERS)
    data = r.content

    # gz处理（安全版）
    if url.endswith(".gz"):
        try:
            data = gzip.decompress(data)
        except:
            pass

    return data


# ===================== XML安全解析 ===================== #
def parse_xml(data):
    try:
        # 防止HTML
        if b"<tv" not in data:
            return None
        return ET.fromstring(data)
    except:
        return None


# ===================== 主逻辑 ===================== #
def main():

    sources = load_sources()

    tv = ET.Element("tv")

    seen = set()

    print("📡 sources:", len(sources))

    for url in sources:

        try:
            data = download(url)
            root = parse_xml(data)

            if root is None:
                print("❌ skip invalid:", url)
                continue

            print("✅ OK:", url)

            for prog in root.findall("programme"):

                ch = prog.attrib.get("channel", "")
                start = prog.attrib.get("start", "")
                stop = prog.attrib.get("stop", "")

                title_node = prog.find("title")
                title = title_node.text.strip() if title_node is not None and title_node.text else ""

                if not ch or not start:
                    continue

                key = ch + start + title
                if key in seen:
                    continue
                seen.add(key)

                p = ET.SubElement(tv, "programme", {
                    "channel": ch,
                    "start": start,
                    "stop": stop
                })

                t = ET.SubElement(p, "title")
                t.text = title

        except Exception as e:
            print("❌ FAIL:", url, e)

    # ===================== 输出 ===================== #
    xml = ET.tostring(tv, encoding="utf-8")

    with gzip.open(OUTPUT_FILE, "wb") as f:
        f.write(xml)

    print("🎉 DONE →", OUTPUT_FILE)
    print("📦 total programs:", len(seen))


if __name__ == "__main__":
    main()
