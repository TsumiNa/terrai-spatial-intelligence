# PLATEAU UC24-16 日本橋地下埋設物

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: 観測外部 sample として接続済み、local cache はオンデマンド
- Publisher: Project PLATEAU / 国土交通省
- Dataset/API key: `plateau_uc24_16_nihonbashi` / `uc24_16_nihonbashi`

## データの内容

- **形式・構造:** 公式 ZIP 9件。各 archive は 3D Tiles 1.1 tileset 1件と `EXT_structural_metadata` 付き glTF 2.0 を含みます。再構築可能 cache は archive 9件、`tileset.json` 9件、glTF 80件の合計98 files です。source archive と展開 asset は commit しません。
- **範囲・空間参照:** cache 対象は日本橋 demonstration area、約東経139.767043–139.780303°、北緯35.680907–35.691726°です。`boundingVolume.region` は WGS 84 経緯度角を radian、WGS 84 楕円体高を metre で表し、全体範囲は2.385–15.779 mです。この絶対高は `uro:minDepth`/`uro:maxDepth` ではありません。
- **粒度・容量:** utility resource 9件、glTF tile 80件、構造 metadata feature 1,121 rows。source archive 合計は2,398,270 bytesです。1,121件すべての `uro:id` が存在し一意です。
- **時点:** 全1,121 rows の `core:creationDate` は2025-01-31、CKAN package 最終更新は2025-06-04、取得日は2026-07-21です。`UC24` は demonstration project 系列を示し、live 台帳の時点ではありません。
- **Resource class:** 下水道管路162、電力マンホール92、通信マンホール92、通信ケーブル162、下水道マンホール92、電力ケーブル162、水道管路162、ガス管路162、通信ハンドホール35。
- **Field・単位:** `uro:id`、`uro:minDepth`、`uro:maxDepth`、`uro:outerDiamiter`、`uro:material`、`uro:length`、`uro:mesureType`、geometry/thematic source code、作成日を含む上流の正確な23 string keysを保持します。`uro:outerDiamiter` と `uro:mesureType` は上流表記で TerrAI の修正ではありません。glTF property table は depth、diameter、length の単位を符号化していないため audit index の unit は `null` です。metre が明示されるのは3D Tiles region heightだけです。
- **既知の欠落:** depth、length、material、measurement は1,121 rows中810件、outer diameter は486件に存在します。access structure 311件には管寸法がありません。code を人間可読の精度 class に推測変換しません。通信 asset は光 fiber と表示されません。coverage、鮮度、位置完全性は保証されません。

## 出典

- [UC24-16 公式 catalog](https://www.geospatial.jp/ckan/dataset/plateau-uc24-16)
- [公式 CKAN `package_show` API](https://www.geospatial.jp/ckan/api/3/action/package_show?id=plateau-uc24-16)
- [PLATEAU open data guide](https://www.mlit.go.jp/plateau/open-data/)

固定した9 resource の選択は `data/plateau/uc24_16_nihonbashi/source_manifest.json` にあります。`uv run python -m terrai_spatial fetch underground_utilities` は公式 package record を照会し、現在の ZIP を安全に download/展開し、参照 glTF を全件検証して hash と audit metadata を再生成します。欠落 cache は通常の online startup で自動復旧し、offline startup は部分 cache を ready とせず scene unavailable と報告します。

## 本 project での利用

将来の地下 network view 向けの観測 Foundation Data Layer evidence です。`GET /api/v1/catalog` は cache readiness、1,121 features、9件の on-demand tileset roots を返し、`GET /api/v1/datasets/uc24_16_nihonbashi` は取得 manifest を返します。asset は local 復旧後のみ `/api/v1/assets/external/plateau_uc24_16/` 以下で配信され、`/bootstrap` には入りません。

`data/plateau/uc24_16_nihonbashi/audit_index.json` は各 source feature ID を resource、glTF tile、正確な source attributes、欠落、取得時刻、archive hash に対応付けます。source depth attribute は絶対3D位置と分離し、二重に減算してはいけません。

## License

公式 catalog は [PLATEAU Site Policy 第3項](https://www.mlit.go.jp/plateau/site-policy/) を適用します。商用を含む再利用は原則として可能ですが、出典表示、編集表示、個別に示された第三者権利の確認が必要です。取得 manifest は公式 resource URL と license 文を保持します。

## 商用利用時の注意

限定 demonstration model であり、権威的・完全・最新の utility ledger ではありません。掘削照会、設計、asset ownership、緊急対応、状態/capacity 判断に使用しません。PLATEAU attribution を保持し、再利用 resource ごとの第三者 notice を確認し、TerrAI audit index が派生 metadata であることを明示します。単位、survey method、datum の unknown は適格 source が与えるまで unknown のままにします。

## Reference-only adjacent sources

同じ UC24-16 catalog の名古屋・大阪 demonstration resource は runtime cache/FL dataset に登録しません。[UC23-04](https://www.geospatial.jp/ckan/dataset/plateau-uc23-04) は CKAN license field 未選択のため reference-only です。[横浜市下水道案内](https://www.city.yokohama.lg.jp/faq/kukyoku/gesui/kanro-hozen/20211015085255270.html) は bulk-open contract 未確認の viewer/印刷 reference、[横浜市水道管路情報](https://www.city.yokohama.lg.jp/business/bunyabetsu/suido/mizumore/kanro.html) は申請/login 必須、[東京ガス埋設管照会](https://itm-external22.tokyo-gas.co.jp/maicho/) は登録制・地点別 service です。日本の authoritative な bulk-open optical-fibre route source は確認できていません。TerrAI はこれら reference-only source を自動取得、scrape、公開しません。
