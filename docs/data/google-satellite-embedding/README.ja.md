# Google Satellite Embedding V1 / AlphaEarth Foundations

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み
- 解像度：10 m、年次64次元表現
- 現在年：2023、2024

## 出典

Google と Google DeepMind が製造し、TerrAI は Source Cooperative 公開 COG mirror の必要 window を読みます。mirror は Google 公式 support ではありません。catalog：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL 、mirror：https://registry.opendata.aws/aef-source/

## 本 project での利用

横浜7,820、茂原19,877 valid pixel を年次 cosine 変化、類似地域確認、将来の少数顧客 label 転移に使います。変化画像、類似 preview、100 m evidence cell を生成します。現 suitability/resilience score に入れません。外部生成表現なので FL であり TerrAI SL ではありません。

## License

CC BY 4.0。指定出典：`The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`

## 商用利用時の注意

64軸は土地被覆 class ではありません。年次変化は撮像条件も含み得るため画像/現地確認が必要です。公開 mirror は現在 Google account/Earth Engine 不要ですが、自前 network/storage/compute は負担します。公式 provider-pays 経路へ変える場合は費用再評価が必要です。
