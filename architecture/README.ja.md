# TerrAI フロントエンド—バックエンド呼び出し構造

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

状態：現在の Demo 実装

更新日：2026-07-21

本書は、顧客向け TerrAI Demo におけるブラウザ、静的フロントエンド、FastAPI、Python データサービス、ファイルベースデータ間の実行時呼び出し構造を説明します。内部の FL → SL → AL 製品概念は `docs/architecture/FL_SL_AL_CONCEPT.ja.md` を参照してください。

## 1. コンポーネントと責務

| コンポーネント | 現在の実装 | 責務 |
|---|---|---|
| 顧客ブラウザ | Chrome、Safari など | ページ読込、モジュール・表示・言語・監査操作 |
| 静的フロントエンド | `frontend/index.html`、`app.js`、`audit.js`、`i18n.js` | 展示 payload を取得し、地図・指標・キュー・三言語 UI を描画。ローカルデータの直接読込、業務結果の計算・並べ替えは行わない |
| FastAPI | `terrai_spatial/api.py` | `/api/v1` HTTP 境界、検証、エラー変換、CORS、OpenAPI、読取専用アセット |
| Python DataService | `terrai_spatial/data_service.py` | 安定 key からファイルを解決し、mtime キャッシュ、検索、地域抽出、集計、推薦キュー順位付けを実施 |
| データタスク | `terrai_spatial/data_tasks.py` と `scripts/` | 起動前に確認・取得・解析・再構築。通常 API リクエスト内では高コスト処理を行わない |
| FL ファイル | `data/**/*.json`、`data/**/*.geojson`、タイル、リモートセンシング画像 | 現在の読取専用ストア。フロントエンド呼び出しを変えずに将来 SQLite へ置換可能 |

既定のローカル待受先：

- フロントエンド：`http://127.0.0.1:4176/`
- API：`http://127.0.0.1:8000/api/v1`
- OpenAPI：`http://127.0.0.1:8000/docs`

`api` クエリパラメータで API origin を上書きできます。

```text
http://127.0.0.1:4176/?api=http://127.0.0.1:9000
```

## 2. 起動時の呼び出し順序

`terrai_spatial serve` はデータ確認と二つの独立 HTTP リスナーを管理します。データが不足・期限切れの場合、タスク登録表が対応する Python スクリプトを実行し、準備完了後にのみフロントエンドと API を起動します。

```mermaid
sequenceDiagram
    autonumber
    actor Operator as 利用者/展示担当者
    participant CLI as terrai_spatial CLI
    participant Tasks as Python Data Tasks
    participant Files as data/ FL ファイル
    participant Scripts as 取得/解析/構築スクリプト
    participant API as FastAPI :8000
    participant Web as Static Frontend :4176

    Operator->>CLI: uv run python -m terrai_spatial serve
    CLI->>Tasks: ensure_data(allow_network)
    Tasks->>Files: 存在、完全性、鮮度を確認
    alt 完全かつ最新
        Files-->>Tasks: ready
    else 不足または期限切れ
        Tasks->>Scripts: 対応タスクを実行
        Scripts->>Files: 生成物を原子的に作成/更新
        Files-->>Tasks: ready
    end
    Tasks-->>CLI: データ確認完了
    CLI->>API: Uvicorn / FastAPI を起動
    API-->>CLI: started
    CLI->>Web: 静的ファイルサービスを起動
    CLI-->>Operator: フロントエンドと /docs URL を表示
```

タスクが失敗すると、`serve` は HTTP サービス起動前に停止し、不足入力または復旧方法を表示します。確認を省くには `--no-ensure-data`、ネットワークを禁止するには `--offline` を使用します。

## 3. 現在の顧客フロントエンドが実際に行うリクエスト

