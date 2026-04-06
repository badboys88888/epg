import json
import re

INPUT = "alias.txt"
OUTPUT = "alias_map.json"


def load_txt():
    exact = {}
    regex = []

    with open(INPUT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, values = line.split("=", 1)
            aliases = [v.strip() for v in values.split("|") if v.strip()]

            if key.startswith("~"):
                pattern = key[1:]
                regex.append((pattern, aliases))
            else:
                exact[key] = aliases

    return exact, regex


def main():
    exact, regex = load_txt()

    # 直接输出 JSON（结构化）
    data = {
        "exact": exact,
        "regex": [
            {"pattern": p, "aliases": a}
            for p, a in regex
        ]
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ alias生成完成")


if __name__ == "__main__":
    main()
