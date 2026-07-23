# OSM 关东建筑轮廓

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入、按需查询
- 图层：供高缩放细节层使用的建筑数据对象

## 数据内容

关东本土采集窗口内的建筑轮廓,抽取自固定快照 `kanto-260101.osm.pbf`(抽取时间戳 2026-01-01T21:21:30Z):共 5,371,292 个多边形,每个都带稳定的 `osm_id`/`osm_type`、`building` 类别、有标注时的 `name`/`building:levels`,以及完整获取溯源。源数据中 14 个退化多边形被跳过并计入清单。覆盖度依赖社区测绘:建成区密、其余稀疏——没有建筑不代表实地不存在。

- **格式** — 单个 GeoJSON FeatureCollection(`buildings.geojson`,约 3.1 GB,MultiPolygon 几何)加 `metadata.json` 清单。
- **坐标系** — EPSG:4326(WGS 84 经纬度)。
- **范围** — 关东本土采集窗口 (138.65, 34.85, 140.95, 36.30)。

## 来源

[OpenStreetMap](https://www.openstreetmap.org/copyright) 数据的 [Geofabrik extract](https://download.geofabrik.de/asia/japan/kanto.html)。使用日期固定快照而非 `-latest`,重跑可复现同一清单。

## 在本项目中的使用

高缩放细节层:超过交接缩放级后,底图的制图建筑让位于这些轮廓,每栋可点击进入原始审计记录。API key 为 `osmBuildings`,由 `osm_kanto` 任务刷新。仅作基础证据展示,不进入评分。

## License

Open Database License (ODbL) 1.0。图层渲染处必须标注「© OpenStreetMap contributors」。

## 商业使用注意

公开的派生数据库适用 ODbL 的 share-alike 条款。完整性与现势性由社区决定、无保证;`building:levels` 等标签稀疏。不得将本清单当作权威建筑登记出示。
