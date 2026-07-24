# PR2 Plan: Merged Tile Generation

- Status: In progress — `scripts/merge_kanto_buildings.py` merges OSM (primary) +
  FGD (fill), **clipped to the `coverage.json` mesh footprint** (aligns OSM to the
  FGD range), keeping an FGD footprint only where no OSM footprint covers its
  representative point (STRtree). Baked schema `feature_id`/`footprint_source`/
  `building`; PMTiles z0–16 via **tippecanoe**; registered as `merged_tiles`. The
  real spike is recorded below; flips to Completed on merge.
- Refactor: `osm-basemap-tiles`

## Spike (real, 2026-07-24)

The merge + tile build over the actual acquisitions, on the owner's Mac (128 GB):

- **13,640,510 merged buildings** = **5,177,191 OSM** (primary; 194,101 clipped
  outside the coverage footprint) + **8,463,319 FGD fill**. FGD nearly doubled the
  fabric with buildings OSM lacked; **4,850,720 FGD footprints were dropped** where
  OSM already covered the ground, so the layer never double-draws.
- **PMTiles z0–16: 1.1 GB** (`buildings.pmtiles`, valid PMTiles v3); merged
  line-delimited GeoJSON intermediate: 4.9 GB (gitignored).
- **Wall-clock ~29 min**, peak RAM 4.25 GB — a comfortable one-time offline batch.
  (The overview projected 300–700 MB for OSM-only; the government fill roughly
  doubles the building count, hence ~1.1 GB — still a static, CDN-served,
  range-request PMTiles with near-zero serving CPU.)
- Known limitation (documented refinement): the OSM/FGD dedup uses a
  representative-point-in-OSM test, fast and correct for the common case; offset
  digitisation in dense blocks can leak a few doubles/gaps. An area-overlap
  threshold is the follow-up if spot-checks show it matters.

## Goal

One offline command merges the pinned OSM and FGD building sources (OSM primary,
FGD filling OSM's gaps) and generates a single PMTiles building tileset with the
baked schema, written into the gitignored data tree with a committed manifest —
and the real size and time are measured so the feasibility projection becomes
fact.

## Scope

- A merge step that combines `data/osm/kanto_buildings/buildings.geojson`
  (primary) with `data/fgd/kanto_buildings/buildings.geojson` (fill): an FGD
  footprint is kept only where no OSM building already covers that ground
  (spatial-join deduplication), so OSM identity and tags win and the government
  data only fills the empty areas. Every output feature carries the baked schema
  from the overview: `feature_id` (`osm:<id>` / `fgd:<id>`), `footprint_source`
  (`osm` | `fgd`), and `building` class. `height`/`height_source` are added in
  PR4; PR2 bakes no height.
- Tile generation to `data/tiles/kanto_buildings/buildings.pmtiles` (z0–16).
  Prefer planetiler; tippecanoe over the merged GeoJSON is the fallback and the
  quickest spike.
- Registered as a data task (`automatic=False`, gitignored product, manifest the
  only declared output — the PMTiles is gigabyte-scale), depending on PR1's FGD
  source and the existing OSM source.
- A committed `metadata.json`: both source vintages, merged feature count, the
  OSM/FGD split (how many footprints each source contributed), tile count, zoom
  range, sha256, generation tool and version.
- Spike recorded in the completion note: actual merge time, PMTiles size and
  wall-clock, and the OSM-vs-FGD contribution split, so the overview's projection
  is replaced by measurement.

## Non-goals

- Nothing serves the tiles yet (PR3). No heights/extrusion (PR4). No
  roads/water/labels — buildings first.

## Implementation steps

1. Implement the spatial-join merge (OSM primary, FGD fill) emitting one merged
   GeoJSON (or a stream planetiler consumes directly) with the baked schema.
2. Generate the PMTiles z0–16 from the merged features; verify a low-zoom tile
   generalizes and a z16 tile carries the per-building properties.
3. Register the task; write and commit `metadata.json` including the source
   split; gitignore the tileset.
4. Record the spike numbers in this plan's completion note and the history entry.

## Acceptance

- The tileset generates end to end from the two pinned sources; merge time,
  size, wall-clock, and OSM/FGD split recorded.
- Every tile feature carries `feature_id`, `footprint_source`, and `building`;
  FGD footprints appear only where OSM had none (spot-checked in a thin
  suburban/rural area).
- `uv run python -m terrai_spatial validate` passes; `data status` shows the new
  task; CI unaffected (opt-in, gitignored).
