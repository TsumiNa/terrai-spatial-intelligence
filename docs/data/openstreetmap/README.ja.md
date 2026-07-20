# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み、local GeoJSON 化
- 種類：建物、道路、水域、土地利用、送電線

## データの内容

- **形式** — コミュニティのベクタデータをエクストラクトとして取得し、GeoJSON `FeatureCollection`（EPSG:4326、RFC 7946）へ変換したもの。実行時に OSM API やタイルサーバへはアクセスしません。
- **抽出テーマ** — 建物フットプリント、道路、水域、土地利用、送電線。
- **粒度** — OSM オブジェクト 1 件につき 1 地物。建物地物は `osm_id` を保持し、上流まで追跡できます。
- **データ量** — `data/yokohama/building_risk.geojson` に建物ポリゴン 2,128 件、`data/yokohama/road_priority.geojson` に道路区間 272 件。茂原の水域・土地利用・電力コンテキストは `data/mobara/context.geojson`。
- **project が読むフィールド** — 建物では `building`、`levels`、`footprint_m2`（m²）、`name`、`osm_id`。道路優先度モデルでは道路種別と名称。茂原の候補セルでは `landuse`、`distance_water_m`、`distance_building_m`、`distance_grid_m`（いずれも m）。
- **時点** — 特定時点のエクストラクトであり、ライブミラーではありません。OSM 本体は継続的に更新されます。
- **既知の欠測と留意点** — クラウドソースであるため網羅性・正確性・鮮度は保証されず、オブジェクトが無いことはそれが存在しない証拠にはなりません。特に `levels` の欠測が多く、屋根容量を直接読み取らず代理値として計算しているのはこのためです。

## 出典

OpenStreetMap community database：https://www.openstreetmap.org/copyright 。Demo は download・標準化済み local data を使い、runtime で公共 API/tile server に依存しません。

## 本 project での利用

建物輪郭は斜面 exposure と屋根容量 proxy、道路は continuity/accessibility/solar logistics、水域・土地利用は setback/context、送電線は茂原距離 proxy に使います。主な生成物は `data/yokohama/`、`data/mobara/`、`data/joint/` にあります。

## License

Open Database License（ODbL）。OpenStreetMap contributors の出典表示が必要で、公開派生 DB は share-alike 義務を生じ得ます。

## 商用利用時の注意

ODbL は database と produced work で義務が異なるため、商用公開前に成果物を分類してください。crowdsourced data の完全性、精度、鮮度は保証されず、欠落は現実不存在の証明ではありません。公共本番 API/tile を濫用しないでください。
