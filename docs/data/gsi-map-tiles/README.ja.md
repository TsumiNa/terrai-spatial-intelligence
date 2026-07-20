# GSI 地図・視覚タイル

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み、pilot 範囲 cache 済み
- Layer：標準地図、全国最新写真、陰影起伏図、傾斜量図

## データの内容

- **形式** — `https://cyberjapandata.gsi.go.jp/xyz` から取得した XYZ ラスタタイル（256 × 256 px）。標準地図・陰影起伏・傾斜量は PNG、正射画像は JPEG です。
- **キャッシュ済みレイヤとズーム** — `std`（標準地図）z15、`seamlessphoto`（全国最新写真／衛星モザイク）z15–17、`hillshademap`（DEM 由来の陰影起伏）z15–16、`slopemap`（DEM 由来の傾斜量図）z15。
- **CRS** — Web メルカトル（EPSG:3857）、標準的な XYZ タイル方式。
- **ここでキャッシュしている範囲** — 2 つのデモ矩形のみで、それ以上の広域は含みません。
- **データ量と配置** — タイル 141 ファイル。すべて `data/tiles/manifest.json` に列挙され、`data/tiles/<region>/[layer]/<z>/<x>-<y>.<ext>` に格納されます。標準レイヤはレイヤ階層を省略します。
- **時点** — キャッシュ作成時点の固定スナップショットで、自動更新はありません。上流レイヤは発行元が独自に更新します。
- **既知の欠測と留意点** — 陰影起伏と傾斜量は数値ラスタではなく**描画済み画像**です。標高や度数として読み取ることはできず、本 project の数値地形量はすべて DEM 製品側から取得しています。キャッシュしたズーム上限が表示可能な詳細度の上限であり、UI でより深いズームを指定してもタイルを追加取得せず拡大表示になります。

## 出典

GSI layer 一覧：https://maps.gsi.go.jp/development/ichiran.html 。`seamlessphoto`、`hillshademap`、`slopemap` 等の pilot tile を cache しています。

## 本 project での利用

basemap および屋根、植生、農地、水面、建設状態、尾根谷、傾斜の目視確認に利用します。tile は `/api/v1/assets/*` から提供し、runtime は GSI server にアクセスしません。visual basemap は score に入りません。

## License

GSI content 利用規約に従い出典・加工を表示します。一部 tile は第三者権利や個別法令制限を含み得ます。https://maps.gsi.go.jp/help/termsofuse.html

## 商用利用時の注意

「全国最新写真」は高 zoom で主に正射航空写真、一部だけ衛星画像です。全てを satellite map と呼ばないでください。公開 offline 再配布前に layer ごとに確認し、公式 tile service に過負荷をかけないでください。
