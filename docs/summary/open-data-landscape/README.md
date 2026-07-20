# Data Sources and Licensing

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

Updated 2026-07-20. This inventory covers data used, confirmed script-accessible, or excluded after evaluation for the current TerrAI directions: solar siting, road/facility resilience, and slope exposure. It is not an exhaustive global geodata catalog.

## How to read this inventory

- **Integrated**: the Demo contains real downloaded data or local products derived from it; runtime needs no network, API key, or paid service.
- **Available**: an official bulk download, COG, GIS, or API exists, but its values are not used in the current Demo.
- **Excluded after evaluation**: access platform, commercial cost, or duplication conflicts with the zero-purchase constraint.
- **Free** means no current data purchase fee. Storage/compute/network, free accounts or keys, attribution, share-alike, Survey Act procedures, and statutory due diligence may still apply.

## One-page asset catalog

### Used by the current Demo

| Source | Status | Use | Data/service cost | Commercial use and limits |
|---|---|---|---|---|
| GSI DEM5A | Integrated | Slope, relief, low points, building/road terrain exposure | Free download; free account; local compute | Attribute and identify processing under GSI rules; some reproduction/use of Fundamental Geospatial Data may require Survey Act procedures |
| GSI standard, latest imagery, hillshade, and slope tiles | Integrated | Basemap and visual review of roofs, vegetation, surface, ridges, valleys | Free online access; pilot tiles cached | Do not call all latest imagery satellite imagery; attribution required; some layers include third-party/statutory limits; review before offline republication |
| Google Satellite Embedding V1 / AEF | Integrated | 10 m annual change, similar areas, future sparse-label transfer | Free Source Cooperative COG mirror; no Google account; local compute | CC BY 4.0 and specified attribution; mirror is unsupported by Google; 64-D axes are not land classes and do not enter current scores |
| OpenStreetMap | Integrated | Buildings, roads, water, land use, transmission lines | Free download and local processing | ODbL attribution/share-alike may apply to public derivative databases; completeness/freshness not guaranteed; do not abuse public OSM tile servers |
| Yokohama Regional Disaster-Prevention Bases | Integrated | Official facility identity, address, location, joined to roofs/roads/community demand | Free CSV | Default CC BY 4.0, commercial use allowed; attribute and mark changes; third-party rights remain; roof/capacity/service areas are TerrAI proxies |
| NASA POWER | Integrated | Long-term solar climate context for Mobara | Free API; result cached | NASA data is generally open; credit recommended, no implied endorsement; climate means are not site-level yield models |
| TEPCO “Expected Power Flows, etc.” | Integrated, restricted | Regional spare-capacity/upstream-constraint screen and consultation ranking | Free public ZIP/CSV; automatic official download | **Not open-licensed**; notice says redistribution prohibited; provisional simplified values do not guarantee connection. Raw files stay outside Git; public/commercial redistribution requires rights review and formal connection study |

### Confirmed script-accessible, not used by the Demo

| Source | Modules | Added value | Cost/access | Key limits |
|---|---|---|---|---|
| ESA WorldCover 2020/2021 | Solar, remote-sensing interpretation | Global 10 m, 11 classes, quality layer | Direct free COG, CC BY 4.0 | Only 2020/2021; algorithm versions differ, so all differences are not real change |
| Copernicus Sentinel-2 L2A | Solar, post-disaster/construction change | Reflectance, NDVI/NDWI/NDBI, seasonal change | Open data; free Data Space account/quota; local compute | Cloud/shadow/date/composite QA required; 10 m is unsuitable for single-roof diagnosis |
| GSI Hazard Map Portal open layers | Slope, roads, facilities | Landslide, flood, pluvial, tsunami background | Open layers free and commercially usable | Check each layer's open-data flag, authority, date, and scale; visual tiles do not replace statutory source data |
| MAFF field polygons | Solar | Farmland boundaries and conversion-sensitivity screening | Free bulk download; Chiba 2026 about 318 MB | Attribute/identify processing; not ownership, parcel number, or conversion permission |
| Ministry of Justice registry maps | Solar | Parcel shapes, lot numbers, candidate assemblage | Free after login, GML/map data | No public owner list; includes Article 14 maps and less-accurate map-equivalent drawings that do not establish boundaries |
| MLIT Real Estate Information Library | Solar, investment | Transactions, land prices, planning, hazards/facilities | Free API after application/review/key | Required notice, rate/service change; incomplete/non-real-time; not for important-matters explanations or building confirmation |
| National Land Numerical Information / Environmental GIS | Solar exclusion | Parks, conservation, wildlife protection, forests | Mostly free GIS downloads | Confirm commercial-use terms per dataset; accuracy/update periods differ; authorities decide final applicability |
| METI FIT/FIP published business plans | Solar market | Approved projects, capacity, competition/cluster context | Free public search/files | Not a complete operating-asset inventory; scale/address publication limits; review current reuse terms |
| e-Stat statistical GIS boundaries | Expansion | Administrative/statistical aggregation, population/demand normalization | Free download | Statistical expression only, not legal boundaries; follow attribution/use terms |

