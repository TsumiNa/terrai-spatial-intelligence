# TerrAI Spatial Intelligence Platform — Integrated PoC

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

面向客户展示的空间决策 Demo：用地图和优先队列直接回答“哪里值得先行动、为什么、证据是否可信”。当前覆盖横滨城市韧性与茂原光伏开发；每个指标、队列结果和地图字段都能追溯来源、公式与适用限制。

项目采用独立静态前端和 FastAPI 后端。前端只负责数据加载、地图和审计交互；Python 后端负责文件数据读取、健康检查、条件/空间查询、汇总及推荐队列排序。基础数据暂时保留为独立 JSON/GeoJSON，数据库与 SQLite 留到后续开发。

## 运行

首次运行只需要已安装 `uv`。在本目录执行：

```bash
uv run python -m terrai_spatial serve --port 4176
```

然后访问 `http://localhost:4176/`。同一命令会启动：

- 客户展示前端：`http://127.0.0.1:4176/`
- FastAPI 后端与交互文档：`http://127.0.0.1:8000/docs`

运行不需要数据库或外部 API Key；底图、分析结果与 2023–2024 Satellite Embedding 裁剪均已缓存到本地。

`serve` 启动双端服务前会自动检查数据任务：缺失的打包基础数据优先从本地 Git 历史恢复，缺失的公开遥感/地图缓存会调用对应下载脚本，缺失或早于输入的派生结果会自动重建。东京电力原始本地缓存缺失时，也会从其官方 ZIP 自动下载到 Git 忽略目录，再解析摘要；因此标准 GitHub 克隆首次在线启动也会补齐原 CSV。每个实际执行的任务都会打印到终端，不会静默修改数据。若需要严格离线启动，可使用 `--offline`；若已确认数据完整，可使用 `--no-ensure-data`。

前后端也可以分别启动：

```bash
# 后端：API 与 /docs
uv run python -m terrai_spatial api --port 8000

# 前端：默认连接 http://127.0.0.1:8000/api/v1
uv run python -m terrai_spatial frontend --port 4176
```

常用工程命令：

```bash
# 校验必需文件和全部 JSON / GeoJSON
uv run python -m terrai_spatial validate

# 查看每条数据任务是 ready / missing / stale / blocked
uv run python -m terrai_spatial data status

# 补齐缺失数据并重建过期派生结果（启动时自动执行的同一逻辑）
uv run python -m terrai_spatial data ensure

# 主动刷新所有可自动更新的数据
uv run python -m terrai_spatial data update

# 只更新指定任务，可重复 --only
uv run python -m terrai_spatial data update --only tiles
uv run python -m terrai_spatial data update --only embedding
uv run python -m terrai_spatial data update --only grid

# 依次重建可再发布的联合分析与多尺度证据
uv run python -m terrai_spatial build

# 只重建一个管线：grid / joint / evidence
uv run python -m terrai_spatial build --only joint
```

`uv.lock` 固定 FastAPI、Uvicorn 与 Python 项目环境。只有重新获取 Satellite Embedding 时才安装 `remote` 可选依赖。

## FastAPI 接口

| 接口 | 用途 |
|---|---|
| `GET /api/v1/health` | 服务与 18 个文件数据集的完整性状态 |
| `GET /api/v1/catalog` | 数据文件目录、类型、记录数和更新时间 |
| `GET /api/v1/bootstrap` | 前端首屏需要的完整展示契约 |
| `GET /api/v1/datasets/{key}` | 按稳定 key 读取一个 JSON/GeoJSON |
| `GET /api/v1/features/{key}` | 按字段、数值范围、bbox、排序和 limit 查询 GeoJSON |
| `GET /api/v1/recommendations/{analysis}` | 获取 Python 服务端排序后的行动队列 |
| `/api/v1/assets/*` | 本地地图瓦片与遥感图像资产 |

前端不直接读取 `data/` 路径；文件位置、缓存与排序逻辑集中在 Python 数据服务中。

数据任务也可以直接作为脚本运行：

```bash
# 与程序启动共享同一个任务注册表
uv run python scripts/ensure_data.py status
uv run python scripts/ensure_data.py ensure
uv run python scripts/ensure_data.py update --only joint

# 单条底层脚本仍可独立执行
uv run python scripts/build_joint_analysis.py
uv run python scripts/build_multiscale_evidence.py
uv run python scripts/fetch_visual_tiles.py
uv run --extra remote python scripts/fetch_google_satellite_embedding.py
uv run python scripts/fetch_tepco_grid.py
uv run python scripts/update_tepco_grid.py
uv run python scripts/parse_tepco_grid.py
```

