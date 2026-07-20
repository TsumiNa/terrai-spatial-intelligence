# FL 数据集目录

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

本目录只记录已经接入 TerrAI Foundation Data Layer（FL）的数据集。每个数据集独立说明来源、项目用途、license、商业使用注意事项、当前本地产物和更新方式。

| 数据集 | 状态 | 数据卡 |
|---|---|---|
| GSI DEM5A | 已接入 | [地形高程](../gsi-dem5a/README.zh.md) |
| GSI 地图与视觉瓦片 | 已接入 | [标准/影像/起伏/坡度](../gsi-map-tiles/README.zh.md) |
| Google Satellite Embedding V1 | 已接入 | [年度遥感表征](../google-satellite-embedding/README.zh.md) |
| OpenStreetMap | 已接入 | [建筑、道路与场景对象](../openstreetmap/README.zh.md) |
| 横滨市地域防灾拠点 | 已接入 | [官方公共设施](../yokohama-disaster-bases/README.zh.md) |
| NASA POWER | 已接入 | [太阳辐照气候背景](../nasa-power/README.zh.md) |
| TEPCO 公开系統信息 | 已接入但再分发受限 | [区域并网容量筛查](../tepco-grid/README.zh.md) |

已确认但尚未接入、以及评估后排除的数据，见 [`docs/summary/open-data-landscape/`](../../summary/open-data-landscape/README.zh.md)。机器可读状态见 `data/external/source_registry.json`。
