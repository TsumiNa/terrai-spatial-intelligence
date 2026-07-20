# TerrAI Frontend–Backend Architecture and Call Structure

[中文](FRONTEND_BACKEND.md) | [日本語](FRONTEND_BACKEND.ja.md) | [English](FRONTEND_BACKEND.en.md)

Status: current Demo implementation

Updated: 2026-07-21

This document describes the runtime call structure of the customer-facing TerrAI Demo: how the browser, static frontend, FastAPI service, Python data service, and file-backed data interact. See `docs/architecture/FL_SL_AL_CONCEPT.en.md` for the internal FL → SL → AL product concept.

## 1. Components and responsibilities

| Component | Current implementation | Responsibility |
|---|---|---|
| Customer browser | Chrome, Safari, etc. | Load the page and trigger module, view, language, and audit interactions |
| Static frontend | `frontend/index.html`, `app.js`, `audit.js`, `i18n.js` | Request the exhibition payload and render maps, metrics, queues, and the trilingual UI; never read local data files or calculate/sort business results |
| FastAPI | `terrai_spatial/api.py` | Provide the `/api/v1` HTTP boundary, validation, error mapping, CORS, OpenAPI, and read-only assets |
| Python DataService | `terrai_spatial/data_service.py` | Resolve stable keys to files, cache by mtime, query/filter, aggregate, and rank recommendation queues |
| Data tasks | `terrai_spatial/data_tasks.py` and `scripts/` | Check, download, parse, and rebuild data before startup; never run expensive jobs inside normal API requests |
| FL files | `data/**/*.json`, `data/**/*.geojson`, tiles, and remote-sensing images | Current read-only store; can later be replaced by SQLite without changing frontend calls |

Default local listeners:

- Frontend: `http://127.0.0.1:4176/`
- API: `http://127.0.0.1:8000/api/v1`
- OpenAPI: `http://127.0.0.1:8000/docs`

Override the API origin with the frontend `api` query parameter:

```text
http://127.0.0.1:4176/?api=http://127.0.0.1:9000
```

## 2. Startup call sequence

`terrai_spatial serve` coordinates the data check and two independent HTTP listeners. The task registry invokes the relevant Python script when data is missing or stale; the frontend and API start only after data is ready.

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    participant CLI as terrai_spatial CLI
    participant Tasks as Python Data Tasks
    participant Files as data/ FL Files
    participant Scripts as Download/Parse/Build Scripts
    participant API as FastAPI :8000
    participant Web as Static Frontend :4176

    Operator->>CLI: uv run python -m terrai_spatial serve
    CLI->>Tasks: ensure_data(allow_network)
    Tasks->>Files: Check presence, integrity, and freshness
    alt Complete and fresh
        Files-->>Tasks: ready
    else Missing or stale
        Tasks->>Scripts: Run the corresponding task
        Scripts->>Files: Atomically write/update output
        Files-->>Tasks: ready
    end
    Tasks-->>CLI: Data checks passed
    CLI->>API: Start Uvicorn / FastAPI
    API-->>CLI: started
    CLI->>Web: Start static file server
    CLI-->>Operator: Print frontend and /docs URLs
