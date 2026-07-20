# Google Satellite Embedding V1 / AlphaEarth Foundations

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入
- 分辨率：10 m，年度64维表征
- 当前年份：2023、2024

## 数据内容

- **格式** — 64 波段 Cloud Optimized GeoTIFF（int8，NODATA = −128），通过 HTTP 字节范围从 Source Cooperative 公开镜像 `tge-labs/aef/v1/annual` 读取。仅传输覆盖两个演示范围的窗口，不会完整下载全球瓦片。
- **分辨率与频次** — 10 m 像元，每个日历年一期合成。本地缓存年份为 2023 与 2024。
- **坐标系** — UTM 54N 带（EPSG:32654），与来源分幅一致；派生成果重投影为 WGS84 用于展示。
- **单个像元的含义** — 每个像元是概括该年度卫星观测的 64 维单位长度嵌入向量。它不是地表反射率、不是光谱指数、也不是土地覆盖类别，各维度没有可单独解释的物理意义。
- **本地成果与字段** — `data/google/satellite_embedding/embedding_evidence.geojson` 含 300 个单元，字段为 `cell_id`、`region`、`year_pair`、`cosine_change`、`change_score`、`support_pct`、`valid_pixels`、`evidence_status`、`embedding_preview`；另有分区域的变化图与潜在 RGB 图共 4 张 PNG 叠加层以及 `summary.json`。
- **数据量** — 两个区域合计 300 个证据单元，由两个年度图层的窗口读取生成。
- **已知缺失与限制** — 该镜像为公开副本，并非 Google 官方支持。`cosine_change` 度量像元年度向量的移动幅度，因此 `change_score` 高只代表「值得核查」，绝不等于已识别原因；nodata 像元较多处 `support_pct` 与 `valid_pixels` 会下降。这些数值在通过本地验证前不进入决策评分。

## 来源

数据由 Google 与 Google DeepMind 生产，本项目从 Source Cooperative 的公开 COG 镜像读取必要窗口；该镜像不由 Google 官方支持。目录：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL ，镜像：https://registry.opendata.aws/aef-source/

## 在本项目中的使用

横滨 7,820、茂原 19,877 个有效像素，用于年度余弦变化、相似区域核查和未来少量客户标签迁移。生成变化图、相似表征图和100 m证据单元。当前不进入适宜性或韧性评分；外部生产的表征属于 FL，不是 TerrAI SL。

## License

CC BY 4.0。指定署名：`The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`

## 商业使用注意

64维轴不能直接解释为土地类别；年度变化也可能来自成像条件，必须结合影像和现场核查。公开镜像目前无需 Google 账号或 Earth Engine，但 TerrAI 承担自身网络、存储和计算；若改用官方 provider-pays 路径需重新评估费用。
