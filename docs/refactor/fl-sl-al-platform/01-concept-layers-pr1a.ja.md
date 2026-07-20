# PR1a 計画：FL → SL → AL 概念境界の確立

[中文](01-concept-layers-pr1a.md) | [日本語](01-concept-layers-pr1a.ja.md) | [English](01-concept-layers-pr1a.en.md)

- 状態：Completed
- Refactor：`fl-sl-al-platform`
- PR：#1 / part a

## 目的

observed / synthetic / unresolved、multiscale missing、品質 gate、現成熟度を含む唯一の FL/SL/AL 語彙を定義し、AL heuristic を model 予測として表示できないようにします。

## 範囲

1. 三層 concept と Mermaid overview。
2. `geo_pfn` 疎 context 結果を確認し機構証拠に限定。
3. GSI、OSM、横浜、NASA POWER、TEPCO、Satellite Embedding を FL に mapping。
4. 横浜/茂原地表 SL が現在0であることを明示。
5. concept contract test。

## 非目標

schema、層間 API、DB、model registry、顧客権限、本番地表 model は定義しません。

## 受入

- 定義、代替案、結果、非目標を `00-overview` と `docs/architecture/FL_SL_AL_CONCEPT.ja.md` に集約。
- AL risk、suitability、capacity proxy を SL と呼ばない。
- 中日英版が文書検証を通過。
