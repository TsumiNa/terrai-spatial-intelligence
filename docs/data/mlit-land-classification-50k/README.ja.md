# 国土交通省 5万分の1土地分類基本調査
[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## データの内容
地質・土壌等の図郭単位Shapefileです。年代と属性は図郭ごとに異なります。TerrAIはGIS化済みの関東15図郭をGeoJSONへ切り出し、原属性・レイヤ名・時刻を保持します。GIS化は一部図郭のみのため、範囲には図郭単位の欠落があります。
## 出典
[国土調査ダウンロード](https://nlftp.mlit.go.jp/kokjo/inspect/landclassification/download.html)
## 本 project での利用
斜面安定性、施工制約、浸透性、用地DDのFL根拠。APIキーは`landClassification50k`、更新は`uv run python -m terrai_spatial data update --only mlit`。
## License
現行の原則は公共データ利用規約1.0。出典と加工表示が必要です。
## 商用利用時の注意
背景図等は測量法手続が必要な場合があります。原パッケージの無加工再配布を避け、図郭ごとに条件を再確認します。
