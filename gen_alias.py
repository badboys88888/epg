import json

INPUT = "alias.txt"
OUTPUT = "alias_map.json"

def main():
    data = {}

    with open(INPUT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            k, v = line.split("=", 1)
            aliases = [x.strip() for x in v.split("|") if x.strip()]

            data[k.strip()] = aliases

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"exact": data, "regex": []}, f, ensure_ascii=False, indent=2)

    print("✅ alias生成完成:", len(data))


if __name__ == "__main__":
    main()
