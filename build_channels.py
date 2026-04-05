import gzip
import xml.etree.ElementTree as ET
import json

INPUT_FILE = "epg.xml.gz"
OUTPUT_FILE = "channels.json"
ICON_MAP_FILE = "icon_map.json"
ALIAS_FILE = "alias_map.json"


# ===================== 读取EPG ===================== #
def load_epg():
    with gzip.open(INPUT_FILE, "rb") as f:
        return ET.parse(f).getroot()


# ===================== 读取logo ===================== #
def load_icon_map():
    try:
        with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


# ===================== 读取alias ===================== #
def load_alias():
    try:
        with open(ALIAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


# ===================== 统一规则 ===================== #
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
    alias_map = load_alias()

    channels = {}

    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")
        if not cid:
            continue

        # ===== display-name ===== #
        names = []
        for n in ch.findall("display-name"):
            if n.text:
                names.append(n.text.strip())

        if not names:
            names = [cid]

        # ⭐ 自动归类 key
        key = normalize(names[0])

        # ===== 初始化 ===== #
        if key not in channels:
            channels[key] = {
                "epgid": cid,
                "names": [],
                "logo": ""
            }

        # ===== 合并EPG names ===== #
        for n in names:
            if n not in channels[key]["names"]:
                channels[key]["names"].append(n)

        # ===== ⭐ alias 手动补充（关键） ===== #
        # 支持 CCTV1 / CGTN 等补充
        if cid in alias_map:
            for a in alias_map[cid]:
                if a not in channels[key]["names"]:
                    channels[key]["names"].append(a)

        # ===== ⭐ 再做一次去重（防重复） ===== #
        seen = set()
        final_names = []

        for n in channels[key]["names"]:
            nn = normalize(n)
            if nn not in seen:
                final_names.append(n)
                seen.add(nn)

        channels[key]["names"] = final_names

        # ===== logo匹配 ===== #
        logo = ""
        for n in channels[key]["names"]:
            if n in icon_map:
                logo = icon_map[n]
                break

        if logo:
            channels[key]["logo"] = logo

    # ===================== 输出 ===================== #
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    print("DONE:", len(channels))


if __name__ == "__main__":
    main()