### 自动修复边界

- `bootstrap`：基础 GeoJSON/CSV/JSON 缺失或损坏时，优先通过 `git show HEAD:<path>` 原子恢复；源码压缩包环境才回退到 GitHub，私有仓库需提供 `GITHUB_TOKEN`。
- `tiles`、`embedding`：仅在缓存缺失时由启动流程联网获取；`data update` 才会主动刷新。
- `joint`、`evidence`：输出缺失、损坏，或脚本/输入比输出更新时自动重建。
- `grid`：在线首次启动发现本地原始缓存缺失时，自动从东京电力官方 URL 下载 ZIP、校验并只解压两份预期 CSV，然后重建摘要；原 ZIP、CSV 和包含哈希/下载时间的本地元数据均由 `.gitignore` 排除。缓存完整后启动不会重复下载；`data update --only grid`、`fetch tepco` 或 `build --only grid` 会主动刷新。
- `--offline`：禁止联网；已有仓库内筛查摘要时，即使本地原 CSV 缺失也能启动；如果摘要缺失但本地东京电力 ZIP/CSV 缓存完整，仍可解析，否则明确停止而不带着半套数据启动。
- 自动流程失败时不会带着半套数据启动服务器，而会显示具体任务、缺失输入和恢复方法。

## 可审计数值与三语界面

- 每个指标卡数值和说明、右侧队列摘要与分数、地图弹窗字段都有虚线下划线；点击打开同一个审计抽屉。
- **原始数据**显示主管/发布来源、来源字段、快照版本、本地证据文件和使用限制。
- **模型输出**显示模型/版本、输入输出、不确定性和本地验证状态。当前 Google AEF 不提供逐像素置信区间，因此明确显示“未校准”，不冒充确定性预测。
- **计算数据**显示公式、当前对象的代入数据、结果和数据血缘。现有风险分、适宜分、联合分均标为启发式计算，而不是预测概率。
- 顶部“中 / 日 / EN”可即时切换；选择保存在浏览器本地，URL 也支持 `?lang=zh|ja|en`。

## 内部产品架构记录（不在客户界面展示）

| 层 | 概念职责 | 当前 Prototype 状态 |
|---|---|---|
| **FL · Foundation Data Layer** | 保存公开、商业或客户授权的现实证据，以及不改变观测语义的确定性加工；如实保留多尺度 missing、时点、分辨率和许可边界 | 已接入 6 组公开/官方来源及本地派生证据 |
| **SL · Synthetic Data Layer** | 在适用性判断后，用场景化模型群非破坏性地补值/增强可预测的 missing；保留不确定性、模型身份、来源链和拒答 | 概念已定义；当前横滨/茂原地表模块补值数为 **0** |
| **AL · Application Layer** | 把合格 FL/SL 证据转为场景规则、排序、核查和行动出口 | 坡地暴露、道路韧性和光伏选址等 Demo 已接入 |

两个容易混淆的边界：Google Satellite Embedding 是外部生产的 FL 表征，不是 TerrAI 生成的 SL；当前容量代理、风险分和适宜分属于 AL 透明计算，也不是 SL。地权、许可、正式并网与结构安全等 missing 不应由模型擅自填补，必须保持 unknown，等待权威数据或现场尽调。

- [完整概念架构](../../architecture/FL_SL_AL_CONCEPT.zh.md)
- [重构背景与决策理由（英文）](../../refactor/fl-sl-al-platform/00-overview.md)
- [本次 PR 分步计划（英文）](../../refactor/fl-sl-al-platform/01-concept-layers-pr1a.md)
- [前端—后端调用结构与 Mermaid 时序图](../../architecture/FRONTEND_BACKEND.zh.md)

FastAPI v1 只建立演示所需的最小读取、查询和排序边界，不提前定义正式数据对象 schema、模型注册、任务编排、数据库、多租户权限或部署拓扑；这些仍属于客户数据与目标变量明确后的后续开发。

### 当前成本结论

