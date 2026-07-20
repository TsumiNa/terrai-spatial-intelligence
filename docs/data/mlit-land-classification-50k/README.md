# MLIT 1:50,000 Land Classification Survey
[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## Data description
Map-sheet Shapefiles covering geology, soil and related classification themes; source vintage and schemas vary by sheet. TerrAI clips Yokohama and Mobara to GeoJSON and preserves original fields, layer names and timestamps.
## Source
[National Land Survey download](https://nlftp.mlit.go.jp/kokjo/inspect/landclassification/download.html)
## Use in this project
FL evidence for slope stability, construction constraints, infiltration and site due diligence. API key: `landClassification50k`; refresh: `uv run python -m terrai_spatial data update --only mlit`.
## License
Public Data License 1.0 is the current default; attribution and edited-data notice are required.
## Commercial-use cautions
Some background-map survey products may require Survey Act procedures. Do not redistribute the original package unchanged; verify each map sheet before customer delivery.
