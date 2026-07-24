# PR3 Plan: Basemap Integration

- Status: In progress — the merged PMTiles renders as a MapLibre vector fill (in
  the neutralized-GSI gray) below the z16 handover, replacing GSI's building
  texture **inside the coverage footprint**; the `pmtiles` protocol is registered
  and the tile URL is configurable (`?buildings=`, default `/basemap/buildings.pmtiles`,
  an R2/minio/GCS URL in production). Adds the owner's **out-of-service boundary**:
  at building zoom, when the viewport lies wholly outside `coverage.json` the tiles
  hide, GSI's own buildings render as the fallback, and a trilingual badge shows.
  Both attributions (ODbL + 基盤地図情報) render. A 3.7 MB fixture PMTiles + the
  coverage footprint are served from `webapp/public/basemap/` for dev and e2e.
- Refactor: `osm-basemap-tiles`

## Out-of-service boundary (owner addition, 2026-07-24)

The plan below neutralizes GSI's buildings where the tiles show; the owner refined
this to a **coverage-aware** swap so panning outside mainland Kanto does not read as
an empty map. At building zoom (≥ z13), the map tests the viewport against the
served coverage footprint (`coverage.ts`): **inside** coverage it shows our tiles
and hides GSI's buildings (no double-draw, same gray); **wholly outside** it hides
our (empty) tiles, lets GSI's building texture render as the fallback, and shows an
"out of service" badge. The GSI-vs-tiles toggle is factored out of the terrain/pitch
path so the per-`moveend` coverage check never re-enters MapLibre's camera ease.

## Goal

The wide view renders dense, complete building fabric at every zoom from the
self-built merged tiles, replacing GSI's building texture below the z16 handover,
while the windowed clickable OSM objects continue above it — one seamless
building experience, available offline, with no empty areas where OSM was thin.

## Scope

- Serve the PMTiles (static file + HTTP range, optionally behind a CDN) and add
  it to the map style as a vector source; its building layer takes the place of
  the neutralized GSI building texture below the handover, in the same gray so
  crossing z16 to the windowed objects reads as continuity.
- Style keyed on the baked schema: `footprint_source` and `building` drive the
  KuniJiban-style differentiation (outline weight, colour, optional hatch) so
  government-filled and OSM footprints are legible without re-baking.
- Keep clickability where the tiles already carry ids: `feature_id` baked into
  tile features resolves the audit record without an API call (full retirement of
  the windowed path is PR5).
- Attribution: both credits render wherever the fabric shows — ODbL "©
  OpenStreetMap contributors" and the GSI 基盤地図情報 attribution + 加工表示.
- Offline proof: with the GSI vector-tile host blocked, the wide-view building
  fabric still renders from the local tiles.

## Non-goals

- No change to imagery/hillshade/slope (live GSI). No roads/water/labels yet.
- No removal of the windowed z16+ layer; it stays for the clickable detail
  (PR5). No heights/extrusion yet (PR4).

## Implementation steps

1. Register the PMTiles source and building layer in the map style; place it
   under the handover, matching the neutralized-GSI gray.
2. Add the attribute-keyed style for `footprint_source`/`building`.
3. Wire the tile `feature_id` into the existing building-click path where
   available; keep the windowed popup as the z16+ source of record.
4. Add both attributions; add an offline check to the e2e suite.

## Acceptance

- `cd webapp && npm run build && npm run test` and the Playwright suites pass;
  survey-zoom screenshots show dense city fabric where it was sparse before —
  including a suburban/rural area that OSM-alone would have left empty.
- Blocking the GSI vector host leaves the building fabric intact; both
  attributions present; `uv run python -m terrai_spatial validate` green.
