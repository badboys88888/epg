import gzip
import xml.etree.ElementTree as ET
import re

INPUT = "epg.xml.gz"
OUTPUT = "alias_auto.txt"


# ===================== 清洗名字 ===================== #
def clean_name(name):
    name = name.strip()

    # 去掉常见垃圾词（可自己加）
    name = re.sub(r"(高清|HD|频道|電視台|电视台)$", "", name, flags=re.I)

    return name.strip()


def main():

    with gzip.open(INPUT, "rb") as f:
        root = ET.parse(f).getroot()

    result = {}

    for ch in root.findall("channel"):
        cid = ch.attrib.get("id")
        if not cid:
            continue

        names = []

        for n in ch.findall("display-name"):
            if n.text:
                name = clean_name(n.text)

                if name and name not in names:
                    names.append(name)

        if not names:
            continue

        # 🔥 排序（短的优先=主名）
        names = sorted(names, key=len)

        result[cid] = names

    # 写入 txt
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for cid, names in result.items():
            line = cid + "=" + "|".join(names)
            f.write(line + "\n")

    print("✅ 自动生成 alias:", len(result))


if __name__ == "__main__":
    main()
