# TEPCO 公開系統情報

[中文](tepco-grid.md) | [日本語](tepco-grid.ja.md) | [English](tepco-grid.en.md)

- FL 状態：接続済み、原 data 再配布制限
- 範囲：千葉送電線・変電設備「系統の予想潮流等」

## 出典

東京電力 Power Grid 公式ページ：https://www.tepco.co.jp/pg/consignment/system/index-j.html 。downloader は実 ZIP の HTTP `Last-Modified`、ETag、取得時刻、byte、SHA-256 を記録し、page 公告日を snapshot に固定しません。

## 本 project での利用

raw ZIP/CSV を `data/mobara/tepco_grid_screen.json` に解析し、地域空容量、上位制約、接続事前相談順位に利用します。茂原 signal は変電所単体5 MW空容量 proxy、上位制約後0 MW、平常時出力制御可能性です。筆単位容量や接続確約ではありません。

## License

無償公開 download 可能ですが **open license ではありません**。公式注意事項は転載禁止です：https://www.tepco.co.jp/pg/consignment/system/pdf/yosouchoryu_points_to_note.pdf

## 商用利用時の注意

raw ZIP/CSV と `download_metadata.local.json` は Git ignore とし、TEPCO 許可なしに commit/再配布しません。geometry は候補筆への容量配分に不足し、値は暫定簡略 data です。商用 product は制約を保持し正式接続検討を必要とします。

## 取得と local cache

本ディレクトリでは、東京電力 Power Grid の元 ZIP、CSV、ローカル取得メタデータを意図的に Git 管理外としています。ファイルは無償取得できますが、公式注意事項には転載禁止と記載されています。

アプリケーションは東京電力の公式 URL から直接取得できます。ブラウザでの手作業、データベース購入、API Key は不要です。

1. [公式系統情報ページ](https://www.tepco.co.jp/pg/consignment/system/index-j.html)で現行条件と注意事項を確認します。
2. `uv run python -m terrai_spatial fetch tepco` または `uv run python scripts/update_tepco_grid.py --force` を実行します。
3. downloader は ZIP を検証し、`csv_yosochoryu_chiba_soudensen.csv` と `csv_yosochoryu_chiba_hendensyo.csv` だけを展開し、取得時刻、HTTP metadata、SHA-256 を `download_metadata.local.json` に記録します。
4. parser は Demo 用の標準化スクリーニング概要を `data/mobara/tepco_grid_screen.json` に書きます。

通常の Git clone 後、最初にオンラインで `terrai serve` を起動すると、Git 管理外キャッシュの不足を検知し、同じ取得・解析経路を自動実行します。キャッシュ完成後は再取得しません。`--offline` はローカルソースがなくてもコミット済み概要を表示でき、既存 ZIP/CSV からの再構築もできますが、ネットワーク要求はすべて拒否します。

`uv run python -m terrai_spatial fetch tepco` で更新します。`--offline` は commit 済み標準 summary を利用、または既存 local cache から再構築できます。
