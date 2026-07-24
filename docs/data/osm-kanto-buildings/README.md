# OSM Kanto Building Footprints

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated, on demand
- Layer: building footprints as data objects for the high-zoom detail layer

## Data description

Building footprints for the mainland-Kanto acquisition window, extracted from the pinned Geofabrik snapshot `kanto-260101.osm.pbf` (extract timestamp 2026-01-01T21:21:30Z): 5,371,292 polygons, each carrying its stable `osm_id`/`osm_type`, the `building` class, `name`/`building:levels` where mapped, and full retrieval provenance. 14 degenerate multipolygons in the source are skipped and counted in the manifest. Coverage is community-mapped: dense in built-up areas, thinner elsewhere — an absent building is not proof of absence.

- **Format** — one GeoJSON FeatureCollection (`buildings.geojson`, ~3.1 GB, MultiPolygon geometries) plus a `metadata.json` manifest.
- **CRS** — EPSG:4326 (WGS 84 longitude/latitude).
- **Bounds** — the mainland-Kanto acquisition window (138.65, 34.85, 140.95, 36.30).

## Source

[Geofabrik extract](https://download.geofabrik.de/asia/japan/kanto.html) of [OpenStreetMap](https://www.openstreetmap.org/copyright) data. Pinned dated snapshot, never `-latest`, so a re-run reproduces the same inventory.

## Use in this project

The primary footprint source of the merged self-hosted building tiles (`osm-basemap-tiles`): OSM identity + tags, with 基盤地図情報 filling the gaps and PLATEAU heights joined in. Rendered as the `terrai-buildings` PMTiles layer, clickable at inspection zoom to a raw audit record built from the baked tile properties — no API call. Refreshed by the `osm_kanto` task, which feeds the offline tile merge. Foundation evidence only — never scored. (The windowed `osmBuildings` served collection was retired in `osm-basemap-tiles` PR5.)

## License

Open Database License (ODbL) 1.0. Attribution "© OpenStreetMap contributors" is mandatory wherever the layer renders.

## Commercial-use cautions

ODbL share-alike applies to derivative databases made public. Completeness and currency are community-driven and unwarranted; tags such as `building:levels` are sparse. Do not present the inventory as an authoritative building register.
