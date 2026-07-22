# PR6 Plan: Surface the Kanto Coverage

- Status: In progress
- Refactor: `kanto-foundation-coverage`
- PR: #56

## Completion record (to flip to Completed once #56 merges)

- The registry extent is the acquisition window verbatim; the sheet-gap reality is
  stated where the extent is declared, and a window inside a gap reports `empty`
  truthfully rather than `outside`.
- The edge-touching-window unit test kept its intent and moved to the Kanto
  window's western edge.
- All thirty card files updated in one pass with per-string assertions; the two
  sheet-based sources carry the partial-coverage caveat in all three languages.
- Verified against the coherent re-acquired store: webapp unit 113, Playwright 39
  (visual byte-stable), identity suite 8, `terrai validate` green.

## Goal

The exhibition UI requests foundation windows across mainland Kanto, and the ten MLIT
data cards describe the Kanto acquisition in all three languages without any
demonstration-context framing.

## Scope

- `webapp/src/lib/features/registry.ts`: `MLIT_EXTENTS` becomes the Kanto window from
  `terrai_spatial/pipeline/regions.py`, comment updated to name its source. Sapporo
  untouched.
- e2e and unit expectations that encode the former demo framing (for example
  `terrai_region` values) follow the single scope.
- `docs/data/mlit-*/README{,.ja,.zh}.md`: coverage statements describe the Kanto
  window and the four prefectures, with the partial-sheet reality for the 1:50k land
  classification (15 digitised Kanto sheets) and the 2011 land-history package (14
  Kanto sheets). Vintage, licence and caution sections stay as the source states
  them.

## Non-goals

- No zoom-floor or styling changes; no new layers; no i18n key additions.

## Acceptance

- `cd webapp && npm run build && npm run test` and the Playwright suites pass against
  the Kanto-scope store.
- Visual baselines: the map pane is masked in the visual suite, so baselines are
  expected byte-stable; if CI disagrees, regenerate per the platform-split procedure
  and show the diffs in the PR.
- `terrai validate` passes (trilingual partners and section headings intact).
