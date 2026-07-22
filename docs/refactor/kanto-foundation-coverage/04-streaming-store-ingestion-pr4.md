# PR4 Plan: Streaming Store Ingestion

- Status: Planned
- Refactor: `kanto-foundation-coverage`

## Goal

`build_store` ingests a feature collection of any size in bounded memory: features
stream from disk and insert in batches, and only files under a size threshold are
still parsed whole. Nothing about the built store changes — two builds from the same
inputs remain byte-identical, whichever path ingested them.

## Scope

- `terrai_spatial/store.py`: `stream_feature_collection(path)` — an incremental
  GeoJSON reader over `json.JSONDecoder.raw_decode` with a chunked, compacting
  buffer. It returns the top-level envelope members (in file order, `features`
  emptied) plus a feature iterator; envelope members that follow the features array
  are completed once the iterator is exhausted, which is the order `build_store`
  consumes them in. Malformed input fails with the file path and byte offset.
- `build_store` gains a `stream_threshold` (default 64 MB): smaller files keep the
  exact `json.loads` path, larger files stream and insert in batches of 10,000 rows.
  Dataset bbox, envelope JSON, counts, stamps and determinism are unchanged.
- Tests: a collection forced through the streaming path parses identically to
  `json.loads` (envelope and features); a store built with `stream_threshold=0` is
  byte-identical to one built with the default; truncated and trailing-garbage files
  fail loudly.

## Non-goals

- No change to the read side (`read_collection`, `window_features`) or to any service
  behaviour; no acquisition or data change (PR5).
- No new dependency: the reader is the standard library decoder over our own writer's
  format, tolerant of whitespace.

## Acceptance

- `uv run pytest` passes; the byte-identity build test proves both ingestion paths
  produce the same store file.
- `uv run python -m terrai_spatial data ensure --only store --force` rebuilds the
  committed-scope store unchanged (verified by `terrai validate`).