- **Demo 运行时付费数据/分析服务：0 项。** 断网后仍可展示全部模块。
- **重新生成现有核心数据：不需要购买数据库或 Earth Engine。** Satellite Embedding 从公开 COG 镜像按需读取；其他来源为公开下载/API，并在本地处理。
- “免费访问”不等于“无条件商用”：GSI 有署名、加工说明和部分测量法/第三方权利限制；OpenStreetMap 有 ODbL 署名与数据库共享要求；东京电力 CSV 可免费读取，但不是开放许可数据，公开再发布前必须复核。
- 当前已接入数据逐项说明见 [`docs/data`](../../data/README.zh.md)；候选数据评估见 [`open-data-landscape`](../open-data-landscape/README.zh.md)。

### Demo 当前实际使用的 6 组外部来源

| 来源 | 用于什么 | 获取/运行成本 | 商用与主要限制 |
|---|---|---|---|
| GSI DEM5A 与地图/影像/起伏/坡度瓦片 | 地形分析、视觉核查 | 免费下载/读取；已本地缓存 | 可按 GSI 规则利用；需署名和加工说明，部分用途可能涉及测量法，个别瓦片含第三方权利 |
| Google Satellite Embedding V1（Source Cooperative 镜像） | 2023→2024 变化、相似性、未来少样本迁移 | 免费公开 COG；无需 Google 账号 | CC BY 4.0；必须使用指定署名；64 维轴不能当土地类别解释 |
| OpenStreetMap | 建筑、道路、水体、土地利用、输电线 | 免费下载；已转为本地 GeoJSON | ODbL；公开衍生数据库要履行署名/共享相同方式义务；完整性不保证 |
| 横滨市开放数据 | 官方地域防灾据点 | 免费 CSV | 默认 CC BY 4.0、允许商用；需署名，改动要标明，第三方权利另行处理 |
| NASA POWER | 茂原太阳辐照气候背景 | 免费 API；当前结果已缓存 | NASA 数据通常开放；应致谢且不得暗示 NASA 背书；不等于场址级发电量 |
| 东京电力公开系統信息 | 茂原区域级并网容量预筛 | 免费公开 ZIP/CSV；缺失时可从官方 URL 自动下载到本地 | **不是开放许可数据**；原说明标注禁止转载，且容量不是并网承诺；原文件不进 Git，仅作内部筛查，公开产品需复核权利与接续検討 |

## 八个客户入口

1. **决策总览**：在横滨城市韧性与茂原新能源开发之间切换。
2. **城市韧性项目**：查看社区光储节点与复合巡检走廊。
3. **光伏开发准备度**：查看可交付候选、规则冲突与东京电力公开容量信号。
4. **建筑坡地风险**：横滨保土谷区 2,128 栋建筑的地形暴露初筛。
5. **道路连续性**：272 段道路的巡检与社区影响优先级。
6. **公共设施改造**：两处横滨市官方地域防灾据点的改造机会队列。
7. **光伏候选地**：千叶茂原市 70 个候选网格的适宜性筛查。
8. **证据与可靠性**：10 m Satellite Embedding 年度变化、相似表征和逐项审计。

## Google 遥感数据的取舍

### Satellite Embedding V1：已真实接入

- 来源：Source Cooperative 的公开 COG 镜像，CC BY 4.0；数据由 Google 与 Google DeepMind 生产。
- 范围：横滨 7,820 个、茂原 19,877 个有效 10 m 像素。
- 时间：2023 与 2024 年度嵌入。
- 当前用途：64 维年度余弦变化、相似区域表征、未来少量客户标签迁移。
- 当前边界：不直接解释为土地类别，不进入适宜性或韧性评分。

重新裁剪只会读取 COG 的必要字节范围：

```bash
uv run --extra remote python -m terrai_spatial fetch embedding
```

### Dynamic World：已从 Demo 与数据管线移除

数据本身是 CC BY 4.0，但官方访问路径依赖 Earth Engine；TerrAI 的商业用途需要注册商业项目并承担用量费用。由于现阶段目标是“不购买额外数据库或分析服务”，页面、生成元数据、来源注册表和下载适配器均已删除。需要可解释土地覆盖时，优先评估可直接下载 COG 的 ESA WorldCover；需要近期光谱证据时，评估可本地处理的 Sentinel-2 L2A。

## FL 的多尺度基础与 SL 规划