### Not reliably obtainable from purely open data

| Needed information | Why missing | MVP acquisition |
|---|---|---|
| Actual land/building owners, mortgages, complete rights | Public cadastral maps do not publish full owner lists | Customer-authorized registry certificates, maps/survey drawings, or compliant paid queries |
| Parcel-level grid capacity, schedule, contribution | Public values are regional screens affected by upstream/operating conditions | Preliminary consultation/formal connection study with the distribution utility |
| Approval outcome for farmland conversion, forest development, protected areas | Open layers show scope, not case-specific discretion/current conditions | Authority pre-consultation, legal/engineering advisers, and field documents |
| Roof load, emergency road passability, slope stability | Imagery/DEM/outlines are proxies | Field survey and structural/geotechnical/road-engineering and operator records |

## Geospatial Information Authority of Japan (GSI)

- Data: Fundamental Geospatial Data DEM5A; standard map, latest nationwide imagery, hillshade, and slope tiles.
- Use: slope, local relief, low points, surface review, basemap.
- Layer list: https://maps.gsi.go.jp/development/ichiran.html
- Cached tile IDs: `seamlessphoto`, `hillshademap`, `slopemap`.
- Latest imagery at ZL14–18 is mainly orthophotography and partly satellite imagery such as Landsat-8; do not call every pixel satellite imagery.
- Cost: free; DEM download needs free registration; avoid excessive official-tile load.
- Terms: attribute and mark processing. Some use of Fundamental Geospatial Data may require Survey Act procedures; tiles may contain third-party or statutory restrictions.
- Terms: https://maps.gsi.go.jp/help/termsofuse.html
- Download notes: https://service.gsi.go.jp/kiban/app/help/

## Google Satellite Embedding V1 / AlphaEarth Foundations (integrated)

- Annual 64-D surface embeddings since 2017 at 10 m; the PoC uses 2023/2024.
- Source Cooperative public COG mirror; unsupported by Google; produced by Google and Google DeepMind.
- License: CC BY 4.0. Attribution: `The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`
- Local products: annual cosine-change PNG, 2024 similarity RGB, 300 100-m evidence cells, source VRT identifiers.
- Use: anomaly review, similarity retrieval, future few-label transfer; no current suitability/resilience score input.
- Catalog: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
- Mirror: https://registry.opendata.aws/aef-source/
- Cost: no data purchase, Google account, or Earth Engine through the mirror; TerrAI pays its own network/storage/local compute. Google's official GCS path is provider-pays but unused here.

## Google Dynamic World V1 (excluded)

- Data is CC BY 4.0, but official distribution and bulk analysis rely on Earth Engine; commercial TerrAI use requires a commercial project and usage fees.
- Removed from UI, scripts, registry, derivative metadata, and adapters under the no-paid-service decision.
- Alternatives: ESA WorldCover for static interpretable classes; local Sentinel-2 L2A for recent spectral/change evidence. Neither can replace Dynamic World class probabilities without validation.
- Catalog: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
- Pricing: https://cloud.google.com/earth-engine/pricing

## Yokohama Regional Disaster-Prevention Bases (integrated)

