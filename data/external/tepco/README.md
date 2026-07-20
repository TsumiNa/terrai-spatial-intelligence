# TEPCO 仅保留在本地的原始文件

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

本目录有意不将东京电力 Power Grid 的原始 ZIP、CSV 和本地下载元数据提交到 Git。虽然文件可以免费下载，但官方注意事项标注禁止转载。

程序可以直接从东京电力官方 URL 下载，无需手工浏览器操作、购买数据库或 API Key。

1. 阅读[官方系統信息页面](https://www.tepco.co.jp/pg/consignment/system/index-j.html)的最新条款和注意事项。
2. 执行 `uv run python -m terrai_spatial fetch tepco` 或 `uv run python scripts/update_tepco_grid.py --force`。
3. 下载器验证 ZIP，只提取 `csv_yosochoryu_chiba_soudensen.csv` 和 `csv_yosochoryu_chiba_hendensyo.csv`，并把下载时间、HTTP 元数据和 SHA-256 写入 `download_metadata.local.json`。
4. 解析器将 Demo 的标准化筛查摘要写入 `data/mobara/tepco_grid_screen.json`。

标准 Git clone 后首次在线执行 `terrai serve` 时，启动检查会发现这个被 Git 忽略的缓存缺失，并自动执行相同的下载和解析流程。缓存完整后不会重复下载。`--offline` 可以直接展示仓库中已有的摘要，或从现有本地 ZIP/CSV 缓存重建，同时拒绝所有网络请求。

未经东京电力 Power Grid 确认许可，不得提交或再分发下载的原始文件。