| 层级 | 数据 | 在 Demo 中的职责 |
|---|---|---|
| 5–10 m 栅格 | GSI DEM、Satellite Embedding | 地形证据、变化与相似性核查 |
| 对象 | 建筑、道路、官方设施、光伏网格 | 可行动资产 |
| 100–300 m 邻域 | 服务圈、道路影响带、证据区 | 需求、可达性与设施缺口 |
| 区域/组合 | 电网门槛、项目队列、证据覆盖 | 投资排序与停止条件 |

`geo_pfn` 羽田实验提供了 SL 的机制证据：25–50 个完整上下文孔的中等稀疏区间显示 coherent context 与场景模型可能优于通用表格基线；但稠密最优模型不等于极稀疏最优模型，点预测、不确定性和逐样本误差排序也必须分别验证。因此 SL 规划采用模型群、按密度选择、校准和拒答，而不是用一个模型填满地图。该地下实验不被外推为横滨或茂原地表模块精度，详细数字与边界见[完整概念架构](../../architecture/FL_SL_AL_CONCEPT.zh.md#5-geopfn-作为-sl-的机制证据)。

## 四类视觉证据

地图右上方可随时切换：

- **标准**：国土地理院标准地图。
- **影像**：全国最新无缝正射影像；高缩放级别以航空影像为主，部分覆盖使用卫星影像。
- **起伏**：由 DEM5A / DEM5B / DEM10B 生成的阴影起伏图，突出山脊、谷地和微地形。
- **坡度**：由同一高程数据生成的倾斜量图，帮助直观核查土方、排水和坡地风险。

所有试点区域瓦片均已缓存到本地。重新获取：

```bash
uv run python -m terrai_spatial fetch tiles
```

## 1＋1＋1 ＞ 3 的实现

平台不是简单叠加三个图层，而是在各自同域范围内生成新的决策对象：

- **社区光储韧性枢纽**：寻找自身坡度较低、屋顶光伏容量代理较高、靠近重要道路且能服务周边高风险建筑群的候选建筑。可用于发现“光伏＋储能＋应急服务”组合项目。
- **官方设施改造项目**：先把同一逻辑落在真实的横滨防灾据点上，再把算法发现的普通建筑作为补充节点；官方身份与模型代理不混为一谈。
- **复合干预走廊**：把高优先道路、沿线高风险建筑密度和建筑平均风险联算，形成可打包的道路排水、边坡和建筑巡检走廊。
- **可交付光伏单元（茂原）**：在光伏适宜性基础上，提高道路运输、坡度工程和输电线距离的权重，把“适合”收敛为“更值得先踏勘”。它是独立的新能源开发产品，不与横滨数据直接叠加。

## 重新生成联合分析

```bash
uv run python -m terrai_spatial build --only joint
uv run python -m terrai_spatial build --only evidence
```

脚本只依赖 Python 标准库，输出：

- `data/joint/resilience_hubs.geojson`
- `data/joint/compound_corridors.geojson`
- `data/joint/solar_delivery_cells.geojson`
- `data/joint/joint_summary.json`

## 公开电网容量筛查

平台已接入东京电力千叶县“系統の予想潮流等”CSV。Git 仓库不保存原始表，只保留 Demo 使用的标准化筛查摘要；带有“転載禁止”限制的原始 ZIP/CSV 与逐文件哈希元数据仅保留在本地工作副本，不进入 Git 历史。页面显示的快照日期取自下载响应的 `Last-Modified`，下载时间和 SHA-256 保存在本地审计元数据中：

- 千叶县全表：175 条送电线、201 条变电设备记录。
- 茂原匹配：4 条相关线路、1 个“茂原”配电变电所。
- 茂原变电所：自身空容量代理 5 MW；计入上位系统约束后为 0 MW；公开表标注存在平常时出力控制可能。

主动下载当前官方版本并重新解析：

```bash
uv run python -m terrai_spatial fetch tepco
# 等价的数据任务命令
uv run python -m terrai_spatial data update --only grid
# 底层脚本
uv run python scripts/update_tepco_grid.py --force
```

仅使用已经存在的本地 ZIP/CSV 重新解析：

```bash
uv run python scripts/update_tepco_grid.py --offline
```

兼容的构建命令也会主动刷新官方 ZIP：

```bash
uv run python -m terrai_spatial build --only grid
```

输出为 `data/mobara/tepco_grid_screen.json`。程序下载不改变东京电力的权利条件：这些数值只用于区域级项目发现和并网预咨询排序，不是正式接续検討结果；原 CSV 也没有足够几何信息把容量准确分配到每个候选网格。完整缓存行为见 [`tepco-grid`](../../data/tepco-grid/README.zh.md)。

## 重要边界

这是最小可行 PoC，所有分数均为透明的启发式相对评分。结果不等同于：

- 建筑结构安全或已确认灾害；
- 实际屋顶可用面积、光伏发电量或储能设计；
- 道路中断概率或应急通行保证；
- 土地权属、环境许可、地质灾害法规、电网容量或并网承诺。

进入试点前，建议优先补入：

- 横滨：官方防灾据点位置已经接入；仍需补充公共建筑属性、真实屋顶、灾害深度/警戒区与配电约束。
- 茂原：法务省地籍、MAFF 2026农地笔、地价/都市规划和保护区；电网公开快照已经接入，但仍需项目级并网咨询。

## 已确认可继续接入、但当前 Demo 未使用

这些来源都不要求购买商业数据库；部分需要免费注册/API Key、遵守调用限额或逐图层检查许可：

- ESA WorldCover 2020/2021：10 m、11 类土地覆盖 COG，CC BY 4.0；适合静态地表语义，但跨年变化会混入版本/算法差异。
- Copernicus Sentinel-2 L2A：免费开放多光谱影像；适合 NDVI、湿润/水体、裸地和施工变化，本地处理需做云/云影掩膜。
- GSI Hazard Map Portal：土砂、洪水、内水、津波等；仅使用官方标为开放数据的图层，并分别保留来源/时点。
- MAFF 笔ポリゴン：农地边界与耕作单元筛查；不代表地权，也不能单独判断农地转用许可。
- 法务省登記所備付地図：宗地边界与地番；免费下载但需登录，不提供开放所有者名单，部分“公图”不是精确测量边界。
- 国土交通省不动产信息库：交易、地价、都市规划和部分防灾信息；API 免费但需申请 Key、显示规定声明，不能替代重要事项说明。
- 国土数值信息/环境相关 GIS：自然公园、自然保全、鸟兽保护、森林等排除条件；必须逐数据集确认“商用可”。
- METI FIT/FIP 公表数据：既有/认定可再生能源项目竞争背景；公开信息有规模与隐私/地址边界，不能等同于完整在运资产库。

Dynamic World 只保留在数据决策记录的“评估后排除”一栏，不属于上述待接入队列。完整链接与许可判断见 [`open-data-landscape`](../open-data-landscape/README.zh.md)。

## 原始 Demo

- `../terrai_slope_screen_poc`
- `../terrai_resilience_road_poc`
- `../terrai_solar_site_screen_poc`

原目录未删除，便于回溯每个分析模块的独立方法和数据生成过程。

## 项目结构

```text
terrai-spatial-intelligence/
├── pyproject.toml              # uv 项目、Python 版本和 remote 可选依赖
├── uv.lock                     # 可复现环境锁文件
├── terrai_spatial/             # FastAPI 后端与统一 CLI
│   ├── api.py                  # health / catalog / data / query / recommendations API
│   ├── data_service.py         # JSON/GeoJSON 读取、缓存、查询、汇总与服务端排序
│   └── data_tasks.py           # 启动与手动命令共享的数据任务注册表
├── frontend/                   # 独立静态客户展示前端
│   ├── index.html              # 展览型信息架构
│   ├── app.js                  # API 加载、地图与交互展示
│   ├── audit.js                # 原始/模型/计算三类审计契约
│   ├── i18n.js                 # 中日英界面词典
│   └── styles.css              # 地图、结果队列、审计抽屉与响应式样式
├── scripts/                    # 可直接执行的数据获取、恢复与派生管线
│   ├── ensure_data.py          # status / ensure / update 脚本入口
│   └── bootstrap_packaged_data.py # 从 Git 恢复缺失基础快照
├── docs/
│   ├── architecture/           # 当前概念与前后端调用结构；中日英三语
│   ├── data/                   # 已接入 FL 数据卡与许可说明；中日英三语
│   ├── refactor/               # 英文重构总览与按 PR 拆分的计划
│   ├── summary/                # 验证、评估与项目决策；中日英三语
│   └── others/                 # 最后手段的未分类英文文档
└── data/                       # FL 文件快照、标准化数据和分析结果；暂不使用数据库
```