- Yokohama CSV for regional disaster bases and temporary shelters for stranded commuters, updated 2026-04-01.
- Default Yokohama Open Data license is CC BY 4.0; commercial use allowed with attribution and change notice; user handles third-party rights.
- The PoC selects two official bases inside the Hodogaya study window; position, name, and address are observed official fields.
- Nearest roof, PV capacity, road distance, and 250 m high-risk-building association are explicit PoC proxies.
- Resource: https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv
- Terms: https://data.city.yokohama.lg.jp/terms.html

## Copernicus Sentinel-2 (confirmed, not cached)

- Sentinel-2 L2A multispectral surface reflectance via Copernicus Data Space STAC.
- Planned NDVI, vegetation activity, bare land, seasonal, and before/after construction change.
- Docs: https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- Data is free/open; account, quotas, and service terms apply. TerrAI can process locally without buying a commercial database.
- Cloud/shadow masks, dates, and quality flags are required before integration; single-scene color does not become a siting score.

## OpenStreetMap

- Buildings, roads, water, land use, transmission lines for exposure, networks, setbacks, and context.
- ODbL; free commercial use with attribution and possible share-alike for public derivative databases.
- OSMF does not promise free production APIs/tiles; the Demo uses local data.
- https://www.openstreetmap.org/copyright

## NASA POWER

- 2001–2020 solar climatology, `ALLSKY_SFC_SW_DWN`.
- Mobara context: annual mean GHI about 1,378 kWh/m².
- https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
- Free API. NASA data is generally not US-copyrighted; credit, no logo, no implied endorsement, and dataset-specific notices still apply.

## TEPCO public system information (integrated)

- Chiba transmission-line and transformer “Expected Power Flows, etc.” CSV. The program versions data from actual ZIP `Last-Modified` and local retrieval time, not a hard-coded page announcement date.
- On the first online startup after a normal clone, the task downloads the official Chiba ZIP, validates it and two expected CSVs, extracts atomically to `data/external/tepco/`, then parses. Complete caches are not repeatedly downloaded; `uv run python -m terrai_spatial fetch tepco` refreshes.
- `download_metadata.local.json` stores URL, retrieval time, HTTP `Last-Modified`/ETag, byte counts, and SHA-256 for ZIP/CSVs. It and raw files are Git-ignored.
- Standard output: `data/mobara/tepco_grid_screen.json`.
- Mobara signal: transformer-local spare-capacity proxy 5 MW; 0 MW after upstream constraints; normal-operation output control may apply.
- Official page: https://www.tepco.co.jp/pg/consignment/system/index-j.html
- Free public HTTPS download with no database, key, or Earth Engine; this is not an open-data license.
- Notice says redistribution prohibited; geometry is insufficient for parcel joins; values are provisional simplified data and not a connection commitment. Confirm rights before distributing raw or reversibly reconstructed data commercially.
- Notes: https://www.tepco.co.jp/pg/consignment/system/pdf/yosouchoryu_points_to_note.pdf

## Custom joint-analysis assumptions

- Roof PV proxy: footprint area × 60% usable × 0.20 kWp/m² = footprint × 0.12 kWp.
- Service demand: count of high-risk-building associations within 150 m of a hub.
- Road influence: buildings within 55 m of road centerlines.
- Distances use a planar approximation near latitude 35.45°; production should use a suitable projected CRS.
- Associations may count one building more than once. They rank candidates and are not independent beneficiaries or avoided losses.

## Scriptable entry points

- ESA WorldCover: https://esa-worldcover.org/en/data-access
- Copernicus Data Space: https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- GSI Hazard Map open data: https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html
- MAFF field polygons: https://www.maff.go.jp/j/tokei/census/shuraku_data/2025/mb/index.html
- Ministry of Justice registry maps: https://www.moj.go.jp/MINJI/minji05_00494.html
- MLIT Real Estate API: https://www.reinfolib.mlit.go.jp/help/apiManual/
- National Land Numerical Information: https://nlftp.mlit.go.jp/ksj/
- METI FIT/FIP: https://www.fit-portal.go.jp/PublicInfoSummary
- e-Stat GIS: https://www.e-stat.go.jp/gis/statmap-search?aggregateUnitForBoundary=A&page=1&type=2

Machine-readable integration status is in `data/external/source_registry.json`. It lists batch-processable sources only, not marketing screenshots or untraceable manual samples.
