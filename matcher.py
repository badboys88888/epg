import json
from rules import make_epgid, norm

with open("epg_index.json", "r", encoding="utf-8") as f:
    INDEX = json.load(f)


def match(channel_name: str):
    n = norm(channel_name)

    # 1️⃣ 直接 index
    if channel_name in INDEX:
        return INDEX[channel_name]

    if n in INDEX:
        return INDEX[n]

    # 2️⃣ 规则匹配
    return make_epgid(channel_name)


if __name__ == "__main__":

    print("TEST MODE")

    while True:
        name = input("channel> ").strip()
        if name == "exit":
            break

        print(match(name))
