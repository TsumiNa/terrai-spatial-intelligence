# TerrAI 开发与贡献

[中文](CONTRIBUTING.md) | [日本語](CONTRIBUTING.ja.md) | [English](CONTRIBUTING.en.md)

## 本地开发

```bash
uv sync
uv run python -m terrai_spatial validate
uv run python -m unittest discover -s tests -v
uv run python -m terrai_spatial serve --port 4176
```

前端位于 `frontend/`，FastAPI 与数据服务位于 `terrai_spatial/`，可直接执行的数据任务位于 `scripts/`，文件型基础数据及缓存位于 `data/`。

## 文档约定

项目文档集中在 `docs/` 的 `architecture`、`refactor`、`data`、`summary`、`others` 五类中。每份文档必须同时提供中文 `.md`、日文 `.ja.md` 与英文 `.en.md`。详细边界与命名规则见 [repository-doc-boundaries.instructions.md](.github/instructions/repository-doc-boundaries.instructions.md)。

新增或修改文档后运行 `uv run python -m terrai_spatial validate`。校验器会自动发现文档，不需要维护手写文件清单；它会检查三语伙伴、目录边界、语言导航、refactor 命名和数据卡必需章节。

## 分支与 PR

遵循 [branch-and-pr-workflow.instructions.md](.github/instructions/branch-and-pr-workflow.instructions.md)：一个目标对应一个 branch/PR；已有同目标 PR 时继续在原分支提交；把可审查阶段写入对应 `docs/refactor/<refactor>/` 计划。
