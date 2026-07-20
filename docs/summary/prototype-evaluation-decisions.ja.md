# TerrAI リファクタリング意思決定記録

[中文](prototype-evaluation-decisions.md) | [日本語](prototype-evaluation-decisions.ja.md) | [English](prototype-evaluation-decisions.en.md)

## FL → SL → AL 概念アーキテクチャ（2026-07-20）

TerrAI の共有基盤を Foundation Data Layer（FL）、Synthetic Data Layer（SL）、Application Layer（AL）に分けます。公開・公式観測と意味を変えない決定論的加工は FL、held-out・校正・適用性 gate を通った将来の疎補完は SL、現在の斜面・道路レジリエンス・太陽光適地・統合スコアは AL です。

第一段階は Factor of Concept であり schema、DB、orchestration を定義しませんでした。後続の展示リファクタは最小読取 API を追加しましたが三層境界は変えません。詳細は [`FL_SL_AL_CONCEPT.ja.md`](../architecture/FL_SL_AL_CONCEPT.ja.md)、判断理由は [`fl-sl-al-platform/00-overview.ja.md`](../refactor/fl-sl-al-platform/00-overview.ja.md) を参照してください。

## 顧客展示 UI と最小 FastAPI 分離（2026-07-20）

- FL/SL/AL 成熟度や内部実験を顧客ナビから外し、機能、結果解釈、信頼性、項目別監査を前面に出す。
- 静的フロントを `frontend/` へ移し、`/api/v1` だけからデータを読む。
- FastAPI が cache、health、catalog、GeoJSON 検索、集計、推薦順位を担当し、再構築は Python script と task registry に残す。
- 独立 JSON/GeoJSON を維持し、安定 dataset key を将来 SQLite 移行の分離境界とする。
- 詳細は [`FRONTEND_BACKEND.ja.md`](../architecture/FRONTEND_BACKEND.ja.md)。

## 三つの Claude Demo から採用したもの

| Claude Demo | 採用 | 却下・書換 |
|---|---|---|
| A1 保土ケ谷リスク概要 | 地域概要→対象 drill-down、100–300 m 意思決定区、出典/手法境界 | 91 標高点から 60 m 面を補間し疎補間を DEM 精度として扱う方法 |
| A3 施設レジリエンス | 実在公共施設を行動対象にすること、施設 portfolio queue | 文京区の越境 sample、固定標高、他施設平均を TPI と呼ぶこと。2026 横浜公式拠点と同域 join に置換 |
| B1 太陽光資産 exposure | 投資/運用 queue、portfolio 視点、発見から due diligence への言語 | 古い WRI 324 施設、20 施設 sample、各3点、`<5 m` 低地規則。代わりに METI/TEPCO 方向を維持 |

## Google データの選択

- **Satellite Embedding**：年次 64 次元・センサー横断表現。変化、類似、将来の少数ラベル転移に利用。公開 COG mirror を使い Earth Engine は不要。
- **Dynamic World**：データは open だが商用 Earth Engine は計算費用が発生。追加有料サービスゼロの制約から Demo と接続候補から削除し、ESA WorldCover / ローカル Sentinel-2 を評価する。

## マルチスケールデータ契約

1. 5–10 m 表面証拠：GSI DEM、Satellite Embedding。将来 Sentinel-2 / ESA WorldCover。
2. 対象資産：建物、道路、公式施設、太陽光 grid。
3. 100–300 m 近傍：サービス需要、道路影響、施設 gap、証拠 support。
4. 地域/portfolio gate：系統制約、許認可データ不足、案件 queue。

各出力は最低限 `evidence_status`、時刻、空間 support、score 参加有無、制約を保持します。

## `geo_pfn` 疎 context 実験との関係

48 query 孔を固定し、192 候補から 3–192 個の完全 context 孔を抽出します。座標+深度では geo-PFN が N=25–50 で約 20 RMSE、TabICL より約 3–6 低い一方、極端疎では安定した点予測優位がなく、密では HGBT/TabICL が強い baseline です。後続学習により「実特徴が悪化させる」という初期説明は学習不足が主因と修正され、2M LCSG は約 22.9 から 17.7、17M は N=25 で約 19.0 に改善しました。残課題は feature 取込、疎目的学習、区間 sharpness、サイト間検証です。

よって採用するのは完全 coherent context、密度/場面別 model 選択、全推論の不確実性、abstention の四機構だけです。地下 Su 実験を地表・遥感精度の証明にはしません。

## Demo → PoC → MVP 検証 gate

| 段階 | 可能 | 主張禁止 |
|---|---|---|
| Demo | データ融合、証拠状態、行動 queue、offline 再現 | 災害確率、発電量、系統接続確約、正式な施設改修便益 |
| PoC | 少数顧客ラベル、HGBT/空間 baseline との held-out・地域間・ablation 比較、不確実性校正 | 独立検証なしの工学適用性 |
| MVP | 権限、version、監査、monitoring、人手確認、検証済 feature の score 組込 | 法定審査や工学判断を black-box score で置換 |
