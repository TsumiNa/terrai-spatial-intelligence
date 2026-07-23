# PR1 Plan: View Modes and the 2.5D Toggle

- Status: Completed
- Refactor: `basemap-view-modes`

> Implementation note: the slope **basemap** is removed; the slope **module**
> (building slope-risk analysis) is untouched. The 2.5D state is `twoAndHalfD`
> in app state (deep-linkable via `?tilt=1`), an on-map `.view25d-toggle` button.
> `applyVisibility` now applies pitch for any basemap in 2.5D and `setTerrain`
> only for photo/hillshade. Visual baselines (both `-darwin` and `-linux`) were
> regenerated for the changed toolbar chrome.

## Goal

The basemap set is `standard` / `photo` / `hillshade` (slope removed), and 2.5D is
an explicit on-map switch decoupled from the basemap, applying per-mode: standard
gets perspective only, photo and hillshade get perspective plus the 3D DEM
surface.

## Scope

- Remove the `slope` basemap: drop it from `BasemapKey`/`BASEMAP_KEYS`
  (`state.svelte.ts`), from `RASTER_KINDS`/`RASTER_SOURCES` (`config.ts`), its i18n
  entries (`basemap.slope*`), the basemap picker UI, and any test/fixture
  referencing it. Update the raster-ceiling comment (slopemap drops out).
- Add a **2.5D toggle** as a switch button placed on the map (a MapLibre control
  or a Svelte control over the map container), holding a `twoAndHalfD` boolean in
  map state; reflected in the URL like `basemap` if the other view state is.
- Rewire terrain/pitch in `map.ts` `applyVisibility` from "terrain iff
  `basemap === "hillshade"`" to the toggle + per-mode rule:
  - `standard` + 2.5D → `easeTo({ pitch })`, **no** `setTerrain`;
  - `photo` | `hillshade` + 2.5D → `setTerrain(DEM)` + `easeTo({ pitch })`;
  - 2.5D off (any mode) → `setTerrain(null)` + `easeTo({ pitch: 0 })`.
  Keep the underground-stage guard (it owns the camera; terrain waits).

## Non-goals

- No colour-by-height tint yet (PR2).
- No change to imagery/hillshade sources beyond removing slope; no self-hosting.
- No building/tile/analysis changes.

## Implementation steps

1. Delete the `slope` basemap across type, sources, i18n, picker, tests, comment.
2. Add `twoAndHalfD` to map state and the on-map switch button; default off.
3. Rewrite `applyVisibility` to the toggle + per-mode terrain/pitch rules; keep
   the underground guard.
4. Update/adjust the map tests and the Playwright suites (mode set, toggle
   behaviour per mode).

## Acceptance

- The basemap picker offers exactly standard/photo/hillshade; no `slope` remains
  in code, i18n, or URL handling.
- The on-map 2.5D switch toggles: standard tilts without terrain; photo and
  hillshade tilt with the DEM surface; turning it off returns every mode to flat
  top-down.
- `cd webapp && npm run build && npm run test` and the Playwright suites pass;
  `uv run python -m terrai_spatial validate` passes.
