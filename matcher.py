import json
from opencc import OpenCC
import re

cc = OpenCC("t2s")

INDEX_FILE = "index.json"
EPG_FILE = "epg_data.json"


def norm(name):
    name = cc.convert(name)
    name = name.lower()
    name = re.sub(r'[\s\-\_\(\)\[\]\.]+', '', name)
    return name


# ===================== 加载索引 ===================== #

def load_index():

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ===================== 匹配核心 ===================== #

def match_channel(name, index):

    key = norm(name)

    # 1. 精确匹配
    if key in index:
        return index[key]

    # 2. 包含匹配（增强）
    for k, v in index.items():
        if k in key or key in k:
            return v

    return None


# ===================== 测试 ===================== #

if __name__ == "__main__":

    index = load_index()

    tests = [
        "CCTV-1 综合",
        "央视一套",
        "湖南卫视 HD",
        "BBC儿童亚洲"
    ]

    for t in tests:
        print(t, "=>", match_channel(t, index))
