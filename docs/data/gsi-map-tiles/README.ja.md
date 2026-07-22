# GSI 地図・視覚タイル

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：全国 live 配信
- Layer：標準ベクトル地図、全国最新写真、陰影起伏図、傾斜量図

## データの内容

- **形式** — 標準 basemap は GSI ベクトルタイル style（`experimental_bvmap`、z4–16）。ラスタ basemap は XYZ タイル（256 × 256 px）：`seamlessphoto`（JPEG、z2–18）、`hillshademap`（PNG、z2–16）、`slopemap`（PNG、z3–15）。すべて `https://cyberjapandata.gsi.go.jp/xyz` から live 配信します。
- **CRS** — Web メルカトル（EPSG:3857）、標準的な XYZ タイル方式。
- **範囲** — 全国。各 source の最大ズームを超えると、404 になるタイルを要求せず UI 側で拡大表示します。
- **時点** — GSI が現在配信している内容そのままで、ローカルスナップショットはありません。上流レイヤは発行元が独自に更新します。
- **既知の欠測と留意点** — 陰影起伏と傾斜量は数値ラスタではなく**描画済み画像**です。標高や度数として読み取ることはできず、本 project の数値地形量はすべて DEM 製品側から取得しています。

## 出典

GSI layer 一覧：https://maps.gsi.go.jp/development/ichiran.html 。`std.json`（ベクトル）、`seamlessphoto`、`hillshademap`、`slopemap` を stream します。

## 本 project での利用

basemap および屋根、植生、農地、水面、建設状態、尾根谷、傾斜の目視確認に、対象範囲内の任意地点で利用します。tile は描画時に GSI から stream し、保存・再配布しません。visual basemap は score に入りません。

## License

GSI content 利用規約に従い出典・加工を表示します。一部 tile は第三者権利や個別法令制限を含み得ます。https://maps.gsi.go.jp/help/termsofuse.html

## 商用利用時の注意

「全国最新写真」は高 zoom で主に正射航空写真、一部だけ衛星画像です。全てを satellite map と呼ばないでください。公開 offline 再配布前に layer ごとに確認し、公式 tile service に過負荷をかけないでください。
