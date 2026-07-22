# PR1 Plan: Wide-scope Acquisition Task

- Status: Planned
- Refactor: `kanto-foundation-coverage`

## Goal

A single opt-in command downloads every MLIT foundation source for mainland Kanto
(Tokyo, Kanagawa, Chiba, Saitama) and writes the ten wide-scope GeoJSON products plus a
manifest into a gitignored cache directory, with the same per-feature provenance the
demo-scope products carry.

## Scope

- `terrai_spatial/pipeline/regions.py`: add the wide acquisition windows —
  `KANTO_WIDE_BOUNDS` `(138.65, 34.85, 140.95, 36.30)` for every archive, plus the
  small `(138.90, 35.10, 139.00, 35.33)` window that clips primary mesh 5238 to the
  Hakone-west sliver of Kanagawa instead of ingesting a block of Shizuoka.
- `scripts/fetch_mlit_foundation_wide.py`: the wide dataset table (same ten dataset
  keys, same upstream dataset ids, wide archive lists probed in `00-overview.md`),
  reusing the demo script's pure helpers (`_layers`, `_json_value`, `_bbox_in_crs`).
  Features are **streamed to the output file one at a time** — the land-use mesh is
  ~2 million features and must never be accumulated as Python dicts. Output files are
  written atomically (temp file + rename), compact, with the same
  `{"type","name","metadata","features"}` envelope and `terrai_*` provenance
  properties; `terrai_region` is `"kanto"` (or `"hakone_west"` for the 5238 clip).
  `metadata.json` records per-dataset downloads, sha256, counts and the wide scope
  statement.
- `scripts/fetch_mlit_foundation_wide_test.py`: archive-table sanity (exactly the ten
  MLIT keys, well-formed nlftp URLs, known region labels), the streaming writer
  producing byte-identical output to `write_json_atomic(compact=True,
  trailing_newline=False)` for a small collection, and the 5238→Hakone-west window
  mapping.
- `terrai_spatial/data_tasks.py`: register `mlit_wide` — `network=True`,
  `automatic=False`, `force_argument=True`, `check_stale=False`, and **only**
  `data/external/mlit_wide/metadata.json` declared as output. The multi-gigabyte
  GeoJSON products are deliberately not declared: `valid_data_file` parses whole files,
  and `data status` must stay cheap. The store build is the loud validator of the wide
  files themselves.
- `.gitignore`: `data/external/mlit_wide/`.
- The demo script `scripts/fetch_mlit_foundation.py` is not modified; its committed
  outputs stay byte-stable.

## Non-goals

- No serving-side changes: nothing reads the wide cache yet (PR2).
- No re-run of the demo-scope fetch; no change to committed data.
- No webapp or docs-card changes (PR3).

## Acceptance

- `uv run pytest` passes; `uv run python -m terrai_spatial validate` passes.
- `uv run python -m terrai_spatial data status` lists `mlit_wide` as missing and
  everything else unchanged; `data ensure` (automatic set) does not attempt it.
- CI runs unchanged: no workflow touches the new task.
- The wide fetch itself is exercised after the sequence merges, not in CI; the PR's
  tests cover the table, the writer and the window mapping.
