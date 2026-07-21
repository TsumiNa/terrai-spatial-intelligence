# PR1 Plan: Shared Pipeline Library

- Status: Completed
- Refactor: `data-pipeline-and-store`
- PR: #42

## Completion record

- All 56 committed JSON/GeoJSON files hash identically before and after the migration; `joint`
  and `evidence` were rebuilt through the migrated writers to prove it, and no re-fetch was
  needed.
- One deviation: `pipeline.provenance` ships the timestamp producer and the three-spelling
  parser but no source/licence stamp-block helpers — the fetchers' stamp blocks share no
  structure beyond `retrieved_at`, so a common helper would have been abstraction without a
  second real caller.
- The 3D-Tiles domain helpers (`_tile_content_paths`, tileset discovery, `_asset_url`,
  `_relative`) stay in `fetch_plateau_uc24_16.py` with `fetch_plateau_uc24_13.py` importing
  them as a sibling: they are format knowledge, not pipeline infrastructure, and moving them
  would make the library format-aware.
- Discovered, not fixed: the committed `scene_handoff.json` files were built from a
  `manifest.json` older than the one #37 committed (`retrieved_at` 10:13:01Z vs 12:39:12Z).
  Rebuilding `underground_scenes` reproduces that diff exactly; it was reverted here to keep
  the data diff empty and is left for a later PR in this sequence.

## Goal

Extract the infrastructure every acquisition and build script currently carries its own copy of
into one `terrai_spatial/pipeline/` package, migrate all scripts onto it, and prove the committed
outputs did not change.

## Scope

1. **`pipeline.http`** — one download function: single User-Agent, one timeout policy, retry
   with backoff (generalized from the only existing implementation,
   `fetch_tepco_grid.py:55-78`), streamed sha256 of what was fetched, and byte/stream variants.
   Replaces the six per-script wrappers.
2. **`pipeline.io`** — atomic JSON/GeoJSON write via temp file and rename, with an explicit
   style parameter (indented or compact, trailing newline or not) so each migrated script can
   reproduce its current output bytes exactly. One GeoJSON validity check, replacing the three
   copies in `bootstrap_packaged_data.py:78-87`, `data_tasks.py:178-187`, and
   `validate_json_outputs`. Safe zip extraction, merging the two existing hardening strategies:
   reject absolute paths and traversal, and enforce size caps.
3. **`pipeline.provenance`** — one `retrieved_at` producer with one format, and helpers for the
   source/licence stamp blocks the fetchers attach.
4. **`pipeline.regions`** — the study-area registry: each region's bbox defined once, in one
   coordinate convention, with named variants where a wider window is intentional. The current
   four encodings disagree on both shape and extent; writing this module forces the decision
   about which numbers are correct, and that decision is recorded in the module, not rediscovered
   per script.
5. Migration of every script in `scripts/` onto the library. The underground family is the
   easiest migration and the template: `fetch_plateau_uc24_16.py` already hosts a de-facto
   shared library that `fetch_plateau_uc24_13.py:18-41` and `fetch_osm_sapporo_underground.py:16`
   import from — promote those helpers into the package and turn the cross-script imports into
   library imports. `build_underground_scenes.py:47` re-implemented the atomic writer instead;
   it migrates like the older scripts. Each script keeps its `main()`, its CLI flags, and its
   one-to-one mapping to a `DataTask`.
6. `data_tasks.py` and `bootstrap_packaged_data.py` switch to the shared validity check.

## Non-goals

No output content changes. No new datasets, no removed datasets. No store, no schema, no service
changes — those are PR2 and PR3. No formula changes in the analysis builders; the planar
geometry duplicates stay in place for `projected-crs-measurement` to replace, unless that
refactor has already landed, in which case its measurement module moves into the library
unchanged.

## Implementation notes

- **Byte-identical migration is the review contract.** Capture checksums of every committed
  output before the migration; after it, only `retrieved_at`-bearing files refreshed by an
  actual re-fetch may differ, and no re-fetch should be needed. A migration PR whose data diff
  is empty is reviewable in minutes; one that reformats 22 GeoJSON files is not.
- The style parameter on the writer exists to make byte-identity achievable, not to bless the
  inconsistency forever. Normalizing formats is a candidate follow-up once the store makes the
  committed files less load-bearing; do not do it here.
- The `retrieved_at` unification changes future stamps, not committed ones. Three formats exist
  in committed data; consumers must already tolerate that, and a test should pin that the parser
  accepts all three.
- One User-Agent for the project, with the repository URL, per the strictest existing string.
  Politeness settings (timeout, backoff, per-host delay for tile fetching) live in the library
  with the values the strictest current script uses.
- `pipeline.regions` is the deliberate decision point for the bbox discrepancy. The wider MLIT
  context window (`fetch_mlit_foundation.py:27`) looks intentional — acquisition context versus
  analysis window — so the registry should name both rather than silently unifying them. The
  two-metre-scale disagreement between the analysis scripts' reference latitudes is not
  intentional and dies here. The Sapporo access bbox
  (`fetch_osm_sapporo_underground.py:26`) joins the registry as its own named region; the
  Nihonbashi extent is computed from ingested tiles rather than declared, and stays that way.
- Keep the library free of source-specific knowledge. If a helper needs to know it is fetching
  MLIT, it belongs in the script, not the library.

## Acceptance

- No script under `scripts/` contains its own HTTP wrapper, atomic-write helper, sha256 helper,
  zip extractor, validity check, timestamp formatter, or bbox literal for the study regions.
- `git diff` over `data/` after migration is empty, demonstrated in the PR description with the
  checksum comparison.
- The library modules have direct unit tests, including retry-on-transient-failure, atomicity
  under a simulated crash between write and rename, zip traversal rejection, and bbox registry
  values pinned against the numbers the scripts used before.
- Every existing script-level test still passes; `uv run python -m terrai_spatial data status`
  reports every task ready.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python, and
  `git diff --check` pass.
