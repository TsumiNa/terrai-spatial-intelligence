# PR2 Plan: Per-file Store Scope Resolution

- Status: Planned
- Refactor: `kanto-foundation-coverage`

## Goal

The spatial store, and every service surface derived from it, is built from the wide
product when one exists and from the committed demo subset otherwise — decided per
file, recorded in the store manifest, and invisible to the API contract.

## Scope

- `terrai_spatial/data_service.py`: a resolution step for the ten `data/mlit/` dataset
  paths — `data/external/mlit_wide/<name>.geojson` wins when it is a non-empty file
  (a cheap `stat`, never a JSON parse; the atomic writer guarantees a wide file is
  either complete or absent). `path_for`, `store_sources()` and `catalog()` follow the
  resolved path, so the catalog's `path` and `modified_at` fields tell the truth about
  what the store serves in that environment.
- `terrai_spatial/data_tasks.py`: `STORE_INPUTS` already derives from
  `store_sources()`, so store staleness follows resolution with no further change —
  landing or refreshing wide files makes the store stale and the next
  `data ensure` rebuilds it.
- `terrai_spatial/data_service_identity_test.py`: a store-freshness guard — before any
  byte comparison, `verify_store` must pass against the current resolved sources, and
  a drifted store fails with the rebuild instruction instead of a wall of JSON diff.
- `AGENTS.md` §8: document the second scope — committed demo data unchanged, wide
  cache gitignored and preferred by the store when present, CI always demo-scope.
- Tests (`data_service_test.py` or colocated): with a `tmp_path` root, resolution picks
  the wide file when present, falls back when absent or empty, and non-MLIT datasets
  never resolve elsewhere.

## Non-goals

- No change to `/api/v1` routes or payload shapes; `datasets`/`features`/`catalog`
  keep their contracts. Full-collection reads of a wide layer are legal and large;
  the exhibition frontend never issues them (it windows), and this PR does not add a
  guard the demo scope never needed.
- No webapp changes (PR3).
- No CI workflow changes: CI has no wide files, resolves to committed data, and its
  store build stays byte-deterministic.

## Acceptance

- `uv run pytest` passes in a demo-scope checkout (CI's situation) — resolution falls
  back everywhere and the store is byte-identical to before this PR.
- Resolution unit tests prove the wide-wins/fallback behaviour against `tmp_path`
  fixtures without any real wide download.
- `uv run python -m terrai_spatial validate` passes; `data status` stays fast.
