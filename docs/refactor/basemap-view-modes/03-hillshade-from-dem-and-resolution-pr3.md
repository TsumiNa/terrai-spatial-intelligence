# PR3 Plan: Hillshade Computed from a High-Resolution DEM

- Status: Completed
- Refactor: `basemap-view-modes`

> Correction (verified during implementation): the earlier draft claimed "DEM5A
> (5 m) gives z16-17." That was wrong — **5 m resolves to ~z15** (GSI serves
> `dem5a_png` only to z15 for exactly this reason). z16-17 needs **1 m data
> (DEM1A ≈ z17)**, which GSI *does* serve live as `dem1a_png` to z17 — but only in
> **LiDAR-surveyed areas** (Yokohama ✓, Nihonbashi ✓, Mobara ✗). So the fix is a
> per-tile **resolution chain**, not a single self-hosted source, and needs no
> self-hosting and no Phase-2 dependency.

## Goal

Hillshade stops going blurry past z16 where high-resolution data exists. It is
computed on the client from the DEM (not the pre-rendered `hillshademap` raster,
capped at z16), driven per tile by the finest available GSI DEM — **DEM1A (1 m,
~z17)** where LiDAR covers it, degrading to DEM5A (5 m, z15) then DEM10B (10 m,
z14). The same DEM feeds `setTerrain`, so the 2.5D surface sharpens too. No
fabricated detail: sharpness comes from real elevation data, never image upscaling.

## Why (the corrected physics)

Blur past z16 is a **data-resolution ceiling**. Web-Mercator resolution at lat 35°:
10 m ≈ z13.6, **5 m ≈ z14.6 (z15)**, **1 m ≈ z17**. So only 1 m data resolves
z16-17. GSI serves:

- `dem_png` (DEM10B, 10 m) → z14 — the app's old source.
- `dem5a_png` (DEM5A, 5 m) → z15.
- `dem1a_png` (DEM1A, 1 m) → **z17** — but LiDAR coverage only.

Upscaling/super-resolving the z16 raster cannot add real relief, and would
fabricate measured-looking terrain (against provenance). The honest path is the
finer DEM where it exists.

## Scope

- **DEM resolution chain in the `gsidem://` protocol** (`dem.ts`): per requested
  tile, try DEM1A → DEM5A → DEM10B; the finest that has a tile wins. DEM1A is
  tried only at z ≥ 16 (its advantage zone) to avoid a wasted 404 across the wide
  view. Where a source only reaches a lower zoom, its **parent tile is upsampled
  by interpolating decoded elevations** (interpolating the encoded RGB would
  corrupt them). A fully-uncovered tile is flat sea level. `DEM_MAX_ZOOM` = 17;
  the raster-dem `maxzoom` follows.
- **Computed hillshade**: replace the pre-rendered `hillshademap` raster with a
  MapLibre native `hillshade` layer over the terrain `raster-dem`, so shading is
  per-pixel at render resolution and consistent with the 3D surface; tuned toward
  GSI's grayscale relief (palette-locked shadow/highlight, NW illumination).
- **Optional 2× DPR** behind `?hidpi=1`: `map.setPixelRatio` supersamples the
  render (incl. the computed hillshade) for crisper shading — anti-aliasing, not
  fabricated detail — weighed against GPU/fill-rate and handheld power.
- The colour-by-height tint (PR2) sits over the computed hillshade unchanged.

## Non-goals

- **No image super-resolution / ML upscaling** — fabricates measured-looking
  terrain, against provenance. Sharpness comes from DEM resolution only.
- **No self-hosting** — GSI's `dem1a_png` already serves 1 m to z17; the earlier
  "self-host DEM5A / FGD" premise was based on the wrong physics and is dropped.
- No change to the 2.5D toggle / per-mode rules (PR1) or the tint layer (PR2).

## Acceptance (met)

- In hillshade mode at survey zoom in a LiDAR area (Yokohama), the relief is
  computed from **1 m DEM1A** tiles and the pre-rendered `hillshademap` raster is
  no longer requested (e2e). Non-LiDAR areas (Mobara) degrade to DEM5A/DEM10B via
  overscale rather than losing terrain.
- No image-upscaling path; sharpness is attributable to DEM resolution.
- The colour-by-height tint still composites over the computed hillshade.
- `npm run build`, 122 unit, 48 e2e (1 skipped), and `terrai validate` pass.
