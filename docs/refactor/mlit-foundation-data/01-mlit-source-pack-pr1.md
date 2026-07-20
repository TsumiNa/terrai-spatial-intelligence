# PR1 — MLIT Foundation Source Pack

## Status

Completed

## Goal

Make the commercially usable requested MLIT datasets reproducibly downloadable, normalized, timestamped, licensed, and queryable as Foundation Data Layer evidence without increasing the normal frontend bootstrap payload. Preserve W05 research as documentation without integrating its data or code.

## Scope

- Add a tested MLIT download/normalization script and geospatial dependency needed for official GML, GeoJSON, and Shapefile archives.
- Produce committed, clipped FL GeoJSON outputs for the ten redistributable/conditionally redistributable datasets.
- Exclude W05 river download code and outputs while retaining a trilingual source evaluation.
- Register automatic data readiness for the committed open MLIT source pack.
- Add on-demand FL API dataset keys without adding the layers to the exhibition bootstrap payload.
- Record source timestamps, retrieval timestamps, archive hashes, source URLs, licences, commercial constraints, and cached feature counts.
- Add/update trilingual data catalog and one dataset card per integrated source.
- Add tests for download safety, geometry clipping, metadata propagation, API separation, and restricted-source behavior.

## Non-goals

- Frontend map controls or new AL scoring logic.
- Retaining downloaded ZIP archives in Git.
- General-purpose ETL configuration or a nationwide data warehouse.
- Commercial use of the W05 river dataset.

## Implementation steps

1. Add the geospatial reader dependency to the existing optional remote group.
2. Implement a concrete source manifest and archive normalizer for the requested releases and demo context windows.
3. Generate and inspect the normalized outputs and metadata.
4. Register the open source pack and exclude the restricted river source from runtime integration.
5. Separate bootstrap datasets from on-demand FL datasets in the data service and expose catalog/query access.
6. Update source registry and trilingual dataset documentation.
7. Run focused tests, full tests, lint, data validation, and a live rebuild check.

## Acceptance

- `uv run pytest -q`
- `uv run python -m terrai_spatial validate`
- Ruff passes for changed Python files.
- The open MLIT task is ready from committed normalized outputs and can be rebuilt from official URLs.
- W05 has no downloader, output, task, bootstrap entry or public API key; its evaluation remains in `docs/summary/`.
- Each new FL output carries source and retrieval timestamps and can be queried by a stable on-demand dataset key.
- All required data cards exist in English, Japanese, and Chinese with matching facts and commands.

## Completion evidence

- Live official-archive rebuild completed on 2026-07-21 with 50,859 clipped features across ten on-demand datasets.
- Every committed GeoJSON carries dataset-level and feature-level source/retrieval provenance; `metadata.json` additionally records archive SHA-256 and HTTP `Last-Modified` where supplied.
- After review, the initially implemented W05 local task was removed completely. Its source registry status is `confirmed_not_integrated`, and a trilingual evaluation remains under `docs/summary/`.
- Full suite: 66 tests passed.
- Repository validation: 34 JSON/GeoJSON files and 26 trilingual document groups passed.
- Ruff passed for every changed Python file.
