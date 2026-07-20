# TerrAI Spatial Intelligence Platform — Integrated PoC

[中文](2026-07-prototype-state.md) | [日本語](2026-07-prototype-state.ja.md) | [English](2026-07-prototype-state.en.md)

「どこから行動すべきか、なぜか、証拠は信頼できるか」を地図と優先 queue で直接答える顧客向け空間意思決定 Demo です。横浜の都市レジリエンスと茂原の太陽光開発を対象とし、すべての指標、queue 結果、map field から出典、式、適用制約へ追跡できます。

静的 frontend と FastAPI backend を分離しています。frontend はデータ読込と表示、Python は file 読込、health、field/space query、aggregate、recommendation ranking を担当します。基礎データは当面独立 JSON/GeoJSON とし、DB/SQLite は後続開発で決めます。

## 実行

`uv` を install し、本 directory で実行します。

```bash
uv run python -m terrai_spatial serve --port 4176
```

`http://localhost:4176/` を開きます。一つの command で以下を起動します。

- 顧客 frontend：`http://127.0.0.1:4176/`
- FastAPI / 対話文書：`http://127.0.0.1:8000/docs`

実行時に DB や外部 API Key は不要です。basemap、分析結果、2023–2024 Satellite Embedding crop は local cache 済みです。

`serve` は二 service 起動前に data task を確認します。欠けた packaged foundation data は local Git から優先復旧し、remote-sensing/map cache 不足は対応 download script、欠落・古い派生結果は自動再構築します。Git ignore の TEPCO raw cache がなければ公式 ZIP を download/parse するため、通常 GitHub clone の最初の online 起動で原 CSV も揃います。実行 task は terminal に表示されます。network 禁止は `--offline`、完全性確認済みなら `--no-ensure-data` を使います。

別々にも起動できます。

```bash
# Backend API と /docs
uv run python -m terrai_spatial api --port 8000

# Frontend（既定 API: http://127.0.0.1:8000/api/v1）
uv run python -m terrai_spatial frontend --port 4176
```

主要 command：

```bash
uv run python -m terrai_spatial validate
uv run python -m terrai_spatial data status
uv run python -m terrai_spatial data ensure
uv run python -m terrai_spatial data update
uv run python -m terrai_spatial data update --only tiles
uv run python -m terrai_spatial data update --only embedding
uv run python -m terrai_spatial data update --only grid
uv run python -m terrai_spatial build
uv run python -m terrai_spatial build --only joint
```

`uv.lock` が FastAPI、Uvicorn、Python 環境を固定します。Satellite Embedding 再取得時だけ optional `remote` dependency を導入します。

## FastAPI

| Endpoint | 用途 |
|---|---|
| `GET /api/v1/health` | service と18 file dataset の準備状態 |
| `GET /api/v1/catalog` | file catalog、type、件数、更新時刻 |
| `GET /api/v1/bootstrap` | 初回展示に必要な完全契約 |
| `GET /api/v1/datasets/{key}` | 安定 key で JSON/GeoJSON を読む |
| `GET /api/v1/features/{key}` | field、range、bbox、sort、limit query |
| `GET /api/v1/recommendations/{analysis}` | Python 順位付け済み行動 queue |
| `/api/v1/assets/*` | local tile と遥感画像 |

frontend は `data/` を直接読みません。file location、cache、filter、aggregate、rank は Python にあります。[呼び出し時系列](../architecture/FRONTEND_BACKEND.ja.md)を参照してください。

Data task は script としても実行できます。

```bash
uv run python scripts/ensure_data.py status
uv run python scripts/ensure_data.py ensure
uv run python scripts/ensure_data.py update --only joint
uv run python scripts/build_joint_analysis.py
uv run python scripts/build_multiscale_evidence.py
uv run python scripts/fetch_visual_tiles.py
uv run --extra remote python scripts/fetch_google_satellite_embedding.py
uv run python scripts/fetch_tepco_grid.py
uv run python scripts/update_tepco_grid.py
uv run python scripts/parse_tepco_grid.py
```

### 自動復旧境界

- `bootstrap`：欠落/破損 base GeoJSON/CSV/JSON を `git show HEAD:<path>` で原子的復旧。source archive は GitHub fallback、private repository は `GITHUB_TOKEN` 必須。
- `tiles`、`embedding`：cache 不足時だけ起動時 download。`data update` は強制更新。
- `joint`、`evidence`：出力不足/破損、または script/input より古ければ再構築。
- `grid`：最初の online 起動で公式 TEPCO ZIP、期待2 CSV を検証・展開し summary を再構築。raw と hash/time metadata は Git ignore。明示更新は `data update --only grid`、`fetch tepco`、`build --only grid`。
- `--offline`：network 禁止。commit 済み summary は raw CSV なしで利用でき、既存 ZIP/CSV cache から再構築可。不足時は明確に停止。
- 復旧失敗時は partial data で server を起動せず、task、input、復旧方法を表示。

## 監査可能値と三言語 UI

