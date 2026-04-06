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


# ===================== EPG ===================== #
def load_epg():
    print("📦 EPG路径:", os.path.abspath(INPUT_FILE))
    with gzip.open(INPUT_FILE, "rb") as f:
        return ET.parse(f).getroot()


# ===================== ICON ===================== #
def load_icon_map():
    try:
        with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print("🖼️ logo_map加载:", len(data))
            return data
    except Exception as e:
        print("❌ logo_map加载失败:", e)
        return {}


# ===================== ALIAS ===================== #
def load_alias():
    try:
        with open(ALIAS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print("✅ alias加载成功")
            return data
    except Exception as e:
        print("❌ alias加载失败:", e)
        return {"exact": {}}


# ===================== normalize ===================== #
def normalize(name):
    if not name:
        return ""

    name = unicodedata.normalize("NFKC", name)
    name = name.upper()
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"[-_()（）·\.]", "", name)

    return name


# ===================== MAIN ===================== #
def main():

    print("🚀 RUNNING extract_channels FINAL (CID VERSION)")

    root = load_epg()
    icon_map = load_icon_map()
    alias_raw = load_alias()

    # ✔ 只用 exact（完全禁用 regex）
    alias_exact = alias_raw.get("exact", {})

    print("📊 alias_exact:", len(alias_exact))

    # ===================== logo normalize ===================== #
    norm_icon_map = {normalize(k): v for k, v in icon_map.items()}

    channels = {}

    # ===================== PARSE CHANNELS ===================== #
    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")
        if not cid:
            continue

        # ---------------- names ---------------- #
        names = []
        for n in ch.findall("display-name"):
            if n.text:
                names.append(n.text.strip())

        if not names:
            names = [cid]

        # ===================== CID 主键（核心） ===================== #
        if cid not in channels:
            channels[cid] = {
                "epgid": cid,
                "names": [],
                "logo": ""
            }

        # ===================== 合并EPG names ===================== #
        for n in names:
            if n not in channels[cid]["names"]:
                channels[cid]["names"].append(n)

        # ===================== alias 精确匹配 ===================== #
        if cid in alias_exact:
            for a in alias_exact[cid]:
                if a not in channels[cid]["names"]:
                    channels[cid]["names"].append(a)

        # ===================== 去重（normalize级） ===================== #
        seen = set()
        final_names = []

        for n in channels[cid]["names"]:
            nn = normalize(n)
            if nn not in seen:
                final_names.append(n)
                seen.add(nn)

        channels[cid]["names"] = final_names

        # ===================== logo匹配 ===================== #
        logo = ""

        for n in channels[cid]["names"]:
            nn = normalize(n)
            if nn in norm_icon_map:
                logo = norm_icon_map[nn]
                break

        channels[cid]["logo"] = logo

    # ===================== 输出结构 ===================== #
    for cid in channels:
        channels[cid]["name"] = ",".join(channels[cid]["names"])
        del channels[cid]["names"]

    print("\n📤 输出路径:", os.path.abspath(OUTPUT_FILE))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    print("✅ DONE:", len(channels))


if __name__ == "__main__":
    main()
