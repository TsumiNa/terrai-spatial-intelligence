# TerrAI リモートセンシング・地形データ接続計画

[中文](REMOTE_SENSING_PLAN.md) | [日本語](REMOTE_SENSING_PLAN.ja.md) | [English](REMOTE_SENSING_PLAN.en.md)

## 接続済み・ローカルキャッシュ済み

| データ | 原生 level | 用途 | 表さないもの |
|---|---:|---|---|
| GSI 全国最新写真 | ZL17 | 屋根、植生、農地、水面、建設状態の目視確認 | 統一撮影日、または全域衛星画像 |
| GSI 陰影起伏図 | ZL16 | 尾根、谷、排水経路、微地形 | 災害確率 |
| GSI 傾斜量図 | ZL15 | 傾斜変化、施工・斜面背景 | 現地測量 |
| GSI DEM5A | 5 m | 建物/道路勾配、局所起伏、低所代理 | 植生・建物遮蔽下でも誤差ゼロの測量 |

視覚タイルは小範囲 snapshot としてキャッシュ済みで、実行時に外部ネットワークを必要としません。

## 接続済み：Google Satellite Embedding V1

両実証地域について 2023/2024 年、10 m、64 次元を実データで切り出しています。

- 横浜：有効 7,820 pixel、平均年次 cosine 変化 0.00969、P95 0.01606。
- 茂原：有効 19,877 pixel、平均 0.02278、P95 0.04355。
- 出力：年次変化 heatmap、2024 類似表現 RGB、100 m 集約証拠 cell。

64 軸は軸ごとに解釈できません。類似 RGB は主成分 preview、年次変化は単位 vector の `1 - dot(v2023, v2024)` です。ローカル hold-out 検証前は業務 score に入れません。

## Dynamic World：評価後に削除

データは CC BY 4.0 ですが、TerrAI の商用 Earth Engine 利用には計算費用がかかります。追加 DB/分析サービス購入ゼロを守るため Demo、生成 pipeline、接続候補から削除しました。静的土地被覆には ESA WorldCover、最近の地表・季節変化にはローカル処理 Sentinel-2 L2A を評価します。

## 次段階：Sentinel-2 L2A 検証

Copernicus Data Space STAC API で次を優先します。

- 同季節の無雲または低雲 scene。
- `SCL` による雲、雲影、雪 mask。
- B02/B03/B04/B08/B11/B12 band。
- 茂原範囲外 2–5 km buffer による edge effect 低減。

計画生成物：

1. **NDVI**：活性植生・継続耕作を識別し、農地転用感度の証拠にする。
2. **NDWI/MNDWI**：水面・季節湿潤域を識別し OSM 水域 setback を補う。
3. **NDBI/裸地指数**：市街地、裸地、耕地、brownfield 候補の区別を補助する。
4. **多時期変化**：土地被覆、施工攪乱、災害後変化を検出する。
5. **品質 flag**：撮影日、雲量、pixel 解像度、合成 window を記録する。

10 m pixel は茂原の農地・大規模敷地に適しますが、横浜の単一屋根構造や一本の道路損傷を直接判定できません。屋根は高解像度正射画像、建物輪郭、現地/ドローン資料を使います。

公式文書：https://documentation.dataspace.copernicus.eu/APIs/STAC.html

## シナリオ分担

### 横浜都市レジリエンス

- 高解像度画像：屋根形状、周辺植生、現地確認 base。
- DEM/起伏/傾斜：斜面、道路縦断勾配、谷、低所。
- Sentinel-2：地域緑地、熱環境、災害後背景だけに使い、単一屋根 score に入れない。

### 茂原再エネ開発

- 高解像度画像：候補地の現利用と道路入口。
- Sentinel-2：耕作活動、水湿、季節変化、裸地。
- DEM/起伏/傾斜：土工、排水、侵食、施工アクセス。
- 後続で筆、農地、保護区、地価、系統 CSV と空間 join する。

## 本番品質ルール

- すべての遥感 score に取得日、sensor、band、解像度、雲 mask 手法を残す。
- 任意の単景より季節合成を優先する。
- 視覚 basemap と分析 raster を分離し、見栄えの良い画像を自動的にモデル証拠としない。
- 指数は screening feature に限定し、土地性質と許認可は主管機関データに従う。
