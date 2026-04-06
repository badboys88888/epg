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

    # 去编号：76.xxx
    name = re.sub(r"^\d+\.", "", name)

    # 去清晰度/杂质
    name = re.sub(r"(HD|高清|標清|1080P|720P|4K)", "", name, flags=re.I)

    # 去“频道”
    name = name.replace("频道", "").replace("頻道", "")

    # 去多余符号
    name = name.replace("-", "").replace("_", "")

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

    headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://epg.pw/",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

    try:
        html = requests.get(url, headers=headers, timeout=10).text
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

        # ⭐ 强制加后缀（关键）
        logo = logo + ".png"

        # ===== 精准拿频道名 ===== #
        tds = row.find_all("td")

        if len(tds) >= 2:
            name = tds[1].get_text(strip=True)
        else:
            # fallback
            text = row.get_text(" ", strip=True)
            name = text.split()[0]

        name = clean_name(name)

        if not name:
            continue

        key = normalize(name)

        result[key] = logo

        print("✔", name, "->", logo)

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
