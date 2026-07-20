# Google Satellite Embedding V1 / AlphaEarth Foundations

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated
- Resolution: 10 m annual 64-D representation
- Current years: 2023 and 2024

## Data description

- **Format** — 64-band Cloud Optimized GeoTIFF (int8, NODATA = −128), read by HTTP byte range from the Source Cooperative public mirror at `tge-labs/aef/v1/annual`. Only the windows covering the two demo bounds are transferred; no global tile is downloaded in full.
- **Resolution and cadence** — 10 m pixels, one composite per calendar year. Years cached here: 2023 and 2024.
- **CRS** — UTM zone 54N (EPSG:32654), matching the source tiling; derived products are reprojected to WGS84 for display.
- **What a pixel means** — each pixel is a 64-dimensional unit-length embedding vector summarising a year of satellite observation. It is not surface reflectance, not a spectral index, and not a land-cover class; the dimensions have no individually interpretable physical meaning.
- **Local products and fields** — `data/google/satellite_embedding/embedding_evidence.geojson` holds 300 cells with `cell_id`, `region`, `year_pair`, `cosine_change`, `change_score`, `support_pct`, `valid_pixels`, `evidence_status`, and `embedding_preview`. Four PNG overlays (per-region change and latent RGB) plus `summary.json` accompany it.
- **Volume** — 300 evidence cells across both regions, from windowed reads of two annual layers.
- **Known gaps** — the mirror is a public copy and is not officially supported by Google. `cosine_change` measures how far a pixel's yearly vector moved, so a high `change_score` means "worth inspecting", never an identified cause; `support_pct` and `valid_pixels` fall where nodata pixels reduce coverage. These values stay out of the decision scores until locally validated.

## Source

Produced by Google and Google DeepMind. TerrAI reads required windows from the public Source Cooperative COG mirror, which is not officially supported by Google. Catalog: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL ; mirror: https://registry.opendata.aws/aef-source/

## Use in this project

7,820 valid pixels in Yokohama and 19,877 in Mobara support annual cosine change, similarity review, and future few-label transfer. Products include change images, similarity previews, and 100 m evidence cells. It does not enter current suitability/resilience scores. As an externally produced representation it is FL, not TerrAI SL.

## License

CC BY 4.0. Required attribution: `The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`

## Commercial-use cautions

The 64 axes are not land-cover classes. Annual change can reflect imaging conditions and requires imagery/field review. The public mirror currently needs no Google account or Earth Engine, but TerrAI pays its own network/storage/compute. Reassess cost before using the official provider-pays path.
