# 数据来源与许可说明

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

更新：2026-07-20。本清单覆盖 TerrAI 当前三个分析方向（光伏选址、道路/设施韧性、坡地暴露）中已经使用、已确认可脚本接入，以及评估后排除的数据；不是全球地理数据的穷举。

## 怎么读这份清单

- **已接入**：Demo 文件中存在真实下载数据或由其生成的本地结果；页面运行无需联网、API Key 或付费服务。
- **可接入**：已经确认有官方批量下载、COG、GIS 或 API 入口，但当前 Demo 没有使用其数值。
- **评估后排除**：数据可能开放，但其唯一/主要访问平台、商业费用或重复性不符合当前零采购约束。
- **免费**只表示来源方当前不收数据购买费。自有存储/计算、网络流量、免费账号/API Key、署名、共享相同方式、测量法审批和法定尽调都可能仍然存在。

## 一页式资产目录

### 当前 Demo 实际使用

| 数据源 | 状态 | 能做什么 | 数据/服务成本 | 商用和限制 |
|---|---|---|---|---|
| GSI DEM5A | 已接入 | 坡度、起伏、低点，建筑/道路地形暴露 | 免费下载；需免费账号；本地计算 | 依 GSI 规则署名并标明加工；作为基本测量成果，部分复制/使用方式可能需要测量法手续 |
| GSI 标准、全国最新照片、阴影起伏、倾斜量瓦片 | 已接入 | 地图背景、屋顶/植被/地表、山脊谷地的视觉核查 | 免费在线读取；试点瓦片已缓存 | 不可把全国最新照片全部称为卫星影像；需署名，部分瓦片有第三方权利/个别法令限制，公开离线再发布前逐图层复核 |
| Google Satellite Embedding V1 / AEF | 已接入 | 10 m 年度变化、相似区域、未来稀疏标签迁移 | Source Cooperative COG 镜像免费、无需 Google 账号；本地计算 | CC BY 4.0 和指定署名；镜像非 Google 官方支持；64 维轴不可直接解释为土地类别，当前不进入决策分数 |
| OpenStreetMap | 已接入 | 建筑、道路、水体、土地利用、输电线 | 免费下载；本地处理 | ODbL；需署名，公开衍生数据库可能触发共享相同方式；众包完整性/时效不保证，生产底图服务不能滥用 OSM 公共瓦片 |
| 横滨市地域防灾拠点 | 已接入 | 官方设施身份、地址、位置；与屋顶/道路/社区需求联算 | 免费 CSV | 默认 CC BY 4.0、允许商用；需署名并注明加工，第三方权利另行处理；屋顶、容量和服务圈是 TerrAI 代理而非官方字段 |
| NASA POWER | 已接入 | 茂原太阳辐照长期气候背景 | 免费 API；当前结果已缓存 | NASA 数据通常开放；建议致谢且不得暗示 NASA 背书；气候平均值不能替代逐场址发电建模 |
| 东京电力“系統の予想潮流等” | 已接入（受限） | 区域级空容量/上位约束预筛、并网咨询排序 | 免费公开 ZIP/CSV；可从官方 URL 自动下载到本地 | **非开放许可**；官方注意资料标注“転載禁止”，数值为暂定简化值且不保证接入。原 ZIP/CSV 不进 Git，只保留内部可追溯缓存；公开/商业再发布需权利复核和正式接续検討 |

### 已确认可脚本接入，当前 Demo 未使用

