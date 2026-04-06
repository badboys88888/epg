import requests
from bs4 import BeautifulSoup
import json

URL = "https://epg.pw/areas/tw.html?lang=zh-hans"
OUTPUT = "icon_map.json"


def normalize(name):
    return (
        name.upper()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def main():
    print("🚀 抓取页面...")

    html = requests.get(URL, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")

    icon_map = {}

    # 👉 找所有频道行
    rows = soup.select("table tr")

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        # 👉 频道名
        name = tds[1].get_text(strip=True)

        # 👉 logo
        img = row.find("img")
        if not img:
            continue

        logo = img.get("src")
        if not logo:
            continue

        # 👉 规范key
        key = normalize(name)

        icon_map[key] = logo

        print("✔", name, "->", logo)

    # 保存
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(icon_map, f, ensure_ascii=False, indent=2)

    print("✅ DONE:", len(icon_map))


if __name__ == "__main__":
    main()
