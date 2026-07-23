# PR1 Plan: Box-Select and Local-Scene Shell

- Status: Planned
- Refactor: `local-3d-work-mode`

## Goal

A user can draw a box on the map and open it as a dedicated local 3D scene, and
close it back to the map — the mode exists end to end with an empty scene over
the selected footprint, before any heavy data loads.

## Scope

- A box-select interaction in map mode: drag to draw a rectangle, which yields a
  bounding box in map coordinates and the mesh code(s) it covers.
- A mode switch into a local-scene view rendered by the existing renderer-neutral
  scene handoff (the one built for the UC24 underground scenes), and back out to
  the map, preserving the map's camera on return.
- The empty scene: terrain surface for the selected footprint (reusing the DEM
  the map already loads) with correct extent and orientation, camera framed on
  the box. No buildings or subsurface yet.
- The selection is expressed in the same mesh vocabulary PLATEAU and the
  subsurface use, so PR2/PR3 can request data by mesh without re-deriving it.

## Non-goals

- No PLATEAU models (PR2), no subsurface or analysis overlays (PR3), no
  telemetry/localisation (PR4).

## Implementation steps

1. Add the rectangle-draw interaction to the map; emit `{bbox, meshCodes}`.
2. Add the local-scene route/state and the enter/exit transition through the
   scene handoff; keep and restore the map camera.
3. Render the terrain-only scene for the selection with correct extent.
4. Unit-test the bbox→mesh derivation; e2e the draw → enter → exit round trip.

## Acceptance

- Drawing a box opens a local scene framed on that footprint with terrain, and
  closing returns to the map at the prior camera.
- `bbox → meshCodes` is covered by unit tests; the round trip passes in e2e.
- `cd webapp && npm run build && npm run test` and
  `uv run python -m terrai_spatial validate` pass.
