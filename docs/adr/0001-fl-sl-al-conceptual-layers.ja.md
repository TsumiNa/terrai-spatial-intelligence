# ADR-0001：TerrAI 概念アーキテクチャとして FL → SL → AL を採用

[中文](0001-fl-sl-al-conceptual-layers.md) | [日本語](0001-fl-sl-al-conceptual-layers.ja.md) | [English](0001-fl-sl-al-conceptual-layers.en.md)

- 状態：Accepted（Factor of Concept）
- 日付：2026-07-20
- 決定者：TerrAI
- 範囲：製品ナラティブ、Demo 情報設計、後続開発の境界

## Context

現在の TerrAI Prototype は複数のオープン空間データと三つの応用方向を統合していますが、従来の「統一データ基盤」という表現では、観測、決定論的加工、将来の疎予測、アプリケーションスコアが消費すべきものを明確に区別できませんでした。

戦略文書 v4 は、顧客横断で再利用できる engine core、標準 delivery layer、限定された application layer を求めています。Cyber Port/羽田は「疎観測下での地盤パラメータ予測」という入口能力の証明であり、完全なアプリケーションではありません。ユーザーはこれを Foundation Data Layer、Synthetic Data Layer、Application Layer として具体化しました。

`geo_pfn` は性能が context 密度、feature 群、model 規模で変化することも示します。一つのモデルで全域を埋める構造ではなく、適用性、校正、棄却を備えた場面別モデル群を支持します。

## Decision

三層の概念アーキテクチャを採用します。

1. **FL**：公開、商用、顧客許諾の現実観測と、観測意味を変えない決定論的加工を保存し、マルチスケール missing を許容する。
2. **SL**：FL 上に検証済みの疎補完・拡張を非破壊で生成する。observed、synthetic、unresolved を区別し、不確実性と適用境界を保持する。
3. **AL**：FL/SL 証拠を場面ルール、順位、行動出口へ変換し、synthetic を事実として隠さない。

同時に以下を定めます。

- すべての missing を補完してはならない。法的権利、所有、正式な工学結論は unknown のまま権威ある手続へ送る。
- 現在の空間 Demo には検証済み地表 SL がない。リスク、適地、容量代理、統合スコアは AL の heuristic である。
- Google Satellite Embedding は外部生成 FL 表現であり、TerrAI 生成 SL ではない。
- `geo_pfn` は疎転移、モデル選択、不確実性の機構証拠であり、斜面、道路、太陽光の精度証明ではない。

## 検討した代替案

### A. 「統一データ基盤＋複数応用」を継続

単純ですが、事実、代理、モデル補完の混同を残し、疎予測を横断資産として説明できません。却下。

### B. 各アプリケーションが独自補完モデルを保有

短期納品は速い一方、顧客学習と検証が個別案件に閉じ、「次回導入ほどカスタムを減らす」という scaling test に反します。全体構造として却下。

### C. FL → SL → AL

公開/顧客データ蓄積、疎予測能力、応用収益出口を別々に進化させ、不確実性と監査境界を応用より前に置けます。採用。

## Consequences

利点：

- 再利用資産が共有地図コードから FL 証拠蓄積と SL モデル能力へ拡張する。
- 新規応用は missing 処理を業務スコアへ埋めず SL を再利用できる。
- observed/synthetic 分離により監査、不確実性、人手確認が製品構造になる。
- 顧客や疎密度に応じたモデル群と abstention の位置が明確になる。

コストとリスク：

- 一部地域が unknown のまま残ることを受け入れ、全面塗りつぶしだけを完成条件にしない。
- SL の場面横断再利用には厳密な検証が必要で、地下証拠を地表へ直接移せない。
- 後続開発では version、権限、モデル選択、lineage が必要だが、本 ADR は実装を先決めしない。

## Non-goals

本 ADR はデータ構造、API、DB、model registry、orchestration、deployment、顧客権限方式を定義しません。後続 Factor of Develop ADR で決定します。

## Validation

- 工学文書に唯一で明確な FL/SL/AL 定義と非目標がある。
- 内部アーキテクチャ文書が成熟度を正直に示し、顧客 Demo は内部概念を主ナビゲーションにしない。
- 既存応用が動作し、heuristic を SL と誤表示しない。
- 三言語 UI が一致する。
- PR に理由、手順、証拠変更、後続開発課題を残す。
