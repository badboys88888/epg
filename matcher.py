#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import sys
from rapidfuzz import process, fuzz
from opencc import OpenCC

INDEX_FILE = "index.json"
ENTITY_FILE = "epg_entities.json"

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


# ===================== 候选池 ===================== #
def build_candidates(index):
    return list(index.keys())


# ===================== 匹配 ===================== #
def match_channel(name, index, candidates):

    n = norm(name)

    # 1️⃣ 精确
    if n in index:
        return index[n], "exact_norm", 100

    if name in index:
        return index[name], "exact_raw", 100

    # 2️⃣ 子串
    for k, v in index.items():
        if n in k or k in n:
            return v, "substring", 85

    # 3️⃣ fuzzy
    best = process.extractOne(n, candidates, scorer=fuzz.WRatio)

    if best:
        match, score, _ = best
        if score >= 75:
            return index[match], f"fuzzy_{score}", score

    return None, "unmatched", 0


# ===================== 主程序 ===================== #
def main():

    index = load_json(INDEX_FILE)
    entities = load_json(ENTITY_FILE)

    candidates = build_candidates(index)

    print("✅ index size:", len(index))
    print("✅ entities:", len(entities))

    # ===================== CI模式 ===================== #
    if not sys.stdin.isatty():

        test_cases = [
            "CCTV1",
            "CCTV-1 HD",
            "央视一套",
            "中央一套",
            "BBC ONE",
            "HBO HD",
            "cttv1",
            "凤凰卫视",
            "未知频道xxx"
        ]

        run_tests(test_cases, index, candidates)
        return

    # ===================== 手动模式 ===================== #
    print("\n👉 输入频道名（exit退出）\n")

    while True:
        name = input("channel> ").strip()
        if name.lower() == "exit":
            break

        epgid, mode, score = match_channel(name, index, candidates)
        print(f"{name} → {epgid} ({mode}, {score})")


# ===================== 测试统计 ===================== #
def run_tests(test_cases, index, candidates):

    total = len(test_cases)
    ok = 0
    fuzzy = 0
    exact = 0
    failed = []

    print("\n================= MATCH TEST =================\n")

    for name in test_cases:
        epgid, mode, score = match_channel(name, index, candidates)

        if epgid:
            ok += 1
            if "fuzzy" in mode:
                fuzzy += 1
            if "exact" in mode:
                exact += 1

            print(f"✔ {name} → {epgid} ({mode}, {score})")
        else:
            failed.append(name)
            print(f"❌ {name} → 未匹配")

    print("\n================= STATS =================")

    hit_rate = round(ok / total * 100, 2)

    print(f"📊 总数: {total}")
    print(f"📊 命中: {ok}")
    print(f"📊 命中率: {hit_rate}%")
    print(f"📊 精确命中: {exact}")
    print(f"📊 fuzzy命中: {fuzzy}")

    if failed:
        print("\n❌ 未匹配列表:")
        for f in failed:
            print(" -", f)


if __name__ == "__main__":
    main()
