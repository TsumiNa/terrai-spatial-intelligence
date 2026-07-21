# PR2 Plan: UC24-13 and OSM Underground Access Foundation Data

- Status: Completed
- Refactor: `underground-observation-foundation`
- Depends on: PR1 merged
- Downstream consumer: `maplibre-migration/07-site-scene-three-pr7`

## Goal

Make Sapporo Station's observed underground structures and independently sourced public-access topology reproducibly available as a coherent, auditable scene input without claiming that OSM validates PLATEAU geometry.

## Scope

1. Query the official CKAN record for `plateau-uc24-13` and select the Sapporo underground-mall model and municipal-subway Sapporo Station model. Keep the North Ichijo parking, Shibuya passage and Takamatsu parking resources as reference-only inventory entries.
2. Acquire, hash, timestamp and structurally validate the selected 3D Tiles using the cache rules established by PR1. Reuse concrete acquisition behavior rather than creating a parallel downloader or task framework.
3. Define and version a bounded Overpass query for the same Sapporo scene extent. Extract only public OSM evidence relevant to access: subway rail/tunnel ways, stations/platforms where present, `railway=subway_entrance`, and public underground footways/corridors carrying `tunnel`, `indoor`, `level` or negative `layer` evidence.
4. Preserve OSM element ID/version, changeset timestamp where returned, tags, retrieval timestamp and ODbL attribution. Do not convert absence of a tag into an asserted surface location.
5. Keep PLATEAU structural geometry and OSM topology as separate FL datasets linked only by scene ID and spatial context. Any future reconciliation must expose confidence and must not silently snap one source to the other.
6. Produce committed lightweight OSM GeoJSON and retrieval metadata; keep PLATEAU ZIP/3D Tiles as reproducible local cache. Register readiness so a missing PLATEAU cache is restored online while the committed OSM snapshot keeps its own explicit refresh path.
7. Add a trilingual UC24-13 card and extend the existing trilingual OpenStreetMap card with the exact underground query, snapshot date, tag set, feature counts, known gaps and ODbL obligations.
8. In the UC24-13 card, keep Shibuya, Takamatsu and UC23-05 as reference-only resources. Do not create integrated catalog rows for resources not selected into the canonical scene.

## Source-precedence rule

There is no national/local precedence relationship between PLATEAU and OSM here because they describe different evidence:

- PLATEAU is the observed 3D structural sample.
- OSM is a community public-access/topology supplement.

OSM may add entrances or paths absent from the sample, but may not overwrite PLATEAU geometry, height or identity. PLATEAU may not be used to imply that an OSM path is legally public or currently open.

## Non-goals

- No routing engine or claim of a complete pedestrian graph.
- No real-time closures, fare-gate state, opening hours or accessibility inference.
- No reconciliation by nearest-neighbour snapping in this PR.
- No Svelte, MapLibre or Three.js code.
- No utility network is fabricated for Sapporo; UC24-16's canonical utilities remain in geographically separate Nihonbashi.
- No scraping of operator floor maps, BIM portals or authenticated station systems.

## Implementation order

1. Freeze the selected UC24-13 resources and Sapporo bbox.
2. Add tests for 3D asset completeness and OSM tag/filter semantics, including empty Overpass results and ambiguous levels.
3. Extend the existing PLATEAU cache path for the Sapporo structure assets.
4. Run the bounded Overpass query and normalize a reproducible snapshot without discarding original tags.
5. Generate measured manifests and independent provenance for both sources.
6. Register on-demand datasets and update trilingual documentation.
7. Verify clean online restore, offline behavior and repeatable OSM refresh.

## Acceptance

- The two selected UC24-13 asset roots load and validate from a clean online cache.
- The committed OSM snapshot contains only the documented bbox/tag scope, and every feature exposes its OSM ID, version/timestamp when available and original tags.
- PLATEAU and OSM objects remain distinguishable in files, catalog, audit metadata and identifiers.
- Unknown level, depth, accessibility and public-opening status stay unknown.
- The cards state measured asset/feature counts and explicitly distinguish integrated Sapporo resources from reference-only Shibuya, Takamatsu and UC23-05 resources.
- The frontend bootstrap is unchanged.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python and `git diff --check` pass.

## Handoff

This PR supplies observed structures and access context, but does not by itself unblock MapLibre PR7. PR7 should move to `Planned` only after PR3 publishes the scene-local frame and evidence-availability handoff.
