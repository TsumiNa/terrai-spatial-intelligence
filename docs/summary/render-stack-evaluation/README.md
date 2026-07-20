# Rendering Stack Evaluation: CesiumJS vs MapLibre + deck.gl

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- Date: 2026-07-20
- Status: decided — MapLibre GL JS + deck.gl for the map, standalone Three.js for the site scene
- Scope: the browser rendering stack, evaluated ahead of the planned frontend refactor

## Why this evaluation exists

Leaflet renders 2D raster tiles and nothing else. The roadmap adds 3D terrain and subsurface visualisation, which it cannot express at all. Two candidate stacks were built as throwaway spikes against the same region, the same `building_risk.geojson` (2,128 buildings), and the same GSI sources.

This document records what was measured, and the decision those measurements led to.

## GSI source ceilings

Probed directly against the two demo bounding boxes.

| Layer | Deepest level served | Note |
|---|---|---|
| `slopemap` | z15 | z16 returns 404 |
| `hillshademap` | z16 | z17 returns 404 |
| `seamlessphoto` | z18 | z19 returns 404 |
| `ort` | z18 | ~57 KB per tile against seamlessphoto's ~17 KB at the same level |
| `dem5a_png` | z15 | numeric elevation, available for both regions |
| `dem_png` | z14 | DEM10B fallback |
| `experimental_bvmap` | z16 | vector tiles; an official style with 774 layers is published |

All GSI tiles respond with `access-control-allow-origin: *`, so decoding their pixels in the browser is possible.

## Ground resolution, and why the raster slope map cannot be sharpened

At 35.45°N:

| Level | Resolution |
|---|---|
| z15 | 3.89 m/px |
| z16 | 1.95 m/px |
| z17 | 0.97 m/px |
| z18 | 0.49 m/px |

DEM5A is a 5 m grid, so z15 already slightly oversamples the elevation data that `slopemap` and `hillshademap` are derived from. GSI stopping `slopemap` at z15 is an information limit, not an arbitrary cap.

Consequence: the blur seen when the exhibition renders slope at z17 cannot be fixed by caching deeper tiles, and would not be fixed by rendering the same pre-rendered raster client-side either. It changes only with a finer DEM, or by interpolating elevation and computing slope from it rather than interpolating a rendered image.

## Elevation decode, verified against project data

`dem5a_png` encodes elevation as `x = R*65536 + G*256 + B`, with `h = x*0.01` below 2^23, `h = (x - 2^24)*0.01` above it, and `(128,0,0)` reserved for nodata.

One Yokohama z15 tile decodes to min/median/max of 3.6 / 36.8 / 72.4 m, with 186 nodata pixels out of 65,536. `building_risk.geojson` carries `elevation_m` of 7.0 / 28.2 / 64.4 m across the smaller building-footprint area. The ranges are consistent, so the decode is correct.

## Library weight, measured

| | Raw | gzip | brotli |
|---|---|---|---|
| CesiumJS 1.143 `Cesium.js` | 5.64 MB | 1.64 MB | 1.31 MB |
| MapLibre GL 5 | 1.0 MB | 269 KB | — |
| deck.gl 9 (UMD, all layers) | 1.6 MB | 459 KB | — |
| MapLibre CSS | 72 KB | 10 KB | — |

Cesium's full `Build/Cesium` directory is 22 MB on disk, but `Assets` (4.6 MB), `Workers` (1.3 MB) and `ThirdParty` (1.1 MB) load on demand rather than on first paint.

Stack totals over the wire, gzip: **Cesium 1.64 MB, MapLibre + deck.gl 738 KB.** The deck.gl figure is the complete UMD bundle; a bundler importing only the layers in use would be smaller.

## CesiumJS findings

- **No Cesium Ion dependency is required.** Setting `baseLayerPicker: false` and `geocoder: false`, and supplying GSI imagery plus a custom terrain provider, keeps every request on GSI. The default configuration would otherwise contact Cesium's servers.
- **A terrain provider for GSI elevation is roughly 50 lines.** Community modules target the pre-1.104 constructor API and the most cited one is archived, so writing it is preferable to depending on them.
- **Scene-mode morphing is unusable as a 2D/3D toggle.** `morphTo2D` and `morphTo3D` rebuild all geometry for the new projection; with 2,128 extruded buildings the stutter was unacceptable. Setting `scene3DOnly: true` and moving the camera instead — top-down plus `switchToOrthographicFrustum()` — is instant and visually equivalent.
- **The Entity API is the wrong path for bulk geometry.** `GeoJsonDataSource` with `CLAMP_TO_GROUND` over 2,128 polygons was slow to load and slow to switch. One batched `Primitive` built at absolute heights, using the `elevation_m` already present in the data, removes terrain sampling entirely and loads without perceptible delay.
- **`requestRenderMode: true` makes idle frame rate a meaningless metric**, because idle frames are deliberately not drawn. It remains the correct setting for an analytical view.
- **Cesium is CPU-bound on the main thread.** Tile selection, culling and draw-command generation run in single-threaded JavaScript every frame. Observed frame rate stayed below 60 on an M4 Max, where additional cores do not help.

## MapLibre + deck.gl findings

