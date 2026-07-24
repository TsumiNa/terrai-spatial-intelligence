# PR1 Plan: 基盤地図情報 Building Acquisition

- Status: Completed — the acquisition mechanism merged in #88 (URL fix #89); the
  owner then completed the registration-gated download, and this change clips it
  to mainland Kanto and commits the real `metadata.json` + `coverage.json`. The
  2026-04-30 FGD 建築物の外周線 yields **13,314,039 building footprints** across
  **180 mainland meshes** (29 Pacific-island meshes excluded), each feature
  tagged `footprint_source: "fgd"` + FGD id.
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

## Coverage — mainland Kanto only (data-derived)

The FGD download service sells 建築物の外周線 by **whole prefecture**, and 東京都
legally reaches deep into the Pacific. The real 2026-04-30 download (4 prefectures,
209 unique 2次メッシュ, 2.3 GB compressed) therefore included **29 island meshes** —
the Izu Islands, the Ogasawara/Bonin chain, and the remote outposts **Minamitorishima
(154°E)** and **Okinotorishima (20°N)**, 1000+ km out. Left in, they blow the coverage
bbox from mainland-Kanto scale to ~1600 km, which is meaningless for a mainland
exhibition (every analysis area — Yokohama, Mobara, Nihonbashi — is mainland).

So the task **clips to mainland** via `MAINLAND_BOUNDS`, keeping the **180 mainland
meshes** and dropping the 29 island meshes (count recorded in the manifest). The
retained meshes define the **coverage footprint**, emitted as a committed
`coverage.json` (mesh list + tight bbox ≈ `(138.63, 34.83, 140.88, 36.33)`). This
is the "redefined Kanto window" — derived from the real data, not the old hardcoded
rectangle — and it is the contract PR2's merge clips OSM to and PR3's map uses for
the out-of-service boundary. Mesh dedup handles the ~10 border meshes that appear in
more than one prefecture's download.

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
