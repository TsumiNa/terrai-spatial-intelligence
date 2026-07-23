# PR2 Plan: Production-raster Fallback

- Status: Completed
- Refactor: `basemap-resilience`

> Implementation note: activation must NOT gate on the map `"load"` event —
> when the vector source is dead, `"load"` (first complete render) may never
> fire, so the fallback would never show. Both triggers avoid it: the ops switch
> bakes the layer's visibility into the style before construction, and the
> auto-promotion path shows the layer once the *style* is loaded
> (`isStyleLoaded`/`styledata`), independent of tiles. Auto threshold: 4 vector
> tile errors within a 20 s window, one-way per session.

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

## Implementation steps

1. Add the production `std` raster source and a hidden raster layer through
   the existing plumbing in `composeStyle`.
2. Wire the ops switch (build-time flag or query parameter) that starts the
   app on the raster basemap.
3. Subscribe to MapLibre tile-error events for the vector source; measure a
   failure threshold that avoids flapping, then promote one-way per session
   with a console note.
4. e2e: block `experimental_bvmap` requests, assert streets render from the
   raster fallback and `osmBuildings` windows keep serving.
5. Confirm normal operation is unchanged (fallback hidden, baselines stable).

## Non-goals

- No UI for the fallback beyond the attribution line (it is an availability
  measure, not a basemap option); no self-hosted tiles.

## Acceptance

- Blocking `experimental_bvmap` in a test leaves a fully navigable map:
  raster streets wide, OSM building objects past the handover, analyses
  intact.
- Normal operation is byte-identical (the fallback stays hidden); visual
  baselines untouched.
