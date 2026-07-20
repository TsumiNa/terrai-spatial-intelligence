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
| 横浜市地域防災拠点 | 接続済み・地方検証/補足 | [公式公共施設](yokohama-disaster-bases/README.ja.md) |
| NASA POWER | 接続済み | [日射気候背景](nasa-power/README.ja.md) |
| TEPCO 公開系統情報 | 接続済み・再配布制限 | [地域系統容量 screening](tepco-grid/README.ja.md) |

接続確認済み未使用および除外 source は [`docs/summary/open-data-landscape/`](../summary/open-data-landscape/README.ja.md) を参照してください。機械可読状態は `data/external/source_registry.json` にあります。
