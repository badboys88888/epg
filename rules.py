# rules.py
import re
from opencc import OpenCC

cc = OpenCC("t2s")

def norm(name: str) -> str:
    name = cc.convert(name)
    name = name.lower()
    name = re.sub(r'[\s\-\_\(\)\[\]\.]+', '', name)
    return name


# ===================== CCTV规则 ===================== #
CCTV_REGEX = re.compile(r'^cctv[-\s]*(\d{1,2})(?!.*(美洲|欧洲))', re.I)

ALIASES = {
    "中央一套": "cctv1",
    "央视一套": "cctv1",
    "中央电视台1": "cctv1",
    "凤凰卫视": "phoenix_tv",
    "湖南卫视": "hunan_tv",
}


def make_epgid(name: str) -> str:
    n = norm(name)

    # 1️⃣ CCTV regex
    m = CCTV_REGEX.match(n.upper())
    if m:
        num = re.findall(r'\d{1,2}', m.group(1))
        if num:
            return f"cctv{num[0]}"

    # 2️⃣ alias
    if n in ALIASES:
        return ALIASES[n]

    # 3️⃣ fallback
    return n
