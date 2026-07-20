# Customer Exhibition Frontend–Backend Separation

[中文](FRONTEND_BACKEND_SPLIT.md) | [日本語](FRONTEND_BACKEND_SPLIT.ja.md) | [English](FRONTEND_BACKEND_SPLIT.en.md)

Status: Implemented for Demo

Date: 2026-07-20

## Goal

The customer UI should answer only questions about functionality, results, reliability, and traceability. The internal FL → SL → AL product concept remains in architecture documentation but does not occupy customer navigation or the landing view.

The browser no longer knows or reads paths under `data/`:

    frontend/ static presentation
      └─ HTTP JSON → FastAPI /api/v1
                         ├─ data/ JSON / GeoJSON
                         └─ scripts/ Python outputs

## Responsibility boundaries

### Frontend

- Load a stable exhibition contract from FastAPI.
- Render maps, legends, metrics, and recommendation queues.
- Handle Chinese/Japanese/English and click interactions.
- Present source, formula, uncertainty, and limitations.
- Contain no filesystem-path mapping and never read `data/*.json` directly.
- Perform no recommendation sorting or facility aggregation.

### FastAPI backend

- Load JSON/GeoJSON and cache by file modification time.
- Expose health and the file dataset catalog.
- Query fields, numeric ranges, bbox, sort order, and result limits.
- Use Python to create ranked slope, road, solar, facility, corridor, and delivery queues.
- Aggregate facility metrics required by the exhibition.
- Serve map tiles and remote-sensing images through a read-only asset path.

### Python data pipelines

Existing download, parse, joint-analysis, and multiscale-evidence scripts remain Python and continue to run through the shared task registry at startup or by explicit command. API requests read their outputs and do not trigger expensive rebuilds.

## Minimal API v1

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Dataset readiness and number of source groups |
| GET | `/api/v1/catalog` | File catalog, types, record counts, and update times |
| GET | `/api/v1/bootstrap` | Complete contract required by the exhibition frontend |
| GET | `/api/v1/datasets/{key}` | Retrieve one dataset by stable key |
| GET | `/api/v1/features/{key}` | Query by where/equals/min/max/bbox/sort/limit |
| GET | `/api/v1/recommendations/{analysis}` | Server-filtered and ranked action queue |
| GET | `/api/v1/assets/*` | Local tiles, images, and other read-only binaries |

FastAPI provides interactive OpenAPI documentation at `/docs`.

## Current storage decision

- Keep independent JSON/GeoJSON files; they are sufficient for the current data volume and read-only Demo.
- Stable dataset keys isolate the browser from file paths, so changing storage will not require a frontend rewrite.
- Do not introduce an ORM, migrations, or database schema yet.
- Reconsider SQLite when frequent incremental updates, concurrent writes, complex joins, customer permissions, or historical-version queries appear. Consider a service database for larger or multitenant workloads.

## Runtime

`terrai_spatial serve` starts two independent listeners in one development process:

- 4176: static frontend
- 8000: FastAPI

Use `terrai_spatial frontend` and `terrai_spatial api` to run them separately for later independent deployment.
