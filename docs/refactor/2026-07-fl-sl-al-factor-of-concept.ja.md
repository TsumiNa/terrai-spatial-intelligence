# FL → SL → AL Factor of Concept リファクタリング記録

[中文](2026-07-fl-sl-al-factor-of-concept.md) | [日本語](2026-07-fl-sl-al-factor-of-concept.ja.md) | [English](2026-07-fl-sl-al-factor-of-concept.en.md)

- 日付：2026-07-20
- branch：`refactor/fl-sl-al-concept`
- baseline：`main` / `4ceb7ba`
- 種別：第一段階は概念リファクタ。同一 PR の顧客展示段階で最小 frontend/backend 分離を追加

## 1. 理由

Prototype は地図、データ、監査基盤を共有していましたが、物語は三つの応用 Demo 中心でした。マルチスケール missing を応用横断能力として説明できず、観測、決定論加工、代理、heuristic、将来補完を混同し得ました。

本リファクタは TerrAI を蓄積可能なデータインフラと複数応用出口として定義します。

1. **FL**：公開、商用、顧客許諾証拠を蓄積し multiscale missing を保持。
2. **SL**：ローカル検証済み場面 model 群で予測可能 missing を不確実性・abstention 付きで非破壊拡張。
3. **AL**：適格 FL/SL を斜面、道路、太陽光などの業務出口へ変換。

商用可読性を維持し、`geo_pfn` のような疎 context 予測を正しい位置へ置きます。

## 2. 確認した証拠

- `TerrAI_Narrative_Product_Strategy_Update_v4.docx` §4、§6–7：疎地下予測は入口証明、再利用 engine/delivery と制御された application が長期資産。
- `TsumiNa/geo_pfn` commit `07c7ee0` の `stage-report.html` と `sparse-context-results.html`：model 順位は密度、feature、学習量で変わり、区間 coverage と行単位誤差順位は別問題。
- 現 Prototype lineage：外部6 source group が FL、現 score は透明 AL rule、横浜/茂原地表 SL は held-out、校正、地域間検証未実施。

後続学習は「実 feature が悪化」という初期説明を under-training 主因へ修正しました。そのため固定 model/feature でなく、場面・疎密度別選択、強 baseline、不確実性、abstention を採用します。

## 3. 実施手順と commit 意図

### Commit 1：`docs: define FL SL AL conceptual architecture`

- 三層定義、multiscale missing、observed/synthetic/unresolved 境界。
- 理由、代替案、結果、非目標の ADR。
- `geo_pfn` 解釈修正。

### Commit 2：`feat: add FL SL AL architecture lens`

- 初期内部 architecture view と三言語説明。
- FL live、地表 SL zero、AL live を表示。
- 応用結果を変えず audit drawer に成熟度・校正証拠を接続。

### Commit 3：`docs: map prototype maturity and validate concept`

- README、concept、ADR、refactor record を接続。
- AL heuristic の SL 誤表示を防ぐ契約 test。
- review と Factor of Develop 境界を記録。

### Commit 4：`feat: rebuild exhibition demo with FastAPI backend`

- 顧客 navigation は内部成熟度でなく業務入口、結果、信頼性、監査を表示。
- 静的 file を `frontend/` に移し `/api/v1/bootstrap` で読込。
- Python service が cache、query、集計、地域抽出、queue 順位を担当。
- FL は独立 JSON/GeoJSON のまま、ORM/schema/write API/DB は導入しない。
- API・顧客境界 test を追加。

### Commit 5：`docs: record customer exhibition service boundary`

- 起動、独立 service、API、顧客入口を更新。
- frontend/FastAPI/pipeline 境界と SQLite 条件を記録。
- 顧客・内部 audience の review path を修正。

正確な hash/diff は Git と PR Commits に保持し、本書は製品意図を残します。

## 4. 現資産 mapping

| 資産 | 層 | 理由 |
|---|---|---|
| GSI、OSM、横浜 open data、NASA POWER、TEPCO CSV | FL | 公開/観測証拠と local snapshot |
| Google Satellite Embedding | FL | Google 外部表現、TerrAI 補完ではない |
| DEM 傾斜、座標変換、空間集計 | FL | 観測意味を維持する決定論加工 |
| risk/suitability/joint score、capacity proxy | AL | 透明業務 rule と代理 |
| `geo_pfn` 羽田実験 | SL 機構証拠 | 疎域候補機構、地表精度ではない |
| 横浜/茂原地表 sparse imputation | 未存在 | target、held-out、校正、地域間検証なし |

## 5. PR review 順序

1. Demo 初期画面が横浜レジリエンスと茂原再エネを即時説明すること。
2. portfolio と専門分析の地図、行動 queue、一文解釈を確認。
3. 破線指標、score、popup から出典、式、不確実性、制約を確認。
4. 中/日/英と狭幅画面を確認。
5. FastAPI `/docs` の health、catalog、data、GeoJSON query、recommendation を確認。
6. 内部では `FL_SL_AL_CONCEPT.ja.md` と ADR を読み、runtime が AL を SL と呼ばないことを確認。
7. concept、API、data task、asset の自動検証を実行。

## 6. Factor of Develop に残すもの

- FL/SL/AL object、field、table、file schema。
- 層間 API、orchestration、model registry、version、rollback。
- 顧客 import、権限、tenant 分離、顧客間学習。
- 最初の地表 target、label、欠測機構、model portfolio。
- SL held-out、校正、時間/地域検証、AL 取込閾値。
- DB、feature/object store、online inference、deployment topology。

第一顧客 PoC の target、risk tolerance、data authorization で制約して決めます。

## 7. 受入コマンド

```bash
node --check frontend/app.js
node --check frontend/audit.js
node --check frontend/i18n.js
uv run python -m unittest discover -s tests -v
uvx ruff check .
uv run python -m terrai_spatial validate
git diff --check
```

## 8. 顧客展示と FastAPI の後続リファクタ

初版 concept UI は内部整合には有用でしたが展示には不適でした。同じ PR で：

1. FL/SL/AL を内部文書に残し顧客 navigation から外す。
2. 初期画面を opportunity、4 metric、map、queue、平易な結果へ変更。
3. 内部実験、Claude 比較、model shell 説明を runtime から削除。
4. static file を `frontend/` へ移し FastAPI のみから data 読込。
5. Python JSON/GeoJSON cache、query、aggregate、ranking を追加。
6. 安定 dataset key の背後に file storage を維持し将来 SQLite 移行を可能にする。

詳細は `docs/architecture/FRONTEND_BACKEND_SPLIT.ja.md`。
