---
description: 'Use when creating, editing, or reorganizing repository documentation. Keep public and developer entrypoints distinct, classify docs into the fixed five-folder structure, and maintain every document as a Chinese/Japanese/English group.'
applyTo: '**/{README,README.ja,README.en,CONTRIBUTING,CONTRIBUTING.ja,CONTRIBUTING.en}.md,docs/**'
---

# Repository Documentation Boundaries

## Root entrypoints

- `README.md` is user-facing: product purpose, audience, installation, quick start, primary CLI/API usage, concise examples, and links to deeper documentation.
- `CONTRIBUTING.md` is developer-facing: repository layout, local development, testing, coding/documentation conventions, branch/PR workflow, and contribution expectations.
- Do not put internal architecture rationale, refactor history, or long evaluation reports in the root entrypoints. Link to the appropriate `docs/` document.
- Root `README` and `CONTRIBUTING` are also trilingual groups.

## Language groups

Every Markdown document under `docs/`, plus root `README` and `CONTRIBUTING`, must exist as one semantic group:

- Simplified Chinese canonical file: `name.md`
- Japanese file: `name.ja.md`
- English file: `name.en.md`

All three must link to one another near the title. Create, rename, move, and update all three in the same change. Keep meaning, status, links, diagrams, and commands aligned even when wording is not a literal translation.

## Fixed `docs/` structure

Only `docs/README.md`, `docs/README.ja.md`, and `docs/README.en.md` may be files directly under `docs/`. `docs/` contains exactly these five top-level directories; do not create another category:

1. `architecture/`
2. `refactor/`
3. `data/`
4. `summary/`
5. `others/`

### `docs/architecture/`

Store the currently valid system structure: component responsibilities, stable conceptual or runtime boundaries, data/control flow, and frontend–backend call structure. Architecture documents describe what is true now. Put migration steps and commit/PR history in `refactor/`, not here.

### `docs/refactor/`

Use one independent folder per refactor: `docs/refactor/<refactor-name>/`. This folder fully replaces ADR; do not create `docs/adr/`.

Each refactor folder must contain a trilingual `00-overview` group. It records the context, problem, decision and rationale, considered alternatives, consequences, scope, non-goals, and the map of planned PR stages.

Put concrete plans in files named `NN-topic-prXa.md`, with matching `.ja.md` and `.en.md` files:

- `NN` is the planned PR sequence number, starting at `01`.
- Plans split within the same PR reuse `NN` and add parts such as `pr1a`, `pr1b`, and `pr1c`.
- The next PR advances the number, for example `02-topic-pr2.md`.
- Each plan states status, goal, scope, non-goals, implementation steps, and acceptance criteria.

Follow `.github/instructions/branch-and-pr-workflow.instructions.md` when mapping plans to branches, commits, and PRs.

### `docs/data/`

Document every dataset integrated into the Foundation Data Layer in its own trilingual dataset card. The card must include:

- source/publisher and acquisition endpoint;
- how the project uses it, including local outputs or transformations;
- license or governing terms;
- extra cautions for commercial use, redistribution, attribution, third-party rights, freshness, and fitness for decision-making.

`docs/data/README.*` is the catalog. Candidate datasets that are not integrated belong in an evaluation under `summary/`, not as integrated data cards.

### `docs/summary/`

Store summaries produced while validating or evaluating features: experiments, comparisons, feasibility reviews, prototype-state reports, and important project decisions that are not refactor plans. A summary may explain evidence and conclusions, but must not become the normative current architecture or an active migration plan.

### `docs/others/`

Use only when a text genuinely cannot fit `architecture`, `refactor`, `data`, or `summary`. State in the document why the four primary categories do not apply. Reclassify it when a clearer home emerges.

## Change checklist

- Move or update all three language files together.
- Repair all repository links after a move; do not leave aliases in obsolete folders.
- Run `uv run python -m terrai_spatial validate`; document discovery is automatic.
- For data cards, verify source, project use, license, and commercial cautions.
- For refactors, verify `00-overview` and plan filenames before opening or updating the PR.
