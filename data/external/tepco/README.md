# TEPCO local-only source files

This directory intentionally excludes the original TEPCO Power Grid ZIP and CSV files from Git. The official notice marks redistribution as prohibited even though the files can be downloaded without charge.

To reproduce the regional screening result for internal use:

1. Review the current terms and notes on the [official system-information page](https://www.tepco.co.jp/pg/consignment/system/index-j.html).
2. Download the Chiba predicted-flow ZIP from the official source.
3. Extract these files into this directory:
   - `csv_yosochoryu_chiba_soudensen.csv`
   - `csv_yosochoryu_chiba_hendensyo.csv`
4. Run `uv run python -m terrai_spatial build --only grid`.

Do not commit or redistribute the downloaded source files without confirming permission with TEPCO Power Grid.
