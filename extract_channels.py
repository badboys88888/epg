import gzip
import xml.etree.ElementTree as ET
import json
import os
import re
import unicodedata

INPUT_FILE = "epg.xml.gz"
OUTPUT_FILE = "channels.json"
ICON_MAP_FILE = "icon_map.json"
ALIAS_FILE = "alias_map.json"


# ===================== 读取EPG ===================== #
def load_epg():
    print("📦 EPG路径:", os.path.abspath(INPUT_FILE))
    with gzip.open(INPUT_FILE, "rb") as f:
        return ET.parse(f).getroot()


# ===================== 读取logo ===================== #
def load_icon_map():
    try:
        with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print("🖼️ logo_map加载:", len(data))
            return data
    except Exception as e:
        print("❌ logo_map加载失败:", e)
        return {}


# ===================== 读取alias ===================== #
def load_alias():
    try:
        with open(ALIAS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print("✅ alias加载成功:", len(data))
            return data
    except Exception as e:
        print("❌ alias加载失败:", e)
        return {}


# ===================== 🔥 统一规范化（关键修复） ===================== #
def normalize(name):
    if not name:
        return ""

    name = unicodedata.normalize("NFKC", name)
    name = name.upper()
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"[-_()（）·\.]", "", name)

    return name


# ===================== 主逻辑 ===================== #
def main():

    print("🚀 RUNNING extract_channels FINAL")

    root = load_epg()
    icon_map = load_icon_map()
    alias_map = load_alias()

    print("📊 alias_map内容:", alias_map)

    # 🔥 关键：先把 icon_map 全部 normalize 一遍（性能+命中率提升）
    norm_icon_map = {normalize(k): v for k, v in icon_map.items()}

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

        key = normalize(names[0])

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

        # ===== alias ===== #
        if cid in alias_map:
            for a in alias_map[cid]:
                if a not in channels[key]["names"]:
                    channels[key]["names"].append(a)

        # ===== 去重（normalize级） ===== #
        seen = set()
        final_names = []

        for n in channels[key]["names"]:
            nn = normalize(n)
            if nn not in seen:
                final_names.append(n)
                seen.add(nn)

        channels[key]["names"] = final_names

        # ===================== 🔥 LOGO匹配（核心修复） ===================== #
        logo = ""

        for n in channels[key]["names"]:

            # ✔ 关键：必须 normalize 后再匹配
            nn = normalize(n)

            if nn in norm_icon_map:
                logo = norm_icon_map[nn]
                break

        channels[key]["logo"] = logo


    # ===================== 输出结构 ===================== #
    for key in channels:
        channels[key]["name"] = ",".join(channels[key]["names"])
        del channels[key]["names"]


    print("\n📤 输出路径:", os.path.abspath(OUTPUT_FILE))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    print("✅ DONE:", len(channels))


if __name__ == "__main__":
    main()
