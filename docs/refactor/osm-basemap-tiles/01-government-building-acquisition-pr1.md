# PR1 Plan: 基盤地図情報 Building Acquisition

- Status: In progress — the acquisition task, its GML parser, the committed
  `source_manifest.json` pin, the `fgd_kanto` registration, gitignore/validate
  wiring and the manual-download procedure are merged and verified against a
  synthetic FGD-schema fixture. Producing and committing the real `metadata.json`
  (feature count + per-archive sha256 + vintage) awaits the registration-gated
  FGD download, a documented manual owner step.
- Refactor: `osm-basemap-tiles`

## Goal

The 基盤地図情報 (FGD) building outlines for mainland Kanto are acquired as a
pinned, gitignored source with per-feature provenance, mirroring the existing
OSM acquisition — so the merge in PR2 has a complete government footprint layer
to fill OSM's gaps with.

## Scope

- A data task acquiring FGD building outlines (建築物 / 建築物の外周線) for the
  four mainland-Kanto prefectures (Tokyo, Kanagawa, Chiba, Saitama), matching
  the OSM acquisition's area. Source is the Fundamental Geospatial Data download
  service (JPGIS GML; user-registration gated, so the download is a pinned,
  documented manual step recorded like other registration-gated sources — the
  task verifies and normalizes the pinned archive rather than fetching it fresh).
- Normalize GML → GeoJSON footprints written to
  `data/fgd/kanto_buildings/buildings.geojson`, each feature carrying its FGD
  identifier and a `footprint_source: "fgd"` tag; `automatic=False`, gitignored
  product, manifest declared as output — same pattern as the OSM acquisition.
- A committed `metadata.json`: FGD publication vintage, prefecture list, feature
  count, sha256, source-service URL, and the licence line (測量法-exempt,
  attribution + 加工表示).
- A trilingual data card is **not** created here — FGD is not yet integrated as a
  served Foundation dataset; it is an intermediate build input. The source facts
  live in `docs/summary/government-3d-building-sources/`.

## Non-goals

- No merge and no tiles yet (PR2). No heights (that is PLATEAU, PR4). No change
  to any served layer or the map.

## Implementation steps

1. Add the acquisition/normalization task under the pipeline, reading the pinned
   GML archive and emitting one GeoJSON of footprints with FGD ids and
   `footprint_source`.
2. Record the pinned-snapshot provenance and licence in `metadata.json`;
   gitignore the GeoJSON, commit the manifest.
3. Document the manual download + pin procedure alongside the task, so a fresh
   checkout can reproduce the pinned input.
4. `data status` lists the new task; `terrai validate` passes.

## Acceptance

- The task produces `data/fgd/kanto_buildings/buildings.geojson` from the pinned
  source, feature count and sha256 recorded in the committed manifest.
- Every feature carries an FGD id and `footprint_source: "fgd"`.
- `uv run python -m terrai_spatial validate` passes; `data status` shows the new
  task; CI unaffected (opt-in, gitignored product).
