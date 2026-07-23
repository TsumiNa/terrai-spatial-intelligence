# PR1 Plan: Tile Generation Task

- Status: Planned
- Refactor: `osm-basemap-tiles`

## Goal

One offline command turns the pinned Kanto snapshot into a single PMTiles
building tileset, written into the gitignored data tree with a committed
manifest, and the real size/time are measured so the feasibility projection
becomes fact.

## Scope

- A generation script/task producing `data/osm/kanto_basemap/buildings.pmtiles`
  (z0–16) from the pinned Geofabrik snapshot the acquisition already uses.
  Prefer planetiler (reads the pbf directly); tippecanoe over the existing
  `data/osm/kanto_buildings/buildings.geojson` is the fallback and the quickest
  spike.
- Registered as a data task (network for the snapshot, `automatic=False`,
  gitignored product, only the manifest declared as output — the PMTiles is
  gigabyte-scale), mirroring the acquisition tasks.
- A committed `metadata.json`: snapshot date, feature count, tile count, zoom
  range, sha256, generation tool and version.
- Spike recorded in the completion note: actual PMTiles size and wall-clock, so
  the overview's projection is replaced by measurement.

## Non-goals

- Nothing serves the tiles yet (PR2). No roads/water/labels — buildings first.

## Acceptance

- The tileset generates end to end from the pinned snapshot; size and time
  recorded.
- `uv run python -m terrai_spatial validate` passes; `data status` shows the
  new task; CI unaffected (opt-in, gitignored).
