# TEPCO ローカル専用ソースファイル

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

本ディレクトリでは、東京電力 Power Grid の元 ZIP、CSV、ローカル取得メタデータを意図的に Git 管理外としています。ファイルは無償取得できますが、公式注意事項には転載禁止と記載されています。

アプリケーションは東京電力の公式 URL から直接取得できます。ブラウザでの手作業、データベース購入、API Key は不要です。

1. [公式系統情報ページ](https://www.tepco.co.jp/pg/consignment/system/index-j.html)で現行条件と注意事項を確認します。
2. `uv run python -m terrai_spatial fetch tepco` または `uv run python scripts/update_tepco_grid.py --force` を実行します。
3. downloader は ZIP を検証し、`csv_yosochoryu_chiba_soudensen.csv` と `csv_yosochoryu_chiba_hendensyo.csv` だけを展開し、取得時刻、HTTP metadata、SHA-256 を `download_metadata.local.json` に記録します。
4. parser は Demo 用の標準化スクリーニング概要を `data/mobara/tepco_grid_screen.json` に書きます。

通常の Git clone 後、最初にオンラインで `terrai serve` を起動すると、Git 管理外キャッシュの不足を検知し、同じ取得・解析経路を自動実行します。キャッシュ完成後は再取得しません。`--offline` はローカルソースがなくてもコミット済み概要を表示でき、既存 ZIP/CSV からの再構築もできますが、ネットワーク要求はすべて拒否します。

東京電力 Power Grid の許可を確認せず、取得した原ファイルをコミットまたは再配布しないでください。