```

If a data task fails, `serve` stops before starting HTTP services and reports the missing input or recovery action. Use `--no-ensure-data` to skip the check or `--offline` to forbid network access.

## 3. Actual customer-frontend request sequence

The current Demo follows a “load once, switch views locally” strategy. The first page load requests one aggregated exhibition contract. Module, language, and audit interactions reuse that payload. Map tiles and remote-sensing images are fetched on demand for the current viewport.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant Browser
    participant Frontend as frontend/app.js
    participant API as FastAPI /api/v1
    participant Service as Python DataService
    participant FL as JSON / GeoJSON
    participant Assets as Local Tiles/Remote-sensing Images

    Customer->>Browser: Open :4176
    Browser->>Frontend: Load HTML/CSS/JS
    Frontend->>API: GET /bootstrap
    API->>Service: bootstrap()
    loop 18 stable dataset keys
        Service->>FL: stat mtime
        alt Cache missing or file changed
            Service->>FL: read + json.load
            FL-->>Service: JSON / GeoJSON
        else mtime cache hit
            Service->>Service: Return an in-memory copy
        end
    end
    Service->>Service: Aggregate facilities, select regions, rank queues
    Service-->>API: Exhibition payload + health/source metadata
    API-->>Frontend: 200 application/json
    Frontend->>Frontend: Render module, metrics, map, and action queue

    par Map resources for the viewport
        Browser->>API: GET /assets/tiles/...
        API->>Assets: Read tile
        Assets-->>API: PNG/JPEG
        API-->>Browser: Image resource
    and Remote-sensing evidence overlay
        Browser->>API: GET /assets/google/...image...
        API->>Assets: Read image
        Assets-->>API: PNG
        API-->>Browser: Image resource
    end

    Customer->>Frontend: Switch module/view/language
    Frontend->>Frontend: Re-render prepared bootstrap data
    Note over Frontend,API: No additional API request today

    Customer->>Frontend: Click a dashed value
    Frontend->>Frontend: audit.js opens source/formula/limits
    Note over Frontend,API: Audit metadata is already loaded
```

## 4. Fine-grained API query sequence

Besides `/bootstrap` and `/assets/*`, FastAPI exposes smaller endpoints for OpenAPI inspection, future on-demand frontend loading, and external clients.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Frontend/External Client
    participant API as FastAPI
    participant Service as DataService
    participant FL as JSON / GeoJSON

    Client->>API: GET /features/solar?where=status&equals=preferred&sort=score&limit=20
    API->>API: Validate key, ranges, bbox, and limit
    alt Unknown key or unavailable file
        API-->>Client: 404
    else Invalid parameters or incompatible data type
        API-->>Client: 422
    else Valid request
        API->>Service: query_features(...)
        Service->>FL: Load by stable key or hit mtime cache
        FL-->>Service: FeatureCollection
        Service->>Service: Field filter → bbox intersection → sort → limit
        Service-->>API: Result + matched/returned
        API-->>Client: 200 GeoJSON
    end
```

## 5. Endpoints and callers

| Endpoint | Called by the current customer UI? | Purpose |
|---|---:|---|
| `GET /api/v1/bootstrap` | Yes, once at startup | All exhibition data, server-ranked queues, facility aggregates, and health metadata |
| `GET /api/v1/assets/*` | Yes, by viewport | Local map tiles, Satellite Embedding visualizations, and other binary evidence |
| `GET /api/v1/health` | No; embedded in bootstrap metadata | Independently monitor the service and 18 datasets |
| `GET /api/v1/catalog` | No | Inspect stable keys, file types, record counts, and update times |
| `GET /api/v1/datasets/{key}` | No | Retrieve a complete JSON/GeoJSON dataset by key |
| `GET /api/v1/features/{key}` | No | Query GeoJSON by field, range, bbox, sort, and limit |
| `GET /api/v1/recommendations/{analysis}` | No; results are embedded in bootstrap | Retrieve one server-filtered and ranked action queue |

## 6. Boundaries and evolution

- The API is read-only; the browser cannot modify FL files or trigger rebuilds.
- Normal requests do not invoke download scripts, preventing a page view from starting a long job or external dependency.
- `/bootstrap` suits the small local Demo. At larger scale, load `/features/{key}` and `/recommendations/{analysis}` by module, viewport, and page.
- A SQLite migration should replace the repository/load/query internals of `DataService` while preserving `/api/v1` paths and response semantics.
- Customer data requires authentication, tenant isolation, authorization audit, and version selection in front of the API; these are outside the current PoC.

## 7. Code map

- Frontend API origin and startup request: `frontend/app.js`
- HTTP routes and error mapping: `terrai_spatial/api.py`
- File cache, queries, aggregates, and queues: `terrai_spatial/data_service.py`
- Dual-service startup and automatic data checks: `terrai_spatial/cli.py`
- Task registry and dependencies: `terrai_spatial/data_tasks.py`
- Refactor rationale and implementation plan: `docs/refactor/fl-sl-al-platform/01-exhibition-fastapi-pr1b.md`