- metric、説明、action queue、score、popup の破線値から共通 audit drawer を開きます。
- **観測 data**：publisher、source field、snapshot、local evidence、limits。
- **model output**：model/version、input/output、不確実性、local validation。Google AEF に pixel confidence interval がないため「未校正」と明示。
- **計算 data**：式、代入値、結果、lineage。risk/suitability/joint score は heuristic で確率ではない。
- 「中 / 日 / EN」は即時切替し、local と `?lang=zh|ja|en` に保存。

## 内部製品アーキテクチャ（顧客 navigation ではない）

| 層 | 責務 | 現在 |
|---|---|---|
| **FL** | 許諾された現実証拠と決定論加工、missing/時点/解像度/license を保持 | 公開・公式6 source group と local derivative 接続済み |
| **SL** | 予測可能 missing の非破壊 augmentation、不確実性/model identity/lineage/abstention | 概念定義済み、横浜/茂原地表補完 **0** |
| **AL** | 適格 FL/SL 上の場面 rule、rank、review、action | 斜面、道路、施設、太陽光 Demo 接続済み |

Google Satellite Embedding は外部 FL で TerrAI SL ではありません。capacity proxy と risk/suitability score は透明 AL 計算です。所有、許認可、正式系統、構造安全は権威 data/due diligence まで unknown のままです。

- [概念 architecture](../architecture/FL_SL_AL_CONCEPT.ja.md)
- [refactor 背景と判断理由（英語）](../refactor/fl-sl-al-platform/00-overview.md)
- [本 PR の段階 plan（英語）](../refactor/fl-sl-al-platform/01-concept-layers-pr1a.md)
- [frontend–backend 呼び出し時系列](../architecture/FRONTEND_BACKEND.ja.md)

FastAPI v1 は最小 read/query/rank 境界だけを作り、正式 schema、model registry、orchestration、DB、tenant、deployment は後続です。

### 現在の費用結論

- **実行時有料 data/analysis service：0。** offline でも全 module を表示可能。
- **core 再生成に DB 購入/Earth Engine 不要。** Satellite Embedding は公開 COG mirror、他は公開 download/API と local compute。
- 無料アクセスは無条件商用ではありません。GSI は出典/加工/測量法/第三者制約、OSM は ODbL、TEPCO CSV は無料読込可能でも open license でなく再公開前 review 必須。
- 接続済み data の個別説明は [`docs/data`](../data/README.ja.md)、候補評価は [`open-data-landscape.ja.md`](open-data-landscape.ja.md)。

### Demo が使う外部6 source group

| Source | 用途 | 費用 | 主な制約 |
|---|---|---|---|
| GSI DEM5A と map/image/relief/slope tile | 地形・目視確認 | 無料、local cache | 出典・加工表示、測量法/第三者制約の可能性 |
| Google Satellite Embedding V1 mirror | 2023→2024変化、類似、将来少数label | 無料 COG、Google account 不要 | CC BY 4.0 指定出典、64Dは土地 class でない |
| OpenStreetMap | 建物、道路、水域、土地、送電線 | 無料、local GeoJSON | ODbL、完全性保証なし |
| 横浜 open data | 公式地域防災拠点 | 無料 CSV | 原則 CC BY 4.0、出典/加工/第三者権利 |
| NASA POWER | 茂原日射気候 | 無料 API、cache | credit、endorsement 不可、地点発電量でない |
| TEPCO 公開系統情報 | 地域容量 screening | 無料 ZIP/CSV、自動 local download | **open license でない**、転載禁止、接続確約でない |

## 八つの顧客入口

1. **意思決定概要**：横浜レジリエンスと茂原再エネを切替。
2. **都市レジリエンス案件**：community solar-storage node と複合点検 corridor。
3. **太陽光開発 ready**：deliverable candidate、rule conflict、TEPCO signal。
4. **建物斜面 risk**：保土ケ谷 2,128 棟の地形 exposure。
5. **道路 continuity**：272 road segment の点検・community impact priority。
6. **公共施設改修**：横浜公式2防災拠点の opportunity queue。
7. **太陽光候補地**：茂原70 cell の suitability。
8. **証拠と信頼性**：10 m embedding 年次変化、類似、項目監査。

## Google 遥感の選択

### Satellite Embedding V1：接続済み

- Source Cooperative 公開 COG、CC BY 4.0、Google/Google DeepMind 製造。
- 横浜7,820、茂原19,877の有効10 m pixel。
- 2023/2024 年次 embedding。
- 64D cosine 変化、類似、将来少数label転移。土地class解釈・現score入力なし。

```bash
uv run --extra remote python -m terrai_spatial fetch embedding
```

### Dynamic World：削除

CC BY 4.0 でも公式 access は Earth Engine 依存で商用 usage fee が発生します。追加 DB/service 購入ゼロ制約から UI、metadata、registry、adapter を削除。解釈可能土地被覆は ESA WorldCover、最近の spectral evidence は local Sentinel-2 L2A を評価します。

## FL multiscale 基盤と SL 計画

