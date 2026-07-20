# PR1b 计划：客户展示 UI 与 FastAPI 分离

[中文](01-exhibition-fastapi-pr1b.md) | [日本語](01-exhibition-fastapi-pr1b.ja.md) | [English](01-exhibition-fastapi-pr1b.en.md)

- 状态：Completed
- 所属重构：`fl-sl-al-platform`
- PR：#1 / part b

## 目标

把内部概念看板改造成客户能立即理解功能、结果、可靠性和追溯性的展示产品，同时建立最小的静态前端—FastAPI 边界。

## 范围

1. 客户首页改为项目机会、关键指标、地图、行动队列和一句话解释。
2. FL/SL/AL、Claude 对比和模型壳子退出客户导航。
3. 静态文件移动到 `frontend/`，只通过 `/api/v1` 读取数据。
4. Python 负责文件缓存、健康、查询、设施汇总和推荐排序。
5. FL 暂时继续使用独立 JSON/GeoJSON。

## 关键权衡

`/bootstrap` 降低 Demo 复杂度并支持离线展示，但不适合未来大规模数据；届时按模块、视窗和分页使用 `/features` 与 `/recommendations`。SQLite 只有在增量更新、并发写入、复杂联表或历史查询出现时才引入。

## 验收

- 客户界面不暴露内部成熟度。
- 前端不执行业务 filter/sort/reduce 或评分。
- 指标、队列和地图字段可审计。
- API、桌面、移动端和中日英界面通过测试。
