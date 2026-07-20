# 客户展览版前后端分离

[中文](FRONTEND_BACKEND_SPLIT.md) | [日本語](FRONTEND_BACKEND_SPLIT.ja.md) | [English](FRONTEND_BACKEND_SPLIT.en.md)

状态：Implemented for Demo
日期：2026-07-20

## 目标

客户界面只回答功能、结果、可靠性和追溯问题。内部 FL → SL → AL 产品概念仍保留在架构文档中，但不占据客户导航或首屏。

技术上，浏览器不再直接知道或读取 data/ 下的文件路径：

    frontend/ 静态展示
      └─ HTTP JSON → FastAPI /api/v1
                         ├─ data/ JSON / GeoJSON
                         └─ scripts/ Python 数据产物

## 职责边界

### 前端

- 加载 FastAPI 返回的稳定展示契约；
- 渲染地图、图例、指标和推荐队列；
- 处理中/日/英切换和点击交互；
- 展示来源、公式、不确定性与限制；
- 不包含文件系统路径映射，不直接读取 data/*.json；
- 不负责推荐队列的排序或公共设施汇总。

### FastAPI 后端

- 统一加载并按文件修改时间缓存 JSON/GeoJSON；
- 提供健康状态与文件数据目录；
- 提供字段、数值范围、bbox、排序和数量限制查询；
- 用 Python 生成坡地、道路、光伏、设施、走廊和交付候选的推荐队列；
- 汇总客户展示需要的设施指标；
- 通过只读资产路径提供地图瓦片和遥感图像。

### Python 数据管线

现有下载、解析、联合分析与多尺度证据脚本均为 Python，并继续通过统一数据任务注册表被启动流程或用户命令调用。API 只读取其产物，不在请求时执行昂贵重建。

## 最小 API v1

| Method | Path | 说明 |
|---|---|---|
| GET | /api/v1/health | 数据集就绪状态与来源组数量 |
| GET | /api/v1/catalog | 文件目录、类型、记录数、更新时间 |
| GET | /api/v1/bootstrap | 展览前端一次加载所需的完整契约 |
| GET | /api/v1/datasets/{key} | 按稳定 key 读取单一数据集 |
| GET | /api/v1/features/{key} | where/equals/min/max/bbox/sort/limit 查询 |
| GET | /api/v1/recommendations/{analysis} | 服务端筛选和排序后的行动队列 |
| GET | /api/v1/assets/* | 本地瓦片、影像和其他只读二进制资产 |

OpenAPI 交互文档由 FastAPI 自动提供在 /docs。

## 当前存储决定

- 继续使用数个独立 JSON/GeoJSON；它们足以支撑当前数据量和只读 Demo。
- API 的稳定 dataset key 隔离了浏览器与文件路径，日后换存储不需要重写前端。
- 当前不引入 ORM、迁移或数据库 schema。
- 当出现高频增量更新、并发写入、复杂联表、客户权限或历史版本查询时，再评估 SQLite；更大规模或多租户场景再评估服务型数据库。

## 运行方式

terrai_spatial serve 在一个开发进程中启动两个独立监听端口：

- 4176：静态前端；
- 8000：FastAPI。

也可以分别使用 terrai_spatial frontend 与 terrai_spatial api 启动，方便后续独立部署。