現在の Demo は「一度読み込み、表示をローカル切替」方式です。初回に集約展示契約を一度取得し、モジュール、言語、監査操作では同じ payload を再利用します。地図タイルとリモートセンシング画像は表示範囲に応じて取得します。

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 顧客
    participant Browser as ブラウザ
    participant Frontend as frontend/app.js
    participant API as FastAPI /api/v1
    participant Service as Python DataService
    participant FL as JSON / GeoJSON
    participant Assets as ローカルタイル/リモートセンシング画像

    Customer->>Browser: :4176 を開く
    Browser->>Frontend: HTML/CSS/JS を読み込む
    Frontend->>API: GET /bootstrap
    API->>Service: bootstrap()
    loop 18 個の安定 dataset key
        Service->>FL: mtime を確認
        alt キャッシュなし、またはファイル更新
            Service->>FL: read + json.load
            FL-->>Service: JSON / GeoJSON
        else mtime キャッシュ命中
            Service->>Service: メモリ内コピーを返す
        end
    end
    Service->>Service: 施設集計、地域抽出、推薦順位付け
    Service-->>API: 展示 payload + health/source metadata
    API-->>Frontend: 200 application/json
    Frontend->>Frontend: モジュール、指標、地図、行動キューを描画

    par 表示範囲の地図リソース
        Browser->>API: GET /assets/tiles/...
        API->>Assets: タイルを読む
        Assets-->>API: PNG/JPEG
        API-->>Browser: 画像
    and リモートセンシング証拠オーバーレイ
        Browser->>API: GET /assets/google/...image...
        API->>Assets: 画像を読む
        Assets-->>API: PNG
        API-->>Browser: 画像
    end

    Customer->>Frontend: モジュール/表示/言語を切替
    Frontend->>Frontend: bootstrap 済みデータを再描画
    Note over Frontend,API: 現在は追加 API リクエストなし

    Customer->>Frontend: 破線付き数値をクリック
    Frontend->>Frontend: audit.js が出典/式/制約を表示
    Note over Frontend,API: 監査 metadata は読込済み
```

## 4. 細粒度 API 検索の呼び出し順序

`/bootstrap` と `/assets/*` のほか、FastAPI は OpenAPI 確認、将来のオンデマンド画面、外部クライアント向けに細粒度 API を提供します。

```mermaid
sequenceDiagram
    autonumber
    actor Client as フロントエンド/外部クライアント
    participant API as FastAPI
    participant Service as DataService
    participant FL as JSON / GeoJSON

    Client->>API: GET /features/solar?where=status&equals=preferred&sort=score&limit=20
    API->>API: key、範囲、bbox、limit を検証
    alt key 不明またはファイル利用不可
        API-->>Client: 404
    else パラメータ不正またはデータ型不適合
        API-->>Client: 422
    else 有効なリクエスト
        API->>Service: query_features(...)
        Service->>FL: 安定 key で読込、または mtime キャッシュ命中
        FL-->>Service: FeatureCollection
        Service->>Service: フィールド絞込 → bbox 交差 → 並替 → limit
        Service-->>API: 結果 + matched/returned
        API-->>Client: 200 GeoJSON
    end
```

## 5. エンドポイントと呼び出し元

| エンドポイント | 現在の顧客 UI が呼ぶか | 用途 |
|---|---:|---|
| `GET /api/v1/bootstrap` | はい、起動時に一度 | 全展示データ、サーバー順位付け済みキュー、施設集計、health metadata |
| `GET /api/v1/assets/*` | はい、表示範囲に応じて | ローカル地図タイル、Satellite Embedding 可視化など |
| `GET /api/v1/health` | いいえ、bootstrap metadata に含む | サービスと 18 データセットの独立監視 |
| `GET /api/v1/catalog` | いいえ | 安定 key、ファイル型、件数、更新時刻の確認 |
| `GET /api/v1/datasets/{key}` | いいえ | key で完全な JSON/GeoJSON を取得 |
| `GET /api/v1/features/{key}` | いいえ | フィールド、範囲、bbox、並替、limit による GeoJSON 検索 |
| `GET /api/v1/recommendations/{analysis}` | いいえ、bootstrap に含む | サーバーで抽出・順位付けした行動キューを単独取得 |

## 6. 境界と今後の発展

- API は読取専用で、ブラウザは FL ファイル変更や再構築を起動できません。
- 通常リクエストは取得スクリプトを呼ばず、ページ表示による長時間タスクや外部依存の偶発起動を防ぎます。
- `/bootstrap` は小規模ローカル Demo に適します。規模拡大時は `/features/{key}` と `/recommendations/{analysis}` をモジュール、表示範囲、ページ単位で取得します。
- SQLite 移行時は `/api/v1` のパスと応答意味を維持し、`DataService` 内部の repository/load/query を置き換えます。
- 顧客データ導入時は API の前段に認証、テナント分離、権限監査、バージョン選択が必要です。現 PoC の対象外です。

## 7. コード位置

- フロントエンド API origin と初期要求：`frontend/app.js`
- HTTP ルートとエラー変換：`terrai_spatial/api.py`
- ファイルキャッシュ、検索、集計、キュー：`terrai_spatial/data_service.py`
- 二サービス起動と自動データ確認：`terrai_spatial/cli.py`
- タスク登録と依存関係：`terrai_spatial/data_tasks.py`
- 責務分離の決定：`docs/architecture/FRONTEND_BACKEND_SPLIT.ja.md`
