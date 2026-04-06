import json

INPUT = "alias.txt"
OUTPUT = "alias_map.json"


def load_txt():
    result = {}

    with open(INPUT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, values = line.split("=", 1)

            aliases = [v.strip() for v in values.split("|") if v.strip()]

            result[key.strip()] = aliases

    return result


def main():
    data = load_txt()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ alias_map 生成完成:", len(data))


if __name__ == "__main__":
    main()
