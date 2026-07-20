# PR2 Plan: App Shell and Compile-Time i18n

- Status: Planned
- Refactor: `maplibre-migration`
- PR: #2

## Goal

Port everything that is not the map — navigation, metrics, action queues, the audit drawer, language switching — into the Svelte app, with translations checked at build time rather than by grep.

## Scope

1. Port the module navigation, region switching, portfolio metrics and the per-module action queues, reading from the typed `/bootstrap` client.
2. Port the audit drawer, preserving all three record kinds (`raw`, `calculation`, `model`) and every source, formula and limitation field.
3. Replace the `i18n.js` dictionary with compile-time messages carrying typed identifiers. Missing translations become build errors.
4. Settle the UI source language question — Simplified Chinese as today, or English to match the documentation policy — and record the answer in the overview.
5. Playwright coverage for navigation, language switching, queue ordering, and opening an audit record.
6. The map area renders a placeholder.

## Non-goals

No map library. No layer rendering. The old frontend remains the served default.

## Implementation notes

- The audit drawer is the highest-risk port. Its content is derived client-side from feature properties; a value that loses its provenance path is a product regression, not a UI bug.
- Translation identifiers are a rename of every UI string. Do it in this stage, not spread across later ones.
- Queue ordering comes from the server. Do not re-sort client-side; that would fork the ranking logic.

## Acceptance

- Every panel present in the current exhibition renders with the same values.
- Switching among Chinese, Japanese and English changes all visible text with no reload.
- A deliberately removed translation fails the build.
- Playwright covers navigation, language switching and one audit record end to end.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
