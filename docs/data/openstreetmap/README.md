# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated and converted to local GeoJSON
- Types: buildings, roads, water, land use, transmission lines

## Data description

- **Format** — community vector data downloaded as an extract and converted to GeoJSON `FeatureCollection` files (EPSG:4326, RFC 7946). No OSM API or tile server is called at runtime.
- **Themes extracted** — building footprints, roads, water bodies, land use, and transmission lines.
- **Granularity** — one feature per OSM object; building features retain `osm_id` so a record can be traced back upstream.
- **Volume** — 2,128 building polygons in `data/yokohama/building_risk.geojson` and 272 road segments in `data/yokohama/road_priority.geojson`; water, land-use, and power context for Mobara in `data/mobara/context.geojson`.
- **Fields the project reads** — `building`, `levels`, `footprint_m2` (m²), `name`, and `osm_id` for buildings; road classification and name for the priority model; `landuse`, `distance_water_m`, `distance_building_m`, and `distance_grid_m` (all metres) for Mobara candidate cells.
- **Vintage** — a point-in-time extract, not a live mirror; OSM itself changes continuously.
- **Known gaps** — coverage is crowdsourced, so completeness, accuracy, and freshness are not guaranteed and the absence of an object is not evidence that it does not exist. `levels` in particular is frequently missing, which is why roof capacity is computed as a proxy rather than read directly.

## Source

OpenStreetMap community database: https://www.openstreetmap.org/copyright . The Demo uses downloaded and standardized local data, not public APIs or tile servers at runtime.

## Use in this project

Building footprints support slope exposure and roof-capacity proxies; roads support continuity, accessibility, and solar logistics; water/land use support setbacks and context; transmission lines provide distance proxies in Mobara. Main products are under `data/yokohama/`, `data/mobara/`, and `data/joint/`.

## License

Open Database License (ODbL). Attribute OpenStreetMap contributors; publicly distributed derivative databases may trigger share-alike obligations.

## Commercial-use cautions

ODbL obligations differ for databases and produced works, so classify commercial deliverables before release. Crowdsourced completeness, accuracy, and freshness are not guaranteed; absence is not proof that an object does not exist. Do not rely on or overload public production APIs/tiles.
