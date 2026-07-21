# PR7 Plan: Standalone Site Scene

- Status: Planned
- Refactor: `maplibre-migration`
- PR: #7

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

## Acceptance

- Box selection opens the matching catalogued scene and cannot combine Nihonbashi with Sapporo.
- A section cut can be positioned and reveals the interior.
- Available observed evidence is visible; unresolved and not-applicable families produce no geometry or invented counts.
- Any element picked in the scene resolves through the supplied inverse transform to real-world coordinates and its source audit record.
- Leaving the scene returns to the map with its previous state intact.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
