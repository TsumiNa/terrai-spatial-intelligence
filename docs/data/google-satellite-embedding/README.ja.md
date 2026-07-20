# Google Satellite Embedding V1 / AlphaEarth Foundations

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み
- 解像度：10 m、年次64次元表現
- 現在年：2023、2024

## データの内容

- **形式** — 64 バンドの Cloud Optimized GeoTIFF（int8、NODATA = −128）。Source Cooperative の公開ミラー `tge-labs/aef/v1/annual` から HTTP バイトレンジで読み出します。2 つのデモ範囲に対応するウィンドウのみを転送し、全球タイルを丸ごとダウンロードすることはありません。
- **解像度と頻度** — 10 m ピクセル、暦年ごとに 1 コンポジット。ここでキャッシュしているのは 2023 年と 2024 年です。
- **CRS** — UTM ゾーン 54N（EPSG:32654）で出典のタイル方式に一致。派生成果は表示用に WGS84 へ再投影します。
- **1 ピクセルの意味** — 各ピクセルは 1 年分の衛星観測を要約した 64 次元・単位長の埋め込みベクトルです。地表反射率でも分光指数でも土地被覆クラスでもなく、各次元に個別の物理的解釈はありません。
- **ローカル成果とフィールド** — `data/google/satellite_embedding/embedding_evidence.geojson` に 300 セルを保持し、`cell_id`、`region`、`year_pair`、`cosine_change`、`change_score`、`support_pct`、`valid_pixels`、`evidence_status`、`embedding_preview` を持ちます。加えて地域別の変化・潜在 RGB の PNG オーバーレイ 4 枚と `summary.json` があります。
- **データ量** — 2 地域あわせて証拠セル 300 件。年次 2 レイヤのウィンドウ読み出しによる生成物です。
- **既知の欠測と留意点** — ミラーは公開コピーであり Google の公式サポート対象ではありません。`cosine_change` は年次ベクトルの移動量を測るもので、`change_score` が高いことは「確認する価値がある」を意味するだけで原因の特定ではありません。nodata ピクセルが多い箇所では `support_pct` と `valid_pixels` が低下します。これらの値はローカル検証を経るまで意思決定スコアには組み込みません。

## 出典

Google と Google DeepMind が製造し、TerrAI は Source Cooperative 公開 COG mirror の必要 window を読みます。mirror は Google 公式 support ではありません。catalog：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL 、mirror：https://registry.opendata.aws/aef-source/

## 本 project での利用

横浜7,820、茂原19,877 valid pixel を年次 cosine 変化、類似地域確認、将来の少数顧客 label 転移に使います。変化画像、類似 preview、100 m evidence cell を生成します。現 suitability/resilience score に入れません。外部生成表現なので FL であり TerrAI SL ではありません。

## License

CC BY 4.0。指定出典：`The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`

## 商用利用時の注意

64軸は土地被覆 class ではありません。年次変化は撮像条件も含み得るため画像/現地確認が必要です。公開 mirror は現在 Google account/Earth Engine 不要ですが、自前 network/storage/compute は負担します。公式 provider-pays 経路へ変える場合は費用再評価が必要です。
