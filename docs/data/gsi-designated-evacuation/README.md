# GSI Designated Evacuation Data

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated as the national base
- Municipality: Yokohama (`14100`)
- Source update: 2026-01-16 (GSI publication history)
- Access: free direct download; no account, API key, Earth Engine, or paid service

## Data description

- **Distribution** — GSI publishes municipality-level CSV and GeoJSON for designated shelters (`14100_1`) and designated emergency evacuation places (`14100_2`), plus a machine-readable publication-history CSV.
- **Volume** — the current normalized snapshot contains 459 designated-shelter records and 1,796 emergency-place records.
- **Granularity** — a shelter is generally one facility record. Emergency places may contain several building or gymnasium records at one school, so they must not be interpreted as 1,796 distinct sites without aggregation.
- **Hazard fields** — emergency-place records state designation applicability for flood, landslide/debris flow, storm surge, earthquake, tsunami, large fire, inland flooding, and volcanic phenomena.
- **Time metadata** — the normalizer reads `source_updated_at` from GSI publication history and writes a UTC `retrieved_at` to dataset metadata and every feature. These timestamps serve different audit purposes and are not collapsed into one “latest” date.

## Source

- [GSI publication and download page](https://hinanmap.gsi.go.jp/hinanjocp/hinanbasho/koukaidate.html)
- [Designated shelters GeoJSON](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/geoJSON/14100_1.geojson)
- [Designated emergency evacuation places GeoJSON](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/geoJSON/14100_2.geojson)
- [Municipality publication history](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/publicHistoryCSV/publicHistoryListData.csv)

## Use in this project

GSI designated shelters form the national FL base for the facility-resilience view. Yokohama regional disaster-base records validate matching facilities and add local descriptions; unmatched Yokohama records remain explicitly labelled local supplements. GSI emergency-place components contribute hazard-designation evidence after facility-name aggregation, but they are not relabelled as designated shelters.

The normalized FL artifact is `data/external/gsi_evacuation/yokohama_evacuation.geojson`; metadata is stored beside it. The reconciled AL evidence is `data/yokohama/official_facility_resilience.geojson`, and the raw normalized dataset is available from the backend as dataset key `gsiEvacuation`.

Refresh directly with:

```bash
uv run python -m terrai_spatial data update --only gsi_evacuation
```

Startup also runs this task automatically if the files are missing and network access is allowed.

## License

GSI states that its [content terms](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html) apply and use Public Data License 1.0 unless a page says otherwise. Reuse normally requires source attribution; edited or processed content must be identified, and third-party rights remain the user's responsibility.

## Commercial-use cautions

The records are registered by municipalities under the Disaster Countermeasures Basic Act, but GSI warns that data may be outdated or incomplete. A designated emergency evacuation place is hazard-specific and is not the same concept as a designated shelter. Before emergency guidance, customer delivery, or operational decisions, confirm current designation, opening conditions, capacity, accessibility, and detailed hazards with Yokohama City. Pass these cautions to downstream users and never present TerrAI resilience, roof, PV, or access proxies as GSI fields.

