# GSI Maps and Visual Tiles

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Streamed live, nationwide
- Layers: standard vector map, latest nationwide imagery, hillshade, slope map

## Data description

- **Format** — the standard basemap is the GSI vector tile style (`experimental_bvmap`, z4–16); the raster basemaps are XYZ tiles, 256 × 256 px: `seamlessphoto` (JPEG, z2–18), `hillshademap` (PNG, z2–16), `slopemap` (PNG, z3–15). All stream live from `https://cyberjapandata.gsi.go.jp/xyz`.
- **CRS** — Web Mercator (EPSG:3857), the standard XYZ tiling scheme.
- **Coverage** — nationwide; beyond each source's maximum zoom the UI upsamples instead of requesting tiles that would 404.
- **Vintage** — whatever GSI currently publishes; there is no local snapshot, and the publisher updates the layers independently.
- **Known gaps** — hillshade and slope are *rendered images*, not numeric rasters: they cannot be sampled for elevation or degrees, and any numeric terrain value in this project comes from the DEM products instead.

## Source

GSI layer catalog: https://maps.gsi.go.jp/development/ichiran.html . The project streams `std.json` (vector), `seamlessphoto`, `hillshademap`, and `slopemap`.

## Use in this project

Basemap and visual review of roofs, vegetation, farmland, water, construction state, ridges/valleys, and slope, at any location in the coverage. Tiles stream from GSI at render time and are never stored or redistributed. Visual basemaps do not enter scores.

## License

Attribute GSI and identify processing under its content-use rules. Some tiles may contain third-party rights or statutory restrictions: https://maps.gsi.go.jp/help/termsofuse.html

## Commercial-use cautions

“Latest nationwide imagery” is mainly orthophotography at high zoom and only partly satellite imagery; do not call it all satellite maps. Review every layer before public offline redistribution and do not place excessive load on official tile services.
