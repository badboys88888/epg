import requests
from bs4 import BeautifulSoup
import json
import os

URLS = [
    "https://epg.pw/areas/tw.html?lang=zh-hans",
    "https://epg.pw/areas/hk.html?lang=zh-hans",
    "https://epg.pw/areas/cn.html?lang=zh-hans"
]

OUTPUT = "icon_map.json"


def normalize(name):
    return (
        name.upper()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def load_old():
    if os.path.exists(OUTPUT):
        try:
            with open(OUTPUT, "r", encoding="utf-8") as f:
                data = json.load(f)
                print("📦 旧icon_map:", len(data))
                return data
        except:
            return {}
    return {}


def fetch_one(url):
    print(f"🌐 抓取: {url}")
    html = requests.get(url, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")

    result = {}

    rows = soup.select("table tr")

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        name = tds[1].get_text(strip=True)

        img = row.find("img")
        if not img:
            continue

        logo = img.get("src")
        if not logo:
            continue

        if logo.startswith("/"):
            logo = "https://epg.pw" + logo

        key = normalize(name)

        result[key] = logo

    print(f"✔ 获取: {len(result)}")
    return result


def main():
    # ✅ 读取旧数据（关键）
    final_map = load_old()

    before = len(final_map)

    for url in URLS:
        data = fetch_one(url)

        for k, v in data.items():
            # ⭐ 不覆盖已有（保护你原来的）
            if k not in final_map:
                final_map[k] = v

    after = len(final_map)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(final_map, f, ensure_ascii=False, indent=2)

    print("✅ 新增:", after - before)
    print("📊 总数:", after)


if __name__ == "__main__":
    main()
