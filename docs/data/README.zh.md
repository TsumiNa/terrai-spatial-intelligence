# FL 数据集目录

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

本目录只记录已经接入 TerrAI Foundation Data Layer（FL）的数据集。每个数据集独立说明来源、项目用途、license、商业使用注意事项、当前本地产物和更新方式。

| 数据集 | 状态 | 数据卡 |
|---|---|---|
| GSI DEM5A | 已接入 | [地形高程](gsi-dem5a/README.zh.md) |
| GSI 地图与视觉瓦片 | 已接入 | [标准/影像/起伏/坡度](gsi-map-tiles/README.zh.md) |
| GSI 指定避难数据 | 已接入，全国基线 | [指定避难所与分灾种紧急避难场所](gsi-designated-evacuation/README.zh.md) |
| Google Satellite Embedding V1 | 已接入 | [年度遥感表征](google-satellite-embedding/README.zh.md) |
| OpenStreetMap | 已接入 | [建筑、道路与场景对象](openstreetmap/README.zh.md) |
| PLATEAU UC24-13 札幌 | 已接入，按需样例 | [观测地下结构](plateau-uc24-13-sapporo/README.zh.md) |
| PLATEAU UC24-16 日本桥 | 已接入，按需样例 | [观测地下管线](plateau-uc24-16-nihonbashi/README.zh.md) |
| KuniJiban 钻孔 | 已接入，按需区域数据 | [钻孔、地层与 SPT](kunijiban-boreholes/README.zh.md) |
| 横滨市地域防灾拠点 | 已接入，地方校验/补充 | [官方公共设施](yokohama-disaster-bases/README.zh.md) |
| NASA POWER | 已接入 | [太阳辐照气候背景](nasa-power/README.zh.md) |
| TEPCO 公开系統信息 | 已接入但再分发受限 | [区域并网容量筛查](tepco-grid/README.zh.md) |
| MLIT 五万分之一土地分类 | 已接入，按需 | [地质与土壤](mlit-land-classification-50k/README.zh.md) |
| MLIT 全期间水害 GIS | 已接入，按需 | [历史洪灾](mlit-flood-history/README.zh.md) |
| MLIT 土地履历调查 | 已接入，按需 | [地貌与历史利用](mlit-land-history/README.zh.md) |
| MLIT A33 土砂灾害警戒区 | 已接入，按需 | [土砂约束](mlit-a33-landslide/README.zh.md) |
| MLIT A53 多阶段淹水 | 已接入，按需 | [分频率淹水](mlit-a53-multistage-flood/README.zh.md) |
| MLIT L01 地价公示 | 已接入，按需 | [2026标准地](mlit-l01-published-land-price/README.zh.md) |
| MLIT A56 填土管制区 | 已接入，按需 | [监管筛查](mlit-a56-embankment-regulation/README.zh.md) |
| MLIT N02 铁路 | 已接入，按需 | [线路与车站](mlit-n02-railway/README.zh.md) |
| MLIT L03-b 土地利用细分 | 已接入，按需 | [2021年100米网格](mlit-l03b-land-use/README.zh.md) |
| MLIT L02 都道府县地价调查 | 已接入，按需 | [2025基准地](mlit-l02-prefectural-land-price/README.zh.md) |

已确认但尚未接入、以及评估后排除的数据，见 [`docs/summary/open-data-landscape/`](../summary/open-data-landscape/README.zh.md)。机器可读状态见 `data/external/source_registry.json`。
