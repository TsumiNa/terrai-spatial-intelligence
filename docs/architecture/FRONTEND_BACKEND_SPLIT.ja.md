# 顧客展示版フロントエンド—バックエンド分離

[中文](FRONTEND_BACKEND_SPLIT.md) | [日本語](FRONTEND_BACKEND_SPLIT.ja.md) | [English](FRONTEND_BACKEND_SPLIT.en.md)

状態：Demo 実装済み

日付：2026-07-20

## 目的

顧客 UI は機能、結果、信頼性、追跡可能性だけを明確に回答します。内部の FL → SL → AL 製品概念はアーキテクチャ文書に保持しますが、顧客ナビゲーションや初期画面には出しません。

ブラウザは `data/` 配下のパスを認識せず、直接読みません。

    frontend/ 静的表示
      └─ HTTP JSON → FastAPI /api/v1
                         ├─ data/ JSON / GeoJSON
                         └─ scripts/ Python 生成物

## 責務境界

### フロントエンド

- FastAPI の安定した展示契約を読み込む。
- 地図、凡例、指標、推薦キューを描画する。
- 中/日/英切替とクリック操作を扱う。
- 出典、式、不確実性、制約を表示する。
- ファイルシステムのパスマッピングを持たず、`data/*.json` を直接読まない。
- 推薦順位付けや施設集計を行わない。

### FastAPI バックエンド

- JSON/GeoJSON を読み、ファイル更新時刻でキャッシュする。
- health とファイルデータカタログを提供する。
- フィールド、数値範囲、bbox、並べ替え、件数制限を検索する。
- Python で斜面、道路、太陽光、施設、回廊、デリバリー候補を抽出・順位付けする。
- 展示に必要な施設指標を集計する。
- 読取専用パスから地図タイルとリモートセンシング画像を提供する。

### Python データパイプライン

既存の取得、解析、統合分析、マルチスケール証拠スクリプトは Python のままとし、起動時または利用者コマンドから共通タスク登録表を通じて実行します。API は生成物を読み、リクエスト内で高コスト再構築を行いません。

## 最小 API v1

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/v1/health` | データセット準備状態と出典グループ数 |
| GET | `/api/v1/catalog` | ファイル、型、件数、更新時刻 |
| GET | `/api/v1/bootstrap` | 展示フロントエンドに必要な完全契約 |
| GET | `/api/v1/datasets/{key}` | 安定 key で一つのデータセットを取得 |
| GET | `/api/v1/features/{key}` | where/equals/min/max/bbox/sort/limit 検索 |
| GET | `/api/v1/recommendations/{analysis}` | サーバーで抽出・順位付けした行動キュー |
| GET | `/api/v1/assets/*` | ローカルタイル、画像、読取専用バイナリ |

FastAPI の対話型 OpenAPI は `/docs` で利用できます。

## 現在のストレージ判断

- 独立 JSON/GeoJSON を継続利用する。現在のデータ量と読取専用 Demo には十分である。
- 安定 dataset key がブラウザとファイルパスを分離するため、ストレージ交換時もフロントエンドを書き直さない。
- 現段階では ORM、migration、database schema を導入しない。
- 高頻度差分更新、同時書込、複雑 join、顧客権限、履歴版検索が必要になった時点で SQLite を再評価し、大規模またはマルチテナントではサービス型 DB を検討する。

## 実行方式

`terrai_spatial serve` は一つの開発プロセスで二つの独立リスナーを起動します。

- 4176：静的フロントエンド
- 8000：FastAPI

将来の独立配備に向け、`terrai_spatial frontend` と `terrai_spatial api` で別々に起動することもできます。
