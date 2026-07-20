# データソースとライセンス

[中文](open-data-landscape.md) | [日本語](open-data-landscape.ja.md) | [English](open-data-landscape.en.md)

更新：2026-07-20。本一覧は現在の TerrAI 三方向（太陽光適地、道路/施設レジリエンス、斜面 exposure）で使用済み、script 接続確認済み、または評価後除外したデータを対象とし、世界の地理データ全体を網羅しません。

## 読み方

- **接続済み**：実データまたはそのローカル生成物が Demo に存在し、実行時に外部 network、API Key、有料 service が不要。
- **接続可能**：公式 bulk download、COG、GIS、API を確認済みだが現 Demo では値を未使用。
- **評価後除外**：主要アクセス platform、商用費用、重複が追加購入ゼロ制約に不適合。
- **無料**は現在データ購入費がない意味だけです。自前 storage/compute/network、無料 account/key、出典、share-alike、測量法手続、法定 due diligence は残り得ます。

## 一覧

### 現 Demo で使用

| ソース | 状態 | 用途 | 費用 | 商用・制約 |
|---|---|---|---|---|
| GSI DEM5A | 接続済み | 傾斜、起伏、低所、建物/道路地形 exposure | 無料 download、無料 account、local compute | GSI 規則に従う出典・加工表示。基本測量成果の複製/利用は測量法手続が必要な場合あり |
| GSI 標準、全国最新写真、陰影起伏、傾斜量 tile | 接続済み | basemap、屋根/植生/地表/尾根谷の目視確認 | 無料、pilot tile cache 済み | 全国最新写真を全て衛星画像と呼ばない。出典必須。第三者権利・個別法令を layer ごとに確認 |
| Google Satellite Embedding V1 / AEF | 接続済み | 10 m 年次変化、類似地域、将来疎 label 転移 | Source Cooperative COG 無料、Google account 不要、local compute | CC BY 4.0・指定出典。mirror は Google 非公式 support。64D 軸を土地 class と解釈せず現 score に入れない |
| OpenStreetMap | 接続済み | 建物、道路、水域、土地利用、送電線 | 無料 download/local 処理 | ODbL 出典、公開派生 DB は share-alike の可能性。完全性/鮮度保証なし。公共 tile server を本番濫用しない |
| 横浜市地域防災拠点 | 接続済み | 公式施設 identity/address/location、屋根・道路・需要との join | 無料 CSV | 原則 CC BY 4.0、商用可、出典・加工表示。第三者権利別扱い。屋根/容量/service area は TerrAI proxy |
| NASA POWER | 接続済み | 茂原長期日射気候背景 | 無料 API、結果 cache | NASA data は一般に open。credit 推奨、endorsement 不可。気候平均は地点発電 model ではない |
| TEPCO「系統の予想潮流等」 | 接続済み・制限 | 地域空容量/上位制約 screening、接続相談順位 | 無料公開 ZIP/CSV、自動公式 download | **open license ではない**。転載禁止、暫定簡略値で接続保証なし。原 file は Git 外、公開/商用再配布は権利確認と正式接続検討が必要 |

### Script 接続確認済み、未使用

