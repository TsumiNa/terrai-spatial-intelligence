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

### Why one source is simpler than deduping two

Today buildings come from two heterogeneous sources: GSI's generalized
cartography below z16 and the windowed OSM data objects above it. Making them
coexist without double-drawing is not a matter of layer indexing — the two
have **non-corresponding geometry** (GSI symbols vs OSM footprints, no 1:1
match) and **different load lifecycles** (the map engine pulls GSI tiles; a
debounced, quantized windowed client pulls OSM), so a true "show GSI only
where OSM is absent" would be a per-building spatial join at render time —
expensive and imprecise. A single self-built OSM source removes the question
entirely: there is nothing to reconcile.

### The endgame this enables

Vector tiles carry feature properties, and MapLibre's `queryRenderedFeatures`
makes tile features clickable. So one PMTiles source can serve **both** the
wide-view fabric **and** the z16+ clickable objects — buildings become one
layer, clickable at every zoom, with **no per-request API path at all**. That
collapses the whole current stack (GSI building layers + neutralization + the
z16 `maxzoom` clamp + the windowed `osmBuildings` client + the handover logic)
into a single tile source, and retires the `osmBuildings` query endpoint —
which also removes the store's largest collection (3.1 GB) and the unwindowed
full-scan cliff that came with it. The windowed store stays the right tool for
the queryable, filterable, provenance-bearing evidence layers (MLIT,
analysis), which are small and benefit from live querying.

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
- **Monthly cost — depends heavily on the host, and the cheapest is near-free.**
  On GCP the bill is egress-driven: kiosk ~$5, small public ~$25–45, larger
  public ~$180–320. But that egress is the whole cost, and it is exactly what
  a zero-egress object store erases: **Cloudflare R2 charges $0 for egress**,
  so serving the PMTiles from R2 behind Cloudflare's CDN costs essentially only
  storage (~$0.015/GB·month → a ~1 GB tileset is a few cents a month) **regardless
  of traffic**. PMTiles is purpose-built for this — a single file served by
  HTTP range requests from any object store plus a CDN. Trades the GSI
  operational risk (free, no SLA) for near-zero, predictable cost plus offline
  capability and full version control.

Conclusion: **technically feasible, near-zero cost on a zero-egress host
(Cloudflare R2 + CDN), no runtime dependency added.** Awaiting the owner's
decision to execute.

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
- No self-hosted raster pyramid; vector tiles only.
- No change to the MLIT and analysis evidence layers — they stay on the
  windowed store, which is the right tool for queryable, scored, provenance-
  bearing data. Only the building **basemap** moves to tiles.

## Planned PRs

Ordered introduce → migrate → remove, so the map stays working at each step.

1. `01-tile-generation-pr1.md` — a data task that builds the PMTiles from the
   pinned snapshot, with a spike recording real size and time; gitignored
   product, committed manifest.
2. `02-basemap-integration-pr2.md` — serve the PMTiles as the wide-view
   building fabric under the handover, keep clickability, prove offline. The
   windowed `osmBuildings` layer still handles z16+ at this step.
3. `03-retire-windowed-buildings-pr3.md` — the tile source absorbs the z16+
   clickable objects (`queryRenderedFeatures` on baked-in `osm_id`), and the
   windowed `osmBuildings` client, its endpoint usage, and the dataset's place
   in the store are retired — one source, clickable at every zoom, no
   per-request building query.
