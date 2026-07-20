# 横浜市地域防災拠点

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み
- Snapshot：2026-04-01
- 種類：公式施設名、住所、位置

## 出典

横浜市地域防災拠点・帰宅困難者一時滞在施設 CSV：https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv

## 本 project での利用

保土ケ谷 study window 内の公式2拠点を公共施設レジリエンス改修の実行対象とします。位置、名称、住所は公式観測です。最近屋根、PV容量、道路距離、250 m high-risk 建物関連は TerrAI proxy です。出力：`data/yokohama/official_facility_resilience.geojson`。

## License

横浜市 open data は原則 CC BY 4.0 で商用可。出典・加工表示が必要です。https://data.city.yokohama.lg.jp/terms.html

## 商用利用時の注意

第三者権利は利用者が別途確認します。TerrAI の屋根、容量、service area、resilience score を横浜市公式 field、正式改修提案、災害保証として表示してはいけません。施設状態と snapshot を定期更新してください。
