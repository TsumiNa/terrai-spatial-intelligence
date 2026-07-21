# PLATEAU UC24-13 札幌地下结构

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：作为外部观测样例接入，按需恢复本地缓存
- 发布方：Project PLATEAU / 日本国土交通省
- 数据集/API key：`plateau_uc24_13_sapporo` / `uc24_13_sapporo`

## 数据内容

- **格式与结构：** 2 个官方 ZIP，内含 3D Tiles 1.0、B3DM 内容和源 batch table。可复现缓存含 2 个压缩包、2 个 `tileset.json`、6,423 个 B3DM；完整性 manifest 共跟踪 6,427 个文件。压缩包与展开资产不提交到 Git。
- **范围与 CRS：** 札幌场景约覆盖东经 141.349593–141.356914°、北纬 43.054916–43.070981°。`boundingVolume.region` 以弧度表达 WGS 84 经纬角、以米表达椭球高，合并高度范围为 35.373–57.879 m；这不是地下深度。
- **粒度与数据量：** 地下街资源含 4,828 个 B3DM、52,826 条 batch row；市营地铁札幌站资源含 1,595 个 B3DM、17,892 条 row。合计 70,718 条 row 均带非空 `gml_id`。每条 row 表示用于渲染的 CityGML 表面、房间或设施 batch，并非独立建筑数或可通行路段数。源压缩包共 63,139,254 bytes，展开后的本地缓存约 367 MB。
- **时间：** 源数据为 2024 财年；CKAN package 更新于 2025-05-26，本项目获取于 2026-07-21。
- **字段与单位：** batch table 保留 `gml_id`、`feature_type`、`city_code`、`meshcode`、嵌套 `attributes` 和已发布的 `uro:*` 字段。主要 feature type 包括 wall、floor、ceiling、door、room 和 building-installation surface。几何坐标与 region 高度遵循 3D Tiles。源字段不提供步行楼层、地下深度、法律通行权或开放状态，因此这些值保持 unknown。
- **已知缺口：** 这是验证用几何，不是完整或实时的车站模型。两个资源分别使用 city code `01100` 与 `01102`，项目保留差异而不强行合并。batch-table 字段存在大量 null，也没有可路由 centerline graph；绝对椭球高不能解释成勘测深度或正高基准。

## 来源

- [UC24-13 官方目录](https://www.geospatial.jp/ckan/dataset/plateau-uc24-13)
- [官方 CKAN `package_show` API](https://www.geospatial.jp/ckan/api/3/action/package_show?id=plateau-uc24-13)
- [PLATEAU 网站政策](https://www.mlit.go.jp/plateau/site-policy/)

选定资源 ID 固定于 `data/plateau/uc24_13_sapporo/source_manifest.json`。`uv run python -m terrai_spatial fetch underground_structures` 从官方地址下载压缩包，并验证安全解压、每个 tileset 引用、每个 B3DM header、batch-table 长度、压缩包哈希及缓存完整性。正常在线启动会恢复缺失缓存；离线启动不会把残缺缓存判为可用。

## 在本项目中的使用

该数据为 `sapporo-station-underground` 场景提供观测结构几何。`GET /api/v1/catalog` 报告 readiness、70,718 条 batch row 和两个按需 asset root；`GET /api/v1/datasets/uc24_13_sapporo` 返回 manifest。恢复后的资产从 `/api/v1/assets/external/plateau_uc24_13/` 提供，不进入 `/bootstrap`。

独立的 OSM 快照只补充社区 access/topology 上下文，不校验、覆盖或吸附 PLATEAU 几何。共同 scene ID 仅表示空间背景；各自的 ID、时间戳、文件和 license 始终分离。

## License

官方目录适用 [PLATEAU Site Policy 第 3 节](https://www.mlit.go.jp/plateau/site-policy/)。通常允许商业使用，但必须注明来源和修改，并检查单独标出的第三方权利。

## 商业使用注意

不得将该样例描述为权威车站平面、公共通行权记录、实时无障碍地图、疏散模型或工程测量。运营状态、通行权、基准与几何应向相关运营方或主管机构核实；保留 PLATEAU 署名，并披露 TerrAI 的转换和缓存日期。

## 仅供参考的资源

北一条停车场、涩谷站西口地下通道、Sunport 高松地下停车场仅作为同一 UC24-13 目录中的参考条目。[UC23-05 东京站地下街](https://www.geospatial.jp/ckan/dataset/plateau-uc23-05)同样仅供参考。它们均未下载、未注册为运行时数据集，也未加入札幌 canonical scene。
