# GSI DEM5A

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み
- 公開者：国土地理院（GSI）
- 原生解像度：5 m

## 出典

GSI 基盤地図情報数値標高モデル DEM5A。download には無料登録が必要です。https://service.gsi.go.jp/kiban/app/help/

## 本 project での利用

横浜・茂原の標高、傾斜、局所起伏、低所代理、建物/道路地形 exposure に利用します。決定論的な傾斜/起伏計算は FL であり、災害確率や斜面安定判断ではありません。`data/yokohama/building_risk.geojson`、`road_priority.geojson`、solar cell の地形 field に派生値があります。

## License

GSI content 利用規約に従い出典・加工を表示します。DEM は基本測量成果です。https://maps.gsi.go.jp/help/termsofuse.html

## 商用利用時の注意

複製、地図作成、公開方法によって測量法手続が必要な場合があります。本番前に成果と表現方法を確認してください。植生・建物遮蔽・測定誤差があり、現地測量や地質工学判断の代替ではありません。
