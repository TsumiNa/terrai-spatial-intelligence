# GSI Maps and Visual Tiles

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated and cached for pilot areas
- Layers: standard map, latest nationwide imagery, hillshade, slope map

## Data description

- **Format** — XYZ raster tiles, 256 × 256 px, fetched from `https://cyberjapandata.gsi.go.jp/xyz`. PNG for the standard, hillshade, and slope layers; JPEG for the orthophoto layer.
- **Layers and zoom levels cached** — `std` (standard map) at z15; `seamlessphoto` (nationwide latest orthophoto/satellite mosaic) at z15–17; `hillshademap` (DEM-derived hillshade) at z15–16; `slopemap` (DEM-derived slope rendering) at z15.
- **CRS** — Web Mercator (EPSG:3857), the standard XYZ tiling scheme.
- **Coverage cached here** — only the two demo bounding boxes, not any wider area.
- **Volume and layout** — 141 tile files, each listed in `data/tiles/manifest.json`, stored as `data/tiles/<region>/[layer]/<z>/<x>-<y>.<ext>`. The standard layer omits the layer folder segment.
- **Vintage** — a fixed snapshot taken when the cache was built; there is no automatic refresh, and the publisher updates the upstream layers independently.
- **Known gaps** — hillshade and slope are *rendered images*, not numeric rasters: they cannot be sampled for elevation or degrees, and any numeric terrain value in this project comes from the DEM products instead. The cached zoom ceilings bound the maximum visible detail; requesting deeper zooms in the UI upsamples these tiles rather than fetching new ones.

## Source

GSI layer catalog: https://maps.gsi.go.jp/development/ichiran.html . The project caches pilot tiles including `seamlessphoto`, `hillshademap`, and `slopemap`.

## Use in this project

Basemap and visual review of roofs, vegetation, farmland, water, construction state, ridges/valleys, and slope. Tiles are served through `/api/v1/assets/*`; runtime does not contact GSI. Visual basemaps do not enter scores.

## License

Attribute GSI and identify processing under its content-use rules. Some tiles may contain third-party rights or statutory restrictions: https://maps.gsi.go.jp/help/termsofuse.html

## Commercial-use cautions

“Latest nationwide imagery” is mainly orthophotography at high zoom and only partly satellite imagery; do not call it all satellite maps. Review every layer before public offline redistribution and do not place excessive load on official tile services.
