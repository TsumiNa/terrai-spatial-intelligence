# PR1 Plan: Kanto OSM Building Acquisition

- Status: Completed
- Refactor: `osm-highzoom-detail`
- PR: #65

## Completion record

- Full acquisition: **5,371,292 buildings / 3.1 GB / 3m20s** including the ~400 MB
  snapshot download; extract timestamp `2026-01-01T21:21:30Z` read from the PBF
  header as the vintage.
- Real data promptly justified the honesty counter: 14 degenerate OSM
  multipolygons are rejected by the geometry factory, skipped, and recorded in the
  manifest as `invalid_geometries_skipped`.
- pyosmium v4 wrinkle worth remembering: `SimpleWriter` silently writes empty
  objects from plain dicts — the test fixture must use `osmium.osm.mutable`
  objects, and the tag filter passed to `with_areas` does not exempt the caller
  from checking `building` in tags.

## Goal

One command acquires every OSM building footprint inside the mainland-Kanto
acquisition window from a pinned Geofabrik extract, and writes a streaming GeoJSON
product with per-feature identity and provenance into the gitignored data tree.

## Scope

- `scripts/fetch_osm_kanto_buildings.py`: download the Geofabrik Kanto extract
  (`kanto-latest.osm.pbf`, ~400 MB) with the pipeline http helper; walk it with
  `pyosmium` (new locked dependency via `uv add`), keep closed ways and
  multipolygon relations tagged `building=*` whose bbox intersects
  `MLIT_ACQUISITION_BOUNDS["kanto"]`; write features one at a time through the
  streamed atomic writer to `data/osm/kanto_buildings/buildings.geojson`, each
  carrying `osm_id`, `osm_type`, the `building` tag value, `name`/`levels` when
  present, and provenance (`terrai_source_url`, extract timestamp from the PBF
  header as `source_updated_at`, `retrieved_at`).
- A `metadata.json` manifest (counts, sha256, extract timestamp, scope statement).
  The script writes both the manifest and the streamed GeoJSON product, but only
  the manifest is *declared* as a task output for readiness checks — the product
  is expected in the hundreds of megabytes to a few gigabytes, and declared JSON
  outputs are parsed in full on every status check.
- `data_tasks.py`: register `osm_kanto` (network, automatic, `check_stale=False`),
  mirroring the `mlit` task; `.gitignore` gains `data/osm/kanto_buildings/`.
- Tests without network: tag/geometry filtering and provenance stamping against a
  small synthetic PBF fixture; manifest shape; bbox rejection.

## Non-goals

- Nothing reads the product yet (PR2). No roads/POI. No committed full product —
  the CI fixture arrives with the dataset registration in PR2.

## Acceptance

- The full acquisition runs locally end to end; feature count, product size and
  wall-clock are recorded in the completion note.
- `uv run pytest` and `terrai validate` pass with and without the product present.
