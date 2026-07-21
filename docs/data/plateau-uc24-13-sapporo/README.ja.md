# PLATEAU UC24-13 札幌地下構造物

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：観測外部 sample として接続済み、オンデマンド local cache
- 公開者：Project PLATEAU / 国土交通省
- Dataset/API key：`plateau_uc24_13_sapporo` / `uc24_13_sapporo`

## データの内容

- **形式と構造：** 3D Tiles 1.0、B3DM content、source batch table を含む公式 ZIP 2 件。再現可能 cache は archive 2 件、`tileset.json` 2 件、B3DM 6,423 件で、完全性 manifest は計 6,427 file を追跡します。archive と展開 asset は Git 対象外です。
- **範囲と CRS：** 札幌 scene の範囲は概ね東経 141.349593–141.356914°、北緯 43.054916–43.070981°。`boundingVolume.region` は WGS 84 の角度を radian、楕円体高を metre で表し、統合範囲は 35.373–57.879 m です。これは地表下深度ではありません。
- **粒度と量：** 地下街 resource は B3DM 4,828 件・batch row 52,826 件、市営地下鉄さっぽろ駅 resource は 1,595 件・17,892 row。計 70,718 row すべてに空でない `gml_id` があります。1 row は描画用 CityGML の surface、room または installation batch であり、固有建物数や通行可能 segment 数ではありません。source archive は計 63,139,254 bytes、展開済み local cache は約 367 MB です。
- **時点：** source は 2024 年度。CKAN package は 2025-05-26 更新、2026-07-21 取得です。
- **field と unit：** batch table は `gml_id`、`feature_type`、`city_code`、`meshcode`、nested `attributes`、公開済み `uro:*` field を保持します。主な feature type は wall、floor、ceiling、door、room、building-installation surface です。geometry 座標と region height は 3D Tiles に従います。歩行 level、地表下 depth、法的 accessibility、開場状況を示す source field はないため unknown のままです。
- **既知の欠測：** 実証 geometry であり、完全・live な駅 model ではありません。2 resource の city code は `01100` と `01102` で、統合せずそのまま保持します。batch-table field は null が多く、routing centerline graph はありません。絶対楕円体高を survey depth や標高 datum と解釈できません。

## 出典

- [UC24-13 公式 catalog](https://www.geospatial.jp/ckan/dataset/plateau-uc24-13)
- [公式 CKAN `package_show` API](https://www.geospatial.jp/ckan/api/3/action/package_show?id=plateau-uc24-13)
- [PLATEAU site policy](https://www.mlit.go.jp/plateau/site-policy/)

選択 resource ID は `data/plateau/uc24_13_sapporo/source_manifest.json` に固定しています。`uv run python -m terrai_spatial fetch underground_structures` は公式 archive を download し、安全な展開、全 tileset 参照、全 B3DM header、batch-table length、archive hash、cache 完全性を検証します。通常の online 起動は欠落 cache を復元し、offline 起動は部分 cache を拒否します。

## 本 project での利用

scene `sapporo-station-underground` の観測構造 geometry を提供します。`GET /api/v1/catalog` は readiness、70,718 batch row、2 つの on-demand asset root を返し、`GET /api/v1/datasets/uc24_13_sapporo` は manifest を返します。復元後の asset は `/api/v1/assets/external/plateau_uc24_13/` から配信され、`/bootstrap` には入りません。

別の OSM snapshot は community の access/topology context を追加しますが、PLATEAU geometry の検証、上書き、snap は行いません。共通 scene ID は空間的 context のみを表し、source 固有 ID、timestamp、file、license は分離します。

`data/plateau/uc24_13_sapporo/scene_handoff.json` は同じ dataset key が所有する派生 auxiliary metadata です。実測 extent、可逆な `EPSG:4979` → `EPSG:4978` → local ENU-metre frame、WGS 84 楕円体高 reference、`unknown` の正高 datum を記録します。PLATEAU 70,718 rows は observed underground-structure evidence、OSM 195 features は独立した observed access context です。terrain/building、borehole、strata、SL prediction は unresolved、地理的に別の日本橋 utility は not applicable とします。`data/scenes/underground/catalog.json` は別の FL dataset key を作らず scene を発見します。両 file は `uv run python -m terrai_spatial data ensure --only underground_scenes --offline` で決定論的に再生成でき、`/bootstrap` には入りません。

## License

公式 catalog は [PLATEAU Site Policy 第3項](https://www.mlit.go.jp/plateau/site-policy/)を適用します。出典表示、改変表示、個別第三者権利の確認を条件に商用利用も概ね可能です。

## 商用利用時の注意

公式駅図、通行権台帳、最新 accessibility map、避難 model、engineering survey として表示しないでください。運用、access、datum、geometry は operator/authority に確認し、PLATEAU attribution、TerrAI の変換内容と cache 日を明示してください。

## 参照のみの resource

北一条駐車場、渋谷駅西口地下歩道、サンポート高松地下駐車場は同じ UC24-13 catalog 内の reference-only entry です。[UC23-05 東京駅地下街](https://www.geospatial.jp/ckan/dataset/plateau-uc23-05)も reference-only です。いずれも download、runtime dataset 登録、canonical 札幌 scene への追加を行いません。
