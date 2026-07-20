# TerrAI Spatial Intelligence

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

TerrAI 是面向清洁能源与气候韧性的空间决策演示平台。它把公开基础数据、可追溯的增强证据和场景分析组合起来，用地图与行动队列回答“哪里应优先核查、为什么、证据是否可靠”。

当前 Demo 覆盖横滨的坡地暴露与道路/设施韧性，以及茂原的光伏选址和跨模块联合分析。所有核心指标均可查看来源、公式、模型状态与限制；界面支持中、日、英即时切换。

## 快速启动

需要安装 [uv](https://docs.astral.sh/uv/)，无需数据库或付费数据服务：

```bash
uv run python -m terrai_spatial serve --port 4176
```

打开：

- 展示界面：`http://127.0.0.1:4176/`
- FastAPI 文档：`http://127.0.0.1:8000/docs`

首次在线启动会检查并补齐可自动获取的数据，再重建缺失或过期的派生结果。严格离线运行可加 `--offline`。

## 文档入口

- [产品与运行状态](docs/summary/2026-07-prototype-state.md)
- [系统架构](docs/architecture/FRONTEND_BACKEND.md)
- [FL → SL → AL 概念](docs/architecture/FL_SL_AL_CONCEPT.md)
- [已接入数据与许可](docs/data/README.md)
- [重构计划](docs/refactor/fl-sl-al-platform/00-overview.md)
- [开发与贡献](CONTRIBUTING.md)

本项目当前是用于客户交流和技术验证的 Prototype；排序结果是筛查与尽调入口，不替代工程、许可、并网或投资决策。