| 数据源 | 适合的模块 | 能增加什么 | 费用/访问 | 关键限制 |
|---|---|---|---|---|
| ESA WorldCover 2020/2021 | 光伏、遥感解释 | 全球 10 m、11 类土地覆盖与质量层 | COG 免费直下，CC BY 4.0 | 只有 2020/2021；两个年度算法版本不同，不能把差异全部解释为真实变化 |
| Copernicus Sentinel-2 L2A | 光伏、灾后/施工变化 | 多光谱反射率、NDVI/NDWI/NDBI、季节变化 | 数据免费开放；Copernicus Data Space 免费账号/配额；可本地计算 | 必须做云、云影、日期和合成质量控制；10 m 不适合单栋屋顶结构诊断 |
| GSI Hazard Map Portal 开放图层 | 坡地、道路、设施 | 土砂、洪水、内水、津波等法定/官方风险背景 | 开放图层免费、可商用 | 逐图层检查“オープンデータ”标记、主管机关、时点和缩尺；不能用视觉瓦片替代原始法定数据 |
| MAFF 笔ポリゴン | 光伏 | 农地边界、耕作单元、农地敏感性初筛 | 免费批量下载；千叶 2026 约 318 MB | 署名与加工说明；不是地权、地番或农地转用许可结果 |
| 法务省登記所備付地図 | 光伏 | 宗地形状、地番、候选地拼接 | 登录后免费 GML/地图数据 | 不含公开所有者名单；同时包含法14条地图和“地图に準ずる図面”，后者位置/边界不能视为确界 |
| 国土交通省不动产信息库 | 光伏、投资排序 | 交易价格、地价、都市规划、防灾/设施接口 | API 免费但需申请、审查、API Key | 必须显示规定声明；可能限流/变更，非全域、非实时，不能用于重要事项说明或建筑确认 |
| 国土数值信息 / 环境 GIS | 光伏排除 | 自然公园、自然保全、鸟兽保护、森林等约束 | 多数免费 GIS 下载 | **逐数据集**确认“商用可”或政府标准条款；精度和更新期不同，最终以主管机关确认为准 |
| METI FIT/FIP 事业计划公表数据 | 光伏市场 | 已认定项目、容量、竞争/集聚背景 | 免费公开查询/文件 | 不是完整在运资产库；小规模光伏和地址字段有公开边界；批量再利用按当期网站条款复核 |
| e-Stat 统计 GIS 边界 | 两区域拓展 | 行政/统计区聚合、人口与需求归一化 | 免费下载 | 边界用于统计表达，不是法定地界；遵守政府统计利用条件和出典要求 |

### 当前无法用纯开放数据可靠获得

| 需要的信息 | 为什么仍缺 | MVP 获取方式 |
|---|---|---|
| 土地/建筑真实所有者、抵押与完整权利关系 | 公开地籍图不公开完整所有者名单 | 客户授权的登記事项证明、公图/地积测量图或合规付费查询 |
| 宗地级真实并网容量、工期和负担金 | 公布值是区域筛查且可能受上位系统/运行条件影响 | 向一般送配电企业申请事前咨询/接续検討 |
| 农地转用、林地开发、保护区等“能否批准”结论 | 开放图层只表达对象/范围，不包含个案裁量与最新案件条件 | 主管机关预咨询、法务/工程顾问与现场材料 |
| 屋顶结构承载、道路灾时可通行、边坡稳定性 | 遥感/DEM/建筑轮廓只能提供代理 | 现场踏勘、结构/地质/道路工程资料和客户运维记录 |

## 日本国土地理院（GSI）

- 数据：基盘地图信息数值高程模型 DEM5A；标准地图、全国最新照片、阴影起伏图、倾斜量图瓦片。
- 用途：坡度、局部起伏、低点、地表覆盖核查和地图背景。
- 官方说明：https://maps.gsi.go.jp/development/ichiran.html
- 瓦片地址：`seamlessphoto`、`hillshademap`、`slopemap`，试点范围均已缓存到本地。
- 全国最新照片在 ZL14–18 主要来自正射航空影像，部分区域包含 Landsat-8 等卫星影像；不能把所有像素统一描述为卫星影像。
- 获取成本：免费；基盘地图信息下载需要免费注册，地图瓦片不应对官方服务器造成过大负载。
- 许可：按国土地理院内容利用规则署名并标注加工。DEM 属基本测量成果，某些公开地图复制/利用方式可能需要依据测量法办理手续；瓦片还可能包含第三方权利或个别法令限制。
- 官方条款：https://maps.gsi.go.jp/help/termsofuse.html
- 基盘地图信息下载注意：https://service.gsi.go.jp/kiban/app/help/

