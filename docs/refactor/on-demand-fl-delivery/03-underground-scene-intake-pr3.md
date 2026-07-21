# PR3 Plan: Underground Scene Intake

- Status: Blocked — PR1 and PR2 of this refactor are not merged, and `maplibre-migration` 06/07,
  which own the endpoint shape and renderer this stage feeds, have not landed
- Refactor: `on-demand-fl-delivery`
- Depends on: PR1 and PR2 merged, and the outcome of `maplibre-migration` 06/07
- Related: `docs/refactor/maplibre-migration/06-underground-networks-pr6.md`

## Goal

Bring the underground scene catalog and its per-scene handoff into the frontend through the
windowed client, so the MapLibre and Three.js underground stages consume a delivery path that
already exists instead of building one under deadline.

## What the underground refactor actually delivered

The underground refactor merged as PRs #31-#33; the assumptions this plan was first written
against have been checked off against the implementation:

- **Confirmed, with one nuance** — the scene catalog (`data/scenes/underground/catalog.json`)
  and per-scene handoffs exist and are on-demand, but they are served through
  `DataService.scene_catalog()` / `scene_handoff()` (`data_service.py:121-133`) with **no API
  route**; today they are reachable only via the static `/api/v1/assets` mount, and
  `/api/v1/catalog` rows carry `scene_handoff_path` / `scene_handoff_ready`. The route is
  deliberately left to `maplibre-migration` PR7. This stage must consume whatever route PR7
  defines, not invent a parallel one.
- **Confirmed** — each handoff publishes a full local frame: `EPSG:4979` source, `EPSG:4978`
  ECEF world, ENU axes in metres, origin, both 16-element row-major matrices, and a declared
  round-trip tolerance (1e-08 degrees, 0.1 mm height).
- **Confirmed** — vertical reference is explicit and honest: `vertical_datum` is the WGS 84
  ellipsoid per 3D Tiles semantics, `orthometric_vertical_datum` is `"unknown"`. Availability
  is per evidence family as `available` / `unresolved` / `not_applicable`, with per-source
  licence, timestamps, and audit index paths on every available family. Sapporo's
  `utility_networks` is `not_applicable` with the non-co-location reason stated in data.
- **Confirmed** — assets remain native 3D Tiles/glTF behind cached-on-demand manifests
  (`ASSET_MANIFEST_DATASETS`); nothing was flattened to GeoJSON except the independently
  sourced OSM access graph, which was GeoJSON from the start.
- **Still to verify at implementation time** — the depth semantics of the glTF structural
  metadata (`uro:minDepth` / `uro:maxDepth` as relative measures). This lives inside the
  tile payloads, which this stage does not parse; it binds the renderer stages, and
  `maplibre-migration` 06 already carries the warning.

The remaining unknown is not the data — it is what `maplibre-migration` 06/07 build against
it. This stage must be finalized against their merged outcome, especially the site-bundle
endpoint PR7 owns.

## Scope

1. Request the scene catalog through the windowed client rather than a new bespoke path.
2. Represent scene identity as application state, with the constraint that Nihonbashi and Sapporo
   are never resolved together, enforced by type or by test rather than by convention.
3. Surface availability honestly. An `unresolved` evidence family renders as a stated absence, not
   as an empty layer, a zero count, or a hidden control.
4. Carry local-frame and vertical-reference facts through to whatever consumes them, without the
   frontend restating, defaulting, or inventing any of them.
5. Present demonstration-grade provenance at the point of use, so an underground model is not
   mistaken for an operational utility or station record.

## Non-goals

- No Three.js canvas, mesh handling, or renderer work. That is `maplibre-migration` PR7.
- No endpoint design. `maplibre-migration` PR7 owns the site-bundle endpoint shape.
- No borehole, strata, or geo_pfn contract.
- No composite scene, and no cross-scene overlay.
- No derivation of centre lines, depth, datum, or material classification the source does not
  state.

## Contract decisions

- The frontend is a consumer of coordinate facts, never a source of them. A local frame typed into
  frontend code is a defect, and the underground plan says so explicitly.
- `unresolved` and `not_applicable` are different and must stay different on screen. Collapsing
  them into "no data" destroys the distinction the data layer paid to preserve.
- A scene with only observed structural evidence is a valid scene. The UI must not require every
  evidence family to be present before it will render anything.
- Underground assets are demonstration products. Any screen showing them must carry that fact,
  not bury it in an audit drawer the user may never open.

## Acceptance

To be finalised against the merged underground refactor. At minimum:

- The scene catalog is requested through the PR1 client, with no second loading path introduced.
- No code path can resolve assets from both canonical scenes into one view; a test proves it.
- Unavailable evidence families carry no geometry, no feature count, and no model identity.
- Local-frame and vertical-reference values reaching the frontend are passed through unmodified,
  and a missing vertical datum surfaces as unknown rather than as a default.
- Demonstration-grade provenance is visible wherever underground assets are shown.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, `npm run build`, the Playwright
  suite, and `git diff --check` pass.
