# Local 3D Work Mode

- Status: Planned

## Context

The webapp has two display intents, and they want different data and different
renderers:

- **Map mode (2D / 2.5D)** — the wide survey view. Fast, complete, offline-capable
  building fabric at every zoom, extruded to 2.5D on the terrain. This is the
  `osm-basemap-tiles` refactor: one merged tile source (OSM + 基盤地図情報 fill +
  PLATEAU height).
- **Local 3D work mode** — the reason for this refactor. The user draws a box on
  the map, and that footprint opens as a **high-fidelity local 3D scene**: real
  PLATEAU building models above ground and the observed subsurface below,
  carrying the SL overlays and AL simulation results for detailed analysis of one
  place, not the whole region.

The map mode's merged tiles deliberately hold only a single extrusion height per
footprint — enough for a 2.5D survey, not enough for local analysis. Roof shapes,
storeys, real geometry, and the below-ground scene need the authoritative
sources. This refactor is where those are brought in, but **only for the small
area the user selected**, on demand.

## The core decision: on-demand, not pre-cached

Kanto is too large, and PLATEAU too heavy, to bake full 3D models into the wide
map. So the local scene loads PLATEAU models **on demand by mesh** for the
selected box, and nothing outside it. The initial and simplest form pulls
straight from the PLATEAU distribution (G-space Information Center / CKAN, the
channel UC24 already uses) at interaction time.

Which areas, if any, get **localised** (mirrored into project storage for speed
or offline) is decided by **usage telemetry**, not upfront: record which meshes
are actually opened, and localise only the hot ones. This avoids pre-caching a
region that may never be inspected, and keeps the first version to a thin
fetch-and-render path.

## Relationship to `osm-basemap-tiles`

Complementary, not overlapping:

- Map mode uses the **merged tiles**; local mode uses **PLATEAU directly**.
  PLATEAU footprints and ids do not correspond to OSM's, so the local scene does
  not try to reconcile them with the tiles — it renders the authoritative model
  for the selected area.
- The two share the **PLATEAU acquisition** work: `osm-basemap-tiles` PR4 pins
  PLATEAU LOD1 heights for the modelled municipalities; this refactor reuses that
  pinned source and extends it to the LOD1/LOD2 **geometry** the local scene
  renders.
- Where a selected area is **not** modelled by PLATEAU, the local scene falls
  back to extruding the merged-tile buildings (the same footprints and heights
  map mode shows), so the box-select always opens *something*, degrading in
  fidelity rather than failing.

## The `osm_id` bridge (aspiration, recorded)

The most convenient future form is to let a building clicked in map mode (which
carries `feature_id`, e.g. `osm:<id>`) resolve directly to its PLATEAU model in
local mode. OSM and PLATEAU ids do not correspond today, so this needs an
`osm_id → plateau gml:id` crosswalk built offline (a spatial match, the same
machinery as the tile merge). This is **not** a launch requirement — the box
selects an *area*, and the scene loads every model in it by mesh regardless of
ids. The crosswalk is an enrichment that makes single-building drill-down exact;
it is recorded here so the schema (`feature_id` in the tiles) already leaves room
for it.

## Decision

Build the local 3D work mode as a box-select that opens an on-demand PLATEAU
scene: draw a box in map mode → load PLATEAU LOD1/LOD2 models for the covered
meshes → render them above ground with the observed subsurface below, carrying SL
overlays and AL simulation. Pull from PLATEAU at interaction time; localise only
what usage telemetry shows is hot; fall back to extruded merged-tile buildings
where PLATEAU has no model. Reuse the renderer-neutral scene handoff already
built for the UC24 underground scenes.

Alternatives considered:

- *Pre-cache all Kanto PLATEAU* — rejected: enormous storage for data most
  sessions never open; telemetry-driven localisation gets the same speed for the
  areas that matter at a fraction of the cost.
- *Render the local scene from the merged tiles alone* — rejected: the tiles hold
  one extrusion height, not roof geometry or storeys; local analysis needs the
  authoritative model. Tiles are the fallback, not the primary.
- *Force an `osm_id → plateau` match before launch* — rejected as a gate: the box
  selects an area, so id correspondence is an enrichment, not a prerequisite.

## Non-goals

- No change to map mode's rendering or the merged tiles — this mode is a separate
  scene, entered from the map.
- No pre-caching of PLATEAU across the region; on-demand first, telemetry-guided
  localisation later.
- No new subsurface data acquisition — the local scene composes the **already
  integrated** observed subsurface (UC24) with on-demand PLATEAU above ground.
- No change to the FL → SL → AL data model or the observed/synthetic/unresolved
  distinction; the local scene presents them, it does not redefine them.

## Planned PRs

Ordered so each step is usable on its own.

1. `01-box-select-scene-shell-pr1.md` — the box-select interaction in map mode
   and the local-scene mode shell (enter/exit, empty 3D scene over the selected
   footprint using the renderer-neutral handoff).
2. `02-on-demand-plateau-loading-pr2.md` — load PLATEAU LOD1/LOD2 models for the
   selected meshes on demand, with the extruded merged-tile fallback where a mesh
   is unmodelled.
3. `03-subsurface-and-analysis-overlays-pr3.md` — compose the observed subsurface
   (UC24) below ground and the SL overlays / AL simulation results into the local
   scene, preserving provenance.
4. `04-usage-telemetry-selective-localisation-pr4.md` — record which meshes are
   opened and add a localisation task that mirrors only the hot meshes into
   project storage for speed/offline.
