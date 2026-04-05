import gzip
import xml.etree.ElementTree as ET
import json
import os

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


# ===================== 统一名称 ===================== #
def normalize(name):
    return (
        name.upper()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


# ===================== 主逻辑 ===================== #
def main():

    print("🚀 RUNNING extract_channels FINAL")

    root = load_epg()
    icon_map = load_icon_map()
    alias_map = load_alias()

    print("📊 alias_map内容:", alias_map)

    channels = {}

    for ch in root.findall("channel"):

        cid = ch.attrib.get("id")
        if not cid:
            continue

        # ===== 读取 display-name ===== #
        names = []
        for n in ch.findall("display-name"):
            if n.text:
                names.append(n.text.strip())

        if not names:
            names = [cid]

        # ⭐ 用 normalize 做 key
        key = normalize(names[0])

        # ===== 初始化 ===== #
        if key not in channels:
            channels[key] = {
                "epgid": cid,
                "names": [],   # ⚠️ 必须是 list
                "logo": ""
            }

        # ===== 合并EPG names ===== #
        for n in names:
            if n not in channels[key]["names"]:
                channels[key]["names"].append(n)

        # ===== alias 扩展 ===== #
        if cid in alias_map:
            for a in alias_map[cid]:
                if a not in channels[key]["names"]:
                    channels[key]["names"].append(a)

        # ===== 去重（normalize级别） ===== #
        seen = set()
        final_names = []

        for n in channels[key]["names"]:
            nn = normalize(n)
            if nn not in seen:
                final_names.append(n)
                seen.add(nn)

        channels[key]["names"] = final_names

        # ===== logo匹配 ===== #
        for n in channels[key]["names"]:
            if n in icon_map:
                channels[key]["logo"] = icon_map[n]
                break

    # ===================== 转换成 name 字符串 ===================== #
    for key in channels:
        names = channels[key]["names"]

        # 👉 拼接成一行
        channels[key]["name"] = ",".join(names)

        # 👉 删除原names字段
        del channels[key]["names"]

    # ===================== 输出 ===================== #
    print("\n📤 输出路径:", os.path.abspath(OUTPUT_FILE))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    print("✅ DONE:", len(channels))


if __name__ == "__main__":
    main()
