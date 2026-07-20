# GSI 地図・視覚タイル

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み、pilot 範囲 cache 済み
- Layer：標準地図、全国最新写真、陰影起伏図、傾斜量図

## 出典

GSI layer 一覧：https://maps.gsi.go.jp/development/ichiran.html 。`seamlessphoto`、`hillshademap`、`slopemap` 等の pilot tile を cache しています。

## 本 project での利用

basemap および屋根、植生、農地、水面、建設状態、尾根谷、傾斜の目視確認に利用します。tile は `/api/v1/assets/*` から提供し、runtime は GSI server にアクセスしません。visual basemap は score に入りません。

## License

GSI content 利用規約に従い出典・加工を表示します。一部 tile は第三者権利や個別法令制限を含み得ます。https://maps.gsi.go.jp/help/termsofuse.html

## 商用利用時の注意

「全国最新写真」は高 zoom で主に正射航空写真、一部だけ衛星画像です。全てを satellite map と呼ばないでください。公開 offline 再配布前に layer ごとに確認し、公式 tile service に過負荷をかけないでください。
