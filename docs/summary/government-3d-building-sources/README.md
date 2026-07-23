# Government Building Data Sources — Evaluation

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

An evaluation of two government building-data sources for the self-built
basemap and the local 3D work mode. Neither is integrated yet; this records
what they provide, their licence, coverage, and how each mode would use them,
so the `osm-basemap-tiles` and `local-3d-work-mode` refactors can proceed on
confirmed facts.

## Why these two sources

OpenStreetMap building footprints are rich in dense cities (stable `osm_id`,
building type, occasional height) but sparse in suburban and rural Japan. A
map drawn from OSM alone reads empty where OSM is thin, even though the ground
has buildings. The two government sources below fill that gap and add real
heights, each in its own way.

## 基盤地図情報 (GSI Fundamental Geospatial Data)

- **What it is:** the national survey base data from the Geospatial Information
  Authority (GSI). Its basic items include building outlines (建築物 / 建築物の
  外周線) as 2D polygons.
- **Coverage:** comprehensive across city-planning areas and populated regions
  — far more complete than OSM in suburban and rural Japan — thinner only in
  the deepest rural/mountainous areas. Nationwide in scope.
- **Format / access:** JPGIS GML (Shapefile export available), via the
  Fundamental Geospatial Data download service (user registration required).
- **Attributes:** building outlines; **no heights** (2D), and no OSM-style
  stable community IDs (it carries its own FGD identifiers).
- **Licence — the decisive finding:** 基盤地図情報 is a 基本測量成果, but the GSI
  approval-application (承認申請) Q&A **explicitly exempts it** from the
  Surveying Law application requirement, together with the GSI tiles. Downloading
  it, processing it into derived vector tiles, and distributing them —
  including commercially and offline — needs **no 測量法 application**, only
  attribution plus a processing note (加工表示). Same tier as the GSI tiles the
  project already streams. Sources listed at the bottom.

## PLATEAU building models (MLIT Project PLATEAU)

- **What it is:** the government 3D city models. Building models come at LOD1
  (block extrusion with a real per-building measured height,
  `bldg:measuredHeight`) and LOD2 (roof shapes); occasional LOD4 (BIM).
- **Coverage:** released **per municipality** — Tokyo's 23 wards are fully
  modelled, and the programme expands from 56 cities (2021) toward ~300 cities
  by end of FY2025. **Not uniform**; rural municipalities may lack a model.
- **Format / access:** CityGML (authoritative source), 3D Tiles (the format
  Cesium renders), and FlatGeobuf/GeoJSON footprint derivatives, via the
  G-space Information Center (CKAN) — the same channel the project already uses
  for the UC24 underground scenes.
- **Attributes:** `measuredHeight` (real height), `usage`, `storeysAboveGround`;
  `yearOfConstruction` where populated (spotty). **No building weight** (that
  can only be derived, e.g. area × height × floors × a density factor — an
  estimate, never source data) and **no builder/developer** (not open data).
- **Licence:** PLATEAU Site Policy §3 (`license_id: plateau`) — attribution,
  commercial use permitted — the same terms the project already accepts for the
  integrated UC24 scenes.

## Intended use across the two display modes

- **Map mode (2D / 2.5D), from `osm-basemap-tiles`.** One tile source built by
  an **offline merge**: OSM primary (identity + attributes), 基盤地図情報 filling
  OSM gaps (nationwide completeness), and PLATEAU `measuredHeight` joined as a
  height attribute where a municipality is modelled. The merge — including the
  "government only where OSM is absent" decision — runs once at build time,
  where a spatial join is affordable, producing one consistent layer with a
  per-building `footprint_source` and `height_source` tag. This solves the
  empty-map problem (government fill), the double-drawing problem (one layer),
  keeps offline capability, and stays honest about which value is measured vs
  estimated. 2.5D extrusion reads the baked height on the terrain surface.
- **Local 3D work mode, from `local-3d-work-mode`.** Box-select an area and
  load high-fidelity PLATEAU 3D models on demand by mesh, above and below
  ground, with SL overlays and AL simulation results. PLATEAU footprints and
  IDs differ from OSM, so this mode uses PLATEAU directly rather than the merged
  tiles; where a municipality is unmodelled it falls back to extruding the merged
  tile buildings. Usage telemetry then guides which hot areas to localise,
  rather than pre-caching all of Kanto.

## Conclusion

Both sources are viable and licence-clear for a self-built, offline-capable,
commercially distributable product, on attribution terms. A final legal
sign-off before commercial launch is prudent for any licence-dependent
decision — not because the finding is in doubt, but because the decision
warrants it. The mixed licence of the merged tiles (OSM ODbL + GSI content
terms) requires crediting both, and ODbL share-alike applies if the merged
**database** (not merely served tiles) is ever published.

## Sources

- 承認申請Q&A | 国土地理院 — <https://www.gsi.go.jp/LAW/2930-qa.html>
- 国土地理院コンテンツ利用規約 — <https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html>
- 国土地理院の測量成果の利用手続 — <https://www.gsi.go.jp/LAW/2930-index.html>
- 出典の記載 | 国土地理院 — <https://www.gsi.go.jp/LAW/2930-meizi.html>
- 基盤地図情報ダウンロードサービス — <https://fgd.gsi.go.jp/download/>
- Project PLATEAU open data — <https://www.mlit.go.jp/plateau/open-data/>
- PLATEAU Site Policy — <https://www.mlit.go.jp/plateau/site-policy/>