| ソース | 対象 | 追加価値 | 費用/アクセス | 主な制約 |
|---|---|---|---|---|
| ESA WorldCover 2020/2021 | 太陽光、遥感解釈 | 全球 10 m、11 class、品質 layer | COG 直接無料、CC BY 4.0 | 2020/2021 のみ、年度間 algorithm 差を実変化とみなさない |
| Copernicus Sentinel-2 L2A | 太陽光、災害/施工変化 | reflectance、NDVI/NDWI/NDBI、季節変化 | open、Data Space 無料 account/quota、local compute | 雲/影/date/composite QA 必須、10 m は単一屋根診断不可 |
| GSI Hazard Map open layer | 斜面、道路、施設 | 土砂、洪水、内水、津波背景 | open layer 無料・商用可 | layer ごとに open 表示、主管、時点、縮尺を確認。visual tile は法定原 data の代替でない |
| MAFF 筆ポリゴン | 太陽光 | 農地境界、耕作単位、転用感度 screening | bulk 無料、千葉2026 約318 MB | 出典・加工表示。所有権、地番、転用許可ではない |
| 法務省登記所備付地図 | 太陽光 | 筆形状、地番、敷地 assemblage | login 後無料 GML/map | 所有者一覧なし。法14条地図と位置精度の低い準ずる図面を含み境界確定でない |
| MLIT 不動産情報ライブラリ | 太陽光、投資 | 取引、地価、都市計画、防災/施設 | 申請・審査・Key 後 API 無料 | 指定表示、rate/service 変更、不完全/非 realtime、重要事項説明等の代替不可 |
| 国土数値情報 / 環境 GIS | 太陽光除外 | 公園、保全、鳥獣、森林 | 多くは無料 GIS | dataset ごとの商用条件、精度、更新を確認し最終判断は主管機関 |
| METI FIT/FIP 公表 | 太陽光市場 | 認定案件、容量、競合/集積 | 無料公開検索/file | 稼働資産全件ではなく規模/address 公開境界あり。現行 reuse 条件確認 |
| e-Stat GIS 境界 | 地域拡張 | 行政/統計集計、人口/需要正規化 | 無料 | 統計表現で法定境界でない。出典・利用条件に従う |

### 純 open data だけでは信頼して取得できないもの

| 情報 | 不足理由 | MVP 取得方法 |
|---|---|---|
| 土地/建物所有者、担保、完全権利 | 公開地籍図は完全所有者一覧を公開しない | 顧客許諾の登記事項証明、公図/地積測量図、適法有料照会 |
| 筆単位の実系統容量、工期、負担金 | 公表値は地域 screening で上位/運用条件に依存 | 一般送配電事業者への事前相談/接続検討 |
| 農地転用、林地開発、保護区の許可可否 | open layer は対象範囲のみで個別裁量・最新条件を含まない | 主管機関事前相談、法務/技術 advisor、現地資料 |
| 屋根耐力、災害時道路通行、斜面安定 | 画像/DEM/輪郭は proxy | 現地、構造/地質/道路資料、運用記録 |

## 国土地理院（GSI）

- DEM5A、標準地図、全国最新写真、陰影起伏図、傾斜量図。
- 用途：傾斜、局所起伏、低所、地表確認、basemap。
- layer：https://maps.gsi.go.jp/development/ichiran.html
- cache ID：`seamlessphoto`、`hillshademap`、`slopemap`。
- ZL14–18 は主に正射航空写真、一部 Landsat-8 等。全 pixel を衛星画像と呼ばない。
- 無料。DEM は無料登録、tile server へ過負荷をかけない。
- 出典・加工表示。一部利用は測量法手続、第三者権利/個別法令制限あり。
- 条件：https://maps.gsi.go.jp/help/termsofuse.html
- download：https://service.gsi.go.jp/kiban/app/help/

## Google Satellite Embedding V1 / AlphaEarth Foundations（接続済み）

- 2017年以降の年次64D地表 embedding、10 m。本 PoC は2023/2024。
- Source Cooperative 公開 COG mirror、Google 非公式 support、Google/Google DeepMind 製造。
- CC BY 4.0。出典：`The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`
- local product：年次 cosine 変化 PNG、2024 類似 RGB、300 個の100 m証拠 cell、source VRT ID。
- 異常確認、類似検索、将来少数 label 転移。現 score に不使用。
- catalog：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
- mirror：https://registry.opendata.aws/aef-source/
- mirror は購入/Google account/Earth Engine 不要。自前 network/storage/compute のみ。公式 GCS provider-pays は未使用。

## Google Dynamic World V1（除外）

- data は CC BY 4.0 だが公式 bulk 分析は Earth Engine 依存、商用利用は project と usage fee が必要。
- UI、script、registry、派生 metadata、adapter から削除。
- 代替：静的 class は ESA WorldCover、最近の spectral/change は local Sentinel-2。検証なしに class 確率を置換しない。
- catalog：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
- pricing：https://cloud.google.com/earth-engine/pricing

## 横浜市地域防災拠点（接続済み）

