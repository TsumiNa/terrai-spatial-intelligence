# TerrAI Documentation Index

`docs/` uses only the following five categories. No document other than this index belongs directly under `docs/`.

| Directory | Content | Language policy |
|---|---|---|
| [`architecture/`](architecture/FRONTEND_BACKEND.md) | Current system boundaries, component responsibilities, and call structure | English default, Japanese and Chinese partners |
| [`refactor/`](refactor/fl-sl-al-platform/00-overview.md) | Context, rationale, and concrete PR-staged plans for each refactor | English by default |
| [`data/`](data/README.md) | Root catalog plus one subfolder per integrated FL dataset, covering source, use, license, and commercial cautions | English default, Japanese and Chinese partners |
| [`summary/`](summary/2026-07-prototype-state/README.md) | One subfolder per validation, evaluation, or important non-refactor decision group | English default, Japanese and Chinese partners |
| [`others/`](others/) | Text that genuinely fits none of the four categories above; explain why it belongs here | English by default |

Only `architecture/`, `data/`, and `summary/` require trilingual document groups. Their unsuffixed `.md` is English, with `.ja.md` and `.zh.md` partners. Data and summary groups each occupy their own subfolder. Root documents, this index, `refactor/`, and `others/` use English-only `.md` files unless a specific need justifies additional translations. See [repository-doc-boundaries.instructions.md](../.github/instructions/repository-doc-boundaries.instructions.md) for the complete rules.
