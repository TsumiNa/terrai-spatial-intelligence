# PR5 Plan: Retire the Windowed Buildings Path

- Status: Completed (#94) — the tile building layers are clickable (a building resolves
  its provenance from the baked properties — `feature_id`, `footprint_source`,
  `building`, `height`/`height_source` — with no API call), the z16 handover/clamp
  and the tile-layer `maxzoom` caps are removed (tiles span all zooms; re-baked to
  z17 for click fidelity), and `osmBuildings` is dropped from the served datasets +
  store. Clicks are gated to an inspection-zoom threshold (owner-tunable
  `BUILDING_CLICK_MIN_ZOOM = 16`, per owner feedback: no click when footprints are
  a few pixels), and deck analytics win a contested click (their audit drawer),
  buildings only on the background. The OSM acquisition + snapshot stay as tile
  inputs.
- Refactor: `osm-basemap-tiles`

## Note — click plumbing

deck's `MapboxOverlay` (interleaved: false) sits above MapLibre and consumes the
map's click, and its own `onClick` only fires on a picked deck feature. So a
background building click is detected from a `pointerdown`/`pointerup` pair (the
same window `pointerup` the box-select uses), deferring to `overlay.pickObject` so
an analytical/foundation feature still wins, then reading the tile layers with
`queryRenderedFeatures` over a small pick box. The click was verified firing with
correct baked properties; the e2e for the *interactive* click is impractical (the
demo analytics overlap the fixture at every reachable camera), so the popup
record is unit-tested (`buildingAuditRecord`) and the retirement is covered by the
tile-vs-windowed e2e.

## Goal

Buildings are one source at every zoom: the merged tile layer carries the
clickable `feature_id` and properties, so the windowed `osmBuildings` client, its
endpoint usage, and its place in the store are removed — no per-request building
query remains.

## Scope

- Clickability from the tiles at all zooms: PR2 already bakes `feature_id`, the
  kept tags, `footprint_source`, and (PR4) `height`/`height_source` into tile
  feature properties; this PR resolves clicks against those baked properties with
  MapLibre `queryRenderedFeatures`, opening the same raw audit record the
  windowed popup produced. No API call.
- Remove the frontend windowed `osmBuildings` layer, the z16 `maxzoom` clamp on
  the GSI building layers, and the handover logic — the tile source spans all
  zooms.
- Drop `osmBuildings` from the served datasets and the store build (it is no
  longer queried), reclaiming the store's largest collection (~3.1 GB) and the
  dataset that carried the unwindowed full-scan risk. The OSM acquisition script
  and the pinned snapshot stay — they feed tile generation (PR2).
- Registry and provenance updated: the building layer's home is the merged
  tileset, not the windowed endpoint. The audit popup shows `footprint_source`
  and `height_source`, so a viewer can tell OSM-vs-government footprint and
  measured-vs-estimated height at the point of inspection.

## Non-goals

- No change to the MLIT/analysis windowed layers or the `/api/v1/features`
  endpoint itself — other datasets keep using it.
- No change to imagery/hillshade/slope.

## Implementation steps

1. Move the building-click resolution fully onto `queryRenderedFeatures` against
   the baked tile properties at every zoom; delete the windowed popup path.
2. Remove the windowed `osmBuildings` layer, the `maxzoom` clamp, and the
   handover logic from the map config.
3. Drop `osmBuildings` from `FOUNDATION_DATASETS` and the store build; keep the
   acquisition + snapshot as tile inputs.
4. Update the data registry/cards; run the store build and full e2e.

## Acceptance

- Clicking any building at any zoom opens its audit record from tile properties
  — including `footprint_source` and `height_source` — with no
  `/api/v1/features/osmBuildings` request.
- `git`/store no longer carry `osmBuildings`; `uv run python -m terrai_spatial
  validate` and the store build pass; the e2e handover/click suites pass against
  the tile source.
- Offline: with the GSI vector host blocked, buildings still render and remain
  clickable from the local tiles, and no `/api/v1/features/osmBuildings` request
  is made. (The app still loads `/bootstrap`; only the building query path is
  gone, so this is not a full API blackout.)
