# FL Dataset Catalog

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

This directory documents datasets already integrated into the TerrAI Foundation Data Layer (FL). Each card records source, project use, license, commercial-use cautions, local products, and refresh path.

| Dataset | Status | Card |
|---|---|---|
| GSI DEM5A | Integrated | [Terrain elevation](gsi-dem5a/README.md) |
| GSI maps and visual tiles | Integrated | [Standard/imagery/relief/slope](gsi-map-tiles/README.md) |
| GSI designated evacuation data | Integrated, national base | [Shelters and hazard-specific emergency places](gsi-designated-evacuation/README.md) |
| Google Satellite Embedding V1 | Integrated | [Annual remote-sensing representation](google-satellite-embedding/README.md) |
| OpenStreetMap | Integrated | [Buildings, roads, and context](openstreetmap/README.md) |
| OSM Kanto building footprints | Integrated, on demand | [High-zoom building objects](osm-kanto-buildings/README.md) |
| PLATEAU UC24-13 Sapporo | Integrated, on-demand sample | [Observed underground structures](plateau-uc24-13-sapporo/README.md) |
| PLATEAU UC24-16 Nihonbashi | Integrated, on-demand sample | [Observed underground utilities](plateau-uc24-16-nihonbashi/README.md) |
| KuniJiban boreholes | Integrated, on-demand regional extract | [Boreholes, strata, and SPT](kunijiban-boreholes/README.md) |
| Yokohama regional disaster bases | Integrated, local validation/supplement | [Official public facilities](yokohama-disaster-bases/README.md) |
| NASA POWER | Integrated | [Solar climate context](nasa-power/README.md) |
| TEPCO public system information | Integrated, redistribution restricted | [Regional grid-capacity screen](tepco-grid/README.md) |
| MLIT 1:50,000 land classification | Integrated, on demand | [Geology and soil](mlit-land-classification-50k/README.md) |
| MLIT all-period flood history | Integrated, on demand | [Observed flood history](mlit-flood-history/README.md) |
| MLIT land history survey | Integrated, on demand | [Landform and former use](mlit-land-history/README.md) |
| MLIT A33 landslide warning zones | Integrated, on demand | [Landslide constraints](mlit-a33-landslide/README.md) |
| MLIT A53 multi-stage inundation | Integrated, on demand | [Flood-frequency scenarios](mlit-a53-multistage-flood/README.md) |
| MLIT L01 published land price | Integrated, on demand | [2026 reference prices](mlit-l01-published-land-price/README.md) |
| MLIT A56 embankment regulation | Integrated, on demand | [Regulatory screening](mlit-a56-embankment-regulation/README.md) |
| MLIT N02 railway | Integrated, on demand | [Lines and stations](mlit-n02-railway/README.md) |
| MLIT L03-b detailed land use | Integrated, on demand | [2021 100 m mesh](mlit-l03b-land-use/README.md) |
| MLIT L02 prefectural land-price survey | Integrated, on demand | [2025 reference prices](mlit-l02-prefectural-land-price/README.md) |

Confirmed but not integrated and excluded sources are summarized in [`docs/summary/open-data-landscape/`](../summary/open-data-landscape/README.md). Machine-readable status is in `data/external/source_registry.json`.
