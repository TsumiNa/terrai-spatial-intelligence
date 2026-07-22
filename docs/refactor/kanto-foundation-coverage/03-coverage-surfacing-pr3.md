# PR3 Plan: Surface the Widened Coverage

- Status: Planned
- Refactor: `kanto-foundation-coverage`

## Goal

The exhibition UI requests foundation windows across all of mainland Kanto instead of
declining outside the two demo boxes, and the ten MLIT data cards state the two-scope
coverage honestly in all three languages.

## Scope

- `webapp/src/lib/features/registry.ts`: `MLIT_EXTENTS` becomes the single wide window
  `(138.65, 34.85, 140.95, 36.30)` from `terrai_spatial/pipeline/regions.py`, with the
  comment updated to name its source. The Sapporo extent is untouched. In an
  environment that has not fetched the wide cache, windows between the demo boxes now
  report `empty` (a truthful zero from the store) rather than `outside`; no e2e test or
  visual baseline asserts `outside`, and the demo views themselves sit inside both the
  old and new extents.
- `webapp/src/lib/features/registry_test.ts` (and any other test pinning extents):
  follow the new window.
- `docs/data/mlit-*/README.md` + `.ja.md` + `.zh.md` (ten cards, thirty files): the
  scope statements gain the wide acquisition — four-prefecture coverage for the
  per-prefecture and national sources, and the explicit partial-sheet reality for the
  1:50k land classification (15 digitised Kanto sheets) and the 2011 land-history
  package (14 Kanto sheets). Vintage, licence and caution sections stay as the source
  states them.

## Non-goals

- No zoom-floor or styling changes; no new layers.
- No i18n key additions — the windowed status copy is already layer- and
  region-neutral.
- No change to `data/external/source_registry.json` semantics.

## Acceptance

- `cd webapp && npm run build && npm run test` pass; Playwright e2e pass against the
  demo-scope store (CI's situation).
- Visual baselines are expected to be byte-stable (the demo views render identical
  data); if CI disagrees, regenerate per the platform-split procedure and show the
  diffs in the PR.
- `uv run python -m terrai_spatial validate` passes (trilingual card partners and
  section headings intact).
