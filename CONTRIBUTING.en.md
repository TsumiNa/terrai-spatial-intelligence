# TerrAI Development and Contribution

[中文](CONTRIBUTING.md) | [日本語](CONTRIBUTING.ja.md) | [English](CONTRIBUTING.en.md)

## Local development

```bash
uv sync
uv run python -m terrai_spatial validate
uv run python -m unittest discover -s tests -v
uv run python -m terrai_spatial serve --port 4176
```

The frontend lives in `frontend/`; FastAPI and data services in `terrai_spatial/`; directly executable data tasks in `scripts/`; and file-backed foundation data and caches in `data/`.

## Documentation convention

Project documentation belongs in the five `docs/` categories: `architecture`, `refactor`, `data`, `summary`, and `others`. Every document requires a Chinese `.md`, Japanese `.ja.md`, and English `.en.md` version. See [repository-doc-boundaries.instructions.md](.github/instructions/repository-doc-boundaries.instructions.md) for detailed boundaries and naming.

Run `uv run python -m terrai_spatial validate` after adding or changing documentation. The validator discovers documents automatically—there is no handwritten file list—and checks language partners, directory boundaries, language navigation, refactor naming, and required data-card sections.

## Branches and PRs

Follow [branch-and-pr-workflow.instructions.md](.github/instructions/branch-and-pr-workflow.instructions.md): use one branch/PR per objective; continue on an existing branch when its PR has the same objective; and record reviewable stages in the relevant `docs/refactor/<refactor>/` plan.
