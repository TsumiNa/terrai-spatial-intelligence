# Self-built Merged Building Basemap Tiles

- Status: Completed — the full PR sequence merged (#88/#90 FGD acquisition + coverage,
  #91 OSM+FGD merge → PMTiles, #92 basemap integration + out-of-service boundary,
  #93 PLATEAU heights + 2.5D extrusion, #94 retire the windowed path). One
  self-hosted, offline-capable merged building tileset (13.64M buildings; 54.7%
  PLATEAU-measured heights), clickable at inspection zoom from the baked
  properties, with a coverage-aware out-of-service fallback.

## Context

The wide-view basemap streams live from GSI, and its building cartography is
sparse at survey zoom — so when a user zooms out to survey, the city fabric
outside an analysis patch reads as nearly empty. The windowed OSM building
layer (`osm-highzoom-detail`) fills this densely, but only at z16+; raw
per-feature GeoJSON cannot carry survey-zoom density (a z12 Tokyo window is
~348 MB). Survey-zoom density is exactly what tiles are for: generalized and
dropped per zoom level.

The naive fix — self-build tiles from OSM alone — trades one gap for another.
OSM building coverage is rich in dense cities but sparse in suburban and rural
Japan, so an OSM-only basemap would read emptier than the GSI cartography it
replaces. The government building data GSI's own cartography derives from is far
more complete, and — as the licence finding below confirms — it is available to
us on attribution terms.

So this refactor builds **one merged building tile source** from the pinned
snapshots the project acquires: OSM as the primary layer (identity and rich
tags), 基盤地図情報 filling OSM's gaps (nationwide completeness), and PLATEAU
heights joined in (real measured height where a municipality is modelled). One
complete, offline-capable tile set replaces the live-GSI building dependency —
no empty map, and no two-source double-drawing seam.

## Why a build-time merge is the right shape

Making GSI and OSM coexist at **render time** is the wrong path: their geometry
does not correspond (GSI symbols vs OSM footprints, no 1:1 match) and their load
lifecycles differ (the engine pulls GSI tiles; a debounced windowed client pulls
OSM), so "show government data only where OSM is absent" would be a per-building
spatial join every frame — expensive and imprecise.

Moved to **build time**, that same join is affordable and can be done once,
carefully, offline. The output is one consistent layer with a per-building
`footprint_source`, so at render time there is exactly one building inventory:
no double-draw, complete coverage (government data fills the OSM gaps, no empty
map), full offline capability, and honest provenance (measured height never
masquerades as estimated or vice versa). This is precisely the operation a
preprocessing step exists for.

## Licence — cleared

Confirmed against the official GSI approval-application Q&A (recorded in
`docs/summary/government-3d-building-sources/`): 基盤地図情報 is a 基本測量成果 but
is **explicitly exempt** from the 測量法 承認申請 requirement, together with the
GSI tiles. Downloading it, processing it into derived tiles, and distributing
them — commercially and offline — needs **no application**, only attribution
plus a processing note (加工表示). PLATEAU is CC-BY-style under its Site Policy
§3, the same terms the project already accepts for the integrated UC24 scenes.
The merged tiles carry a mixed licence (OSM ODbL + GSI content terms); both are
credited, and ODbL share-alike applies only if the merged **database** itself is
ever published (serving tiles does not trigger it). A final legal sign-off before
commercial launch is prudent — not because the finding is in doubt, but because
the decision warrants it.

## Two display modes this feeds

- **Map mode (2D / 2.5D) — this refactor.** The merged tiles are the wide-view
  building fabric at every zoom; 2.5D extrusion reads the baked height on the
  terrain surface (`fill-extrusion` over `setTerrain`).
- **Local 3D work mode — `local-3d-work-mode` (separate refactor).** Box-select
  loads high-fidelity PLATEAU 3D models on demand; it uses PLATEAU directly, not
  these tiles. The two are complementary: tiles give the fast, complete, wide
  map; PLATEAU models give the precise local scene.

## The baked tile schema

The dividing line for what a tile carries is **render, not analyse**: bake only
what the map needs to draw and identify a building. Analytical materials belong
in the FL store, not the tiles (see the boundary below). Buildings are baked as
one merged feature set; every baked value that can be measured or estimated rides
with a `*_source` tag so provenance is never lost:

- `feature_id` — `osm:<id>` where OSM-sourced, `fgd:<id>` where government-sourced.
  The join key back to the FL materials in the store.
- `footprint_source` — `osm` | `fgd`.
- `building` — class for styling and load priority. OSM's own `building` tag is
  already rich; GSI's 堅牢/高層 structural class is an optional later augment.
- `height` (metres) + `height_source` — `plateau` (real `measuredHeight`) |
  `osm_tag` (`height`/`building:levels`) | `estimate` (default). Height is baked
  because extrusion is a **render** need; it rides in high-zoom tiles and
  low-zoom tiles drop it (extrusion is a high-zoom feature).
- Provenance: snapshot date and licence per source.

Visual differentiation — outline weight, colour, hatch fill keyed on class and
`*_source` (the KuniJiban-style treatment the owner liked) — is **frontend style
on these attributes**, not baked, so it changes without re-baking. Re-baking is
a minutes-long offline batch, so enrichment fields (PLATEAU usage/age, the GSI
structural class, an `osm_id → plateau gml:id` crosswalk) are added by later PRs
that re-run the merge.

### What does NOT go in the tiles — the render/analyse boundary

DEM-derived analytical **materials** — `slope`, `relief`, `low_point`, `aspect`,
`curvature`, distance-to-water, and the like — are **not** baked into these
tiles. They are analysis inputs, not rendering inputs, and they belong in the
FL materials layer of the windowed store, keyed by `feature_id`, served by the
read API and joined to the tile geometry on the client (the same "geometry from
the tile, values from the API" split the windowed evidence layers already use).

Baking them here would be the wrong coupling: the basemap tiles are a
rarely-rebuilt CDN artifact optimised for drawing, while analytical materials
evolve with what the AL/SL layers need; folding them in would force a full tile
re-bake and CDN redeploy every time a material is added. The boundary keeps this:
**tiles carry render/identity; the store carries FL materials and analysis.**
Region-wide precomputation of those materials and the interactive AL/SL layers
that consume them are the `interactive-al-compute` refactor.

## Decision

Acquire 基盤地図情報 buildings for Kanto (a new government source), merge them with
the already-acquired OSM buildings offline (OSM primary, FGD fill), generate one
PMTiles set with the baked schema, and serve it as the building fabric —
replacing GSI's building cartography entirely, with PLATEAU heights and 2.5D
extrusion folded in, and the windowed `osmBuildings` path retired once the tiles
carry clickability. Imagery, hillshade and slope stay live GSI (production
endpoints, no OSM equivalent).

The move is staged (see the PR sequence): the map works at every step, the
merged tiles enter below the z16 handover with the windowed clickable objects
still above them, and only the last PR lets the tile source span all zooms and
retires the windowed layer.

Alternatives considered:

- *OSM-only tiles* — rejected: empty map in suburban/rural Japan, the very gap
  the government data closes.
- *Keep GSI live as a fallback under OSM tiles* — reintroduces render-time
  double-drawing wherever both have a building, and keeps the GSI dependency.
  The build-time merge removes both problems.
- *Lower the windowed handover instead of tiling* — rejected by measurement
  (z14 window ~20 MB, z12 ~348 MB); raw GeoJSON cannot do survey density.
- *Commercial basemap (Mapbox/MapTiler)* — per-1000-load SaaS, dearer at scale,
  and cedes control and offline capability.

## Feasibility and cost (assessed 2026-07-23)

Grounded in this repo's real data (Geofabrik `kanto-260101`, 5,371,292 OSM
buildings, 3.1 GB GeoJSON), plus the added 基盤地図情報 fill:

- **Preprocessing** — planetiler (OSM-native) or tippecanoe (GeoJSON-native): a
  Kanto buildings tileset z0–16 is a **3–15 minute offline batch**, one run per
  snapshot refresh, same discipline as every acquisition. The FGD fill and
  PLATEAU height join add a spatial-join step but stay within the same batch.
- **Output** — a single **PMTiles** file, ~300–700 MB buildings-only (vs 3.1 GB
  raw OSM); the government fill adds footprints in the thin areas but tiles
  generalize aggressively at low zoom, so the total stays in that band.
- **Serving** — PMTiles is a static file served by HTTP range requests: near-zero
  application CPU, cacheable at a CDN edge. It *removes* the windowed-tile query
  load rather than adding compute.
- **Cost** — on a zero-egress object store this is near-free: Cloudflare R2
  charges $0 for egress, so serving from R2 behind a CDN costs essentially only
  storage (~$0.015/GB·month → a ~1 GB tileset is a few cents/month) regardless
  of traffic. GCP's egress-driven bill (~$5 kiosk, ~$25–45 small public,
  ~$180–320 larger) is the alternative if a zero-egress host is not used.

