# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入并转为本地 GeoJSON
- 数据类型：建筑、道路、水体、土地利用、输电线、札幌地铁/access 上下文

## 数据内容

- **格式** — 以离线 extract 方式下载的社区矢量数据，转换为 GeoJSON `FeatureCollection`（EPSG:4326，RFC 7946）。运行时不调用 OSM API 或瓦片服务器。
- **抽取主题** — 建筑轮廓、道路、水体、土地利用、输电线路，以及限定札幌范围内的地铁线路/车站/出入口和地下步道候选。
- **粒度** — 每个 OSM 对象对应一个要素；建筑要素保留 `osm_id`，可回溯到上游记录。
- **数据量** — `data/yokohama/building_risk.geojson` 含 2,128 个建筑面，`data/yokohama/road_priority.geojson` 含 272 条道路区段；茂原的水体、土地利用与电力上下文位于 `data/mobara/context.geojson`。札幌快照共 195 个 feature：97 个地铁出入口、6 个地铁站、8 条地铁轨道 way 和 84 个地下步道候选；其中 103 个 point、92 条 line。查询结果中 6 条仅带数值地面/楼上 level、且没有 tunnel 或负 level/layer 证据的 way 不进入输出或计数。
- **项目读取的字段** — 建筑：`building`、`levels`、`footprint_m2`（m²）、`name`、`osm_id`；道路模型读取道路等级与名称；茂原单元读取 `landuse`、`distance_water_m`、`distance_building_m`、`distance_grid_m`（均为 m）。札幌保留 `osm_type`、`osm_id`、`osm_version`、`osm_changeset`、`osm_timestamp`、原始 `tags`、准确的 `level`/`layer`、evidence flag，以及为 null 的 `depth_m`/`elevation_m`。
- **时点** — 都是特定时刻的 extract，而非实时镜像。札幌 OSM base timestamp 为 2026-07-21T10:51:01Z，获取时间为 2026-07-21T10:53:05Z；OSM 本身持续变化。
- **已知缺失与限制** — 众包数据的完整性、精度、法律通行权与时效性均无保证，缺失对象不证明现实中不存在。札幌 way 按东经 141.349592632–141.356913521°、北纬 43.054916388–43.070980841° 的 bbox 选取，保留相交源对象的完整几何而不裁剪。缺失或含糊的 level 不转换为 depth；没有 access 限制 tag 也不证明可依法公共通行或当前开放。

## 来源

OpenStreetMap 社区数据库：https://www.openstreetmap.org/copyright 。当前 Demo 使用已下载和标准化的本地数据，不依赖公共 API 或瓦片服务器。札幌的精确查询提交在 `data/osm/sapporo_underground_access/query.overpassql`；`uv run python -m terrai_spatial fetch underground_access_osm` 通过文档所列公共 Overpass endpoint 显式刷新 GeoJSON 与获取 metadata。

## 在本项目中的使用

建筑轮廓用于坡地暴露和屋顶容量代理；道路用于连续性、可达性和光伏物流；水体/土地利用用于退距和场景；输电线用于茂原候选地距离代理。札幌 OSM feature 为 scene `sapporo-station-underground` 提供独立社区 access/topology 上下文，可通过 dataset key `osmSapporoUndergroundAccess` 按需查询；它与 PLATEAU 几何保持分离，不作校验或覆盖。主要产物位于 `data/yokohama/`、`data/mobara/`、`data/joint/` 和 `data/osm/sapporo_underground_access/`。

## License

Open Database License（ODbL），使用时必须署名 OpenStreetMap contributors；公开衍生数据库可能触发共享相同方式要求。

## 商业使用注意

ODbL 对数据库与生成作品的义务不同，商业发布前应判断交付物是否构成衍生数据库。众包数据的完整性、精度、accessibility 和更新不保证；不能把缺失对象解释为现实中不存在，也不能把候选步道描述成依法公共通行或当前开放。不要滥用 OSM 公共生产 API/瓦片服务。
