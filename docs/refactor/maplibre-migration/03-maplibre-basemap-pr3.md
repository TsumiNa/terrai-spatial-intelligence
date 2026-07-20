# PR3 Plan: MapLibre Basemaps and Camera

- Status: Planned
- Refactor: `maplibre-migration`
- PR: #3

## Goal

Replace the placeholder with a MapLibre map carrying the GSI basemaps and the region camera behaviour, owned by one imperative module.

## Scope

1. A single map module that owns the MapLibre instance and exposes a narrow interface to Svelte. No reactive wrapping of map internals.
2. GSI basemaps: the vector style, plus raster imagery, hillshade and slope. Record which raster layer is served and at which maximum level.
3. Region switching, bounds, and the camera, including `setMaxPitch` above MapLibre's default of 60 so later stages can lower the camera.
4. Attribution for every source.
5. Decide whether cached imagery moves from `seamlessphoto` to `ort`, and whether the cache extends from z17 to z18. Both are open questions from the evaluation; this stage is where they land.

## Non-goals

No deck.gl. No data layers. No terrain — it is not required by any planned stage and remains unproven outside the spike.

## Implementation notes

- Raster layers must declare their real maximum level. The evaluation measured these: `slopemap` z15, `hillshademap` z16, imagery z18. Requesting past them yields 404s or upsampled blur.
- Vector tiles stop at z16 but stay sharp beyond it because geometry scales rather than pixels. Do not cap the map at the tile ceiling.

## Acceptance

- Both regions load with correct bounds and attribution.
- Every basemap switches without a visible camera jump.
- Zooming past a raster layer's maximum level produces no failed requests.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
