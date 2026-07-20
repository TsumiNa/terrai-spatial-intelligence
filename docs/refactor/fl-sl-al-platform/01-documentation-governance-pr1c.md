# PR1c Plan: Documentation Information Architecture and Scoped Multilingual Governance

- Status: Completed
- Refactor: `fl-sl-al-platform`
- PR: #1 / part c

## Goal

Remove overlap among root `architecture/`, `docs/adr/`, flat refactor records, and root evaluation documents; establish a sustainable five-category docs structure with multilingual maintenance limited to customer- and evidence-facing documentation.

## Plan

1. Merge system-call documentation into `docs/architecture/`.
2. Replace ADRs with one refactor folder and `00-overview` per refactor.
3. Split integrated FL sources into per-dataset cards under `docs/data/`.
4. Move evaluation, validation, and non-refactor decisions to `docs/summary/`.
5. Use `docs/others/` only when no category fits.
6. Slim the root README and put development workflow in CONTRIBUTING.
7. Require trilingual groups only in `architecture`, `data`, and `summary`; use English elsewhere by default.
8. Update repository instructions, references, and automated validation.

## Acceptance

- `docs/` contains only README plus architecture/refactor/data/summary/others.
- No `docs/adr/` or root `architecture/` remains.
- Every integrated FL dataset has an independent trilingual card.
- Every refactor folder starts with an English `00-overview.md`; PR files follow `NN-topic-prXa.md`.
- Root, refactor, and others documentation is not subject to blanket trilingual validation.
