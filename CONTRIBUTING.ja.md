# TerrAI 開発・Contribution

[中文](CONTRIBUTING.md) | [日本語](CONTRIBUTING.ja.md) | [English](CONTRIBUTING.en.md)

## Local 開発

```bash
uv sync
uv run python -m terrai_spatial validate
uv run python -m unittest discover -s tests -v
uv run python -m terrai_spatial serve --port 4176
```

frontend は `frontend/`、FastAPI と data service は `terrai_spatial/`、直接実行可能な data task は `scripts/`、file foundation data と cache は `data/` にあります。

## 文書規約

Project 文書は `docs/` の `architecture`、`refactor`、`data`、`summary`、`others` の五分類に置きます。各文書には中文 `.md`、日本語 `.ja.md`、English `.en.md` が必要です。詳細な境界と命名は [repository-doc-boundaries.instructions.md](.github/instructions/repository-doc-boundaries.instructions.md) を参照してください。

追加・更新後は `uv run python -m terrai_spatial validate` を実行します。validator は文書を自動発見し、手書き list は不要です。三言語 partner、directory boundary、language navigation、refactor naming、data card 必須 section を検証します。

## Branch と PR

[branch-and-pr-workflow.instructions.md](.github/instructions/branch-and-pr-workflow.instructions.md) に従います。一つの目的を一つの branch/PR に対応させ、同じ目的の PR があれば同じ branch に追記し、review 可能な段階を `docs/refactor/<refactor>/` に記録します。
