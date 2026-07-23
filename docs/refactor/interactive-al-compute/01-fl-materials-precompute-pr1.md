# PR1 Plan: FL Material-Primitives Precompute

- Status: Planned
- Refactor: `interactive-al-compute`

## Goal

The invariant, DEM-derived analytical materials exist as a region-wide FL layer
in the store — computed once offline, keyed by `feature_id`, provenance-tagged —
so any AL metric can be recombined from them without recomputing the expensive
base, and coverage no longer stops at the Yokohama demo area.

## Scope

- A pipeline task computing the terrain-derivative material set per building
  feature over the whole target region (Kanto): `slope`, `relief`, `low_point`,
  `aspect`, `curvature`, distance-to-water — the bounded, stable set of
  denominators AL metrics are built from. Generalises the existing Yokohama-only
  `building_risk` slope/relief/low-point computation (DEM5A) into a region-wide
  materials product.
- Stored as FL (observed) materials keyed by `feature_id` (the same key the
  basemap tiles carry), each material tagged with its `*_source`/`dem_source` and
  vintage so a value traces to source. `automatic=False`, committed manifest,
  gitignored product for the large layer.
- Served through the existing windowed read API by `feature_id`/bbox — materials
  are queryable/joinable, not baked into tiles (the `osm-basemap-tiles`
  render/analyse boundary).
- Deterministic and validated: one code path produces the materials; the
  byte-identity oracle covers them like every other store product.

## Non-goals

- No AL scoring here — this produces materials, not metrics (PR2 recombines them).
- No lazy fill-on-read; the region is computed uniformly (overview).
- No baking into the basemap tiles.

## Implementation steps

1. Add the materials pipeline task (DEM5A/DEM inputs → per-feature terrain
   derivatives), region-wide, emitting a materials layer keyed by `feature_id`.
2. Ingest into the store as an FL materials collection with provenance; declare
   the manifest, gitignore the product.
3. Expose it on the windowed API (bbox + `feature_id`); extend the identity oracle
   and `data status`.
4. Record the batch time and layer size in the completion note.

## Acceptance

- Every building in the target region has its material set, keyed by
  `feature_id`, each with source/vintage; a spot-checked feature matches the
  DEM-derived values.
- Materials are queryable by bbox/`feature_id` on the read API; no per-request
  computation and no fill-on-read write path.
- `uv run python -m terrai_spatial validate` and the store build pass; the
  identity oracle covers the new layer.
