# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated and converted to local GeoJSON
- Types: buildings, roads, water, land use, transmission lines, Sapporo subway/access context

## Data description

- **Format** — community vector data downloaded as an extract and converted to GeoJSON `FeatureCollection` files (EPSG:4326, RFC 7946). No OSM API or tile server is called at runtime.
- **Themes extracted** — building footprints, roads, water bodies, land use, transmission lines, and a bounded Sapporo snapshot of subway tracks/stations/entrances and underground-walkway candidates.
- **Granularity** — one feature per OSM object; building features retain `osm_id` so a record can be traced back upstream.
- **Volume** — 2,128 building polygons in `data/yokohama/building_risk.geojson` and 272 road segments in `data/yokohama/road_priority.geojson`; water, land-use, and power context for Mobara in `data/mobara/context.geojson`. The Sapporo snapshot contains 195 features: 97 subway entrances, 6 subway stations, 8 subway-track ways and 84 underground-walkway candidates; 103 are points and 92 are lines. Six queried walkways tagged only with a numeric surface/upper level and no tunnel or negative-level/layer evidence are retained in neither output nor count.
- **Fields the project reads** — `building`, `levels`, `footprint_m2` (m²), `name`, and `osm_id` for buildings; road classification and name for the priority model; `landuse`, `distance_water_m`, `distance_building_m`, and `distance_grid_m` (all metres) for Mobara candidate cells. Sapporo retains `osm_type`, `osm_id`, `osm_version`, `osm_changeset`, `osm_timestamp`, original `tags`, exact `level`/`layer`, evidence flags and null `depth_m`/`elevation_m`.
- **Vintage** — point-in-time extracts, not a live mirror. The Sapporo OSM base timestamp is 2026-07-21T10:51:01Z and retrieval time is 2026-07-21T10:53:05Z; OSM itself changes continuously.
- **Known gaps** — coverage is crowdsourced, so completeness, accuracy, legal access and freshness are not guaranteed and absence is not evidence that an object does not exist. Sapporo ways are selected by a bbox of 141.349592632–141.356913521° E and 43.054916388–43.070980841° N; complete intersecting source geometry is retained rather than clipped. Missing or ambiguous levels are not converted to depth. An absent access restriction does not prove public access or current opening.

## Source

OpenStreetMap community database: https://www.openstreetmap.org/copyright . The Demo uses downloaded and standardized local data, not public APIs or tile servers at runtime. The exact Sapporo query is committed at `data/osm/sapporo_underground_access/query.overpassql`; `uv run python -m terrai_spatial fetch underground_access_osm` explicitly refreshes the GeoJSON and retrieval metadata through the documented public Overpass endpoint.

## Use in this project

Building footprints support slope exposure and roof-capacity proxies; roads support continuity, accessibility, and solar logistics; water/land use support setbacks and context; transmission lines provide distance proxies in Mobara. Sapporo OSM features provide independent community access/topology context for scene `sapporo-station-underground` and are queried on demand through dataset key `osmSapporoUndergroundAccess`. They remain separate from PLATEAU geometry and do not validate or overwrite it. Main products are under `data/yokohama/`, `data/mobara/`, `data/joint/`, and `data/osm/sapporo_underground_access/`.

The renderer-neutral Sapporo handoff at `data/plateau/uc24_13_sapporo/scene_handoff.json` references the 195-feature GeoJSON as observed access topology with its own OSM snapshot time, query hash, ODbL licence and audit path. It does not snap OSM features to PLATEAU surfaces, infer depth or treat an absent access tag as permission. The handoff is discovered through `data/scenes/underground/catalog.json`; neither file creates another OSM dataset key or enters `/bootstrap`.

## License

Open Database License (ODbL). Attribute OpenStreetMap contributors; publicly distributed derivative databases may trigger share-alike obligations.

## Commercial-use cautions

ODbL obligations differ for databases and produced works, so classify commercial deliverables before release. Crowdsourced completeness, accuracy, accessibility and freshness are not guaranteed; absence is not proof that an object does not exist. Do not claim that candidate walkways are legally public or currently open. Do not rely on or overload public production APIs/tiles.
