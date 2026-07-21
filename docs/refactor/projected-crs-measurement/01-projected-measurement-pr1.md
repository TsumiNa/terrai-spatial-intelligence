# PR1 Plan: Projected Measurement for the Build Pipelines

- Status: In progress
- Refactor: `projected-crs-measurement`

## Goal

Replace the local planar approximation in both build scripts with measurement in EPSG:6677, keep
storage in EPSG:4326, regenerate the affected outputs, and state exactly which published values
and band assignments changed.

## Scope

1. Add one measurement module holding the target CRS, a cached `pyproj.Transformer` from
   EPSG:4326, and the metric primitives both scripts need: point-to-point distance,
   point-to-segment distance, point-to-line distance, polygon area, and centroid.
2. Migrate `scripts/build_joint_analysis.py` onto it. Delete `LAT0`, `M_PER_DEG_LAT`,
   `M_PER_DEG_LON`, and the `xy` helper at lines 18-36.
3. Migrate `scripts/build_multiscale_evidence.py` onto it. Delete the equivalent block at
   lines 17-19 and its `distance` / `point_segment_distance` / `point_line_distance` helpers.
4. Correct both module docstrings. The stdlib-only claim is false once this lands.
5. Regenerate the `joint` and `evidence` data task outputs.
6. Produce a comparison of old versus new for every numeric property the two tasks emit, and
   record the band-change count.
7. Update the geospatial-measurement provenance record in `webapp/src/lib/audit.ts` so its
   limitation text describes the projected workflow instead of the approximation, in all three
   languages.

## Non-goals

No threshold, weight, or formula changes. No elevation or vertical datum. No storage-format
change. No new module, view, or layer. No touching the MLIT ingest transform, which is already
correct.

## Implementation notes

- Transform once per input feature collection, not once per distance call. The current code calls
  its scale conversion inside the innermost loop of a nearest-neighbour search; a per-call
  `Transformer` would make that pathological.
- Construct the `Transformer` with `always_xy=True` so coordinate order matches the GeoJSON
  convention and the existing `fetch_mlit_foundation.py` call.
- Both scripts perform nearest-feature searches over the full candidate set. Projecting the
  candidates once into arrays, then measuring, is both faster and simpler than projecting inside
  the comparator.
- `area_ha` and `footprint_m2` are pre-existing properties on input features, not computed by
  these scripts. Confirm their provenance before assuming this PR changes them; if they were
  themselves derived planar, say so in the PR and leave them to a follow-up rather than silently
  recomputing values whose source pipeline is out of scope.
- Keep the same output key names and JSON shape. A frontend or schema change in this PR would
  confuse the measurement diff with an interface diff.
- Both tasks write committed artifacts that `terrai validate` checks for staleness, so
  regeneration is part of the PR, not a follow-up.

## Verification of the change itself

The PR is not trustworthy without a before/after comparison, because every reviewer is being
asked to accept that thousands of committed numbers should move.

- Capture the current outputs before migrating.
- After regeneration, report for each numeric property: maximum absolute change, maximum relative
  change, and the count of features whose band or rank changed.
- The expected signature is a systematic north–south shrink of roughly 0.34% plus a smaller
  east–west term. A change far outside that, or a change with no directional structure, means the
  migration is wrong and must be investigated rather than committed.
- Band changes are expected to cluster within a few metres of the 55 m, 90 m, 150 m, and 250 m
  thresholds. A band change far from any threshold is a defect.

## Acceptance

- Neither build script contains a hard-coded metres-per-degree constant.
- Both scripts measure through the shared module; no second implementation of distance survives.
- Regenerated `joint` and `evidence` outputs are committed, and `terrai validate` reports both
  tasks ready rather than stale.
- Round-trip tests prove a representative coordinate transforms EPSG:4326 → EPSG:6677 → EPSG:4326
  within a declared tolerance, and that a known separation measures to its expected metric value.
- Tests cover both demo regions, so a zone that fits Yokohama but not Mobara fails.
- `scripts/build_multiscale_evidence_test.py` passes or is updated with the reason for each
  expected-value change stated in the diff.
- The audit drawer no longer describes the measurement as approximate, in English, Japanese and
  Chinese.
- The PR description carries the before/after comparison and the band-change count.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python, and
  `git diff --check` pass.
