# 横浜市地域防災拠点

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み
- Snapshot：2026-04-01
- 種類：公式施設名、住所、位置

## データの内容

- **形式** — 単一 CSV。市は CP932（Shift-JIS）で公開しますが、証拠パイプラインが初回読み込み時にファイルを UTF-8 へその場で変換するため、本リポジトリにキャッシュされている複製は UTF-8 です。新規にダウンロードした複製は CP932 のままで、素朴な UTF-8 読み取りは失敗します。
- **列** — `Type`、`Definition`、`Name`、`Address`、`Lat`、`Lon`、`Kana`、`Ward`、`WardCode`。`Lat` / `Lon` は WGS84 の十進度です。
- **粒度** — 公式の防災施設 1 件につき 1 行（地域防災拠点、避難場所などの区分は `Type` で判別）。
- **データ量** — `2026-04-01` スナップショット（`hinanjo_20260401.csv`）で施設 628 行。
- **時点** — 日付付きスナップショット。市は独自の頻度で再公開し、ファイル名にスナップショット日付を保持しています。
- **デモに到達する範囲** — 横浜デモの小さな矩形内にある施設のみが空間フィルタを通過するため、`data/yokohama/official_facility_resilience.geojson` は 628 行のうち現在 **2** 地物のみを保持します。
- **既知の欠測と留意点** — 施設の identity・区分・住所・座標は公式情報です。一方で本 project が付加する `matched_roof_area_m2`、`pv_kwp_proxy`、`nearest_road_m`、`served_high_risk_buildings`、`resilience_score` はいずれも他レイヤから計算した PoC 代理値であり、市による施設評価ではありません。本ファイルは指定状況を示すものであり、現在の構造状態・使用中の収容力・運用即応性については何も述べていません。

## 出典

横浜市地域防災拠点・帰宅困難者一時滞在施設 CSV：https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv

## 本 project での利用

保土ケ谷 study window 内の公式2拠点を公共施設レジリエンス改修の実行対象とします。位置、名称、住所は公式観測です。最近屋根、PV容量、道路距離、250 m high-risk 建物関連は TerrAI proxy です。出力：`data/yokohama/official_facility_resilience.geojson`。

## License

横浜市 open data は原則 CC BY 4.0 で商用可。出典・加工表示が必要です。https://data.city.yokohama.lg.jp/terms.html

## 商用利用時の注意

第三者権利は利用者が別途確認します。TerrAI の屋根、容量、service area、resilience score を横浜市公式 field、正式改修提案、災害保証として表示してはいけません。施設状態と snapshot を定期更新してください。
