# PR1c Plan: Documentation Information Architecture and Trilingual Governance

[中文](01-documentation-governance-pr1c.md) | [日本語](01-documentation-governance-pr1c.ja.md) | [English](01-documentation-governance-pr1c.en.md)

- Status: Completed
- Refactor: `fl-sl-al-platform`
- PR: #1 / part c

## Goal

Remove overlap among root `architecture/`, `docs/adr/`, flat refactor records, and root evaluation documents; establish a sustainable five-category docs structure with synchronized Chinese, Japanese, and English.

## Plan

1. Merge system-call documentation into `docs/architecture/`.
2. Replace ADRs with one refactor folder and `00-overview` per refactor.
3. Split integrated FL sources into per-dataset cards under `docs/data/`.
4. Move evaluation, validation, and non-refactor decisions to `docs/summary/`.
5. Use `docs/others/` only when no category fits.
6. Slim the root README and put development workflow in CONTRIBUTING.
7. Update repository instructions, references, and automated validation.

## Acceptance

- `docs/` contains only README plus architecture/refactor/data/summary/others.
- No `docs/adr/` or root `architecture/` remains.
- Every integrated FL dataset has an independent trilingual card.
- Every refactor folder starts with `00-overview`; PR files follow `NN-topic-prXa`.
