# PR2 Plan: Production-raster Fallback

- Status: Planned
- Refactor: `basemap-resilience`

## Goal

When the experimental vector tiles fail, the wide view degrades to GSI's
production raster 標準地図 instead of a blank map — without touching the OSM
detail layer, foundation overlays or analyses.

## Scope

- A hidden raster source/layer for `https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png`
  (z0–18, production endpoint, same attribution terms) through the existing
  raster plumbing in `composeStyle`.
- Activation, two stages:
  - a build/ops switch that starts the app on the raster basemap outright
    (the operational answer if GSI announces a bvmap change);
  - automatic promotion when vector-tile requests fail repeatedly within a
    window (MapLibre error events), with a console note stating the fallback
    is active. Measured thresholds, no flapping (one-way per session).
- e2e: with vector tile requests blocked, the map still renders streets from
  the raster fallback and the OSM detail layer keeps serving buildings.

## Non-goals

- No UI for the fallback beyond the attribution line (it is an availability
  measure, not a basemap option); no self-hosted tiles.

## Acceptance

- Blocking `experimental_bvmap` in a test leaves a fully navigable map:
  raster streets wide, OSM building objects past the handover, analyses
  intact.
- Normal operation is byte-identical (the fallback stays hidden); visual
  baselines untouched.
