# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状態：接続済み、local GeoJSON 化
- 種類：建物、道路、水域、土地利用、送電線

## 出典

OpenStreetMap community database：https://www.openstreetmap.org/copyright 。Demo は download・標準化済み local data を使い、runtime で公共 API/tile server に依存しません。

## 本 project での利用

建物輪郭は斜面 exposure と屋根容量 proxy、道路は continuity/accessibility/solar logistics、水域・土地利用は setback/context、送電線は茂原距離 proxy に使います。主な生成物は `data/yokohama/`、`data/mobara/`、`data/joint/` にあります。

## License

Open Database License（ODbL）。OpenStreetMap contributors の出典表示が必要で、公開派生 DB は share-alike 義務を生じ得ます。

## 商用利用時の注意

ODbL は database と produced work で義務が異なるため、商用公開前に成果物を分類してください。crowdsourced data の完全性、精度、鮮度は保証されず、欠落は現実不存在の証明ではありません。公共本番 API/tile を濫用しないでください。