## Non-goals

- No change to imagery/hillshade/slope (live GSI production).
- No self-hosted raster pyramid; vector tiles only.
- No change to the MLIT and analysis evidence layers — they stay on the windowed
  store, the right tool for queryable, scored, provenance-bearing data. Only the
  building **basemap** moves to tiles.
- No analytical materials in the tiles (slope/relief/low_point/aspect/…): those
  are FL materials for the store, joined by `feature_id` — the render/analyse
  boundary above. Their precomputation is `interactive-al-compute`.
- No PLATEAU 3D model rendering here — that is the local 3D work mode.

## Planned PRs

Ordered introduce → migrate → remove, so the map works at each step. Each cites
`docs/summary/government-3d-building-sources/` for the source facts.

1. `01-government-building-acquisition-pr1.md` — acquire 基盤地図情報 Kanto
   buildings as a pinned, gitignored source with per-feature provenance,
   mirroring the OSM acquisition.
2. `02-merged-tile-generation-pr2.md` — the offline merge (OSM primary + FGD
   fill) and PMTiles generation with the baked schema; a spike recording real
   size and time.
3. `03-basemap-integration-pr3.md` — serve the merged tiles as the wide-view
   fabric under the handover; clickability; prove offline. The windowed
   `osmBuildings` layer still handles z16+ at this step.
4. `04-plateau-height-extrusion-pr4.md` — join PLATEAU `measuredHeight` into the
   tiles (re-bake), add 2.5D `fill-extrusion` on the terrain surface, honest
   `height_source`.
5. `05-retire-windowed-buildings-pr5.md` — the tile source absorbs the z16+
   clickable objects (`queryRenderedFeatures` on baked ids); the windowed
   `osmBuildings` client, endpoint usage, and store collection are retired — one
   source, clickable at every zoom, no per-request building query.
