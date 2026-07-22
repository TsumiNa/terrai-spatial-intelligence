# TerrAI 前端—后端架构与调用结构

[English](FRONTEND_BACKEND.md) | [日本語](FRONTEND_BACKEND.ja.md) | [中文](FRONTEND_BACKEND.zh.md)

状态：当前 Demo 实现

更新日期：2026-07-21

本文描述客户展示版 TerrAI 的**运行时调用结构**。它关注浏览器、构建后的 Svelte 前端、FastAPI、Python 数据服务和文件数据之间如何交互；内部 FL → SL → AL 产品概念见 `docs/architecture/FL_SL_AL_CONCEPT.md`。

## 1. 组件与职责

| 组件 | 当前实现 | 职责 |
|---|---|---|
| 客户浏览器 | Chrome / Safari 等 | 加载页面、触发模块切换和审计交互 |
| Svelte 前端 | `webapp/`（Svelte 5 + Vite；`terrai serve` 提供构建后的 `webapp/dist`） | 请求展示数据，渲染 MapLibre + deck.gl 地图、指标、队列、审计抽屉和编译期校验的三语界面；不读取本地数据文件，不计算或排序业务结果 |
| FastAPI | `terrai_spatial/api.py` | 提供 `/api/v1` HTTP 边界、参数校验、错误码、CORS、OpenAPI 和只读资产服务 |
| Python 数据服务 | `terrai_spatial/data_service.py` | 用稳定 key 定位文件，按修改时间缓存，执行查询、区域筛选、汇总与推荐队列排序 |
| 数据任务 | `terrai_spatial/data_tasks.py` 与 `scripts/` | 启动前检查、下载、解析和重建数据；不在普通 API 请求中执行昂贵任务 |
| FL 文件 | `data/**/*.json`、`data/**/*.geojson`、瓦片与遥感图像 | 当前只读数据存储；未来可由 SQLite 替换而不改变前端调用方式 |

本地默认监听：

- 前端：`http://127.0.0.1:4176/`
- API：`http://127.0.0.1:8000/api/v1`
- OpenAPI：`http://127.0.0.1:8000/docs`

前端可用 URL 参数 `api` 覆盖 API origin，例如：

```text
http://127.0.0.1:4176/?api=http://127.0.0.1:9000
```

## 2. 启动调用顺序

`terrai_spatial serve` 会在 `webapp/dist` 不存在时拒绝启动（先执行 `cd webapp && npm run build`），然后在一个开发命令中管理数据检查和两个独立 HTTP 服务。数据缺失或过期时，统一任务注册表调用对应 Python 脚本；数据可用后才启动前端和 API。

```mermaid
sequenceDiagram
    autonumber
    actor Operator as 用户/展会人员
    participant CLI as terrai_spatial CLI
    participant Tasks as Python Data Tasks
    participant Files as data/ FL 文件
    participant Scripts as 下载/解析/构建脚本
    participant API as FastAPI :8000
    participant Web as Built Frontend webapp/dist :4176

    Operator->>CLI: uv run python -m terrai_spatial serve
    CLI->>Tasks: ensure_data(allow_network)
    Tasks->>Files: 检查存在性、完整性与更新时间
    alt 数据完整且未过期
        Files-->>Tasks: ready
    else 数据缺失或过期
        Tasks->>Scripts: 执行对应下载/解析/重建任务
        Scripts->>Files: 原子写入或更新产物
        Files-->>Tasks: ready
    end
    Tasks-->>CLI: 数据任务通过
    CLI->>API: 启动 Uvicorn / FastAPI
    API-->>CLI: started
    CLI->>Web: 启动静态文件服务
    CLI-->>Operator: 输出前端与 /docs 地址
```

若数据任务失败，`serve` 会在启动 HTTP 服务前停止并报告缺失输入或恢复方法。`--no-ensure-data` 可跳过检查；`--offline` 可禁止联网。

## 3. 当前客户前端的真实请求顺序

