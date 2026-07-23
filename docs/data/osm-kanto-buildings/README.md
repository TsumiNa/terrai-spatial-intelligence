# OSM Kanto Building Footprints

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated, on demand
- Layer: building footprints as data objects for the high-zoom detail layer

## Data description

Building footprints for the mainland-Kanto acquisition window, extracted from the pinned Geofabrik snapshot `kanto-260101.osm.pbf` (extract timestamp 2026-01-01T21:21:30Z): 5,371,292 polygons, each carrying its stable `osm_id`/`osm_type`, the `building` class, `name`/`building:levels` where mapped, and full retrieval provenance. 14 degenerate multipolygons in the source are skipped and counted in the manifest. Coverage is community-mapped: dense in built-up areas, thinner elsewhere — an absent building is not proof of absence.

## Source

[Geofabrik extract](https://download.geofabrik.de/asia/japan/kanto.html) of [OpenStreetMap](https://www.openstreetmap.org/copyright) data. Pinned dated snapshot, never `-latest`, so a re-run reproduces the same inventory.

## Use in this project

The high-zoom detail layer: past the handover zoom the basemap's cartographic buildings yield to these footprints, each clickable to its raw audit record. API key `osmBuildings`; refreshed by the `osm_kanto` task. Foundation evidence only — never scored.

## License

Open Database License (ODbL) 1.0. Attribution "© OpenStreetMap contributors" is mandatory wherever the layer renders.

## Commercial-use cautions

ODbL share-alike applies to derivative databases made public. Completeness and currency are community-driven and unwarranted; tags such as `building:levels` are sparse. Do not present the inventory as an authoritative building register.
