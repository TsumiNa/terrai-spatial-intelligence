# PR3 Plan: Hillshade Computed from a High-Resolution DEM

- Status: Planned
- Refactor: `basemap-view-modes`

## Goal

Hillshade stops going blurry past z16. It is computed on the client from the DEM
(not a pre-rendered raster capped at z16), driven by a **high-resolution DEM5A
(5 m) source**, so the shaded relief — and the 2.5D terrain that shares the same
DEM — stays sharp at high zoom. No fabricated detail: resolution comes from real
elevation data, never from image upscaling.

## Why (the constraint)

The blur is a **data-resolution ceiling**, not a rendering one: GSI's pre-rendered
`hillshademap` raster is `maxzoom` 16, so beyond z16 MapLibre overscales one tile
and interpolates. Upscaling/super-resolving that image cannot add real relief — at
best a smoother blur, at worst **fabricated terrain that reads as measured**, which
violates the project's observed/provenance commitment. The only honest way to more
detail is more DEM resolution. Note the current DEM is only z14 (`dem_png`, 10 m),
**below** the z16 hillshade — so computing hillshade from today's DEM would be
worse; the DEM source upgrade is the necessary part.

## Scope

- Replace the pre-rendered `hillshademap` raster (hillshade mode's shaded base)
  with MapLibre's native **`hillshade` layer computed from a `raster-dem`
  source** — shaded per-pixel at render resolution on the GPU, and consistent with
  the 3D terrain (same DEM).
- Upgrade the DEM source to **DEM5A (5 m)** with a higher `maxzoom` than today's
  z14. Source options, to confirm at implementation: a GSI 5 m elevation-tile
  endpoint if one is published, otherwise **DEM5A tiles derived from the 基盤地図情報
  acquisition** (`osm-basemap-tiles` PR1 already pins FGD, which distributes
  DEM5A) — i.e. the **self-host-DEM** path. The same upgraded `raster-dem` feeds
  `setTerrain`, so the 2.5D relief sharpens too. The `gsidem://` transcode stays if
  the source is GSI-encoded; self-hosted DEM5A tiles are pre-encoded to Mapbox
  terrain-RGB (no runtime transcode — the convergence noted in the DEM self-host
  plan).
- **Optional 2× DPR**: render the hillshade at higher `devicePixelRatio` to
  supersample the *shading computation* (anti-aliasing, real — not fabricated
  detail), behind a flag, weighing the GPU/fill-rate cost (relevant on handheld
  power).
- The colour-by-height tint (PR2) sits over this new DEM-computed hillshade
  unchanged; both remain hillshade-mode + zoom driven.

## Non-goals

- **No image super-resolution / ML upscaling** of the hillshade — it fabricates
  measured-looking terrain, against provenance. Sharpness comes from DEM
  resolution only.
- No change to the 2.5D toggle / per-mode rules (PR1) or the tint layer (PR2)
  beyond swapping the shaded base.
- No change to imagery/standard modes.

## Implementation steps

1. Point the terrain/hillshade `raster-dem` at a DEM5A (5 m) source with a raised
   `maxzoom`; confirm the endpoint or derive tiles from the FGD DEM5A.
2. Replace the hillshade raster with a native `hillshade` layer over that
   `raster-dem`; tune exaggeration/light to match the prior look.
3. Add the optional 2× DPR path behind a flag.
4. Verify the tint (PR2) still composites; update tests for sharpness at z16–17
   and for terrain resolution.

## Acceptance

- In hillshade mode, relief stays sharp at z16–17 (no overscaled mush), driven by
  the 5 m DEM; the 2.5D terrain from the same DEM is correspondingly sharper.
- No image-upscaling path exists; the sharpness is attributable to DEM resolution.
- The colour-by-height tint still composites correctly over the DEM-computed
  hillshade.
- `cd webapp && npm run build && npm run test`, the Playwright suites, and
  `uv run python -m terrai_spatial validate` pass.
