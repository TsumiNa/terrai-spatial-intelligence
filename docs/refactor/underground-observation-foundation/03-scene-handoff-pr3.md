# PR3 Plan: Renderer-neutral Underground Scene Handoff

- Status: Planned
- Refactor: `underground-observation-foundation`
- Depends on: PR1 and PR2 merged
- Downstream consumer: `maplibre-migration/07-site-scene-three-pr7`

## Goal

Publish one renderer-neutral scene catalog and per-scene handoff that lets the later Three.js PR open real observed underground assets in a local metric frame without hard-coded coordinates, false co-location or fabricated synthetic evidence.

## Scope

1. Publish a small scene catalog with at least two explicit scene IDs:
   - Nihonbashi utility scene: UC24-16 utility and access-structure layers; no UC24-13 station space.
   - Sapporo Station public-space scene: UC24-13 underground structures plus independent OSM context; no UC24-16 utility network.
2. For each scene, derive and validate a local frame from source geometry: geographic extent, origin, axis convention, units, source CRS, world-to-local transform, local-to-world inverse, height reference, and vertical datum or explicit `unknown`. Vertical exaggeration is renderer configuration owned by MapLibre PR7, not a coordinate fact in this handoff.
3. List assets by evidence family and availability rather than forcing uniform contents. At minimum distinguish terrain/buildings context, utility networks, underground structures, access topology, boreholes, strata and predicted fields as `available`, `unresolved` or `not_applicable`, with source IDs for every available family.
4. Publish the handoff as derived auxiliary metadata owned by the existing UC24-16 and UC24-13 source-dataset records in the file-backed service. Do not register a separate FL dataset key or create the final site-bundle endpoint here; MapLibre PR7 owns endpoint shape, bbox selection and Three.js delivery.
5. Add round-trip tests proving representative coordinates transform world → local → world within a declared tolerance, asset paths resolve inside approved roots, and the two scenes cannot accidentally share or merge geographically incompatible layers.
6. Add tests that unavailable evidence cannot carry fabricated feature counts, asset paths or model identities. `synthetic` is absent in these scenes because no SL output has been integrated.
7. Document the handoff in the relevant UC24-16, UC24-13 and OSM data cards without adding a separate dataset card for the manifest itself.

## Contract decisions

- The handoff describes evidence and coordinate facts; it contains no renderer configuration, vertical exaggeration, colour, camera preset or Three.js object graph.
- A scene may be useful with only observed structural evidence. Boreholes, strata and predicted fields are optional evidence families, not empty geometry created to satisfy a fixed payload.
- `unresolved` means the product lacks qualified evidence. `not_applicable` means the evidence family does not belong to the scene's stated purpose. They are not interchangeable.
- The local frame is generated from and traceable to source coordinates. It is never typed manually into frontend code.
- Scene selection never unions Nihonbashi and Sapporo. Cross-scene comparison may happen at the catalog level only.

## Non-goals

- No `/site-bundle` API endpoint, box-selection behavior or frontend state.
- No Three.js canvas, mesh conversion, clipping plane or ray marching.
- No terrain/building acquisition beyond references to already integrated context where spatially available.
- No geo_pfn output contract, borehole schema, strata mesh or uncertainty volume.
- No promise that customer datasets will use the same physical file layout; only the evidence concepts and audit requirements are the handoff.

## Implementation order

1. Inventory source coordinate and height semantics from the actual PR1/PR2 caches.
2. Write round-trip, path-safety, missing-evidence and cross-scene-isolation tests before generating manifests.
3. Generate the scene catalog and local-frame handoffs deterministically.
4. Register on-demand access through the existing data service.
5. Update the three affected data-card groups with the final measured facts.
6. Verify the handoff from a clean data restore and from strict offline mode.

## Acceptance

- Both canonical scenes resolve only assets within their own source extents and approved cache roots.
- World/local coordinate round trips meet the documented tolerance, including height, or fail validation when the source vertical reference is insufficient.
- Each available evidence family names its source, retrieval timestamp, source time, licence and audit index; unresolved families contain no geometry or fake model metadata.
- Source assets and their auxiliary scene manifests are on-demand and absent from frontend bootstrap; no independent scene-handoff dataset key is registered.
- Reverting PR3 leaves PR1 and PR2 source integrations usable and valid.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python and `git diff --check` pass.

## Handoff

After this PR merges, update `docs/refactor/maplibre-migration/07-site-scene-three-pr7.md` from `Blocked` to `Planned` and narrow its first implementation to observed structural scenes. The PR7 endpoint may return the handoff plus selected assets for a bbox, but it must preserve availability states and local-frame provenance. Geo_pfn volumetric rendering remains a later plan and must not be smuggled into PR7 merely because its original blocker mentioned prediction shape.
