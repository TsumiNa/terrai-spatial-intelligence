# PR7 Plan: Standalone Site Scene

- Status: Completed
- Refactor: `maplibre-migration`
- PR: #39

## Completion record

- **Shipped picking granularity**: Sapporo reaches **feature level** — the `_BATCHID` vertex attribute at the picked face resolves through the b3dm batch table to the source identity (e.g. a `bdry_…` boundary id); Nihonbashi glTF content picks per asset, feature-level when the asset holds a single feature, matching stage 06's map-side ladder. Every pick resolves through the handoff's inverse transform to WGS 84 ellipsoid coordinates in its audit record.
- **The bundle endpoint** landed as planned: `GET /api/v1/scenes` (catalog) and `GET /api/v1/scenes/{scene_id}` (scene + verbatim handoff, resolved through the catalog's `owner_dataset_key`; unknown ids and owner keys are 404). Both are in the committed OpenAPI schema.
- **Renderer adaptations**, each tested: the stage-06 plural-`contents` normalization reused as a TilesRenderer `fetchData` plugin; PLATEAU b3dm requires `CESIUM_RTC` and Draco, wired through `GLTFExtensionsPlugin` with the Draco decoder vendored under `webapp/public/draco/` so the scene stays offline-capable; the library's accelerated raycast consults internal ECEF bounds that an external local-frame matrix does not update, so plain per-tile raycasting is used.
- **Box selection** listens for `pointerdown` on the map container and `pointermove`/`pointerup` on the window — MapLibre suppresses synthetic mouse events and pointer capture can strand a container-scoped `pointerup`.
- OSM access features without a stated level render at the scene-origin reference plane, stated in the viewer copy; OSM stays an independent overlay and never snaps to PLATEAU geometry.
- A few Sapporo tiles fail Draco decoding upstream; individual tile failures log to the console without flipping a family that has rendered models, and a family reports `error` only when nothing loaded (the CI cache-absent path).
- The visual-baseline suite excludes the scene dialog for the same reason as the stage-06 map: its content depends on the on-demand cache and differs between environments.

## Goal

Let a user box-select one of the catalogued underground observation areas and open an independent 3D scene showing its available above- and below-ground evidence in a traceable local frame, with section cuts and unresolved evidence left empty.

## Scope

1. Box selection on the map, matching the selection to a scene in `data/scenes/underground/catalog.json` rather than unioning geographically incompatible sources.
2. A site bundle endpoint returning the selected handoff plus only the assets whose evidence family is `available`. It preserves `unresolved` and `not_applicable` states and the handoff's approved roots, timestamps, licences and audit indexes.
3. A standalone Three.js scene on its own canvas, sharing no WebGL context with MapLibre, using the handoff's `EPSG:4978` world-to-local ENU-metre transform and inverse.
4. Section cuts via clipping planes and adjustable vertical exaggeration. Exaggeration is renderer configuration, not a coordinate or vertical-datum fact.
5. Observed structures render as observed evidence; unresolved families remain empty. No placeholder geometry is created for terrain/buildings, boreholes, strata or predicted fields.
6. Audit records reachable from inside the scene, resolving through the inverse transform to real coordinates, ellipsoid-height reference, source and source timestamp.

## Non-goals

No editing or capture. No field-client concerns. No map-side rendering of soil or strata. No geo_pfn field, uncertainty volume, borehole or strata renderer in the first implementation; those require a later SL output contract and qualified inputs.

## Satisfied dependency

The `underground-observation-foundation` refactor now publishes two renderer-neutral observed-scene handoffs: Nihonbashi utilities and Sapporo underground structures plus independent OSM access context. Their local frames, evidence availability and audit roots are sufficient for the first observed-scene implementation. The undecided `geo_pfn` output shape no longer blocks this stage because predicted fields remain explicitly unresolved and absent.

## Implementation notes

- Load the local frame from the selected scene handoff. Hard-coding the transform breaks the audit chain at the moment a user enters 3D, which is the single most important thing this stage must not do.
- Keep heavy geometry imperative even if a declarative Three wrapper is used for lights, camera and controls.
- Preserve source separation inside Sapporo: OSM access context supplements but never validates, snaps or overwrites PLATEAU geometry.
- Defer volumetric rendering decisions until a later plan defines an actual predicted-field payload and uncertainty semantics.
- The bundle endpoint is the first HTTP surface over `DataService.scene_catalog()` / `scene_handoff()`, which stage 3 of the data refactor deliberately left service-level: `GET /api/v1/scenes` returns the catalog and `GET /api/v1/scenes/{scene_id}` returns the filtered bundle. `scene_handoff()` resolves by owner dataset key, so the endpoint maps the requested scene id through the catalog to its `owner_dataset_key` before calling it — an unknown scene id is a 404, not a new resolution path. Both routes enter the committed OpenAPI schema through the normal regeneration, so the typed client covers them.
- Tiles-in-Three rendering uses the maintained NASA-AMMOS `3d-tiles-renderer` package rather than a hand-written tileset walker; b3dm batch tables (Sapporo) and glTF structural metadata (Nihonbashi) are its supported paths for picking identity, with the same granularity ladder as stage 06 where support falls short.
- The scene opens as a full-viewport overlay on the dialog primitive already in use, so focus trapping, Escape-to-leave and restoration of the map state come from the primitive, not hand-rolled code.

## Acceptance

- Box selection opens the matching catalogued scene and cannot combine Nihonbashi with Sapporo.
- A section cut can be positioned and reveals the interior.
- Available observed evidence is visible; unresolved and not-applicable families produce no geometry or invented counts.
- Any element picked in the scene resolves through the supplied inverse transform to real-world coordinates and its source audit record.
- Leaving the scene returns to the map with its previous state intact.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
