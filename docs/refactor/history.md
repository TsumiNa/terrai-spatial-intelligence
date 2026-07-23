# Refactor History

The at-a-glance index of every refactor under `docs/refactor/`, so no one has
to open each folder to learn what exists and what is done. One section per
refactor, newest first by creation date. Each section states the folder, a
one-line description, the current state, and a note — the note is where a plan
that was only evaluated but not yet decided for execution says so.

Open a refactor's `00-overview.md` for its full rationale and per-PR plans.

## osm-basemap-tiles

- Folder: `osm-basemap-tiles/`
- Created: 2026-07-23
- Description: Build self-hosted OSM building vector tiles (PMTiles) so dense city fabric renders at every zoom, moving the wide-view basemap from live GSI to snapshot-pinned tiles.
- State: **Planned** — assessed feasible, not started.
- Note: Feasibility assessed 2026-07-23 (3–15 min preprocessing, ~300–700 MB PMTiles, near-zero serving CPU, GCP ~$5–$320/mo by traffic). **Awaiting the owner's go decision before any PR begins.**

## basemap-resilience

- Folder: `basemap-resilience/`
- Created: 2026-07-23
- Description: Pin a local snapshot of the GSI vector style and add a production-raster fallback, so the wide-view basemap survives the experimental endpoints changing or dying.
- State: **Planned** — not started.
- Note: Recorded for owner evaluation; execution not scheduled. Both PR plans carry full Goal/Scope/Non-goals/Implementation/Acceptance.

## osm-highzoom-detail

- Folder: `osm-highzoom-detail/`
- Created: 2026-07-23
- Description: Serve Kanto OSM building footprints as windowed data objects that replace the basemap's cartographic buildings past z16 — every high-zoom building clickable with a stable `osm_id`.
- State: **Completed** — three-PR sequence #65–#67 merged.
- Note: Complements `osm-basemap-tiles` (z16+ clickable objects here; wide-view fabric there).

## kanto-foundation-coverage

- Folder: `kanto-foundation-coverage/`
- Created: 2026-07-22
- Description: Expand the MLIT foundation acquisition from two demonstration windows to the whole mainland-Kanto area (Tokyo, Kanagawa, Chiba, Saitama) as one scope.
- State: **Completed** — eight-PR sequence #52–#59 merged.
- Note: PR3's two-scope surfacing was superseded mid-sequence by the owner's single-scope revision; PR5–PR8 carry the final design.

## underground-observation-foundation

- Folder: `underground-observation-foundation/`
- Created: 2026-07-21
- Description: Integrate the PLATEAU Nihonbashi utilities, Sapporo underground access, and the renderer-neutral scene handoff as observed underground Foundation data.
- State: **Completed** — three PR stages merged.
- Note: —

## ui-design-system

- Folder: `ui-design-system/`
- Created: 2026-07-21
- Description: Establish the visual/a11y baseline, lock the palette to a Tailwind theme with an enforcement guard, and add the overlay primitives.
- State: **Completed** — five PR stages (#1–#5) merged.
- Note: —

## rust-api-backend

- Folder: `rust-api-backend/`
- Created: 2026-07-21
- Description: Direction for eventually re-implementing the read-only API in Rust for the cloud tier.
- State: **Planned** — direction only, no PR stages written.
- Note: Gated on entry conditions recorded in the overview (measured need + scheduled cloud deployment); not started, and one entry condition is recorded as not yet met.

## projected-crs-measurement

- Folder: `projected-crs-measurement/`
- Created: 2026-07-21
- Description: Replace the planar-approximation distance math with a projected CRS (EPSG:6677) in the shared pipeline library.
- State: **Completed** — merged as #44.
- Note: —

## on-demand-fl-delivery

- Folder: `on-demand-fl-delivery/`
- Created: 2026-07-21
- Description: Build the frontend consumers of the windowed feature API — the viewport-driven client, the foundation-overlay UI, and the underground scene intake.
- State: **Completed** — three PRs (#47–#49) merged.
- Note: —

## mlit-foundation-data

- Folder: `mlit-foundation-data/`
- Created: 2026-07-21
- Description: Acquire and subset the open MLIT foundation datasets as the first on-demand Foundation source pack.
- State: **Completed** — merged as PR #3.
- Note: —

## maplibre-migration

- Folder: `maplibre-migration/`
- Created: 2026-07-21
- Description: Migrate the exhibition frontend from Leaflet to MapLibre GL + deck.gl, including the underground and site-scene renderers.
- State: **Completed** — stages #12–#17 reached parity and retired Leaflet; #38–#39 render the underground scenes.
- Note: —

## gsi-national-local-fl

- Folder: `gsi-national-local-fl/`
- Created: 2026-07-21
- Description: Integrate GSI designated evacuation data as a national-base Foundation layer with local validation.
- State: **Completed** — merged as PR #2.
- Note: —

## fl-sl-al-platform

- Folder: `fl-sl-al-platform/`
- Created: 2026-07-21
- Description: Establish the FL → SL → AL conceptual layers, the exhibition FastAPI surface, and the documentation-governance rules.
- State: **Completed** — merged as PR #1.
- Note: The founding refactor; documentation governance from here is what this history extends.

## data-pipeline-and-store

- Folder: `data-pipeline-and-store/`
- Created: 2026-07-21
- Description: Build the shared pipeline library, the spatially indexed SQLite store, and the store-backed data service.
- State: **Completed** — PR1–PR3 (#42, #45, #46) delivered.
- Note: PR4 (large-layer cache migration) and PR5 (Postgres cloud tier) are **Blocked**, each gated on a measured trigger that has not occurred; deliberately outside the executed sequence.
