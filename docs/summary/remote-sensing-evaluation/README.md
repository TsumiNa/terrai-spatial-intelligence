# TerrAI Remote-Sensing and Terrain Data Integration Plan

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## Integrated and cached locally

| Data | Native level | Platform use | Does not represent |
|---|---:|---|---|
| GSI latest nationwide imagery | ZL17 | Visual review of roofs, vegetation, farmland, water, and construction | A uniform acquisition date or all-satellite imagery |
| GSI hillshade | ZL16 | Ridges, valleys, drainage paths, and microtopography | Hazard probability |
| GSI slope map | ZL15 | Spatial slope variation, construction and slope context | A field survey |
| GSI DEM5A | 5 m | Building/road slope, local relief, low-point proxies | Error-free measurement under vegetation/building occlusion |

All visual tiles are cached as small-area snapshots; runtime does not require the internet.

## Integrated: Google Satellite Embedding V1

Real 2023 and 2024 10 m, 64-D crops exist for both areas:

- Yokohama: 7,820 valid pixels; mean annual cosine change 0.00969; P95 0.01606.
- Mobara: 19,877 valid pixels; mean 0.02278; P95 0.04355.
- Outputs: annual-change heatmap, 2024 similarity RGB, and 100 m evidence cells.

The 64 axes are not independently interpretable. Similarity RGB is a principal-component preview; annual change is `1 - dot(v2023, v2024)` for unit vectors. Neither enters business scores before local hold-out validation.

## Dynamic World: evaluated and removed

The data is CC BY 4.0, but TerrAI commercial Earth Engine use incurs compute charges. To keep zero additional database/analysis-service purchases, Dynamic World was removed from the Demo, pipelines, and integration queue. Evaluate ESA WorldCover for interpretable static land cover and locally processed Sentinel-2 L2A for recent surface or seasonal change.

## Next stage: Sentinel-2 L2A validation

Search through the Copernicus Data Space STAC API, prioritizing:

- cloud-free/low-cloud scenes from the same season;
- the `SCL` layer for cloud, shadow, and snow masks;
- bands B02/B03/B04/B08/B11/B12;
- a 2–5 km buffer around Mobara to reduce edge effects.

Planned products:

1. **NDVI** for active vegetation and persistent cultivation as farmland-conversion sensitivity evidence.
2. **NDWI/MNDWI** for water and seasonally wet areas supplementing OSM setbacks.
3. **NDBI/bare-soil indices** to help distinguish built-up, bare, cultivated, and possible brownfield land.
4. **Multitemporal change** for land-cover change, construction disturbance, and post-disaster change.
5. **Quality flags** recording date, cloud, pixel resolution, and compositing window.

Sentinel-2's 10 m pixels suit Mobara farmland and large-site analysis but not single-roof structural judgments or single-road damage in Yokohama. Use high-resolution orthophotos, building outlines, and field/drone evidence for roofs.

Official documentation: https://documentation.dataspace.copernicus.eu/APIs/STAC.html

## Scenario roles

### Yokohama urban resilience

- High-resolution imagery: roof form, vegetation, and field-verification base.
- DEM/relief/slope: slopes, road gradients, valleys, and low points.
- Sentinel-2: regional vegetation, heat-environment, or post-disaster context only; not single-roof scoring.

### Mobara renewable development

- High-resolution imagery: current site use and road access.
- Sentinel-2: cultivation activity, wetness, seasonal change, and bare land.
- DEM/relief/slope: earthworks, drainage, erosion, and construction access.
- Later join parcel, farmland, protected-area, land-price, and grid CSV data.

## Production quality rules

- Every remote-sensing score retains acquisition date, sensor, bands, resolution, and cloud-mask method.
- Prefer seasonal composites to arbitrary single scenes.
- Manage visual basemaps separately from analytical rasters; attractive imagery is not automatically model evidence.
- Derived indices are screening features only; land status and permission remain governed by authoritative data.
