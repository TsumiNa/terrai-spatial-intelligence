# PR5 Plan: Single-scope Kanto Acquisition

- Status: Planned
- Refactor: `kanto-foundation-coverage`

## Goal

The MLIT foundation data has exactly one scope: `scripts/fetch_mlit_foundation.py`
acquires the Kanto window into a gitignored `data/mlit/`, every environment holds the
same data world, and the two-scope machinery disappears.

## Scope

- `scripts/fetch_mlit_foundation.py` becomes the Kanto acquisition script: the archive
  table, streamed writer and windows from the former wide script, writing to
  `data/mlit/`. `scripts/fetch_mlit_foundation_wide.py` and its task are deleted;
  their tests move to the main script's test file.
- `data/mlit/*.geojson` + `metadata.json` leave git (`git rm --cached`, gitignore
  entry); the `mlit` task declares only the manifest as output and stays
  `network=True, automatic=True` — a fresh environment provisions itself on
  `data ensure`, which is the normal development flow.
- `terrai_spatial/data_service.py`: `resolved_dataset_path` and `MLIT_WIDE_DIR` are
  removed; paths are `data/mlit/…` again, and the whole-tree JSON validation skip
  moves to `data/mlit/`. The now-unused `optional` task concept is removed with its
  tests.
- Identity suite scales by collection size: full-collection byte identity for files
  under the threshold; envelope, feature-count and windowed-query identity for files
  over it (the oracle windows through the streaming reader instead of `json.loads`).
  The `terrai_region` query-matrix entries follow the single scope.
- CI (`ci.yml`, `app-ci.yml`, `visual-baselines.yml`): a "Provision foundation data"
  step restores `data/mlit` from the Actions cache keyed on the acquisition table
  (script + regions hash) and runs `fetch mlit` on a miss, before the store build.
- `AGENTS.md` §8 and `docs/refactor/mlit-foundation-data` cross-references updated to
  the single-scope reality.

## Non-goals

- No webapp change (PR6). No zoom-floor changes.
- No rewrite of git history: the formerly committed subsets remain in history.
- The Yokohama/Mobara *analysis* products (AL) keep their areas; this PR is about FL
  acquisition, not the analyses.

## Acceptance

- `uv run pytest` and `terrai validate` pass locally against a fetched `data/mlit`.
- All three workflows pass in CI with the cache step (first run fetches, later runs
  restore); the e2e suite runs against the Kanto-scope store.
- `git ls-files data/mlit` is empty; a fresh `data ensure` provisions and rebuilds
  the store without manual steps.
