# TEPCO local-only source files

This directory intentionally excludes the original TEPCO Power Grid ZIP, CSV files and local retrieval metadata from Git. The official notice marks redistribution as prohibited even though the files can be downloaded without charge.

The application can download them directly from TEPCO's official URL. No manual browser download, database purchase or API key is required.

1. Review the current terms and notes on the [official system-information page](https://www.tepco.co.jp/pg/consignment/system/index-j.html).
2. Run `uv run python -m terrai_spatial fetch tepco` or `uv run python scripts/update_tepco_grid.py --force`.
3. The downloader validates the ZIP, extracts only `csv_yosochoryu_chiba_soudensen.csv` and `csv_yosochoryu_chiba_hendensyo.csv`, and writes `download_metadata.local.json` with retrieval time, HTTP metadata and SHA-256 hashes.
4. The parser writes the Demo's standardized screening summary to `data/mobara/tepco_grid_screen.json`.

If that summary is missing, the normal `terrai serve` startup check runs the same download-and-parse path automatically. It does not download again when a complete summary is already present. `--offline` permits rebuilding from an existing local ZIP/CSV cache and rejects any network request.

Do not commit or redistribute the downloaded source files without confirming permission with TEPCO Power Grid.
