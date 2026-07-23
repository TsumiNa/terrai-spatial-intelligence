# OSM Self-built Basemap Tiles

- Status: Planned

## Context

The wide-view basemap streams live from GSI, and its building cartography is
sparse at survey zoom — so when a user zooms out to survey, the city fabric
outside an analysis patch reads as nearly empty. The windowed OSM building
layer (`osm-highzoom-detail`) fills this densely, but only at z16+; raw
per-feature GeoJSON cannot carry survey-zoom density (a z12 Tokyo window is
~348 MB). Survey-zoom density is exactly what tiles are for: generalized and
dropped per zoom level.

This refactor builds OSM building (and, later, road/water/label) **vector
tiles** from the pinned Kanto snapshot the project already acquires, so the
dense city fabric is available at every zoom — the standing hybrid-basemap
direction, with the wide view moving from GSI to self-built OSM tiles while
imagery stays live GSI.

## Feasibility (assessed 2026-07-23, recorded for the go decision)

Grounded in this repo's real data (Geofabrik `kanto-260101` snapshot,
5,371,292 buildings, 3.1 GB GeoJSON):

- **Preprocessing** — planetiler (OSM-native) or tippecanoe (GeoJSON-native):
  a Kanto buildings-only tileset z0–16 is a **3–15 minute offline batch**, one
  run per snapshot refresh, same discipline as every data acquisition.
- **Output** — a single **PMTiles** file, ~300–700 MB buildings-only (vs 3.1 GB
  raw); ~1–2 GB for a full basemap with roads/water/labels.
- **Serving load** — PMTiles is a static file served by HTTP range requests:
  **near-zero application CPU**, cacheable at a CDN edge. It *removes* the
  windowed-tile query load from the API rather than adding compute; `osm_id`
  can be baked into tile features so clicks resolve without an API call.
- **GCP monthly cost** — driven by egress, not CPU: kiosk ~$5, small public
  ~$25–45, larger public ~$180–320; storage and preprocessing negligible.
  Trades the GSI operational risk (free, no SLA) for a small, traffic-
  proportional bill plus offline capability and full version control.

Conclusion: **technically feasible, low and predictable cost, no runtime
dependency added.** Awaiting the owner's decision to execute.

## Decision

Generate OSM vector tiles from the pinned snapshot and serve them as the
wide-view building fabric, replacing GSI's building texture below the z16
handover (the windowed clickable OSM objects continue above it). Imagery,
hillshade and slope stay live GSI (production endpoints, no OSM equivalent).

Alternatives considered:

- *Do nothing (GSI live)* — free but sparse at survey zoom and no offline; the
  visible-fabric fix (#70) is the accepted interim, not the end state.
- *Lower the windowed handover* — rejected by measurement: a z14 window is
  ~20 MB, z12 ~348 MB; raw GeoJSON cannot do survey density.
- *Commercial basemap (Mapbox/MapTiler)* — per-1000-load SaaS, typically
  dearer than self-hosted static tiles at scale, and cedes control.

## Non-goals

- No change to imagery/hillshade/slope (stay live GSI production).
- No change to the z16+ windowed clickable OSM objects — this is the wide-view
  fabric; the two are complementary.
- No self-hosted raster pyramid; vector tiles only.

## Planned PRs

1. `01-tile-generation-pr1.md` — a data task that builds the PMTiles from the
   pinned snapshot, with a spike recording real size and time; gitignored
   product, committed manifest.
2. `02-basemap-integration-pr2.md` — serve the PMTiles as the wide-view
   building fabric under the handover, keep clickability, prove offline.