## Google Satellite Embedding V1 / AlphaEarth Foundations（已接入）

- 数据：2017 年起的年度 64 维地表嵌入，10 m 分辨率；本 PoC 使用 2023 与 2024 年。
- 来源：Source Cooperative 公开 COG 镜像；镜像不由 Google 官方支持，数据由 Google 与 Google DeepMind 生产。
- 许可：CC BY 4.0。署名：`The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`
- 本地产品：两个区域的年度余弦变化 PNG、2024 相似表征 PNG、300 个 100 m 证据单元及来源 VRT 标识。
- 用途：异常核查、相似区域检索、未来少量客户标签迁移；当前不进入任何适宜性或韧性分数。
- 官方目录：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
- 公开镜像：https://registry.opendata.aws/aef-source/
- 成本：公开镜像当前无需购买数据、Google 账号或 Earth Engine；TerrAI 只承担自己的网络、存储与本地计算。Google 官方 GCS 当前是 provider-pays，但本 Demo 未走该路径。

## Google Dynamic World V1（评估后排除）

- 数据本身为 CC BY 4.0，但官方分发与批量分析依赖 Earth Engine；TerrAI 的商业使用需商业项目和用量计费。
- 决策：现阶段不购买数据库/分析服务，因此已从页面、生成脚本、来源注册表、派生元数据和适配器中移除，不属于 Demo 或待接入清单。
- 免费替代路径：静态可解释类别优先评估 ESA WorldCover；近期光谱/变化优先评估 Sentinel-2 L2A 本地处理。二者都不能无验证地替代 Dynamic World 的逐类概率。
- 数据目录：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
- Earth Engine 商业价格：https://cloud.google.com/earth-engine/pricing

## 横滨市地域防灾拠点（已接入）

- 数据：横滨市地域防灾拠点与帰宅困難者一時滞在施設 CSV，更新于 2026-04-01。
- 许可：横滨市开放数据默认 CC BY 4.0，允许商用；须署名，若加工须声明，第三方权利由使用者处理。
- 本 PoC：筛出保土谷区当前研究窗口内两处官方据点；位置、名称与地址为官方观测。
- 派生代理：最近建筑屋顶、光伏容量、道路距离、250 m 高风险建筑关联；均明确标为 PoC 推断。
- 官方资源：https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv
- 利用条款：https://data.city.yokohama.lg.jp/terms.html

## Copernicus Sentinel-2（已确认，尚未缓存）

- 数据：Sentinel-2 L2A 多光谱地表反射率，可通过 Copernicus Data Space STAC API 检索。
- 计划用途：NDVI/植被活力、裸地识别、季节变化与施工前后变化检测。
- 官方文档：https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- 成本与许可：Sentinel 数据免费、开放；Data Space 的账户、配额与服务条款需遵守。基础数据下载不要求购买商业数据库，TerrAI 可本地处理。
- 接入前必须增加云/云影掩膜、影像日期选择和质量标志；当前 PoC 不把单景影像颜色直接转成选址分数。

## OpenStreetMap

- 数据：建筑轮廓、道路、水体、土地利用与输电线。
- 用途：资产暴露、道路网络、光伏退距和基础场景。
- 许可：Open Database License (ODbL)。
- 成本与限制：数据可免费商业使用；必须署名，公开衍生数据库可能需以 ODbL 提供。OpenStreetMap Foundation 不保证免费的生产 API/瓦片服务，本 Demo 使用本地数据。
- 版权与许可：https://www.openstreetmap.org/copyright

## NASA POWER