- **Frame rate is markedly better than Cesium** on the same machine, region and data.
- **The vector basemap stays sharp past its source ceiling.** `experimental_bvmap` serves to z16; beyond that the geometry scales rather than the pixels, so lines and labels stay crisp where raster imagery blurs.
- **GPU aggregation is available and Cesium has no equivalent.** `HexagonLayer` aggregates the building set by `risk_score` on the GPU.
- **Terrain from GSI elevation is unresolved in the spike.** Three defects were found and fixed in the spike's own code: a shared decode canvas racing across concurrent tile requests; a missing `colorSpaceConversion: "none"`, which let the browser alter RGB values that are data rather than colour; and an encoding mismatch, where the handler emitted terrarium while the source declared MapLibre's default `mapbox` encoding. Terrain still rendered incorrectly after all three. The cause is not established. **This is a limitation of the spike, not a demonstrated limitation of MapLibre.**
- **deck.gl extrusions do not follow terrain automatically.** Extruded polygons start at elevation 0, so with terrain enabled buildings sink into or float above slopes. Cesium's absolute heights aligned without extra work. Correcting this is real additional effort.

## Underground viewing, as originally framed

This was assumed to be the decisive requirement, and on that framing Cesium wins outright. The framing turned out to be wrong; the next section explains why. Recorded here because the capability comparison is still accurate.

Cesium supports underground viewing natively: the camera descends below terrain with navigation adjusted accordingly, and `globe.translucency` fades the surface so subsurface geometry stays visible. It is the standard tool for boreholes, tunnels and geological horizons.

MapLibre's camera is a surface camera, and its terrain mesh occludes anything beneath it. Subsurface geometry can be drawn at negative elevation, but it cannot be viewed from below.

Underground visualisation is a product requirement — the Synthetic Data Layer's entry evidence, `geo_pfn` sparse subsurface prediction, is subsurface. What was wrong was assuming that requirement implies flying a regional camera below ground.

## Where underground data is actually viewed

Two scenarios were separated late in the evaluation, and the separation is what settled the decision.

**On the map — discrete network infrastructure.** Pipes, cables and facilities answer "where does this run", which needs regional context. Lowering the camera (`setMaxPitch(85)`; MapLibre defaults to 60) and making buildings and basemap translucent gives an intuitive view of the network beneath the city. The camera never goes below ground: deck.gl exposes `depthTest`, `depthMask` and `depthCompare`, so the network layer draws through the surface instead. 3D terrain is switched off in this mode, which removes the mesh that would otherwise occlude negative-elevation geometry.

**In a local scene — continuous fields.** Soil, strata and predicted properties answer "what is under this point", which needs section cuts and local precision. The user box-selects a block and switches into an independent Three.js scene holding both above- and below-ground features. Soil prediction and uncertainty appear only here.

Strata and 3D cross-sections rendered on the regional map are unreadable and awkward to operate. They do not belong there.

## Decision

**MapLibre GL JS + deck.gl for the map; a standalone Three.js scene for the site view. CesiumJS is not adopted.**

Cesium was excluded not for lack of capability — its underground support is genuinely the best of the candidates — but because the requirement it satisfies does not have the shape originally assumed. Flying the camera beneath terrain on a regional map is visually striking and answers a question no user asks. Once underground work is split into map-level network viewing and a local site scene, nothing in the map stack needs to descend below the surface, and nothing in the site scene needs a geospatial globe engine.

The stack was chosen for MapLibre's measured advantages — weight, frame rate, 2D handling, basemap sharpness — plus one strategic reason: `flutter-maplibre-gl` exists, so the layer and style model can migrate to a native tablet client later. Cesium has no native equivalent.

Splitting the site view into a separate Three.js canvas also removes several problems at once: no shared WebGL context between three libraries, local metric coordinates instead of Mercator world coordinates (so float32 precision is ample), vertical exaggeration as a simple scale factor, native clipping planes for section cuts, and volumetric ray marching confined to a local bounding box.

## Consequences to carry into implementation

- **The audit chain must survive entry into the site scene.** Local scene coordinates are metres from a site origin, so the origin, rotation, vertical datum and default exaggeration must be returned by the API as first-class data, never hard-coded in the client. A borehole picked in the scene must still resolve to its real coordinates, elevation datum, source and sampling date.
- **Underground network data does not exist yet.** The map-level scenario is unblocked technically but blocked on data.
- **Terrain under MapLibre remains unproven.** It is not needed for the underground scenarios, but it is still wanted for surface context, and the spike never resolved it.

## Related findings, checked but not measured

- **SolidJS was excluded.** Its last stable release is v1.9.0 (2024-09-24); v2.0.0-beta.0 dates from 2026-03 and had not stabilised. Svelte and React both ship releases on a weekly to monthly cadence.
- **Replacing the Python backend with JavaScript was rejected.** The web layer is 380 lines (`api.py` plus `data_service.py`); the pipeline and geospatial layer is 1,951 lines and depends on rasterio/GDAL, pyproj/PROJ, numpy and Pillow, which have no equivalents in the JavaScript ecosystem. Only about 14% of the backend could move, and the Python processes would remain regardless.
- **Flutter is deferred, not excluded.** The earlier exclusion assumed Flutter Web hosting CesiumJS, which cannot work because CanvasKit owns the canvas. For native tablets in the field that premise does not apply. `flutter-maplibre-gl` is active but pre-1.0 and small; the ArcGIS Maps SDK for Flutter watermarks development builds, requires a production license string and an Esri account, and bills ArcGIS Location Services per transaction, which conflicts with the zero-paid-service positioning. A field client is a different product from the exhibition, and Capacitor over the same web application is the cheaper first step.

## Still open

1. Whether MapLibre terrain from GSI elevation works once implemented properly, outside the throwaway spike.
2. Whether `ort` replaces `seamlessphoto` as the cached imagery layer, and whether the cache extends from z17 to z18.
3. The output shape of `geo_pfn` subsurface prediction, which decides whether the site scene needs volumetric ray marching or only discrete surfaces and boreholes.

## Reproducing

The spikes were throwaway and live outside the repository. Every figure above came from probing GSI endpoints directly, measuring the downloaded library builds, or reading the vendored library source, not from vendor marketing.
