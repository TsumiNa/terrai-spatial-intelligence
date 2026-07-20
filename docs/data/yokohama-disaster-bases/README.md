# Yokohama Regional Disaster-Prevention Bases

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated
- Snapshot: 2026-04-01
- Types: official facility name, address, location

## Data description

- **Format** — a single CSV. The city publishes it in CP932 (Shift-JIS); the evidence pipeline transcodes it to UTF-8 in place the first time it reads the file, so the copy cached in this repository is UTF-8. A freshly downloaded copy is still CP932 and fails a naive UTF-8 read.
- **Columns** — `Type`, `Definition`, `Name`, `Address`, `Lat`, `Lon`, `Kana`, `Ward`, `WardCode`. `Lat` / `Lon` are WGS84 decimal degrees.
- **Granularity** — one row per official disaster-prevention facility (regional disaster base, evacuation site, and related categories distinguished by `Type`).
- **Volume** — 628 facility rows in the `2026-04-01` snapshot (`hinanjo_20260401.csv`).
- **Vintage** — a dated snapshot; the city republishes the file on its own schedule, and the filename carries the snapshot date.
- **What reaches the demo** — only facilities inside the small Yokohama demo bounding box survive the spatial filter, so `data/yokohama/official_facility_resilience.geojson` currently holds **2** features out of the 628 rows.
- **Known gaps** — facility identity, category, address, and coordinates are official. Everything the project adds on top — `matched_roof_area_m2`, `pv_kwp_proxy`, `nearest_road_m`, `served_high_risk_buildings`, `resilience_score` — is a PoC proxy computed from other layers, not a municipal statement about the facility. The file describes designated status; it says nothing about current structural condition, capacity in use, or operational readiness.

## Source

Yokohama regional disaster bases and temporary facilities for stranded commuters CSV: https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv

## Use in this project

Two official bases inside the Hodogaya study window become real action objects for public-facility resilience upgrades. Position, name, and address are official observations. Nearest roof, PV capacity, road distance, and 250 m high-risk-building associations are TerrAI proxies. Output: `data/yokohama/official_facility_resilience.geojson`.

## License

Yokohama Open Data defaults to CC BY 4.0 and permits commercial use with attribution and processing notice. Terms: https://data.city.yokohama.lg.jp/terms.html

## Commercial-use cautions

Users must separately clear third-party rights. TerrAI roof, capacity, service-area, and resilience scores must not be presented as official Yokohama fields, formal upgrade advice, or hazard guarantees. Refresh facility status and snapshot dates regularly.