- 地域防災拠点・帰宅困難者一時滞在施設 CSV、2026-04-01 更新。
- 原則 CC BY 4.0、商用可。出典、加工表示、第三者権利対応。
- 保土ケ谷 study window 内の公式2拠点を抽出。位置、名称、住所が公式観測。
- 最近屋根、PV容量、道路距離、250 m高 risk 建物関連は明示 PoC proxy。
- data：https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv
- terms：https://data.city.yokohama.lg.jp/terms.html

## Copernicus Sentinel-2（確認済み、未 cache）

- Copernicus Data Space STAC の Sentinel-2 L2A multispectral surface reflectance。
- NDVI、植生活性、裸地、季節、施工前後変化を計画。
- https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- data は無料/open、account/quota/service 条件あり。商用 DB 購入なしで local 処理可能。
- 接続前に雲/影 mask、date、品質 flag 必須。単景色を適地 score にしない。

## OpenStreetMap

- 建物、道路、水域、土地利用、送電線。exposure、network、setback、context に利用。
- ODbL。商用可、出典、公開派生 DB share-alike の可能性。
- OSMF は無料本番 API/tile を保証しないため Demo は local data。
- https://www.openstreetmap.org/copyright

## NASA POWER

- 2001–2020 日射 climatology、`ALLSKY_SFC_SW_DWN`。
- 茂原背景：年平均 GHI 約1,378 kWh/m²。
- https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
- 無料 API。credit、logo 不使用、endorsement 不可、個別 notice 確認。

## TEPCO 公開系統情報（接続済み）

- 千葉送電線・変電設備「系統の予想潮流等」CSV。version は実 ZIP `Last-Modified` と local 取得時刻で記録。
- 通常 clone 後の初回 online 起動で公式千葉 ZIP と期待2 CSV を検証・原子展開し解析。cache 完成後は再 download せず、`uv run python -m terrai_spatial fetch tepco` で更新。
- `download_metadata.local.json` に URL、取得時刻、HTTP metadata、byte、SHA-256。原 file と共に Git ignore。
- 出力：`data/mobara/tepco_grid_screen.json`。
- 茂原 signal：変電所単体空容量 proxy 5 MW、上位制約後0 MW、平常時出力制御可能性。
- https://www.tepco.co.jp/pg/consignment/system/index-j.html
- 通常 HTTPS 無料、DB/Key/Earth Engine 不要だが open license ではない。
- 転載禁止、筆 join 用 geometry 不足、暫定簡略値、接続確約でない。公開・商用配布前に権利確認。
- https://www.tepco.co.jp/pg/consignment/system/pdf/yosouchoryu_points_to_note.pdf

## 統合分析の独自仮定

- 屋根 PV proxy：輪郭面積 × 60% usable × 0.20 kWp/m² = 輪郭 × 0.12 kWp。
- service demand：hub 150 m 内 high-risk 建物関連数。
- 道路影響：centerline 55 m 内建物。
- 距離は緯度35.45°付近の平面近似。本番は適切な投影 CRS を使う。
- 同じ建物を複数関連に数え得る。候補順位専用で独立受益者/回避損失ではない。

## Script 接続先

- ESA WorldCover：https://esa-worldcover.org/en/data-access
- Copernicus Data Space：https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- GSI Hazard open data：https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html
- MAFF 筆：https://www.maff.go.jp/j/tokei/census/shuraku_data/2025/mb/index.html
- 法務省地図：https://www.moj.go.jp/MINJI/minji05_00494.html
- MLIT 不動産 API：https://www.reinfolib.mlit.go.jp/help/apiManual/
- 国土数値情報：https://nlftp.mlit.go.jp/ksj/
- METI FIT/FIP：https://www.fit-portal.go.jp/PublicInfoSummary
- e-Stat GIS：https://www.e-stat.go.jp/gis/statmap-search?aggregateUnitForBoundary=A&page=1&type=2

機械可読の接続状態は `data/external/source_registry.json` にあります。batch 処理可能な source のみを登録し、marketing screenshot や追跡不能 sample は正式 source としません。
