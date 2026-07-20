# TEPCO 公开系統信息

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入，原始数据再分发受限
- 范围：千叶县送电线与变电设备“系統の予想潮流等”

## 数据内容

- **格式** — 包含两个 CSV 文件的 ZIP 压缩包（UTF-8 带 BOM）。每个 CSV 在表头行之前有 6 行元数据前言，因此把第 1 行当作表头的朴素读取方式会解析错误。
- **文件** — `csv_yosochoryu_chiba_soudensen.csv`（输电线路）与 `csv_yosochoryu_chiba_hendensyo.csv`（变电站与变压器）。
- **覆盖范围** — 东京电力 Power Grid 供电区域中的千叶地区。设备仅以 ID 和名称标识，CSV 中**不含坐标、不含几何**。
- **数据量** — 当前快照含输电线路 175 行、变压器 201 行。
- **项目读取的字段** — `equipment_id`、`name`、`voltage_kv`（kV）、`circuits`、设备容量、`operating_capacity_before_control_mw`（MW）、`existing_olr_mw`（MW）、`operating_capacity_mw`（MW）、`constraint`，以及 `flow_from` / `flow_to` 两端。
- **时点与完整性** — 派生成果记录了来自 HTTP 响应的 `source_file_last_modified_at`，以及压缩包和每个解压 CSV 的 SHA-256，使筛查结果可以绑定到某次确切下载。
- **已知缺失与限制** — 由于没有几何信息，数值无法分配到地块或候选单元，管线仅按名称文本匹配。公开容量是筛查指标，绝不构成并网可用性的保证。因发布方声明禁止再分发，原始 ZIP、CSV 与获取元数据均已加入 Git 忽略，仓库只提交派生的筛查结果。

## 来源

东京电力 Power Grid 官方页面：https://www.tepco.co.jp/pg/consignment/system/index-j.html 。程序记录实际 ZIP 的 HTTP `Last-Modified`、ETag、下载时间、字节数和 SHA-256，不把网页公告日期写死为快照。

## 在本项目中的使用

原始 ZIP/CSV 解析为 `data/mobara/tepco_grid_screen.json`，用于区域级空容量、上位约束和并网预咨询排序。当前茂原信号为变电所自身5 MW空容量代理、考虑上位系统后0 MW，并存在平常时出力控制可能。它不是宗地级容量或并网承诺。

## License

文件可免费公开下载，但**不是开放许可数据**；官方注意资料标注“転載禁止”：https://www.tepco.co.jp/pg/consignment/system/pdf/yosouchoryu_points_to_note.pdf

## 商业使用注意

原始 ZIP、CSV 与 `download_metadata.local.json` 被 Git 忽略，不得未经东京电力确认许可提交或再分发。CSV 几何不足以把容量分配到候选地，公开值是暂定简化数据，商业产品必须保留限制并进行正式接续検討。

## 获取与本地缓存

本目录有意不将东京电力 Power Grid 的原始 ZIP、CSV 和本地下载元数据提交到 Git。虽然文件可以免费下载，但官方注意事项标注禁止转载。

程序可以直接从东京电力官方 URL 下载，无需手工浏览器操作、购买数据库或 API Key。

1. 阅读[官方系統信息页面](https://www.tepco.co.jp/pg/consignment/system/index-j.html)的最新条款和注意事项。
2. 执行 `uv run python -m terrai_spatial fetch tepco` 或 `uv run python scripts/update_tepco_grid.py --force`。
3. 下载器验证 ZIP，只提取 `csv_yosochoryu_chiba_soudensen.csv` 和 `csv_yosochoryu_chiba_hendensyo.csv`，并把下载时间、HTTP 元数据和 SHA-256 写入 `download_metadata.local.json`。
4. 解析器将 Demo 的标准化筛查摘要写入 `data/mobara/tepco_grid_screen.json`。

标准 Git clone 后首次在线执行 `terrai serve` 时，启动检查会发现这个被 Git 忽略的缓存缺失，并自动执行相同的下载和解析流程。缓存完整后不会重复下载。`--offline` 可以直接展示仓库中已有的摘要，或从现有本地 ZIP/CSV 缓存重建，同时拒绝所有网络请求。

执行 `uv run python -m terrai_spatial fetch tepco` 主动更新；`--offline` 可使用提交的标准化摘要，或从已有本地缓存重建。
