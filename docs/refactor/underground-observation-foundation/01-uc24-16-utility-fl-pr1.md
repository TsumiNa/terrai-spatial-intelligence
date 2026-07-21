# PR1 Plan: UC24-16 Underground Utility Foundation Data

- Status: In progress
- Refactor: `underground-observation-foundation`
- Downstream consumer: `maplibre-migration/06-underground-networks-pr6`

## Goal

Make the complete Nihonbashi UC24-16 underground utility sample reproducibly available as auditable, on-demand FL without placing upstream 3D binaries in Git or the frontend bootstrap.

## Scope

1. Query the official CKAN `package_show` record for `plateau-uc24-16` and select every Nihonbashi underground resource: water, sewer, gas, communications and power networks plus their published manhole/handhole assets.
2. Download ZIPs from the returned official resource URLs, reject unsafe members, record resource ID/name, URL, response timestamp, HTTP `Last-Modified`, byte size and SHA-256, and preserve the upstream `tileset.json`/glTF structure in a local cache.
3. Validate 3D Tiles 1.1 references and glTF `EXT_structural_metadata`; create a lightweight audit index that maps source feature identifiers to published attributes without inventing missing values. At minimum retain depth range, outer diameter, material, length, measurement type, geometry/thematic source descriptions, creation/source date and utility class when present.
4. Record horizontal CRS, the 3D Tiles bounding volume, height units, vertical-reference interpretation and whether ground-relative depth can be derived directly. Unknown vertical datum remains `unknown`; do not infer one from visual alignment.
5. Register one automatic, network-aware data task that restores a missing canonical cache and supports the normal explicit update path. Offline mode reports the scene unavailable rather than partially ready.
6. Expose stable on-demand catalog metadata and asset roots needed by a future deck.gl `Tile3DLayer`; do not add these binaries to `/bootstrap` and do not add rendering code.
7. Add a trilingual UC24-16 data card and source-registry entry. The card must state the precise Nihonbashi subset, feature/asset counts measured after ingestion, source vintage, fields and units actually read, licence, sample-data limitation and non-operational status.
8. In the UC24-16 card, retain Nagoya, Osaka, UC23-04, Yokohama utility viewers, Tokyo Gas and the absence of an authoritative open fibre-route source as clearly non-integrated references. Do not create catalog rows or standalone FL cards for them.

## Data semantics required by MapLibre PR6

- An underground object is **observed external sample data**, not SL prediction.
- Absolute 3D position and `minDepth`/`maxDepth` are separate concepts. PR6 must not force a negative absolute elevation or subtract depth twice.
- Surveyed, inferred and unknown positional methods are derived only from published measurement/source fields. Unknown is a first-class state.
- `communications cable` remains that label unless the feature itself identifies fibre.
- A picked feature resolves to source dataset, resource archive, upstream feature ID, retrieval timestamp, source-time metadata, depth/diameter values with units, measurement method and limitations.

## Non-goals

- No MapLibre camera mode, deck.gl layer, legend, colour or interaction changes.
- No mesh-to-centreline reconstruction.
- No Nagoya or Osaka runtime cache in this PR.
- No condition, pressure, capacity, owner contact or excavation-clearance inference.
- No API endpoint designed specifically for Three.js; stage 03 owns the renderer-neutral scene handoff.

## Implementation order

1. Inspect and freeze the official resource selection and licence evidence.
2. Add failure-first tests for unsafe ZIP paths, missing tiles, broken content URIs, absent CRS/height metadata and malformed structural metadata.
3. Implement acquisition and cache validation.
4. Generate the audit index and measured manifest from a real download.
5. Register the data task and on-demand catalog entry.
6. Add the trilingual data card and source-registry record.
7. Run a clean-cache online restore and strict offline-status check.

## Acceptance

- A clean online run restores every selected Nihonbashi archive and produces the same validated asset/audit manifest from official URLs.
- Changing or corrupting an upstream archive is detected by structural validation and recorded hash rather than silently accepted.
- Every indexed feature retains its original ID and source resource; missing depth, diameter, date, method or datum stays explicitly unknown.
- No upstream ZIP, glTF or expanded 3D Tiles file is tracked by Git.
- The frontend bootstrap payload is byte-for-byte unaffected by the new catalog/asset availability.
- The data task is `ready` with a complete cache, reports the whole scene unavailable when offline and incomplete, and never reports a partial scene as ready.
- `docs/data/` contains a complete EN/JA/ZH UC24-16 card with identical facts and a clearly separated reference-only section.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, Ruff for changed Python and `git diff --check` pass.

## Handoff

After this PR merges, update `docs/refactor/maplibre-migration/06-underground-networks-pr6.md` from `Blocked` to `Planned`, link its blocking dependency to the UC24-16 card, and make its implementation consume the published scene/audit contract. That status change belongs to the PR6 implementation branch, not this data PR.
