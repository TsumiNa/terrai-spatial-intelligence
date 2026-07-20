# OpenStreetMap

[中文](openstreetmap.md) | [日本語](openstreetmap.ja.md) | [English](openstreetmap.en.md)

- FL status: Integrated and converted to local GeoJSON
- Types: buildings, roads, water, land use, transmission lines

## Source

OpenStreetMap community database: https://www.openstreetmap.org/copyright . The Demo uses downloaded and standardized local data, not public APIs or tile servers at runtime.

## Use in this project

Building footprints support slope exposure and roof-capacity proxies; roads support continuity, accessibility, and solar logistics; water/land use support setbacks and context; transmission lines provide distance proxies in Mobara. Main products are under `data/yokohama/`, `data/mobara/`, and `data/joint/`.

## License

Open Database License (ODbL). Attribute OpenStreetMap contributors; publicly distributed derivative databases may trigger share-alike obligations.

## Commercial-use cautions

ODbL obligations differ for databases and produced works, so classify commercial deliverables before release. Crowdsourced completeness, accuracy, and freshness are not guaranteed; absence is not proof that an object does not exist. Do not rely on or overload public production APIs/tiles.
