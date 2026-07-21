# PR4 Plan: Large Layers Out of Git

- Status: Blocked — gated on a measured trigger that has not occurred; see the entry condition
- Refactor: `data-pipeline-and-store`
- Depends on: PR1 through PR3 merged

## Entry condition

This stage starts when either committed vector FL exceeds roughly 200 MB, or a routine data
refresh produces a git delta over 50 MB, or clone time becomes a stated contributor complaint —
whichever comes first, recorded with the number that triggered it. Until then, committed GeoJSON
at the current 87 MB is a cost worth paying for zero-infrastructure clones and reviewable data
diffs.

## Goal

Move large FL layers from committed GeoJSON to the cached-acquisition pattern the underground
refactor established — git holds manifests, hashes, and audit indexes; bytes are restored on
demand — without breaking offline operation or the store build.

## Scope

1. A size policy in one place: datasets above a threshold are cache-tier, below it stay
   committed. The exhibition-critical bootstrap datasets stay committed regardless, so a fresh
   clone still runs the demo offline.
2. Cache-tier datasets follow the underground pattern: source manifest with URL resolution,
   sha256, retrieval metadata, and licence record committed; the normalized GeoJSON itself
   restored by the dataset's existing fetch script into a gitignored path.
3. The PR2 store build reads committed and cache-tier datasets identically; the manifest
   records which tier each came from.
4. `ensure_data` distinguishes "missing, restorable offline from git history" (the existing
   `bootstrap_packaged_data.py` mechanism) from "missing, requires network", and says which.
5. History handling decided and recorded: whether the large blobs already in git history are
   left (clones stay heavy until a future rewrite) or removed with a coordinated history
   rewrite. This is a one-time team decision with a forced-push cost; the plan does not
   presuppose the answer, it requires the decision be explicit.

## Non-goals

No new storage format — cache-tier datasets are the same GeoJSON in a different location. No
change to the store schema or the service; both already read from paths the manifest names. No
change to acquisition scripts beyond output location. No LFS unless the history decision
concludes it is wanted; LFS is a variant of this stage, not an assumption.

## Acceptance

- To be finalized when the entry condition fires, with at minimum: a fresh clone runs the
  exhibition offline; `ensure_data` with network restores every cache-tier dataset and the
  store builds identically from either tier; no committed file exceeds the recorded threshold;
  and the trigger measurement appears in the PR description.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python, and
  `git diff --check` pass.
