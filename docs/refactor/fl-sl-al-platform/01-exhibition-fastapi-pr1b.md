# PR1b Plan: Customer Exhibition UI and FastAPI Separation

- Status: Completed
- Refactor: `fl-sl-al-platform`
- PR: #1 / part b

## Goal

Turn the internal concept board into a customer exhibition product that immediately communicates function, result, reliability, and traceability, while creating a minimal static-frontend/FastAPI boundary.

## Scope

1. Replace the landing page with opportunity, metrics, map, action queue, and plain-language interpretation.
2. Remove FL/SL/AL maturity, Claude comparison, and model shells from customer navigation.
3. Move static files to `frontend/` and read data only through `/api/v1`.
4. Move file cache, health, query, facility aggregation, and recommendation ranking to Python.
5. Keep independent JSON/GeoJSON as current FL storage.

## Key trade-off

`/bootstrap` minimizes Demo complexity and supports offline exhibition, but will not scale to large data. Later, load `/features` and `/recommendations` by module, viewport, and page. Introduce SQLite only when incremental updates, concurrent writes, complex joins, or historical queries require it.

## Acceptance

- Customer UI does not expose internal maturity.
- Frontend performs no business filtering, sorting, reduction, or scoring.
- Metrics, queues, and map fields are auditable.
- API, desktop/mobile, and all three customer UI languages pass tests.
