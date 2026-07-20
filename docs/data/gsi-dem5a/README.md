# GSI DEM5A

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated
- Publisher: Geospatial Information Authority of Japan (GSI)
- Native resolution: 5 m

## Source

GSI Fundamental Geospatial Data DEM5A. Download requires free registration. Documentation: https://service.gsi.go.jp/kiban/app/help/

## Use in this project

Provides elevation, slope, local relief, low-point proxies, and building/road terrain exposure in Yokohama and Mobara. Deterministic slope/relief remains FL and is not hazard probability or slope-stability judgment. Local derivatives include terrain fields in `data/yokohama/building_risk.geojson`, `road_priority.geojson`, and solar cells.

## License

Use under GSI content-use rules with source and processing attribution; DEM is Fundamental Geospatial Data. Terms: https://maps.gsi.go.jp/help/termsofuse.html

## Commercial-use cautions

Some reproduction, map production, or public-use patterns may require Survey Act procedures. Confirm the exact product and publication method before production use. Vegetation, buildings, and measurement error mean DEM cannot replace field survey or geotechnical judgment.
