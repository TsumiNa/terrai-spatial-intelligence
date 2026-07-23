# PR2 Plan: Hillshade Colour-by-Height Tint

- Status: Planned
- Refactor: `basemap-view-modes`

## Goal

In hillshade mode a colour-by-height layer is drawn over the shaded relief and
fades with zoom — pronounced at a wide view where regional elevation structure is
meaningful, transparent as the user zooms in, and hidden past a threshold where it
would only muddy the local hillshade.

## Scope

- Add a hypsometric colour-elevation raster for the hillshade mode: GSI's 色別標高図
  (`relief`) tiles, or an equivalent elevation tint, as a raster layer drawn above
  the `hillshademap` layer. Live GSI production endpoint, attribution as with the
  other rasters; confirm the exact endpoint and zoom ceiling at implementation.
- **Zoom-driven opacity**: a `raster-opacity` zoom interpolation — high at low
  zoom, ramping to 0 by a mid zoom, e.g. opaque-ish around z5–8, fading through
  z9–12, ~0 by ~z13 (tunable). Past the source's max zoom / the fade end the layer
  is effectively hidden (opacity 0 and/or `maxzoom`), so no tint tiles are
  requested when it would not show.
- Bound to the **hillshade mode and zoom**, independent of the 2.5D toggle: shown
  whenever hillshade is active and the zoom is wide, whether flat or tilted. When
  2.5D is on and the DEM surface is up, the tint drapes over the terrain, so a wide
  view reads as coloured 3D relief; zooming in fades it to plain hillshade on
  terrain.
- Only visible in hillshade mode: switching to standard/photo hides it.

## Non-goals

- No tint in standard or photo modes.
- No self-hosted / self-computed hypsometric layer (live GSI; the self-host DEM
  path is a separate, unrelated option).
- No change to the 2.5D toggle or per-mode terrain (PR1).

## Implementation steps

1. Register the colour-elevation raster source and a layer above `hillshademap`;
   attribution.
2. Add the `raster-opacity` zoom interpolation and the hide-past-threshold
   (opacity 0 / `maxzoom`); make the stops named constants so the fade is tunable.
3. Gate visibility on the hillshade mode (show/hide with the basemap switch).
4. Tests: opacity is high at a wide zoom and 0 (or layer hidden) at a local zoom;
   the tint appears only in hillshade mode.

## Acceptance

- In hillshade mode, a wide view shows the colour-by-height tint over the shaded
  relief; zooming in fades it out and past the threshold it is gone (no tint tiles
  requested).
- The tint shows only in hillshade mode, and drapes correctly over the DEM surface
  when 2.5D is on.
- `cd webapp && npm run build && npm run test`, the Playwright suites, and
  `uv run python -m terrai_spatial validate` pass.
