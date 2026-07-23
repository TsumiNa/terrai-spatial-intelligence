# PR2 Plan: Merged Tile Generation

- Status: Planned
- Refactor: `osm-basemap-tiles`

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
