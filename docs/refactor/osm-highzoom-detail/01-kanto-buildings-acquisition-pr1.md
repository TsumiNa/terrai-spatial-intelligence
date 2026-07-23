# PR1 Plan: Kanto OSM Building Acquisition

- Status: Planned
- Refactor: `osm-highzoom-detail`

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
- A `metadata.json` manifest (counts, sha256, extract timestamp, scope statement),
  declared as the task's only output — the product is expected in the hundreds of
  megabytes to a few gigabytes, and readiness checks must stay cheap.
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
