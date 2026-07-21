# PR2 Plan: Spatially Indexed Store

- Status: Completed
- Refactor: `data-pipeline-and-store`
- Depends on: PR1 merged
- PR: #45

## Completion record

- Baseline for the PR4 gate: an 88.4 MB store (92,729,344 bytes) from ~87 MB of committed
  sources — 36 datasets, 56,481 features, 13 documents — built in ~2.5 s.
- Features are stored as whole-feature JSON rather than split geometry/properties columns,
  and the dataset row carries an `envelope_json` (top-level collection members with
  `features` emptied in place): per-source member order differs, and PR3's byte-identical
  responses need exact reconstruction. Attribute filters will use `json_extract`.
- `built_at` is the newest source file mtime, not wall clock — the only way a build
  timestamp and byte-identical consecutive builds can both hold.
- The store lives at `var/store/terrai.sqlite`, outside `data/`, because the static
  `/api/v1/assets` mount serves all of `data/` and a derived 88 MB binary does not belong
  on an HTTP endpoint.
- `store_sources()` and the FL/SL/AL tier registry live in `data_service.py` next to the
  key→path mapping, so `store.py` knows no dataset names and PR3's `data_service → store`
  import stays acyclic. The R-tree acts only as a conservative float32 prefilter; float64
  bbox columns preserve the serving scan's exact semantics, pinned against the real
  `railway` layer and an edge-case fixture.

## Goal

Build one gitignored SQLite store from the committed vector FL and derived JSON products,
deterministically, as a data task — with per-feature bounding boxes in a spatial index and a
manifest that ties store content to source file hashes.

## Scope

1. **Schema.** One `features` table: dataset key, stable feature ordinal, geometry as GeoJSON
   text, properties as JSON text, and the feature's bounding box. An R-tree index over the
   bounding boxes. One `datasets` table: key, **tier (`FL`/`SL`/`AL`) and evidence state
   (`observed`/`synthetic`/`unresolved`)**, source path, source sha256, source CRS, licence,
   retrieval and source timestamps, feature count, dataset bbox, build timestamp. Non-feature
   JSON products (summaries, metadata) stored whole in a `documents` table keyed like the
   service keys them today. A schema version stamp in `PRAGMA user_version`; a mismatch at open
   means rebuild, never migrate — this store is derived, and migration files for a rebuildable
   artifact would be machinery without a purpose.
   The SL extension is designed here and deliberately not created: a `model_runs` table
   (model, version, inputs hash, scenario, run timestamp) whose prediction sets enter
   `features` as `SL`-tier datasets referencing their run. It is recorded in the schema
   documentation and lands with the first integrated SL output, because creating empty
   structures ahead of evidence is exactly what the FL/SL/AL commitments prohibit.
2. **Build task.** A new script on the PR1 library reading every dataset the service exposes —
   the bootstrap `DATASETS` and the on-demand `FOUNDATION_DATASETS` — and writing the store
   atomically: build to a temp path, validate, rename over the previous store. Not every
   foundation key is a feature collection: `uc24_16_nihonbashi` and `uc24_13_sapporo` resolve
   to asset manifests (`ASSET_MANIFEST_DATASETS`, `data_service.py:60`), and the scene catalog
   and handoffs are whole-document products — all of these land in `documents`, while
   `osmSapporoUndergroundAccess` and the GeoJSON datasets land in `features`.
3. **Determinism.** Two builds from the same inputs produce byte-identical stores. No wall-clock
   values inside row data; the build timestamp lives in the manifest table only.
4. **Registration.** A `DataTask` wired into `ensure_data` with the GeoJSON files as declared
   inputs, so the existing mtime staleness makes edits to committed data rebuild the store
   automatically. The store path joins `.gitignore`.
5. **Integrity check.** A verification mode that recomputes source hashes against the manifest
   and reports drift, wired into `terrai validate`'s data-task pass.

## Non-goals

No service or API changes — the service still reads GeoJSON until PR3, and this PR must be
revertable without touching serving. No raster, tile, or 3D content. No schema for datasets that
do not exist yet; the underground scene handoff registers like any other dataset when it lands.
No change to committed GeoJSON.

## Implementation notes

- Storing geometry as GeoJSON text is a serving optimization: `query_features` returns features
  verbatim today, so responses become string concatenation rather than decode-encode. WKB would
  be smaller on disk; it would also put a conversion on every response and a second geometry
  encoding in the codebase. Disk is the cheap resource here.
- All SQL is hand-written against `sqlite3` from the standard library — no ORM and no query
  builder, per the overview's decision. Keep every statement a named constant or a function
  returning a string, so the eventual Postgres pairing in the cloud-tier stage is a file
  diff, not an archaeology project.
- Confirm `SQLITE_ENABLE_RTREE` in the interpreter's SQLite at build-task startup and fail with
  a clear message if absent. Fallback if a supported platform lacks it: four B-tree-indexed bbox
  columns answer the same window query with different constants; keep that decision inside the
  store module so PR3 never sees it.
- Feature ordinal must be stable across builds — position in the source file, not a hash — so
  two builds diff as empty and audit references to "feature N of dataset K" stay meaningful.
- Compute each feature's bbox with one vertex walk at build time. This is the walk
  `_intersects_bbox` currently performs per feature per query, moved to the one place it runs
  once.
- Validate the built store before rename: every dataset key present, counts matching the
  manifest, R-tree row count equal to feature count, a sample window query returning known
  features from a fixture dataset.
- Size expectation: roughly the GeoJSON total plus index overhead. At 87 MB of source this is
  not a concern; note the measured store size in the PR description as the baseline the PR4
  gate will cite.

## Acceptance

- A fresh clone followed by `ensure_data` produces the store with no network access.
- Two consecutive builds from unchanged inputs are byte-identical, proven in a test.
- Editing a committed GeoJSON file marks the store task stale and `ensure_data` rebuilds it.
- The manifest ties every dataset to a source sha256, and the verification mode detects a
  deliberately corrupted store in a test.
- A window query through the store module returns exactly the features the current
  `_intersects_bbox` scan returns for the same window, proven against at least one real MLIT
  dataset and one fixture with edge cases: features straddling the window edge, multi-part
  geometries, and a feature whose bbox intersects while its geometry does not (the R-tree answers
  bbox intersection, same as the current scan — pin the semantics, not an idealized one).
- The store file is gitignored; CI proves the working tree stays clean after a build.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python, and
  `git diff --check` pass.
