# PR1c 计划：文档信息架构与三语治理

[中文](01-documentation-governance-pr1c.md) | [日本語](01-documentation-governance-pr1c.ja.md) | [English](01-documentation-governance-pr1c.en.md)

- 状态：Completed
- 所属重构：`fl-sl-al-platform`
- PR：#1 / part c

## 目标

消除根 `architecture/`、`docs/adr/`、扁平 refactor 记录和根级评估文档之间的重叠，形成可持续的五类 docs 结构，并保持所有文档中日英同步。

## 计划

1. 系统调用文档合并到 `docs/architecture/`。
2. 用每个 refactor 的独立 folder 与 `00-overview` 取代 ADR。
3. 按数据集拆分 `docs/data/` FL 数据卡。
4. 把评估、验证和非 refactor 决策移到 `docs/summary/`。
5. 只把无法分类的材料放到 `docs/others/`。
6. 精简根 README，把开发流程放入 CONTRIBUTING。
7. 更新 repository instructions、路径引用和自动验证。

## 验收

- `docs/` 顶层只包含 README 和 architecture/refactor/data/summary/others。
- 不存在 `docs/adr/` 或根 `architecture/`。
- 每个已接入 FL 数据集都有独立三语数据卡。
- 每个 refactor folder 以 `00-overview` 开头，PR 文件按 `NN-topic-prXa` 命名。