- 数据：2001–2020 年太阳辐照气候平均值，ALLSKY_SFC_SW_DWN。
- 用途：茂原市光伏资源背景；年均 GHI 约 1,378 kWh/m²。
- API 文档：https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
- 成本与许可：免费 API；NASA 数据通常不受美国版权保护，使用时仍应致谢，不得使用 NASA 标识或暗示背书，并检查单项数据是否另有标记。

## 东京电力公开系統信息（已接入）

- 数据：千叶县送电线与变电设备“系統の予想潮流等”CSV。东京电力页面于 2026-07-16 公告追加 CSV；程序不把页面公告日期写死为数据快照，而以实际 ZIP 响应的 `Last-Modified` 和本地下载时间记录版本。
- 自动获取：标准 GitHub 克隆首次在线启动发现本地原始缓存缺失时，任务从官方千叶县 ZIP URL 下载，验证 ZIP 与两份预期文件，原子解压到 `data/external/tepco/`，再运行标准化解析。缓存完整后不重复下载；也可执行 `uv run python -m terrai_spatial fetch tepco` 主动刷新。
- 本地审计：`download_metadata.local.json` 保存实际 URL、下载时间、HTTP `Last-Modified`/ETag、ZIP 与两份 CSV 的字节数和 SHA-256。该文件与原始 ZIP/CSV 一起被 Git 忽略，避免自动更新弄脏仓库或变相分发原数据。
- 标准化输出：`data/mobara/tepco_grid_screen.json`。
- 茂原筛查信号：配电变电所自身空容量代理 5 MW，考虑上位系统后为 0 MW，且存在平常时出力控制可能。
- 官方页面：https://www.tepco.co.jp/pg/consignment/system/index-j.html
- 成本：官方 ZIP 可由普通 HTTPS 客户端免费公开下载，无需购买数据库、API Key 或 Earth Engine；只产生用户自己的网络、存储和本地计算成本。这不等于开放数据许可。
- 许可与限制：官方注意资料标注“転載禁止”；CSV 没有可供逐宗地空间连接的完整设备几何，公开值为暂定简化数据，也不是正式接续検討或并网承诺。当前仅用于内部 Demo 的筛查信号；若对外发布原始表、可逆重构数据或商业产品，须先向东京电力确认权利。
- 官方注意事项：https://www.tepco.co.jp/pg/consignment/system/pdf/yosouchoryu_points_to_note.pdf

## 联合分析的自定义假设

- 建筑屋顶光伏容量代理：建筑轮廓面积 × 60% 可用面积 × 0.20 kWp/m²，即轮廓面积 × 0.12 kWp。
- 建筑服务需求：候选枢纽 150m 内的高风险建筑关联数。
- 道路影响带：道路中心线 55m 内的建筑。
- 本地距离采用纬度 35.45° 附近的平面近似；生产系统应使用合适的投影坐标系。
- 所有关联数可能重复计算同一建筑，只用于候选排序，不应解释为独立受益人或避免损失。

## 可脚本化入口

- ESA WorldCover：https://esa-worldcover.org/en/data-access
- Copernicus Data Space：https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- GSI Hazard Map Portal 开放数据：https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html
- MAFF 笔ポリゴン：https://www.maff.go.jp/j/tokei/census/shuraku_data/2025/mb/index.html
- 法务省登記所備付地図：https://www.moj.go.jp/MINJI/minji05_00494.html
- 国土交通省不动产信息库 API：https://www.reinfolib.mlit.go.jp/help/apiManual/
- 国土数值信息：https://nlftp.mlit.go.jp/ksj/
- METI FIT/FIP 公表信息：https://www.fit-portal.go.jp/PublicInfoSummary
- e-Stat GIS：https://www.e-stat.go.jp/gis/statmap-search?aggregateUnitForBoundary=A&page=1&type=2

机器可读接入状态统一登记在 `data/external/source_registry.json`。注册表只记录可批量处理的数据，不把营销地图截图或不可追溯的手工样本列为正式来源。
