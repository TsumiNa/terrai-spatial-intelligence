# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み、local GeoJSON 化
- 種類：建物、道路、水域、土地利用、送電線、札幌の地下鉄/access context

## データの内容

- **形式** — コミュニティのベクタデータをエクストラクトとして取得し、GeoJSON `FeatureCollection`（EPSG:4326、RFC 7946）へ変換したもの。実行時に OSM API やタイルサーバへはアクセスしません。
- **抽出テーマ** — 建物フットプリント、道路、水域、土地利用、送電線、および札幌の限定範囲における地下鉄 track/station/entrance と地下 walkway candidate。
- **粒度** — OSM オブジェクト 1 件につき 1 地物。建物地物は `osm_id` を保持し、上流まで追跡できます。
- **データ量** — `data/yokohama/building_risk.geojson` に建物ポリゴン 2,128 件、`data/yokohama/road_priority.geojson` に道路区間 272 件。茂原の水域・土地利用・電力コンテキストは `data/mobara/context.geojson`。札幌 snapshot は地下鉄 entrance 97、station 6、track way 8、地下 walkway candidate 84 の計 195 feature で、point 103、line 92 です。数値の地上/上階 level のみを持ち、tunnel または負の level/layer evidence がない query 結果 6 way は出力・件数から除外します。
- **project が読むフィールド** — 建物では `building`、`levels`、`footprint_m2`（m²）、`name`、`osm_id`。道路優先度モデルでは道路種別と名称。茂原候補セルでは `landuse`、`distance_water_m`、`distance_building_m`、`distance_grid_m`（すべて m）。札幌は `osm_type`、`osm_id`、`osm_version`、`osm_changeset`、`osm_timestamp`、原文 `tags`、正確な `level`/`layer`、evidence flag、null の `depth_m`/`elevation_m` を保持します。
- **時点** — 特定時点の extract であり live mirror ではありません。札幌 OSM base timestamp は 2026-07-21T10:51:01Z、取得時刻は 2026-07-21T10:53:05Z。OSM 本体は継続更新されます。
- **既知の欠測と留意点** — crowdsourced のため完全性、精度、法的 access、鮮度は保証されず、欠落は不存在の証明ではありません。札幌 way は東経 141.349592632–141.356913521°、北緯 43.054916388–43.070980841° の bbox で選択し、交差する source geometry 全体を clip せず保持します。欠落・曖昧 level を depth に変換しません。access 制限 tag がないことは public access や現在開場の証明ではありません。

## 出典

OpenStreetMap community database：https://www.openstreetmap.org/copyright 。Demo は download・標準化済み local data を使い、runtime で公共 API/tile server に依存しません。札幌の正確な query は `data/osm/sapporo_underground_access/query.overpassql` に commit 済みで、`uv run python -m terrai_spatial fetch underground_access_osm` が明記された公共 Overpass endpoint から GeoJSON と取得 metadata を明示的に更新します。

## 本 project での利用

建物輪郭は斜面 exposure と屋根容量 proxy、道路は continuity/accessibility/solar logistics、水域・土地利用は setback/context、送電線は茂原距離 proxy に使います。札幌 OSM feature は scene `sapporo-station-underground` に独立した community access/topology context を与え、dataset key `osmSapporoUndergroundAccess` で on demand query できます。PLATEAU geometry とは分離し、検証・上書きしません。主な生成物は `data/yokohama/`、`data/mobara/`、`data/joint/`、`data/osm/sapporo_underground_access/` にあります。

## License

Open Database License（ODbL）。OpenStreetMap contributors の出典表示が必要で、公開派生 DB は share-alike 義務を生じ得ます。

## 商用利用時の注意

ODbL は database と produced work で義務が異なるため、商用公開前に成果物を分類してください。crowdsourced data の完全性、精度、accessibility、鮮度は保証されず、欠落は現実不存在の証明ではありません。candidate walkway を法的 public または現在開場と表示しないでください。公共本番 API/tile を濫用しないでください。
