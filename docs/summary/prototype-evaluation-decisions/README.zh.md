# TerrAI 重构决策记录

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## FL → SL → AL 概念架构（2026-07-20）

TerrAI 的共享底座正式分为 Foundation Data Layer（FL）、Synthetic Data Layer（SL）和 Application Layer（AL）。当前开源/官方观测与不改变观测语义的确定性加工属于 FL；未来经过 held-out、校准和适用性闸门的稀疏补值属于 SL；现有坡地暴露、道路韧性、光伏选址及联合评分属于 AL。

该阶段只完成 Factor of Concept，不定义 schema、数据库或调度。后续客户展览重构增加了最小只读 API，但不改变三层概念边界。完整定义见 [`FL_SL_AL_CONCEPT.zh.md`](../../architecture/FL_SL_AL_CONCEPT.zh.md)，决策理由已归入英文 [`fl-sl-al-platform/00-overview.md`](../../refactor/fl-sl-al-platform/00-overview.md)。

## 客户展览 UI 与最小 FastAPI 分离（2026-07-20）

- 客户主界面移除 FL/SL/AL 成熟度与内部实验说明，改为功能入口、结果解释、服务可靠性和逐项审计。
- 静态前端移动到 frontend/，只通过 /api/v1 加载数据；不再直接读取 data/ 文件路径。
- FastAPI 负责文件缓存、健康状态、目录、GeoJSON 查询、汇总和推荐队列排序；数据重建仍由 Python 脚本与任务注册表负责。
- 当前 FL 继续使用独立 JSON/GeoJSON，不引入数据库；dataset key 为未来 SQLite 迁移保留前端隔离层。
- 详细边界见 [`FRONTEND_BACKEND.zh.md`](../../architecture/FRONTEND_BACKEND.zh.md)。

## 从三个 Claude Demo 吸收了什么

| Claude Demo | 并入 TerrAI 的部分 | 舍弃或改写的部分 |
|---|---|---|
| A1 保土谷风险概览 | “区域概览 → 对象下钻”的交互；100–300 m 决策区；来源与方法边界 | 91 个高程点插值成 60 m 表面的做法；不再把稀疏插值当成 DEM 精度 |
| A3 设施韧性 | 以真实公共设施作为商业行动对象；设施组合队列 | 文京区跨域样本、写死高程、把其他设施平均高程称为 TPI；改用横滨 2026 官方据点和同域对象连接 |
| B1 光伏资产暴露 | 面向投资/运营的队列、组合视角、从发现到尽调的动作语言 | 过时 WRI 324 站库、20 站样本、每站 3 点和 `<5 m` 低地区划；当前优先保留 METI/TEPCO 方向 |

## Google 数据取舍

- **Satellite Embedding**：年度、64 维、跨传感器；用于变化、相似性和未来少量标签迁移。PoC 已通过公开 COG 镜像真实接入，无需 Earth Engine。
- **Dynamic World**：数据许可开放，但 TerrAI 商业访问 Earth Engine 会产生计算费用。为保持零付费数据服务，已从 Demo、脚本和待接入队列移除；土地覆盖语义改为优先评估 ESA WorldCover / Sentinel-2 本地管线。

## 多尺度数据契约

1. 5–10 m 表面证据：GSI DEM、Satellite Embedding；未来可加本地处理的 Sentinel-2 / ESA WorldCover。
2. 对象资产：建筑、道路、官方设施、太阳能网格。
3. 100–300 m 邻域：服务需求、道路影响、设施缺口、证据支持率。
4. 区域/组合门槛：电网、许可数据缺口、项目队列。

每个输出至少携带：`evidence_status`、时间、空间支持率、是否参与评分、限制条件。

## 与 geo_pfn 稀疏上下文实验的关系

`TsumiNa/geo_pfn` 当前实验固定 48 个查询孔，从 192 个候选孔中抽取 3–192 个整孔上下文。坐标+深度特征下，geo-PFN 在 25–50 个孔的中等稀疏区间达到约 20 RMSE，比 TabICL 低约 3–6；极稀疏时没有稳定点预测优势，稠密时 HGBT/TabICL 仍是强基线。后续训练已将“真实特征使模型变差”修正为主要是训练不足：2M LCSG 随训练表增加由约 22.9 改善至 17.7，17M 在 N=25 的 LCSG 达约 19.0。剩余缺口集中在特征摄取、稀疏目标训练、区间锐度与跨站点验证，而不是简单增加一个“更真实”的先验。

因此平台只借用四项机制：相似对象的完整 coherent 上下文、按上下文密度和场景选择模型、所有推断保留不确定性、支持拒答。地下 Su 实验不会被转述成地表风险或遥感模块的精度证明。

## Demo → PoC → MVP 的验证闸门

| 阶段 | 可以做什么 | 不得声称什么 |
|---|---|---|
| Demo（当前） | 展示数据融合、证据状态、行动队列和离线可复现性 | 灾害概率、发电量、并网承诺、正式设施改造收益 |
| PoC | 客户提供少量标签；与 HGBT/空间基线做 held-out、跨区和消融验证；校准不确定性 | 未经独立验证的工程适用性 |
| MVP | 接入权限、版本、审计、监测和人工复核；把验证过的特征加入评分 | 用黑箱评分替代法定审查或工程判断 |
