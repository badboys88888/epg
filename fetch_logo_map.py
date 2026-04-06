import requests
from bs4 import BeautifulSoup
import json
import os
import re

# ===================== 多地区 ===================== #
URLS = [
    "https://epg.pw/areas/tw.html?lang=zh-hans",
    "https://epg.pw/areas/hk.html?lang=zh-hans",
    "https://epg.pw/areas/sg.html?lang=zh-hans",
    "https://epg.pw/areas/my.html?lang=zh-hans",
    "https://epg.pw/areas/us.html?lang=zh-hans"
]

OUTPUT = "icon_map.json"


# ===================== 名称清洗 ===================== #
def clean_name(name):
    if not name:
        return ""

    # 去掉编号：76.xxx
    name = re.sub(r"^\d+\.", "", name)

    # 去掉常见垃圾词
    remove_words = [
        "HD", "高清", "標清", "频道", "頻道",
        "1080P", "720P", "4K"
    ]

    for w in remove_words:
        name = name.replace(w, "")

    return name.strip()


# ===================== 统一key ===================== #
def normalize(name):
    return (
        name.upper()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


# ===================== 读取旧数据 ===================== #
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


# ===================== 抓单个页面 ===================== #
def fetch_one(url):
    print(f"\n🌐 抓取: {url}")

    try:
        html = requests.get(url, timeout=10).text
    except Exception as e:
        print("❌ 请求失败:", e)
        return {}

    soup = BeautifulSoup(html, "html.parser")

    result = {}

    for row in soup.find_all("tr"):

        img = row.find("img")
        if not img:
            continue

        logo = img.get("src")
        if not logo:
            continue

        # 补全URL
        if logo.startswith("/"):
            logo = "https://epg.pw" + logo

        # 获取整行文本
        text = row.get_text(" ", strip=True)

        if not text:
            continue

        # 取第一个字段作为频道名
        name = text.split()[0]

        name = clean_name(name)

        if not name:
            continue

        key = normalize(name)

        result[key] = logo

        print("✔", name)

    print(f"📊 获取: {len(result)}")
    return result


# ===================== 主逻辑 ===================== #
def main():

    print("🚀 开始抓取 logo...")

    final_map = load_old()
    before = len(final_map)

    for url in URLS:
        data = fetch_one(url)

        for k, v in data.items():

            # ⭐ 不覆盖已有（保护你原来的）
            if k not in final_map:
                final_map[k] = v

    after = len(final_map)

    # 保存
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(final_map, f, ensure_ascii=False, indent=2)

    print("\n==============================")
    print("✅ 新增:", after - before)
    print("📦 总数:", after)


if __name__ == "__main__":
    main()
