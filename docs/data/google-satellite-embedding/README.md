# Google Satellite Embedding V1 / AlphaEarth Foundations

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated
- Resolution: 10 m annual 64-D representation
- Current years: 2023 and 2024

## Source

Produced by Google and Google DeepMind. TerrAI reads required windows from the public Source Cooperative COG mirror, which is not officially supported by Google. Catalog: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL ; mirror: https://registry.opendata.aws/aef-source/

## Use in this project

7,820 valid pixels in Yokohama and 19,877 in Mobara support annual cosine change, similarity review, and future few-label transfer. Products include change images, similarity previews, and 100 m evidence cells. It does not enter current suitability/resilience scores. As an externally produced representation it is FL, not TerrAI SL.

## License

CC BY 4.0. Required attribution: `The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`

## Commercial-use cautions

The 64 axes are not land-cover classes. Annual change can reflect imaging conditions and requires imagery/field review. The public mirror currently needs no Google account or Earth Engine, but TerrAI pays its own network/storage/compute. Reassess cost before using the official provider-pays path.
