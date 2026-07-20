# TEPCO Public System Information

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated; raw-data redistribution restricted
- Scope: Chiba transmission-line and transformer “Expected Power Flows, etc.”

## Data description

- **Format** — a ZIP archive containing two UTF-8 (BOM) CSV files. Each CSV carries a six-row metadata preamble before the header row, so a naive reader that treats row 1 as the header will parse the file incorrectly.
- **Files** — `csv_yosochoryu_chiba_soudensen.csv` (transmission lines) and `csv_yosochoryu_chiba_hendensyo.csv` (substations and transformers).
- **Coverage** — the Chiba area of the TEPCO Power Grid service territory. Equipment is identified by ID and name only; the CSVs carry **no coordinates and no geometry**.
- **Volume** — 175 transmission-line rows and 201 transformer rows in the current snapshot.
- **Fields the project reads** — `equipment_id`, `name`, `voltage_kv` (kV), `circuits`, equipment capacity, `operating_capacity_before_control_mw` (MW), `existing_olr_mw` (MW), `operating_capacity_mw` (MW), `constraint`, and the `flow_from` / `flow_to` endpoints.
- **Vintage and integrity** — the derived output records `source_file_last_modified_at` from the HTTP response, plus the SHA-256 of the archive and of each extracted CSV, so a screening result can be tied to an exact download.
- **Known gaps** — without geometry, values cannot be allocated to a parcel or a candidate cell; the pipeline matches by name text only. Published capacity is a screening indicator, never a guarantee of connection availability. The raw ZIP, CSVs, and retrieval metadata are Git-ignored because the publisher's notice prohibits redistribution — only the derived screen is committed.

## Source

TEPCO Power Grid official page: https://www.tepco.co.jp/pg/consignment/system/index-j.html . The downloader records actual ZIP HTTP `Last-Modified`, ETag, retrieval time, byte count, and SHA-256 instead of hard-coding a page announcement date.

## Use in this project

Raw ZIP/CSV is parsed to `data/mobara/tepco_grid_screen.json` for regional spare-capacity, upstream-constraint, and pre-consultation ranking. Current Mobara signals are 5 MW substation-local spare-capacity proxy, 0 MW after upstream constraints, and possible normal-operation output control. This is not parcel-level capacity or a connection commitment.

## License

Files are publicly downloadable without charge but are **not open-licensed**. Official notes mark redistribution prohibited: https://www.tepco.co.jp/pg/consignment/system/pdf/yosouchoryu_points_to_note.pdf

## Commercial-use cautions

Raw ZIP/CSV and `download_metadata.local.json` are Git-ignored and must not be committed or redistributed without TEPCO permission. Geometry cannot allocate capacity to candidate parcels; values are provisional simplified data. Commercial products must retain limitations and require a formal connection study.

## Retrieval and local cache

This directory intentionally excludes the original TEPCO Power Grid ZIP, CSV files and local retrieval metadata from Git. The official notice marks redistribution as prohibited even though the files can be downloaded without charge.

The application can download them directly from TEPCO's official URL. No manual browser download, database purchase or API key is required.

1. Review the current terms and notes on the [official system-information page](https://www.tepco.co.jp/pg/consignment/system/index-j.html).
2. Run `uv run python -m terrai_spatial fetch grid` or `uv run python scripts/update_tepco_grid.py --force`.
3. The downloader validates the ZIP, extracts only `csv_yosochoryu_chiba_soudensen.csv` and `csv_yosochoryu_chiba_hendensyo.csv`, and writes `download_metadata.local.json` with retrieval time, HTTP metadata and SHA-256 hashes.
4. The parser writes the Demo's standardized screening summary to `data/mobara/tepco_grid_screen.json`.

On the first online `terrai serve` startup after a standard Git clone, the startup check sees that this Git-ignored local cache is missing and runs the same download-and-parse path automatically. It does not download again once the cache is complete. `--offline` can display an existing committed summary without the local source cache, or rebuild from an existing local ZIP/CSV cache, while rejecting every network request.

Run `uv run python -m terrai_spatial fetch grid` to refresh. `--offline` can use the committed standardized summary or rebuild from an existing local cache.