当前页面采用“一次加载、客户端切换视图”的 Demo 策略：首屏只请求一次聚合展示契约，之后的模块切换、语言切换和审计抽屉不再次查询后端。地图瓦片及遥感图片按浏览器视窗按需加载。

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 客户
    participant Browser as 浏览器
    participant Frontend as webapp Svelte app
    participant API as FastAPI /api/v1
    participant Service as Python DataService
    participant FL as JSON / GeoJSON
    participant Assets as 本地瓦片/遥感图像

    Customer->>Browser: 打开 :4176
    Browser->>Frontend: 加载 HTML/CSS/JS
    Frontend->>API: GET /bootstrap
    API->>Service: bootstrap()
    loop 每个稳定 bootstrap dataset key
        Service->>FL: stat 修改时间
        alt 缓存不存在或文件已更新
            Service->>FL: read + json.load
            FL-->>Service: JSON / GeoJSON
        else mtime 缓存命中
            Service->>Service: 返回内存副本
        end
    end
    Service->>Service: 设施汇总、区域筛选、推荐队列排序
    Service-->>API: 展示 payload + health/source metadata
    API-->>Frontend: 200 application/json
    Frontend->>Frontend: 渲染当前模块、指标、地图和行动队列

    par 地图按当前视窗取资源
        Browser->>GSI: GET basemap tiles (cyberjapandata.gsi.go.jp)
        GSI-->>Browser: 矢量/栅格瓦片
    and 遥感证据视图需要覆盖图
        Browser->>API: GET /assets/google/...image...
        API->>Assets: 读取遥感图像
        Assets-->>API: PNG
        API-->>Browser: 图像资源
    end

    Customer->>Frontend: 切换模块/视图/语言
    Frontend->>Frontend: 使用 bootstrap 中已准备的数据重新渲染
    Note over Frontend,API: 当前不会再次请求 API

    Customer->>Frontend: 点击虚线数值
    Frontend->>Frontend: 审计抽屉打开来源/公式/限制
    Note over Frontend,API: 审计内容随展示包加载，不产生网络请求
```

## 4. API 查询调用顺序

除当前页面使用的 `/bootstrap` 和 `/assets/*` 外，FastAPI 还提供细粒度接口，供 API 文档验证、后续按需加载页面或外部客户端使用。

```mermaid
sequenceDiagram
    autonumber
    actor Client as 前端/外部客户端
    participant API as FastAPI
    participant Service as DataService
    participant FL as JSON / GeoJSON

    Client->>API: GET /features/solar?where=status&equals=preferred&sort=score&limit=20
    API->>API: 校验 key、数值范围、bbox 与 limit
    alt key 不存在或文件不可用
        API-->>Client: 404
    else 参数或数据类型不适用
        API-->>Client: 422
    else 请求有效
        API->>Service: query_features(...)
        Service->>FL: 通过稳定 key 加载或命中 mtime 缓存
        FL-->>Service: FeatureCollection
        Service->>Service: 字段过滤 → bbox 相交 → 排序 → limit
        Service-->>API: 查询结果 + matched/returned
        API-->>Client: 200 GeoJSON
    end
```

## 5. 接口与调用方

| 接口 | 当前客户页面是否调用 | 主要用途 |
|---|---:|---|
| `GET /api/v1/bootstrap` | 是，首次加载一次 | 返回全部展示数据、服务端推荐队列、设施汇总和健康元数据 |
| `GET /api/v1/assets/*` | 是，按地图视窗调用 | 返回本地地图瓦片、Satellite Embedding 可视化等二进制资源 |
| `GET /api/v1/health` | 否，包含在 bootstrap metadata | 独立监控服务和全部数据集的就绪状态 |
| `GET /api/v1/catalog` | 否 | 审查稳定 key、文件类型、记录数和更新时间 |
| `GET /api/v1/datasets/{key}` | 否 | 按 key 获取完整 JSON/GeoJSON |
| `GET /api/v1/features/{key}` | 否 | 按字段、范围、bbox、排序与 limit 查询 GeoJSON |
| `GET /api/v1/recommendations/{analysis}` | 否，结果已包含在 bootstrap | 单独取得服务端筛选和排序后的行动队列 |

## 6. 边界与后续演进

- API 当前只读；浏览器不能修改 FL 文件或触发数据重建。
- 普通请求不调用下载脚本，避免一次页面访问意外产生长任务或外部依赖。
- 当前 `/bootstrap` 适合小型本地 Demo。数据量增长后，前端应改用 `/features/{key}` 与 `/recommendations/{analysis}` 按视窗、模块分页加载。
- 迁移 SQLite 时，应替换 `DataService` 内部 repository/load/query 实现，保持 `/api/v1` 路径和响应语义稳定。
- 加入客户数据后，需要在 API 前增加认证、租户隔离、授权审计与版本选择；这些不属于当前 PoC。

## 7. 代码定位

- 前端 API origin 与带类型的启动请求：`webapp/src/lib/api/client.ts`、`webapp/src/App.svelte`
- 地图实例、底图与 deck.gl 图层：`webapp/src/lib/map/`
- 审计记录与消息目录：`webapp/src/lib/audit.ts`、`webapp/src/lib/i18n/messages.ts`
- HTTP 路由与错误映射：`terrai_spatial/api.py`
- 文件缓存、查询、汇总与队列：`terrai_spatial/data_service.py`
- 启动双服务与自动数据检查：`terrai_spatial/cli.py`
- 数据任务注册和依赖：`terrai_spatial/data_tasks.py`
- 前后端职责与调用结构已合并保留在本文；重构过程见英文 [`fl-sl-al-platform`](../refactor/fl-sl-al-platform/00-overview.md)。
