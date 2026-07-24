# PR4 Plan: PLATEAU Height Join and 2.5D Extrusion

- Status: In progress — `fetch_plateau_kanto_buildings.py` distils PLATEAU LOD1
  `measuredHeight` for the modelled mainland-Kanto municipalities (125, all
  prefectures) into a points product, streaming CityGML straight out of each
  pinned CKAN zip (no disk extraction). The merge now bakes `height` +
  `height_source` by the three tiers (PLATEAU measured → OSM `building:levels` →
  class estimate) and the frontend adds a `fill-extrusion` layer read from the
  baked height, shown in the 2.5D view; PLATEAU joins the attribution. Real
  acquisition + re-bake spike recorded in the completion note.
- Refactor: `osm-basemap-tiles`

## Spike (real, 2026-07-24)

- **Acquisition:** 9,967,358 PLATEAU measured buildings across the **125** modelled
  mainland-Kanto municipalities (Tokyo 62, Saitama 49, Kanagawa 8, Chiba 6), ~1 h,
  `heights.geojson` 1.9 GB (gitignored). Peak disk one archive (~0.5 GB), not the
  tens of GB the full CityGML occupies.
- **Re-bake with the height join:** 13,640,510 buildings, ~33 min, peak RAM 7.3 GB.
  `height_source` split: **plateau 7,465,478 (54.7%)** · osm_tag 61,356 (0.4%) ·
  estimate 6,113,676 (44.8%). So over half the fabric now stands up at its
  surveyed height; the estimate share is the footprints outside a PLATEAU-modelled
  municipality (mostly FGD fill), and osm_tag is small because `building:levels` is
  sparse in Japanese OSM. PMTiles grew 1.1 → 1.21 GB with the height fields.

## Notes / deviations

- **CityGML, not FGB.** The plan assumed a FlatGeobuf/GeoJSON footprint
  derivative; the CKAN publishes only CityGML (+3D-Tiles/MVT) per municipality
  (~480 MB each). The acquisition therefore parses `(centroid, measuredHeight)`
  per building straight from the zip stream — all the merge's point-in-footprint
  join needs — and deletes each archive, so peak disk is one archive, not the
  tens of GB the full Kanto CityGML would occupy.
- **osm_tag = `building:levels`.** The OSM acquisition keeps `building:levels`
  (× 3 m/level), not a raw `height` tag; adding `height` to the OSM kept tags is a
  one-line follow-up that needs an OSM re-acquire, deferred.
- **Standard-basemap 2.5D has no terrain** (the basemap-view-modes rule), so the
  extrusion stands buildings up on the flat pitched ground rather than draping the
  DEM; buildings only render on the standard basemap, which carries no terrain.

## Goal

Buildings stand up on the terrain in 2.5D: PLATEAU `measuredHeight` is joined
into the merged tiles where a municipality is modelled, and the map extrudes
each footprint by its baked height on the terrain surface — with `height_source`
keeping measured heights honestly distinct from estimates.

## Scope

- Acquire PLATEAU LOD1 building footprints with `measuredHeight` for the modelled
  Kanto municipalities as a pinned, gitignored source (via the G-space
  Information Center / CKAN, the channel already used for UC24), mirroring the
  FGD acquisition (PR1). Provenance and PLATEAU Site Policy §3 licence recorded
  in its manifest.
- Extend the merge (PR2) to join height onto each building by spatial match:
  - `height` from PLATEAU `measuredHeight` where matched → `height_source: "plateau"`;
  - else from OSM `height`/`building:levels` tags → `height_source: "osm_tag"`;
  - else a class-based estimate → `height_source: "estimate"` (default).
  Height rides only in high-zoom tiles (z14+); low-zoom tiles omit it.
- Re-bake the PMTiles with the height fields; update `metadata.json` with the
  PLATEAU vintage and the match-rate split across the three `height_source`
  values.
- Frontend 2.5D: a `fill-extrusion` building layer reading `height`, rendered on
  the terrain surface (`fill-extrusion-base` following the DEM so buildings sit
  on the relief, not at sea level), enabled in the 2.5D view. Styling may signal
  estimated vs measured height (e.g. flatter opacity on `estimate`), keyed on
  `height_source` — style only, no re-bake.
- Attribution extends to include PLATEAU where its heights contribute.

## Non-goals

- No PLATEAU 3D **models** (roof shapes / LOD2+); this is block extrusion from a
  single height. High-fidelity models are the local 3D work mode.
- No change to the 2D view's flat rendering; extrusion is the 2.5D view.
- No retirement of the windowed path yet (PR5).

## Implementation steps

1. Add the PLATEAU LOD1 acquisition task (pinned, gitignored, manifest).
2. Extend the merge to join height by the three-tier rule and bake
   `height`/`height_source`; re-generate the tiles; record the match-rate split.
3. Add the `fill-extrusion` layer bound to `height` over `setTerrain`; wire it to
   the 2.5D view toggle; key opacity/signal on `height_source`.
4. Add PLATEAU attribution; extend e2e to assert extrusion appears in 2.5D and
   that a known measured-height building matches PLATEAU within tolerance.

## Acceptance

- In 2.5D, buildings extrude on the terrain surface; a spot-checked building in a
  PLATEAU-modelled ward matches its `measuredHeight`; a building outside any
  modelled municipality still extrudes from an `osm_tag` or `estimate` height and
  is tagged as such.
- `metadata.json` records the `height_source` split; all three attributions
  (OSM, GSI, PLATEAU) render.
- `cd webapp && npm run build && npm run test`, the Playwright suites, and
  `uv run python -m terrai_spatial validate` pass.
