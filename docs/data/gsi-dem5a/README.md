# GSI DEM5A

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated
- Publisher: Geospatial Information Authority of Japan (GSI)
- Native resolution: 5 m

## Data description

- **Format** — GML elevation tiles from the GSI Fundamental Geospatial Data DEM series. This project does not ship the raw GML; it stores the values derived from it as attributes on the local GeoJSON products.
- **Resolution** — DEM5A, 5 m grid spacing. Elevation is metres above mean sea level (T.P.).
- **CRS** — JGD2011 geographic coordinates in the source; all derived products are written as WGS84 GeoJSON (EPSG:4326).
- **Coverage cached here** — only the two demo bounding boxes: Yokohama Hodogaya (139.5835–139.5935 E, 35.4426–35.4504 N) and Mobara (140.2757–140.2913 E, 35.4387–35.4513 N).
- **Fields the project reads** — `elevation_m` (m), `slope_deg` (degrees), `local_relief_m` (m), `low_point_m` (m), and `dem_source`, which records the DEM product behind each value. All 2,128 Yokohama buildings currently carry `dem_source = "DEM5A"`.
- **Volume** — terrain attributes on 2,128 building polygons, 272 road segments, and 70 Mobara candidate cells.
- **Known gaps** — DEM5A exists only where airborne laser survey has been flown; other areas fall back to coarser products, which is why `dem_source` is stored per feature. Vegetation, structures, and measurement error mean the surface is not a clean bare-earth model, and slope in degrees is a terrain measurement, not a slope-stability conclusion.

## Source

GSI Fundamental Geospatial Data DEM5A. Download requires free registration. Documentation: https://service.gsi.go.jp/kiban/app/help/

## Use in this project

Provides elevation, slope, local relief, low-point proxies, and building/road terrain exposure in Yokohama and Mobara. Deterministic slope/relief remains FL and is not hazard probability or slope-stability judgment. Local derivatives include terrain fields in `data/yokohama/building_risk.geojson`, `road_priority.geojson`, and solar cells.

## License

Use under GSI content-use rules with source and processing attribution; DEM is Fundamental Geospatial Data. Terms: https://maps.gsi.go.jp/help/termsofuse.html

## Commercial-use cautions

Some reproduction, map production, or public-use patterns may require Survey Act procedures. Confirm the exact product and publication method before production use. Vegetation, buildings, and measurement error mean DEM cannot replace field survey or geotechnical judgment.
