# PR3 Plan: Store-backed Data Service

- Status: In progress
- Refactor: `data-pipeline-and-store`
- Depends on: PR2 merged

## Goal

Move `DataService`'s internals onto the store behind the frozen `/api/v1` contract, remove the
per-request deep copies and linear scans, and measure the difference. This PR produces the
storage-layer measurement that `rust-api-backend` names as its entry condition.

## Scope

1. `query_features` answers from the store: R-tree window first, attribute filters
   (`where`/`equals`/`minimum`/`maximum`) as SQL over the properties JSON, `limit` applied in
   the query, response assembled from stored GeoJSON text.
2. `load`, the bootstrap path, and the scene catalog/handoff readers (`scene_catalog`,
   `scene_handoff`, `data_service.py:121-133`) read from the store's `documents` and `features`
   tables. The mtime-keyed full-file caches and every per-access `deepcopy`
   (`data_service.py:104-119`, `:298`) are deleted, replaced by read-only access to immutable
   store rows.
3. Startup falls back loudly, not silently: if the store is missing or fails its manifest check,
   the service refuses to start and names the `ensure_data` command that fixes it, rather than
   quietly reading GeoJSON and hiding a broken pipeline.
4. **Measurement, before and after, in the PR description:** bootstrap assembly time; a window
   query against `landHistory` (23 MB, 3,780 features) and `landUseMesh` (20 MB, 31,132
   features); an attribute-filtered query; and resident memory after serving each. Same
   machine, same data, stated methodology.
5. Response-identity tests: for a recorded set of requests spanning every endpoint, byte-for-byte
   identical JSON from the old path and the new one, modulo nothing.

## Non-goals

No contract change of any kind — paths, keys, parameters, shapes, and error responses are
frozen, and `terrai validate`'s literal-substring assertions on `api.py` must pass untouched.
No new endpoints. No frontend changes. No query capabilities beyond what the contract already
exposes; adding capability the frontend cannot use yet belongs to `on-demand-fl-delivery`.

## Implementation notes

- The equivalence bar is the current behavior, including its quirks. `_intersects_bbox` matches
  on bbox overlap, not true geometry intersection; the store answers the same question. If a
  quirk turns out to matter, fixing it is a separate, visible change — not a silent side effect
  of the migration.
- Property filters over JSON text use SQLite's JSON functions. Pin the semantics of missing
  properties and type coercion against the current `_matches` implementation with table-driven
  tests before writing the SQL, because "SQL that looks equivalent" is where this migration
  would silently diverge.
- Sort order must be preserved. The current path filters in file order and truncates; the SQL
  path must order by the stable feature ordinal, not by R-tree visit order, or `limit` changes
  which features appear.
- One read-only connection per worker with `mode=ro`; the store is replaced atomically by
  rename, so a serving process never observes a half-built store.
- The audit provenance blocks ride inside properties JSON and come back untouched. A test pins
  one known provenance dict end-to-end.
- Delete the dead code fully: the recursive `_coordinate_pairs` walk and `_intersects_bbox`
  have no callers after this PR. Keeping them "for reference" recreates the two-implementations
  problem this refactor exists to end.

## Acceptance

- All recorded requests return byte-identical responses across the migration.
- The exhibition runs unchanged: full Playwright suite passes against the store-backed service.
- Windowed queries against the two largest MLIT layers are measured and reported; resident
  memory no longer scales with the size of collections not being queried.
- Service startup with a missing or corrupt store fails with the actionable message.
- `data_service.py` remains the only component that knows where data lives; nothing above it
  imports the store module.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, `npm run build`, the Playwright
  suite, Ruff for changed Python, and `git diff --check` pass.

## Handoff

The measurements go two places: the PR description, and an update to
`docs/refactor/rust-api-backend/00-overview.md`'s entry conditions — either the storage layer
resolved the latency question, or the numbers now exist to justify planning stages there.
`on-demand-fl-delivery` PR1 should be implemented against this service, not before it.
