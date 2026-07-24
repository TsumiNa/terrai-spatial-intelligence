# OSM 関東建物フットプリント

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み、オンデマンド
- Layer：高ズーム詳細レイヤ用の建物データオブジェクト

## データの内容

関東本土取得窓内の建物フットプリント。固定スナップショット `kanto-260101.osm.pbf`（抽出時刻 2026-01-01T21:21:30Z）から抽出した 5,371,292 ポリゴンで、安定した `osm_id`/`osm_type`、`building` 種別、記載があれば `name`/`building:levels`、取得来歴を保持します。ソース中の退化マルチポリゴン 14 件はスキップし manifest に計数します。コミュニティマッピングのため市街地は密、それ以外は疎で、建物が無いことは不存在の証明ではありません。

- **形式** — GeoJSON FeatureCollection 1 件（`buildings.geojson`、約 3.1 GB、MultiPolygon 形状）と `metadata.json` manifest。
- **CRS** — EPSG:4326（WGS 84 経緯度）。
- **範囲** — 関東本土取得窓 (138.65, 34.85, 140.95, 36.30)。

## 出典

[OpenStreetMap](https://www.openstreetmap.org/copyright) データの [Geofabrik extract](https://download.geofabrik.de/asia/japan/kanto.html)。`-latest` ではなく日付固定スナップショットを使い、再実行で同じ台帳を再現します。

## 本 project での利用

統合された自前建物タイル（`osm-basemap-tiles`）の主フットプリント源：OSM の同定・タグに、基盤地図情報がギャップを埋め、PLATEAU 高さが結合されます。`terrai-buildings` PMTiles レイヤとして描画され、詳細 zoom でクリックすると、焼き込まれたタイル属性から raw 監査記録が開きます（API 呼び出しなし）。`osm_kanto` タスクで更新し、オフラインのタイル統合に供給します。基盤証拠のみで、スコアには入りません。（ウィンドウ配信の `osmBuildings` コレクションは `osm-basemap-tiles` PR5 で廃止しました。）

## License

Open Database License (ODbL) 1.0。レイヤ表示箇所では「© OpenStreetMap contributors」の表示が必須です。

## 商用利用時の注意

公開する派生データベースには ODbL の share-alike が及びます。網羅性・現勢性はコミュニティ依存で保証されず、`building:levels` 等のタグは疎です。台帳を公的な建物登録として提示しないでください。
