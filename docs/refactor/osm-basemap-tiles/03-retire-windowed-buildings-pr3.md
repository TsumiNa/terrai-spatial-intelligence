# PR3 Plan: Retire the Windowed Buildings Path

- Status: Planned
- Refactor: `osm-basemap-tiles`

## Goal

Buildings are one source at every zoom: the tile layer carries the clickable
`osm_id` and properties, so the windowed `osmBuildings` client, its endpoint
usage, and its place in the store are removed — no per-request building query
remains.

## Scope

- Clickability from the tiles: PR1 bakes `osm_id`, the kept tags and provenance
  into the tile feature properties; this PR resolves clicks against those baked
  properties with MapLibre `queryRenderedFeatures`, opening the same raw audit
  record the windowed popup produced. No API call.
- Remove the frontend windowed `osmBuildings` layer, the z16 `maxzoom` clamp on
  the GSI building layers, and the handover logic — the tile source spans all
  zooms.
- Drop `osmBuildings` from the served datasets and the store build (it is no
  longer queried), reclaiming the store's largest collection (~3.1 GB) and the
  dataset that carried the unwindowed full-scan risk. The acquisition script
  and the pinned snapshot stay — they feed tile generation.
- Data card and registry updated: the building layer's home is the tileset, not
  the windowed endpoint.

## Non-goals

- No change to the MLIT/analysis windowed layers or the `/api/v1/features`
  endpoint itself — other datasets keep using it.
- No change to imagery/hillshade/slope.

## Acceptance

- Clicking any building at any zoom opens its audit record from tile
  properties, with no `/api/v1/features/osmBuildings` request.
- `git`/store no longer carry `osmBuildings`; `terrai validate` and the store
  build pass; the e2e handover/click suites pass against the tile source.
- Offline: with the GSI vector host blocked, buildings still render and remain
  clickable from the local tiles, and no `/api/v1/features/osmBuildings` request
  is made. (The app still loads `/bootstrap`; only the building query path is
  gone, so this is not a full API blackout.)
