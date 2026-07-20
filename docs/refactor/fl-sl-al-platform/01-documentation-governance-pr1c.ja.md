# PR1c 計画：文書情報アーキテクチャと三言語 governance

[中文](01-documentation-governance-pr1c.md) | [日本語](01-documentation-governance-pr1c.ja.md) | [English](01-documentation-governance-pr1c.en.md)

- 状態：Completed
- Refactor：`fl-sl-al-platform`
- PR：#1 / part c

## 目的

root `architecture/`、`docs/adr/`、flat refactor record、root 評価文書の重複を解消し、中日英同期を備えた持続可能な五分類 docs 構造を作ります。

## 計画

1. system call 文書を `docs/architecture/` へ統合。
2. ADR を各 refactor の独立 folder と `00-overview` で置換。
3. 接続済 FL source を `docs/data/` の dataset card に分割。
4. 評価、検証、非 refactor decision を `docs/summary/` へ移動。
5. どの分類にも入らないものだけ `docs/others/` へ置く。
6. root README を簡潔化し開発 workflow を CONTRIBUTING へ移す。
7. repository instruction、参照、自動検証を更新。

## 受入

- `docs/` は README と architecture/refactor/data/summary/others だけを含む。
- `docs/adr/` と root `architecture/` が存在しない。
- 接続済 FL dataset ごとに独立三言語 card がある。
- 各 refactor folder は `00-overview` で始まり、PR file は `NN-topic-prXa` 形式。
