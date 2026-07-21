# FL データセット一覧

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

本 directory は TerrAI Foundation Data Layer（FL）に接続済みの dataset だけを記録します。各 card に出典、project 用途、license、商用注意、local 生成物、更新方法を記載します。

| Dataset | 状態 | Card |
|---|---|---|
| GSI DEM5A | 接続済み | [地形標高](gsi-dem5a/README.ja.md) |
| GSI 地図・視覚 tile | 接続済み | [標準/画像/起伏/傾斜](gsi-map-tiles/README.ja.md) |
| GSI 指定避難データ | 接続済み・全国 base | [指定避難所と災害種別指定緊急避難場所](gsi-designated-evacuation/README.ja.md) |
| Google Satellite Embedding V1 | 接続済み | [年次遥感表現](google-satellite-embedding/README.ja.md) |
| OpenStreetMap | 接続済み | [建物、道路、context](openstreetmap/README.ja.md) |
| PLATEAU UC24-13 札幌 | 接続済み・オンデマンド sample | [観測地下構造物](plateau-uc24-13-sapporo/README.ja.md) |
| PLATEAU UC24-16 日本橋 | 接続済み・オンデマンド sample | [観測地下埋設物](plateau-uc24-16-nihonbashi/README.ja.md) |
| KuniJiban ボーリング | 接続済み・オンデマンド地域抽出 | [ボーリング、地層、SPT](kunijiban-boreholes/README.ja.md) |
| 横浜市地域防災拠点 | 接続済み・地方検証/補足 | [公式公共施設](yokohama-disaster-bases/README.ja.md) |
| NASA POWER | 接続済み | [日射気候背景](nasa-power/README.ja.md) |
| TEPCO 公開系統情報 | 接続済み・再配布制限 | [地域系統容量 screening](tepco-grid/README.ja.md) |
| MLIT 5万分の1土地分類 | 接続済み・オンデマンド | [地質・土壌](mlit-land-classification-50k/README.ja.md) |
| MLIT 全期間の水害GIS | 接続済み・オンデマンド | [被災履歴](mlit-flood-history/README.ja.md) |
| MLIT 土地履歴調査 | 接続済み・オンデマンド | [地形・旧土地利用](mlit-land-history/README.ja.md) |
| MLIT A33 土砂災害警戒区域 | 接続済み・オンデマンド | [土砂制約](mlit-a33-landslide/README.ja.md) |
| MLIT A53 多段階浸水想定 | 接続済み・オンデマンド | [頻度別浸水](mlit-a53-multistage-flood/README.ja.md) |
| MLIT L01 地価公示 | 接続済み・オンデマンド | [2026年標準地](mlit-l01-published-land-price/README.ja.md) |
| MLIT A56 盛土等規制区域 | 接続済み・オンデマンド | [規制screening](mlit-a56-embankment-regulation/README.ja.md) |
| MLIT N02 鉄道 | 接続済み・オンデマンド | [路線・駅](mlit-n02-railway/README.ja.md) |
| MLIT L03-b 土地利用細分 | 接続済み・オンデマンド | [2021年100mメッシュ](mlit-l03b-land-use/README.ja.md) |
| MLIT L02 都道府県地価調査 | 接続済み・オンデマンド | [2025年基準地](mlit-l02-prefectural-land-price/README.ja.md) |

接続確認済み未使用および除外 source は [`docs/summary/open-data-landscape/`](../summary/open-data-landscape/README.ja.md) を参照してください。機械可読状態は `data/external/source_registry.json` にあります。
