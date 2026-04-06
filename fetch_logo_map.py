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
    "https://epg.pw/areas/my.html?lang=zh-hans"
]

OUTPUT = "icon_map.json"


# ===================== 清洗（仅显示用，不影响key） ===================== #
def clean_name(name):
    if not name:
        return ""

    name = re.sub(r"^\d+\.", "", name)
    name = re.sub(r"(HD|高清|標清|1080P|720P|4K)", "", name, flags=re.I)
    name = name.replace("频道", "").replace("頻道", "")
    name = name.replace("-", "").replace("_", "")

    return name.strip()


# ===================== key统一（关键：稳定） ===================== #
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
                print("📦 旧数据:", len(data))
                return data
        except:
            return {}
    return {}


# ===================== 抓单个页面 ===================== #
def fetch_one(url):
    print(f"\n🌐 抓取: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://epg.pw/"
    }

    try:
        html = requests.get(url, headers=headers, timeout=10).text
    except Exception as e:
        print("❌ 请求失败:", e)
        return {}

    soup = BeautifulSoup(html, "html.parser")

    result = {}

    for row in soup.find_all("tr"):

        tds = row.find_all("td")
        if len(tds) < 5:
            continue

        # ✅ 正确列
        raw_name = tds[0].get_text(strip=True)   # 原始频道名（关键）
        img = tds[3].find("img")                 # logo
        cid = tds[4].get_text(strip=True)        # Hot = cid

        if not raw_name or not img:
            continue

        logo = img.get("src")
        if not logo:
            continue

        # 补全URL
        if logo.startswith("/"):
            logo = "https://epg.pw" + logo

        # 防止 .png.png
        if not logo.endswith(".png") and not logo.endswith(".jpg"):
            logo = logo + ".png"

        # ⭐ key 用原始名称（稳定核心）
        key = normalize(raw_name)

        # ⭐ 显示名单独处理
        display_name = clean_name(raw_name)

        # ⭐ 只在本轮中去重
        if key not in result:
            result[key] = {
                "cid": cid,
                "name": display_name,
                "logo": logo
            }

        print("✔", raw_name, "->", display_name)

    print(f"📊 获取: {len(result)}")
    return result


# ===================== 主逻辑 ===================== #
def main():

    print("🚀 开始抓取 logo...")

    old_map = load_old()
    before = len(old_map)

    new_data = {}

    for url in URLS:
        data = fetch_one(url)

        for k, v in data.items():
            # ⭐ 新数据先收集
            if k not in new_data:
                new_data[k] = v

    # ===================== 合并（关键：旧优先） ===================== #
    final_map = old_map.copy()

    added = 0

    for k, v in new_data.items():
        if k not in final_map:
            final_map[k] = v
            added += 1

    # ===================== 保存 ===================== #
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(final_map, f, ensure_ascii=False, indent=2)

    print("\n==============================")
    print("🆕 新增:", added)
    print("📦 总数:", len(final_map))


if __name__ == "__main__":
    main()
