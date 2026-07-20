# PR1a 计划：建立 FL → SL → AL 概念边界

[中文](01-concept-layers-pr1a.md) | [日本語](01-concept-layers-pr1a.ja.md) | [English](01-concept-layers-pr1a.en.md)

- 状态：Completed
- 所属重构：`fl-sl-al-platform`
- PR：#1 / part a

## 目标

建立唯一的 FL、SL、AL 定义，明确 observed / synthetic / unresolved、多尺度 missing、证据质量闸门及当前成熟度，避免把 AL 启发式分数称为模型预测。

## 范围

1. 编写三层概念架构及 Mermaid 总览。
2. 复核 `geo_pfn` 稀疏上下文实验，限定其为机制证据。
3. 将 GSI、OSM、横滨开放数据、NASA POWER、TEPCO、Satellite Embedding 映射到 FL。
4. 明确当前横滨/茂原地表 SL 数量为 0。
5. 建立概念契约测试。

## 非目标

不定义 schema、层间 API、数据库、模型注册、客户权限或生产地表模型。

## 验收

- 三层定义、替代方案、后果与非目标集中在 `00-overview` 和 `docs/architecture/FL_SL_AL_CONCEPT.md`。
- AL 风险、适宜性、容量代理没有被标记为 SL。
- 中日英版本语义一致并通过文档验证。
