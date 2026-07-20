# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入并转为本地 GeoJSON
- 数据类型：建筑、道路、水体、土地利用、输电线

## 数据内容

- **格式** — 以离线 extract 方式下载的社区矢量数据，转换为 GeoJSON `FeatureCollection`（EPSG:4326，RFC 7946）。运行时不调用 OSM API 或瓦片服务器。
- **抽取主题** — 建筑轮廓、道路、水体、土地利用、输电线路。
- **粒度** — 每个 OSM 对象对应一个要素；建筑要素保留 `osm_id`，可回溯到上游记录。
- **数据量** — `data/yokohama/building_risk.geojson` 含 2,128 个建筑面，`data/yokohama/road_priority.geojson` 含 272 条道路区段；茂原的水体、土地利用与电力上下文位于 `data/mobara/context.geojson`。
- **项目读取的字段** — 建筑：`building`、`levels`、`footprint_m2`（m²）、`name`、`osm_id`；道路优先级模型：道路等级与名称；茂原候选单元：`landuse`、`distance_water_m`、`distance_building_m`、`distance_grid_m`（均为 m）。
- **时点** — 某一时刻的 extract，而非实时镜像；OSM 本身持续变化。
- **已知缺失与限制** — 数据由社区众包，完整性、准确性与时效性均无保证，某对象缺失不能作为其不存在的证据。`levels` 缺失尤其普遍，这正是屋顶容量采用代理算法而非直接读取的原因。

## 来源

OpenStreetMap 社区数据库：https://www.openstreetmap.org/copyright 。当前 Demo 使用已下载和标准化的本地数据，不依赖公共 API 或瓦片服务器。

## 在本项目中的使用

建筑轮廓用于坡地暴露和屋顶容量代理；道路用于连续性、可达性和光伏物流；水体/土地利用用于退距和场景；输电线用于茂原候选地距离代理。主要产物位于 `data/yokohama/`、`data/mobara/` 和 `data/joint/`。

## License

Open Database License（ODbL），使用时必须署名 OpenStreetMap contributors；公开衍生数据库可能触发共享相同方式要求。

## 商业使用注意

ODbL 对数据库与生成作品的义务不同，商业发布前应判断交付物是否构成衍生数据库。众包数据的完整性、精度和更新不保证；不能把缺失对象解释为现实中不存在，也不能滥用 OSM 公共生产 API/瓦片服务。
