# 横滨市地域防灾拠点

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入
- 快照：2026-04-01
- 数据类型：官方设施名称、地址、位置

## 数据内容

- **格式** — 单个 CSV。该市以 CP932（Shift-JIS）发布；证据管线在首次读取时就地把文件转码为 UTF-8，因此本仓库缓存的副本是 UTF-8。重新下载得到的副本仍是 CP932，按 UTF-8 朴素读取会失败。
- **列** — `Type`、`Definition`、`Name`、`Address`、`Lat`、`Lon`、`Kana`、`Ward`、`WardCode`。`Lat` / `Lon` 为 WGS84 十进制度。
- **粒度** — 每个官方防灾设施一行（地域防灾据点、避难场所等类别由 `Type` 区分）。
- **数据量** — `2026-04-01` 快照（`hinanjo_20260401.csv`）含 628 行设施。
- **时点** — 带日期的快照；该市按自身节奏重新发布，文件名保留快照日期。
- **进入演示的部分** — 只有落在横滨演示小矩形内的设施能通过空间过滤，因此 `data/yokohama/official_facility_resilience.geojson` 目前在 628 行中只保留 **2** 个要素。
- **已知缺失与限制** — 设施身份、类别、地址与坐标属于官方信息；而本项目附加的 `matched_roof_area_m2`、`pv_kwp_proxy`、`nearest_road_m`、`served_high_risk_buildings`、`resilience_score` 全部是基于其他图层计算的 PoC 代理值，并非市政府对该设施的判断。该文件描述的是指定状态，未涉及当前结构状况、实际可用容量或运行准备度。

## 来源

横滨市地域防灾拠点与帰宅困難者一時滞在施設 CSV：https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv

## 在本项目中的使用

筛出保土谷区研究窗口内两处官方据点，作为公共设施韧性改造的真实行动对象。位置、名称、地址为官方观测；最近建筑屋顶、光伏容量、道路距离和250 m高风险建筑关联均为 TerrAI 代理，产物为 `data/yokohama/official_facility_resilience.geojson`。

## License

横滨市开放数据默认 CC BY 4.0，允许商用；须署名并标明加工。条款：https://data.city.yokohama.lg.jp/terms.html

## 商业使用注意

第三方权利由使用者另行确认。不得把 TerrAI 的屋顶、容量、服务圈或韧性分称为横滨市官方字段、正式改造建议或灾害保证；设施状态和快照日期需定期更新。
