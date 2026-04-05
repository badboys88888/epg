import gzip
import xml.etree.ElementTree as ET
import json

INPUT_FILE = "epg.xml.gz"
OUTPUT_FILE = "channels.json"


# ===================== 读取EPG ===================== #
def load_epg():

    with gzip.open(INPUT_FILE, "rb") as f:
        data = f.read()

    return ET.fromstring(data)


# ===================== 清洗频道名 ===================== #
def clean_name(name: str) -> str:
    if not name:
        return ""

    return name.strip()


# ===================== 主逻辑 ===================== #
def main():

    root = load_epg()

    channels = {}

    # ===================== 解析 channel 表 ===================== #
    for ch in root.findall("channel"):

        cid = ch.attrib.get("id", "")
        if not cid:
            continue

        names = []

        for dn in ch.findall("display-name"):
            if dn.text:
                n = clean_name(dn.text)
                if n:
                    names.append(n)

        # 去重
        names = list(dict.fromkeys(names))

        if names:
            channels[cid] = {
                "epg_id": cid,
                "names": names,
                "logo": ""
            }

    # ===================== 备用：从 programme 补充频道 ===================== #
    for prog in root.findall("programme"):

        cid = prog.attrib.get("channel", "")
        if not cid:
            continue

        if cid not in channels:
            channels[cid] = {
                "epg_id": cid,
                "names": [cid],
                "logo": ""
            }

    # ===================== 输出 ===================== #
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    print("🎉 DONE →", OUTPUT_FILE)
    print("📦 channels:", len(channels))


if __name__ == "__main__":
    main()
