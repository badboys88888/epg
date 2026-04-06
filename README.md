📺 IPTV EPG Auto Build

一个自动化构建 IPTV 节目表（EPG）与频道数据的工具链，支持多源合并、频道别名管理、台标匹配与自动更新。

🚀 功能特性
	•	📡 多 EPG 源合并（XML / XML.GZ）
	•	🧠 自动提取频道名称（alias 自动生成）
	•	✍️ 手动可控 alias（避免数据污染）
	•	🖼️ 自动匹配频道 Logo
	•	📦 生成标准 channels.json
	•	⏱️ GitHub Actions 定时自动更新
	•	🔄 轻量维护（无需数据库）

📂 项目结构

.
├── epg_sources.txt        # EPG源列表
├── merge_epg.py          # 合并多个EPG
├── epg.xml.gz            # 输出EPG

├── auto_alias.py         # 自动提取频道别名（生成alias_auto.txt）
├── alias_auto.txt        # 自动生成的别名（参考用）
├── alias.txt             # 手动维护别名（核心）
├── gen_alias.py          # 生成 alias_map.json
├── alias_map.json        # 别名映射JSON

├── fetch_logo_map.py     # 抓取台标
├── icon_map.json         # 台标映射

├── extract_channels.py   # 生成 channels.json
├── channels.json         # 最终频道数据

├── requirements.txt      # 依赖
⚙️ 使用流程

1️⃣ 合并 EPG
python merge_epg.py
生成：
epg.xml.gz
2️⃣ 自动提取频道别名
python auto_alias.py
生成:
alias_auto.txt
3️⃣ 手动维护 alias（关键）
alias.txt
示例:
370143=華視|华视|CTS|华视HD
370139=民視|民视
4️⃣ 生成 alias_map.json

python gen_alias.py

5️⃣ 抓取台标

