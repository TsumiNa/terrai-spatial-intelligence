# PR5 Plan: PostgreSQL Cloud Tier

- Status: Blocked — starts when cloud deployment is actually scheduled, not before; the trigger
  is a decision to deploy, or the first authoritative table (SL model output or review state)
  that needs concurrent writes
- Refactor: `data-pipeline-and-store`
- Depends on: PR2 and PR3 merged

## Goal

Implement the store's conceptual schema on PostgreSQL with PostGIS as the cloud tier, behind
the same store interface the SQLite tier serves, so deployment to GCP changes where data lives
and nothing about what the service means.

## Scope

1. **The same conceptual schema in PostGIS DDL.** `datasets` with tier and evidence state,
   `features` with geometry, properties as `jsonb`, a GIST index in place of the R-tree, and
   `documents` — plus, if the trigger was an SL output, the `model_runs` table designed in PR2.
2. **Dialect-paired queries.** Each statement in the store module gains its Postgres partner:
   JSON path functions for the attribute filters, bbox overlap via the geometry index for the
   window query, parameter style handled at the module boundary. No shared-dialect abstraction
   layer; two explicit SQL texts per query, side by side.
3. **One semantics suite, two backends.** The table-driven tests that pin filter semantics,
   missing-property behaviour, type coercion, sort order, and window edge cases in PR2/PR3 run
   unchanged against both tiers in CI. A behavioural difference between tiers is a red build,
   not a production surprise.
4. **The migration runner becomes load-bearing.** Forward-only numbered SQL files applied by
   the small in-repo runner, with a `schema_migrations` record table. The FL data itself still
   arrives by the deterministic build — for rebuildable datasets, "migration" on the cloud tier
   is re-running the loader; migration files govern authoritative tables only.
5. **Load path.** The PR2 build task gains a Postgres target: same inputs, same manifest
   semantics, loading into a transactionally swapped schema or table set so a serving instance
   never reads a half-loaded tier.
6. **GCP shape, minimally.** Cloud SQL for PostgreSQL with PostGIS as the instance; connection
   configuration through environment, never code; bulk binaries — tiles, imagery, future
   3D Tiles — go to object storage, not the database. Full deployment (Cloud Run, networking,
   auth, IaC) is its own refactor when it starts; this stage only ensures the data layer is
   ready for it.

## Non-goals

No API contract change — the frozen `/api/v1` surface serves identically from either tier.
No ORM, no query builder, no cross-dialect abstraction layer. No removal of the SQLite tier:
offline demo operation is a recorded must-survive constraint and the local tier remains the
default for clone-and-run. No deployment infrastructure beyond what the data layer itself
requires. No SL modelling work — this stage stores SL outputs if they exist, it does not
create them.

## Implementation notes

- `psycopg` (3.x) is the client, added as a dependency only when this stage lands. Until then
  the project carries no Postgres code and no Postgres dependency.
- The store interface settled in PR3 is the thing that makes this stage small. If implementing
  this PR reveals the interface leaking SQLite assumptions — rowid semantics, `user_version`,
  R-tree quirks — fix the leak in the interface first, as its own commit, before writing
  Postgres code against it.
- `jsonb` changes key-order and duplicate-key behaviour relative to stored JSON text. The
  semantics suite must include a case that would catch reordering if any consumer depends on
  it; the audit provenance round-trip test from PR3 is the natural candidate.
- Geometry lands as real PostGIS geometry (from the GeoJSON via `ST_GeomFromGeoJSON`,
  SRID 4326) rather than text, because the cloud tier is where real spatial predicates become
  available and cheap. The API still returns GeoJSON: serialize on read via `ST_AsGeoJSON` or
  store a text copy alongside — decide by measuring, record the measurement in the PR.
- Postgres in CI via the standard service-container pattern; contributors without Docker still
  run the full SQLite suite locally, and CI owns the cross-tier guarantee.

## Acceptance

- To be finalized when unblocked, with at minimum: the semantics suite green against both
  tiers; the recorded `/api/v1` request set byte-identical from either tier; the migration
  runner applying a fixture migration exactly once and refusing to reapply it; the loader
  producing a cloud tier whose per-dataset manifest matches the SQLite tier's; and no Postgres
  dependency reachable from the offline demo path.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python, and
  `git diff --check` pass.
