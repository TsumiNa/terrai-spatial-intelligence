# PR6 Plan: Underground Utility Networks on the Map

- Status: Planned
- Refactor: `maplibre-migration`
- PR: #6

## Goal

Let a user see buried pipes, cables and access structures in regional context by lowering the camera and making the surface translucent, without the camera ever going below ground.

## What the integrated data actually is

The original plan assumed a network dataset at negative absolute elevation. What the `underground-observation-foundation` refactor integrated is different, and this plan now follows the data:

- The canonical PR6 source is the **UC24-16 Nihonbashi sample**: nine 3D Tiles 1.1 tilesets — five utility networks (water, sewer, gas, communications, power) and four access-structure sets (manholes, handholes) — with per-feature glTF `EXT_structural_metadata` (`uro:minDepth`, `uro:maxDepth`, `uro:outerDiamiter`, `uro:material`, `uro:length`, `uro:mesureType`, source-description codes; upstream misspellings preserved verbatim).
- Assets are an **on-demand reproducible cache** (`data/external/plateau_uc24_16/`, git-ignored), served from the `/api/v1/assets` mount; the `uc24_16_nihonbashi` manifest and the 1,121-feature `audit_index.json` are committed and served the same way. Nothing enters `/bootstrap`.
- Heights follow 3D Tiles `boundingVolume.region` semantics (WGS 84 ellipsoid; the orthometric survey datum is `unknown`). Geometry renders at its published position — no invented offsets, no depth normalisation.
- The sample is in **Nihonbashi, Tokyo** — a third exhibition area alongside Yokohama and Mobara, not an overlay on either.

## Scope

1. A new `underground` exhibition module with a Nihonbashi region camera. Module content reflects the on-demand cache honestly: when `/catalog` reports `uc24_16_nihonbashi` not ready, the module renders an explicit unavailable state naming the fetch command instead of fabricating geometry or counts.
2. The underground view itself: camera pitch lowered toward the stage-03 `maxPitch` ceiling, surface translucency increased, no terrain. The nine tilesets render through deck.gl `Tile3DLayer` with depth reading relaxed so networks read through the surface rather than being occluded by it — verified not to draw over UI panels or the audit drawer.
3. Depth, diameter, material and measurement type carried as data from the audit index. Clicking an element opens an audit record naming its source, creation/retrieval dates, measurement type, and the positional and vertical-reference caveats. **Picking granularity ladder**, resolved empirically against deck's structural-metadata support and recorded here at completion: per-feature where feature IDs reach deck picking; otherwise per-asset (one glTF tile, resolved through the audit index's `source_asset` key); otherwise per-resource (utility class). The audit record states which granularity it represents.
4. A legend that distinguishes measurement classes from `uro:mesureType`, labels grounded in the published PLATEAU codelist; a code whose meaning cannot be confirmed from the codelist stays a code rather than being guessed into "surveyed" or "inferred".
5. Utility-class colours join the palette in both declarations, per `.github/instructions/color-palette.instructions.md`.

## Non-goals

No soil, strata or predicted properties. No camera descent below the surface. No site scene, no Sapporo assets, no box selection — stage 07. No derived centre lines, no depth normalisation, no fibre classification beyond source attributes, no server-side ranking queue for underground features.

## Implementation notes

- `@deck.gl/geo-layers` `Tile3DLayer` (same 9.3.x line as the installed deck packages) with `@loaders.gl/3d-tiles` is the renderer; the map module keeps sole ownership of layer lifecycles.
- Relaxed depth reading happens inside the deck overlay; the overlay canvas already draws above the basemap, so surface translucency is the basemap's, not the overlay's.
- Positional accuracy for buried utilities is metres, not centimetres, and the vertical datum is not an orthometric survey datum. The audit record must say both; a crisp line implies a precision the data does not have.
- CI has no tile cache: end-to-end coverage asserts the unavailable state unconditionally and skips cache-dependent assertions when `/catalog` reports the dataset not ready.

## Acceptance

- Entering the underground module is a single action; leaving it restores the surface exhibition state.
- Network elements are visible through the surface at the lowered camera angle.
- Clicking an element opens an audit record naming its source, dates, measurement type and positional/vertical caveats, at the granularity recorded above.
- Measurement classes are visually distinct in layer colouring or legend.
- With the cache absent, the module states unavailability and produces no failed asset requests.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, `npm run check`, `npm test` and the Playwright suite pass.
