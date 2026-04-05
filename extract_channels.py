import gzip
import xml.etree.ElementTree as ET
import json

INPUT_FILE = "epg.xml.gz"
OUTPUT_FILE = "channels.json"
ICON_MAP_FILE = "icon_map.json"


# ===================== 读取EPG ===================== #
def load_epg():
    with gzip.open(INPUT_FILE, "rb") as f:
        return ET.parse(f).getroot()


# ===================== 读取logo映射 ===================== #
def load_icon_map():
    try:
        with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


# ===================== 统一频道名 ===================== #
def normalize(name):
    return (
        name.upper()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


# ===================== 主逻辑 ===================== #
def main():

    root = load_epg()
    icon_map = load_icon_map()

    channels = {}

    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")
        if not cid:
            continue

        names = []
        for n in ch.findall("display-name"):
            if n.text:
                names.append(n.text.strip())

        if not names:
            names = [cid]

        # ⭐ 用 names 生成唯一 key（核心变化）
        key = normalize(names[0])

        # ⭐ 查logo
        logo = ""
        for n in names:
            nk = normalize(n)
            if nk in icon_map:
                logo = icon_map[nk]
                break

        # ⭐ 初始化
        if key not in channels:
            channels[key] = {
                "epg_id": key,
                "names": [],
                "logo": ""
            }

        # ⭐ 合并 names（防重复）
        for n in names:
            if n not in channels[key]["names"]:
                channels[key]["names"].append(n)

        # ⭐ logo优先写入
        if logo:
            channels[key]["logo"] = logo

    # ===================== 输出 ===================== #
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    print("DONE:", len(channels))


if __name__ == "__main__":
    main()
