# PLATEAU UC24-16 日本桥地下管线

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status：已作为外部观测样例接入；本地缓存按需恢复
- Publisher：Project PLATEAU / 日本国土交通省
- Dataset/API key：`plateau_uc24_16_nihonbashi` / `uc24_16_nihonbashi`

## 数据内容

- **格式与结构：**9个官方 ZIP，每个包含一个 3D Tiles 1.1 tileset 和带 `EXT_structural_metadata` 的 glTF 2.0 内容。可重建缓存包含9个压缩包、9个 `tileset.json` 与80个 glTF，共98个文件。源压缩包和展开后的资产不提交到 Git。
- **范围与空间参考：**缓存子集为日本桥示范区，约东经139.767043–139.780303°、北纬35.680907–35.691726°。`boundingVolume.region` 以弧度表示 WGS 84 经纬度角、以米表示 WGS 84 椭球高，合并范围为2.385–15.779 m。这些绝对高度不是 `uro:minDepth`/`uro:maxDepth`。
- **粒度与容量：**9类管线资源、80个 glTF tile、1,121条结构元数据要素。源压缩包合计2,398,270 bytes。全部1,121个 `uro:id` 都存在且唯一。
- **时间：**1,121条记录的 `core:creationDate` 均为2025-01-31；CKAN package 最后修改于2025-06-04，本项目取回日期为2026-07-21。`UC24` 表示示范项目谱系，并非实时运营台账时间。
- **资源类别：**下水管162、电力人孔92、通信人孔92、通信电缆162、下水人孔92、电力电缆162、供水管162、燃气管162、通信手孔35。
- **字段与单位：**保留23个上游原始字符串键，包括 `uro:id`、`uro:minDepth`、`uro:maxDepth`、`uro:outerDiamiter`、`uro:material`、`uro:length`、`uro:mesureType`、几何/专题来源代码和创建日期。`uro:outerDiamiter` 与 `uro:mesureType` 是上游原始拼写，不是 TerrAI 的修改。glTF 属性表没有编码深度、直径和长度的单位，因此审计索引中的 unit 为 `null`；只有 3D Tiles region height 明确定义为米。
- **已知缺口：**深度、长度、材质和测量字段在1,121条记录中的810条存在，外径在486条存在；311条出入口结构记录没有管线尺寸。代码值不会被猜测为人类可读的精度等级。通信设施不会被标记为光纤。覆盖范围、时效和位置完整性均不作保证。

## 来源

- [UC24-16 官方目录](https://www.geospatial.jp/ckan/dataset/plateau-uc24-16)
- [官方 CKAN `package_show` API](https://www.geospatial.jp/ckan/api/3/action/package_show?id=plateau-uc24-16)
- [PLATEAU 开放数据说明](https://www.mlit.go.jp/plateau/open-data/)

冻结的9项资源选择记录在 `data/plateau/uc24_16_nihonbashi/source_manifest.json`。`uv run python -m terrai_spatial fetch underground_utilities` 查询官方 package record，安全下载和展开当前 ZIP，验证所有被引用的 glTF，并重新生成哈希和审计元数据。正常联网启动会自动恢复缺失缓存；离线启动不会接受不完整缓存，而是报告该场景不可用。

## 在本项目中的使用

这是供后续地下管线视图使用的 Foundation Data Layer 观测证据。`GET /api/v1/catalog` 返回缓存就绪状态、1,121个要素和9个按需 tileset 根路径；`GET /api/v1/datasets/uc24_16_nihonbashi` 返回取回清单。只有本地恢复完成后，资产才会由 `/api/v1/assets/external/plateau_uc24_16/` 提供，并且永不进入 `/bootstrap`。

`data/plateau/uc24_16_nihonbashi/audit_index.json` 将每个源要素 ID 对应到资源、glTF tile、原始属性、缺失状态、取回时间及压缩包哈希。源深度属性与绝对三维位置保持分离，不得重复扣减。

`data/plateau/uc24_16_nihonbashi/scene_handoff.json` 是由同一数据集 key 所有的派生辅助元数据。它记录实测源范围、可逆的 `EPSG:4979` → `EPSG:4978` → 本地 ENU 米制坐标框架、WGS 84 椭球高参考，以及为 `unknown` 的正高基准。810 条管网记录和 311 条出入口结构记录被标为观测证据；同址地形/建筑、钻孔、地层和 SL 预测保持 unresolved，札幌公共地下空间结构为 not applicable。`data/scenes/underground/catalog.json` 在不注册新 FL 数据集 key 的前提下发现该场景。两份文件均可通过 `uv run python -m terrai_spatial data ensure --only underground_scenes --offline` 确定性重建，且不进入 `/bootstrap`。

## License

官方目录适用 [PLATEAU Site Policy 第3节](https://www.mlit.go.jp/plateau/site-policy/)。原则上允许包括商业用途在内的再利用，但必须保留来源署名、说明修改，并检查单独标出的第三方权利。取回清单保留官方资源 URL 和许可声明。

## 商业使用注意

这是范围有限的示范模型，并非权威、完整或最新的地下设施台账。不得用于开挖确认、工程设计、资产权属、应急响应或状态/容量决策。须保留 PLATEAU 署名，检查每项复用资源的第三方声明，并说明 TerrAI 审计索引属于派生元数据。在合格来源给出单位、测量方法和高程基准之前，这些信息必须保持 unknown。

## Reference-only adjacent sources

同一 UC24-16 目录还发布名古屋与大阪示范资源，但它们不进入运行时缓存或 FL 数据集。[UC23-04](https://www.geospatial.jp/ckan/dataset/plateau-uc23-04) 因 CKAN 许可字段未选择而仅作参考。[横滨下水道说明](https://www.city.yokohama.lg.jp/faq/kukyoku/gesui/kanro-hozen/20211015085255270.html) 是尚未确认批量开放契约的查看/打印参考；[横滨供水管线访问](https://www.city.yokohama.lg.jp/business/bunyabetsu/suido/mizumore/kanro.html) 需要申请和登录；[东京燃气埋管查询](https://itm-external22.tokyo-gas.co.jp/maicho/) 是注册制、按地点查询的服务。目前尚未确认日本具有权威性的批量开放光纤路线数据源。TerrAI 不会自动下载、抓取或公开这些 reference-only 来源。