| Scale | Data | Demo の役割 |
|---|---|---|
| 5–10 m raster | GSI DEM、Satellite Embedding | 地形、変化、類似 evidence |
| Object | 建物、道路、公式施設、solar grid | 行動可能 asset |
| 100–300 m neighborhood | service area、road influence、evidence zone | demand、accessibility、facility gap |
| Region/portfolio | grid gate、project queue、coverage | investment rank、stop condition |

`geo_pfn` 羽田実験は25–50 complete context 孔の中疎域で SL 機構証拠を提供しますが、密/極端疎で最良 model は異なり、点予測、不確実性、sample 誤差順位は別検証が必要です。SL は model portfolio、密度別選択、校正、abstention を使い、一 model で地図を埋めません。横浜/茂原の地表精度とは主張しません。

## 四つの視覚証拠

- **標準**：GSI 標準地図。
- **画像**：最新 seamless orthophoto。高 zoom は主に航空、一部衛星。
- **起伏**：DEM5A/5B/10B hillshade。
- **傾斜**：同 elevation evidence の slope map。

全 pilot tile は local cache。更新：

```bash
uv run python -m terrai_spatial fetch tiles
```

## 1 + 1 + 1 > 3

- **Community solar-storage resilience hub**：低傾斜、高 roof capacity proxy、重要道路近接、周辺 high-risk 建物 service。
- **公式施設改修案件**：実在横浜防災拠点に先に適用し、algorithm 発見補助 node と公式 identity を分離。
- **複合介入 corridor**：high-priority road、exposed-building density、平均 risk を組合せ drainage/slope/inspection package を作る。
- **Deliverable solar cell（茂原）**：road logistics、earthwork slope、transmission distance を強め「適地」を「先に踏査」へ絞る。横浜とは直接 join しない独立 product。

```bash
uv run python -m terrai_spatial build --only joint
uv run python -m terrai_spatial build --only evidence
```

`data/joint/` に `resilience_hubs.geojson`、`compound_corridors.geojson`、`solar_delivery_cells.geojson`、`joint_summary.json` を出力します。

## 公開系統容量 screening

TEPCO 千葉「系統の予想潮流等」を接続済みです。Git は標準 summary だけを保存し、転載禁止 ZIP/CSV と local hash metadata は保存しません。snapshot は HTTP `Last-Modified`、取得時刻/SHA-256 は local audit metadata にあります。

- 千葉：送電線175、変電設備201 record。
- 茂原 match：関連4 line、茂原配電変電所1。
- 茂原：local空容量 proxy 5 MW、上位制約後0 MW、平常時出力制御可能性。

```bash
uv run python -m terrai_spatial fetch tepco
uv run python -m terrai_spatial data update --only grid
uv run python scripts/update_tepco_grid.py --force
uv run python scripts/update_tepco_grid.py --offline
uv run python -m terrai_spatial build --only grid
```

出力は `data/mobara/tepco_grid_screen.json`。自動取得は権利条件を変えず、地域発見/事前相談順位専用で正式接続検討ではありません。CSV geometry は各 cell への容量配賦に不足します。[`tepco-grid.ja.md`](../data/tepco-grid.ja.md) を参照。

## 重要境界

全 score は透明な相対 heuristic であり、次と同義ではありません。

- 建物構造安全・確定災害。
- 実 roof usable area、発電量、storage 設計。
- 道路停止確率・緊急通行保証。
- 所有、環境許認可、地質災害法令、系統容量、接続確約。

pilot 前に横浜では公共建物属性、実屋根、公式 hazard depth/zone、配電制約、茂原では登記筆、MAFF 2026筆、地価/都市計画/保護区、案件単位系統相談を優先します。

購入不要の確認済候補は ESA WorldCover、Sentinel-2 L2A、GSI Hazard open layer、MAFF筆、登記地図、MLIT不動産API、国土/環境GIS、METI FIT/FIP です。Dynamic World は評価後除外記録だけに残します。詳細：[`open-data-landscape.ja.md`](open-data-landscape.ja.md)。

## 元 Demo

- `../terrai_slope_screen_poc`
- `../terrai_resilience_road_poc`
- `../terrai_solar_site_screen_poc`

個別手法・生成過程の追跡用に残しています。

## Project 構造

```text
terrai-spatial-intelligence/
├── pyproject.toml              # uv project / optional remote dependencies
├── uv.lock                     # reproducible environment lock
├── terrai_spatial/             # FastAPI backend / unified CLI
│   ├── api.py                  # health/catalog/data/query/recommendations
│   ├── data_service.py         # file cache/query/aggregate/ranking
│   └── data_tasks.py           # startup/manual task registry
├── frontend/                   # static customer frontend
│   ├── index.html
│   ├── app.js
│   ├── audit.js
│   ├── i18n.js
│   └── styles.css
├── scripts/                   # acquisition/rebuild pipeline
├── docs/                      # architecture/data/summary は三言語、refactor は英語
│   ├── architecture/          # 現行 concept と frontend/backend call sequence
│   ├── data/                  # 接続済み FL dataset card と license 注意
│   ├── refactor/              # 英語 refactor overview と PR plan
│   ├── summary/               # 評価、検証、project decision
│   └── others/                # 最終手段の未分類文書
└── data/                      # FL snapshot/result、DB 未使用
```
