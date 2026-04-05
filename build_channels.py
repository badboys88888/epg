import json

with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

with open("icon_map.json", "r", encoding="utf-8") as f:
    logo_map = json.load(f)

def get_logo(name):
    if name in logo_map:
        return logo_map[name]

    for k, v in logo_map.items():
        if k.lower() in name.lower():
            return v

    return ""

for cid, info in channels.items():
    name = info["names"][0]
    info["logo"] = get_logo(name)

with open("channels.json", "w", encoding="utf-8") as f:
    json.dump(channels, f, ensure_ascii=False, indent=2)

print("logo merged done")
