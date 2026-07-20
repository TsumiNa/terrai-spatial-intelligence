# PR1b 計画：顧客展示 UI と FastAPI 分離

[中文](01-exhibition-fastapi-pr1b.md) | [日本語](01-exhibition-fastapi-pr1b.ja.md) | [English](01-exhibition-fastapi-pr1b.en.md)

- 状態：Completed
- Refactor：`fl-sl-al-platform`
- PR：#1 / part b

## 目的

内部 concept board を、機能、結果、信頼性、追跡性を顧客が即時理解できる展示製品へ変え、最小 static frontend/FastAPI 境界を作ります。

## 範囲

1. 初期画面を opportunity、metric、map、action queue、平易な解釈へ変更。
2. FL/SL/AL 成熟度、Claude 比較、model shell を顧客 navigation から削除。
3. static file を `frontend/` へ移し `/api/v1` のみから data 読込。
4. file cache、health、query、facility aggregate、recommendation rank を Python へ移動。
5. FL は独立 JSON/GeoJSON を継続。

## 主な trade-off

`/bootstrap` は Demo を単純化し offline 展示に適しますが大規模化には不向きです。将来は `/features` と `/recommendations` を module、viewport、page 単位で取得します。SQLite は差分更新、同時書込、複雑 join、履歴 query が必要になった時だけ導入します。

## 受入

- 顧客 UI が内部成熟度を表示しない。
- frontend が業務 filter/sort/reduce/score を実行しない。
- metric、queue、map field を監査可能。
- API、desktop/mobile、中日英が test を通過。
