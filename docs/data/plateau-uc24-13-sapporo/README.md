# PLATEAU UC24-13 Sapporo Underground Structures

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated as an observed external sample; on-demand local cache
- Publisher: Project PLATEAU / Ministry of Land, Infrastructure, Transport and Tourism
- Dataset/API key: `plateau_uc24_13_sapporo` / `uc24_13_sapporo`

## Data description

- **Format and structure:** two official ZIP archives containing 3D Tiles 1.0 and B3DM contents with source batch tables. The reproducible cache has 2 archives, 2 `tileset.json` files and 6,423 B3DM files: 6,427 files in the completeness manifest. Archives and expanded assets are Git-ignored.
- **Coverage and CRS:** the selected Sapporo scene spans approximately 141.349593–141.356914° E and 43.054916–43.070981° N. `boundingVolume.region` uses WGS 84 angles in radians and ellipsoid heights in metres; the union is 35.373–57.879 m. This height range is not depth below ground.
- **Granularity and volume:** the underground-mall resource has 4,828 B3DM contents and 52,826 batch rows; the municipal-subway Sapporo Station resource has 1,595 contents and 17,892 rows. All 70,718 rows carry a non-empty `gml_id`. A row represents a rendered CityGML surface, room or installation batch, not a unique building or navigable segment. The source archives total 63,139,254 bytes; the expanded local cache is approximately 367 MB.
- **Vintage:** source vintage is fiscal 2024. The CKAN package was modified on 2025-05-26 and retrieved on 2026-07-21.
- **Fields and units:** the batch tables preserve `gml_id`, `feature_type`, `city_code`, `meshcode`, nested `attributes`, and published `uro:*` fields. Main feature types include wall, floor, ceiling, door, room and building-installation surfaces. Geometry coordinates and region heights follow 3D Tiles; no source field supplies walking level, depth below surface, legal accessibility or opening status, so those values remain unknown.
- **Known gaps:** this is demonstration geometry, not a complete or live station model. The two resources use city codes `01100` and `01102`; this difference is retained rather than reconciled. Batch-table fields are often null, there is no routable centreline graph, and absolute ellipsoid height must not be interpreted as survey depth or an orthometric elevation.

## Source

- [Official UC24-13 catalog](https://www.geospatial.jp/ckan/dataset/plateau-uc24-13)
- [Official CKAN `package_show` API](https://www.geospatial.jp/ckan/api/3/action/package_show?id=plateau-uc24-13)
- [PLATEAU site policy](https://www.mlit.go.jp/plateau/site-policy/)

The selected resource IDs are frozen in `data/plateau/uc24_13_sapporo/source_manifest.json`. `uv run python -m terrai_spatial fetch underground_structures` downloads the official archives, validates safe extraction, every tileset reference, every B3DM header, batch-table length, archive hash and cache completeness. Normal online startup restores a missing cache; offline startup rejects a partial cache.

## Use in this project

This dataset supplies observed structural geometry for scene `sapporo-station-underground`. `GET /api/v1/catalog` reports readiness, 70,718 batch rows and two on-demand asset roots; `GET /api/v1/datasets/uc24_13_sapporo` returns the manifest. Assets are served from `/api/v1/assets/external/plateau_uc24_13/` only after restoration and are excluded from `/bootstrap`.

The separate OSM snapshot adds community access/topology context. It does not validate, overwrite or snap PLATEAU geometry. A shared scene ID expresses spatial context only; source-specific IDs, timestamps, files and licences remain separate.

`data/plateau/uc24_13_sapporo/scene_handoff.json` is derived auxiliary metadata owned by the same dataset key. It records the measured extent, a reversible `EPSG:4979` → `EPSG:4978` → local ENU-metre frame, WGS 84 ellipsoid-height reference and `unknown` orthometric datum. The 70,718 PLATEAU rows are observed underground-structure evidence and the 195 OSM features are independently observed access context; terrain/buildings, boreholes, strata and SL predictions remain unresolved, and the geographically separate Nihonbashi utilities are not applicable. `data/scenes/underground/catalog.json` discovers the scene without creating another FL dataset key. Both files rebuild deterministically with `uv run python -m terrai_spatial data ensure --only underground_scenes --offline` and stay outside `/bootstrap`.

## License

The official catalog applies [PLATEAU Site Policy, section 3](https://www.mlit.go.jp/plateau/site-policy/). Commercial reuse is generally permitted with source attribution, modification notices and checks for separately identified third-party rights.

## Commercial-use cautions

Do not present the sample as an authoritative station plan, public-right-of-way record, current accessibility map, evacuation model or engineering survey. Verify operations, access, datum and geometry with the responsible operator or authority. Retain PLATEAU attribution and disclose TerrAI transformations and cache date.

## Reference-only resources

North Ichijo parking, Shibuya Station west-exit underground passage and Sunport Takamatsu underground parking remain reference-only entries from the same UC24-13 catalog. [UC23-05 Tokyo Station underground mall](https://www.geospatial.jp/ckan/dataset/plateau-uc23-05) is also reference-only. None is downloaded, registered as a runtime dataset or included in the canonical Sapporo scene.
