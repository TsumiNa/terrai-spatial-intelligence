# PLATEAU UC24-16 Nihonbashi Underground Utilities

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated as an observed external sample; on-demand local cache
- Publisher: Project PLATEAU / Ministry of Land, Infrastructure, Transport and Tourism
- Dataset/API key: `plateau_uc24_16_nihonbashi` / `uc24_16_nihonbashi`

## Data description

- **Format and structure:** nine official ZIP archives, each containing one 3D Tiles 1.1 tileset and glTF 2.0 content with `EXT_structural_metadata`. The reproducible cache contains 9 archives, 9 `tileset.json` files and 80 glTF files: 98 files in total. Source archives and expanded assets are not committed.
- **Coverage and spatial reference:** the cached subset is the Nihonbashi demonstration area, approximately 139.767043–139.780303° E and 35.680907–35.691726° N. `boundingVolume.region` uses WGS 84 longitude/latitude angles in radians and WGS 84 ellipsoid heights in metres; the observed union is 2.385–15.779 m. These absolute heights are not the `uro:minDepth`/`uro:maxDepth` values.
- **Granularity and volume:** 9 utility resources, 80 glTF tiles and 1,121 structural-metadata feature rows. The source archives total 2,398,270 bytes. All 1,121 `uro:id` values are present and unique.
- **Vintage:** all cached feature rows carry `core:creationDate=2025-01-31`; the CKAN package was last modified on 2025-06-04 and was retrieved on 2026-07-21. `UC24` identifies the demonstration project lineage; it is not a live operational snapshot.
- **Resource classes:** sewer pipe 162, power manhole 92, communications manhole 92, communications cable 162, sewer manhole 92, power cable 162, water pipe 162, gas pipe 162 and communications handhole 35.
- **Fields and units:** TerrAI preserves 23 exact upstream string keys, including `uro:id`, `uro:minDepth`, `uro:maxDepth`, `uro:outerDiamiter`, `uro:material`, `uro:length`, `uro:mesureType`, geometry/thematic source codes and creation date. `uro:outerDiamiter` and `uro:mesureType` are upstream spellings, not TerrAI corrections. The glTF property tables do not encode units for depth, diameter or length, so the audit index keeps their unit as `null`; only the 3D Tiles region height has an explicit metre definition.
- **Known gaps:** depth, length, material and measurement values exist for 810 of 1,121 rows; outer diameter exists for 486. The 311 access-structure rows do not carry pipe dimensions. Codes are retained without guessing human-readable accuracy classes. Communications assets are not labelled optical fibre. Coverage, currency and positional completeness are not guaranteed.

## Source

- [Official UC24-16 catalog](https://www.geospatial.jp/ckan/dataset/plateau-uc24-16)
- [Official CKAN `package_show` API](https://www.geospatial.jp/ckan/api/3/action/package_show?id=plateau-uc24-16)
- [PLATEAU open-data guidance](https://www.mlit.go.jp/plateau/open-data/)

The frozen nine-resource selection is in `data/plateau/uc24_16_nihonbashi/source_manifest.json`. `uv run python -m terrai_spatial fetch underground_utilities` queries the official package record, safely downloads and expands the current ZIPs, validates every referenced glTF and regenerates hashes and audit metadata. A missing cache is restored automatically during normal online startup; offline startup reports the scene unavailable rather than accepting a partial cache.

## Use in this project

This is observed Foundation Data Layer evidence for the future underground-network view. `GET /api/v1/catalog` reports cache readiness, 1,121 features and nine on-demand tileset roots; `GET /api/v1/datasets/uc24_16_nihonbashi` returns the retrieval manifest. The assets are served below `/api/v1/assets/external/plateau_uc24_16/` only after local restoration and are never included in `/bootstrap`.

`data/plateau/uc24_16_nihonbashi/audit_index.json` maps every source feature ID to its resource, glTF tile, exact source attributes, missingness, retrieval time and archive hash. Source depth attributes remain separate from absolute 3D position and must not be subtracted twice.

`data/plateau/uc24_16_nihonbashi/scene_handoff.json` is derived auxiliary metadata owned by the same dataset key. It records the measured source extent, a reversible `EPSG:4979` → `EPSG:4978` → local ENU-metre frame, the WGS 84 ellipsoid-height reference, and `unknown` orthometric datum. It exposes 810 network rows and 311 access-structure rows as observed evidence; co-located terrain/buildings, boreholes, strata and SL predictions remain unresolved, while Sapporo public-space structures are not applicable. `data/scenes/underground/catalog.json` discovers this scene without registering another FL dataset key. Both files are rebuilt deterministically with `uv run python -m terrai_spatial data ensure --only underground_scenes --offline` and remain outside `/bootstrap`.

## License

The official catalog applies the [PLATEAU Site Policy, section 3](https://www.mlit.go.jp/plateau/site-policy/). Reuse, including commercial reuse, is generally permitted with source attribution, indication of modifications and checks for separately identified third-party rights. The retrieval manifest preserves the official resource URLs and licence statement.

## Commercial-use cautions

This is a limited demonstration model, not an authoritative, complete or current utility ledger. Do not use it for excavation clearance, engineering design, asset ownership, emergency response or condition/capacity decisions. Retain PLATEAU attribution, review third-party notices for each reused resource, and disclose that TerrAI's audit index is a derived metadata product. Unknown units, survey method and datum must remain unknown until a qualified source supplies them.

## Reference-only adjacent sources

The same UC24-16 catalog also publishes Nagoya and Osaka demonstration resources; they are not cached or registered as runtime FL datasets. [UC23-04](https://www.geospatial.jp/ckan/dataset/plateau-uc23-04) remains reference-only because its CKAN licence field is not selected. [Yokohama sewer guidance](https://www.city.yokohama.lg.jp/faq/kukyoku/gesui/kanro-hozen/20211015085255270.html) is a viewer/print reference without a confirmed bulk-open contract; [Yokohama water-pipe access](https://www.city.yokohama.lg.jp/business/bunyabetsu/suido/mizumore/kanro.html) requires an application/login; and [Tokyo Gas buried-pipe inquiry](https://itm-external22.tokyo-gas.co.jp/maicho/) is a registered, site-specific service. No authoritative bulk-open Japanese optical-fibre route source has been confirmed. TerrAI does not automate, scrape or expose any of these reference-only sources.
