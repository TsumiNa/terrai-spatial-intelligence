# GSI Maps and Visual Tiles

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL status: Integrated and cached for pilot areas
- Layers: standard map, latest nationwide imagery, hillshade, slope map

## Source

GSI layer catalog: https://maps.gsi.go.jp/development/ichiran.html . The project caches pilot tiles including `seamlessphoto`, `hillshademap`, and `slopemap`.

## Use in this project

Basemap and visual review of roofs, vegetation, farmland, water, construction state, ridges/valleys, and slope. Tiles are served through `/api/v1/assets/*`; runtime does not contact GSI. Visual basemaps do not enter scores.

## License

Attribute GSI and identify processing under its content-use rules. Some tiles may contain third-party rights or statutory restrictions: https://maps.gsi.go.jp/help/termsofuse.html

## Commercial-use cautions

“Latest nationwide imagery” is mainly orthophotography at high zoom and only partly satellite imagery; do not call it all satellite maps. Review every layer before public offline redistribution and do not place excessive load on official tile services.
