import xml.etree.ElementTree as ET
import gzip
import json
import os

EPG_FILE = "epg.xml.gz"
ICON_MAP_FILE = "icon_map.json"
OUTPUT_FILE = "channels.json"


# ===================== 读取EPG ===================== #
def load_epg(path):
    with gzip.open(path, "rb") as f:
        return ET.parse(f).getroot()


# ===================== 读取icon ===================== #
def load_icons():
    if not os.path.exists(ICON_MAP_FILE):
        return {}
    with open(ICON_MAP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ===================== 核心：正确解析频道 ===================== #
def build_channel_map(root, icon_map):
    channels = {}

    for ch in root.findall("channel"):
        cid = ch.attrib.get("id")
        if not cid:
            continue

        # 1️⃣ 收集所有名字（关键修复点）
        names = []
        for n in ch.findall("display-name"):
            if n.text:
                name = n.text.strip()
                names.append(name)

        # 没有名字就用id兜底
        if not names:
            names = [cid]

        # 2️⃣ logo匹配（用所有名字去匹配）
        logo = ""
        for n in names:
            if n in icon_map:
                logo = icon_map[n]
                break

        # 3️⃣ 写入结构
        channels[cid] = {
            "epg_id": cid,
            "names": names,
            "logo": logo
        }

    return channels


# ===================== 合并旧数据（防覆盖） ===================== #
def merge_old(new_data):
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                old = json.load(f)
            except:
                old = {}
    else:
        old = {}

    for k, v in new_data.items():
        if k in old:
            # 合并 names
            old_names = set(old[k].get("names", []))
            new_names = set(v.get("names", []))

            old[k]["names"] = list(old_names | new_names)

            # logo 优先用新的
            if v.get("logo"):
                old[k]["logo"] = v["logo"]
        else:
            old[k] = v

    return old


# ===================== 主流程 ===================== #
if __name__ == "__main__":
    root = load_epg(EPG_FILE)
    icon_map = load_icons()

    new_channels = build_channel_map(root, icon_map)
    final_data = merge_old(new_channels)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"done -> {OUTPUT_FILE}")
