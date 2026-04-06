import gzip
import xml.etree.ElementTree as ET

INPUT = "epg.xml.gz"
OUTPUT = "alias_auto.txt"


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
                name = n.text.strip()
                if name:
                    names.append(name)

        if not names:
            continue

        # 去重
        names = list(dict.fromkeys(names))

        result[cid] = names

    # 写入 txt
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for cid, names in result.items():
            line = cid + "=" + "|".join(names)
            f.write(line + "\n")

    print("✅ 自动生成 alias:", len(result))


if __name__ == "__main__":
    main()
