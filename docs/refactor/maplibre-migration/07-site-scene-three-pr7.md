# PR7 Plan: Standalone Site Scene

- Status: Blocked on data
- Refactor: `maplibre-migration`
- PR: #7

## Goal

Let a user box-select a block on the map and open an independent 3D scene showing that block above and below ground, with section cuts, and with observed, synthetic and unresolved evidence visually distinct.

## Scope

1. Box selection on the map, producing a bounding box.
2. A site bundle endpoint returning, for that box: the terrain patch, buildings, network elements, boreholes, strata surfaces, any predicted subsurface field, **and the local frame** — origin, rotation, vertical datum and default vertical exaggeration.
3. A standalone Three.js scene on its own canvas, sharing no WebGL context with MapLibre, using local metric coordinates.
4. Section cuts via clipping planes, and adjustable vertical exaggeration.
5. Evidence status rendered as a visual distinction: observed samples solid, synthetic prediction translucent with opacity driven by uncertainty, unresolved regions left empty rather than interpolated.
6. Audit records reachable from inside the scene, resolving back to real coordinates, elevation datum, source and sampling date.

## Non-goals

No editing or capture. No field-client concerns. No map-side rendering of soil or strata.

## Blocking dependency

No subsurface dataset is integrated, and the output shape of `geo_pfn` prediction is undecided. Discrete surfaces and boreholes need only mesh and column rendering; a continuous property field with uncertainty needs volumetric ray marching. Do not start until the shape is known.

## Implementation notes

- The local frame must arrive as data. Hard-coding the transform breaks the audit chain at the moment a user enters 3D, which is the single most important thing this stage must not do.
- Keep heavy geometry imperative even if a declarative Three wrapper is used for lights, camera and controls.
- If volumetric rendering is needed, prefer a custom layer with its own shader over introducing a third rendering library into the application.

## Acceptance

- Box selection opens the scene for the selected block, above and below ground.
- A section cut can be positioned and reveals the interior.
- Observed, synthetic and unresolved evidence are distinguishable without reading the legend.
- Any element picked in the scene resolves to real-world coordinates and its source record.
- Leaving the scene returns to the map with its previous state intact.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
