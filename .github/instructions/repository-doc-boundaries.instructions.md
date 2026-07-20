---
description: 'Use when creating, editing, or reorganizing repository documentation. Keep public and developer entrypoints distinct, classify docs into the fixed five-folder structure, and apply multilingual maintenance only to architecture, data, and summary.'
applyTo: '**/{README,CONTRIBUTING}.md,docs/**'
---

# Repository Documentation Boundaries

## Root entrypoints

- `README.md` is user-facing: product purpose, audience, installation, quick start, primary CLI/API usage, concise examples, and links to deeper documentation.
- `CONTRIBUTING.md` is developer-facing: repository layout, local development, testing, coding/documentation conventions, branch/PR workflow, and contribution expectations.
- Do not put internal architecture rationale, refactor history, or long evaluation reports in the root entrypoints. Link to the appropriate `docs/` document.
- Root `README.md` and `CONTRIBUTING.md` are English-only by default.

## Language policy

Only documents in `docs/architecture/`, `docs/data/`, and `docs/summary/` must exist as one semantic group. English is always the default, unsuffixed file:

- English canonical file: `name.md`
- Japanese file: `name.ja.md`
- Simplified Chinese file: `name.zh.md`

All three must link to one another near the title. Create, rename, move, and update all three in the same change. Keep meaning, status, links, diagrams, and commands aligned even when wording is not a literal translation.

Every other documentation location uses one English `.md` file by default. This includes root `README.md` and `CONTRIBUTING.md`, `docs/README.md`, `docs/refactor/`, and `docs/others/`. Do not create `.ja.md` or `.en.md` partners there unless a specific requirement justifies them; English is the unsuffixed canonical file.

## Fixed `docs/` structure

Only the English `docs/README.md` index may be placed directly under `docs/`. `docs/` contains exactly these five top-level directories; do not create another category:

1. `architecture/`
2. `refactor/`
3. `data/`
4. `summary/`
5. `others/`

### `docs/architecture/`

Store the currently valid system structure: component responsibilities, stable conceptual or runtime boundaries, data/control flow, and frontend–backend call structure. Architecture documents describe what is true now. Put migration steps and commit/PR history in `refactor/`, not here.

Architecture groups may remain directly under `docs/architecture/`, using `name.md`, `name.ja.md`, and `name.zh.md`.

### `docs/refactor/`

Use one independent folder per refactor: `docs/refactor/<refactor-name>/`. This folder fully replaces ADR; do not create `docs/adr/`.

Each refactor folder must contain an English `00-overview.md`. It records the context, problem, decision and rationale, considered alternatives, consequences, scope, non-goals, and the map of planned PR stages.

Put concrete English plans in files named `NN-topic-prXa.md`:

- `NN` is the planned PR sequence number, starting at `01`.
- Plans split within the same PR reuse `NN` and add parts such as `pr1a`, `pr1b`, and `pr1c`.
- The next PR advances the number, for example `02-topic-pr2.md`.
- Each plan states status, goal, scope, non-goals, implementation steps, and acceptance criteria.

Follow `.github/instructions/branch-and-pr-workflow.instructions.md` when mapping plans to branches, commits, and PRs.

### `docs/data/`

Document every dataset integrated into the Foundation Data Layer in its own trilingual dataset card. `docs/data/README.md`, `README.ja.md`, and `README.zh.md` form the catalog and are the only Markdown files allowed directly under `docs/data/`. Every dataset card has its own direct subfolder: `docs/data/<dataset>/README.md`, `README.ja.md`, and `README.zh.md`. Candidate datasets that are not integrated belong in an evaluation under `summary/`, not as integrated data cards.

Card structure and required content — including the `## Data description` section that describes format, coverage, resolution, vintage, fields, units, and known gaps — are specified in `.github/instructions/docs-data-cards.instructions.md`.

### `docs/summary/`

Store summaries produced while validating or evaluating features: experiments, comparisons, feasibility reviews, prototype-state reports, and important project decisions that are not refactor plans. A summary may explain evidence and conclusions, but must not become the normative current architecture or an active migration plan.

Every summary group must have its own direct subfolder: `docs/summary/<summary-name>/README.md`, `README.ja.md`, and `README.zh.md`. Do not place Markdown files directly under `docs/summary/`.

### `docs/others/`

Use English by default and only when a text genuinely cannot fit `architecture`, `refactor`, `data`, or `summary`. State in the document why the four primary categories do not apply. Reclassify it when a clearer home emerges.

## Change checklist

- In `architecture`, `data`, and `summary`, move or update all three language files together.
- Keep English in the unsuffixed `.md`; never use `.en.md` in a multilingual group.
- Keep each dataset card and summary group in its own direct subfolder with `README.*` filenames; the data catalog is the sole `docs/data/README.*` exception.
- Elsewhere, maintain the English `.md` file and do not require translation partners.
- Repair all repository links after a move; do not leave aliases in obsolete folders.
- Run the repository's documentation validation; multilingual discovery is automatic within the three scoped directories.
- For data cards, verify data description, source, project use, license, and commercial cautions; see `docs-data-cards.instructions.md`.
- For refactors, verify `00-overview` and plan filenames before opening or updating the PR.
