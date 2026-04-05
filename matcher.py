#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from rapidfuzz import process, fuzz
from opencc import OpenCC

INDEX_FILE = "index.json"
ENTITY_FILE = "epg_entities.json"
EPG_ENTITY_INDEX = "epg_entity_index.json"  # 可选扩展缓存

cc = OpenCC("t2s")


# ===================== 标准化 ===================== #
def norm(name: str) -> str:
    if not name:
        return ""
    name = cc.convert(name)
    name = name.lower()
    name = re.sub(r'[\s\-\_\(\)\[\]\.]+', '', name)
    return name


# ===================== 加载 ===================== #
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ===================== 构建反向索引 ===================== #
def build_reverse_index(index):
    """
    index.json: name -> epgid
    转成 epgid -> [names]
    """
    rev = {}

    for name, epgid in index.items():
        rev.setdefault(epgid, []).append(name)

    return rev


# ===================== fuzzy候选池 ===================== #
def build_candidates(index):
    return list(index.keys())


# ===================== 三层匹配 ===================== #
def match_channel(name, index, candidates):
    raw = name
    n = norm(name)

    # 1️⃣ 精确匹配
    if n in index:
        return index[n], "exact_norm"

    if name in index:
        return index[name], "exact_raw"

    # 2️⃣ alias/弱匹配（包含匹配）
    for k, v in index.items():
        if n in k or k in n:
            return v, "substring"

    # 3️⃣ rapidfuzz 模糊匹配（核心）
    best = process.extractOne(
        n,
        candidates,
        scorer=fuzz.WRatio
    )

    if best:
        match, score, _ = best
        if score >= 80:
            return index[match], f"fuzzy_{score}"

    return None, "unmatched"


# ===================== 测试入口 ===================== #
def main():

    index = load_json(INDEX_FILE)
    entities = load_json(ENTITY_FILE)

    candidates = build_candidates(index)
    rev = build_reverse_index(index)

    print("✅ index size:", len(index))
    print("✅ entities:", len(entities))

    print("\n👉 输入频道名测试（exit退出）\n")

    while True:
        name = input("channel> ").strip()
        if name.lower() == "exit":
            break

        epgid, mode = match_channel(name, index, candidates)

        if epgid:
            print(f"✔ 匹配成功：{epgid} ({mode})")
        else:
            print("❌ 未匹配")


if __name__ == "__main__":
    main()
