# PR2 Plan: On-Demand PLATEAU Loading

- Status: Planned
- Refactor: `local-3d-work-mode`

## Goal

The local scene fills with real PLATEAU building models for the selected box,
loaded on demand by mesh — and where a mesh has no PLATEAU model, it falls back
to extruding the merged-tile buildings, so a selection always renders something.

## Scope

- For the meshes the box covers, fetch PLATEAU LOD1/LOD2 building geometry on
  demand from the PLATEAU distribution (G-space Information Center / CKAN, the
  UC24 channel), in a renderer-consumable form (3D Tiles, or a FlatGeobuf/GeoJSON
  derivative loaded into the deck.gl scene). No pre-caching — fetched at
  interaction time.
- Render the models above ground on the terrain surface in the local scene, with
  a loading state per mesh so a partial selection shows progress.
- Fallback: for a covered mesh PLATEAU does not model, extrude the same
  merged-tile buildings map mode uses (footprint + baked height), visibly marked
  as fallback fidelity (`height_source` already distinguishes measured from
  estimated), so the scene degrades rather than showing a hole.
- Provenance preserved: each rendered building keeps its source (PLATEAU
  `gml:id` / measuredHeight, or the merged-tile `feature_id` / `height_source`)
  reachable on inspection.
- PLATEAU attribution (Site Policy §3) shown while its models render.

## Non-goals

- No subsurface or SL/AL overlays (PR3). No localisation/telemetry (PR4).
- No `osm_id → plateau` single-building crosswalk — the box loads by area/mesh;
  the crosswalk is a later enrichment (see overview).

## Implementation steps

1. Add an on-demand PLATEAU fetch keyed by mesh, returning renderer-ready
   geometry; cache within the session only.
2. Render the models in the local scene on the terrain; per-mesh loading state.
3. Implement the merged-tile extrusion fallback for unmodelled meshes, marked as
   fallback.
4. Surface per-building provenance; add PLATEAU attribution; e2e a modelled area
   (real models) and an unmodelled area (fallback).

## Acceptance

- Selecting a PLATEAU-modelled area loads and renders its real building models on
  the terrain; selecting an unmodelled area renders the extruded merged-tile
  fallback, marked as such.
- Each building's provenance is reachable; PLATEAU attribution renders.
- `cd webapp && npm run build && npm run test`, the Playwright suites, and
  `uv run python -m terrai_spatial validate` pass.
