import requests
from bs4 import BeautifulSoup
import json
import os
import re

# ===================== 页面 ===================== #
URLS = [
    "https://epg.pw/areas/tw.html?lang=zh-hans",
    "https://epg.pw/areas/hk.html?lang=zh-hans",
    "https://epg.pw/areas/sg.html?lang=zh-hans",
    "https://epg.pw/areas/my.html?lang=zh-hans"
]

OUTPUT = "icon_map.json"


# ===================== key统一 ===================== #
def normalize(name):
    return (
        name.upper()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


# ===================== 旧数据 ===================== #
def load_old():
    if os.path.exists(OUTPUT):
        try:
            with open(OUTPUT, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


# ===================== 抓取单页（核心） ===================== #
def fetch_one(url):

    print(f"\n🌐 抓取: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://epg.pw/"
    }

    try:
        html = requests.get(url, headers=headers, timeout=15).text
    except Exception as e:
        print("❌ 请求失败:", e)
        return {}

    soup = BeautifulSoup(html, "html.parser")

    result = {}

    for row in soup.find_all("tr"):

        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        # ===================== 频道名 ===================== #
        name = cols[0].get_text(strip=True)
        if not name:
            continue

        # ===================== logo（多兜底） ===================== #
        logo = ""

        img = cols[3].find("img") if len(cols) > 3 else None

        if img:
            logo = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-original")
                or ""
            )

        # 兜底：background-image
        if not logo:
            style = row.get("style", "")
            m = re.search(r'url\(["\']?(.*?)["\']?\)', style)
            if m:
                logo = m.group(1)

        # 补全 URL
        if logo and logo.startswith("/"):
            logo = "https://epg.pw" + logo

        # 防重复后缀
        if logo and not logo.endswith(".png") and not logo.endswith(".jpg"):
            logo += ".png"

        # ===================== key ===================== #
        key = normalize(name)

        # ===================== 存储 ===================== #
        if logo:
            result[key] = logo

        print("✔", name)

    print(f"📊 本页数量: {len(result)}")
    return result


# ===================== 主程序 ===================== #
def main():

    print("🚀 开始抓取 icon_map...")

    old = load_old()
    new = {}

    for url in URLS:
        data = fetch_one(url)
        for k, v in data.items():
            new[k] = v

    # ===================== 合并（旧优先） ===================== #
    final = old.copy()

    added = 0

    for k, v in new.items():
        if k not in final:
            final[k] = v
            added += 1

    # ===================== 保存 ===================== #
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print("\n==============================")
    print("🆕 新增:", added)
    print("📦 总量:", len(final))


if __name__ == "__main__":
    main()
