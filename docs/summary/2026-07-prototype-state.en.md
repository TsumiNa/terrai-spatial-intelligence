# TerrAI Spatial Intelligence Platform — Integrated PoC

[中文](2026-07-prototype-state.md) | [日本語](2026-07-prototype-state.ja.md) | [English](2026-07-prototype-state.en.md)

A customer-facing spatial-decision Demo that answers “where should we act first, why, and can the evidence be trusted?” with maps and priority queues. It currently covers Yokohama urban resilience and Mobara solar development. Every metric, queue result, and map field traces to a source, formula, and limitation.

The project separates a static frontend from a FastAPI backend. The frontend loads and presents data; Python reads file data, checks health, queries fields/space, aggregates, and ranks recommendations. Foundation data remains independent JSON/GeoJSON for now; database/SQLite design is deferred.

## Run

Install `uv`, then run:

```bash
uv run python -m terrai_spatial serve --port 4176
```

Open `http://localhost:4176/`. One command starts:

- Customer frontend: `http://127.0.0.1:4176/`
- FastAPI and interactive docs: `http://127.0.0.1:8000/docs`

Runtime needs no database or external API key. Basemaps, results, and 2023–2024 Satellite Embedding crops are cached locally.

Before starting both listeners, `serve` checks all data tasks. Missing packaged foundation data is restored from local Git first; missing public remote-sensing/map caches invoke their download scripts; missing or stale derivatives rebuild automatically. If the Git-ignored TEPCO raw cache is absent, the official ZIP is downloaded and parsed, so a standard GitHub clone obtains the original CSVs on its first online startup. Every executed task is printed. Use `--offline` to forbid network access or `--no-ensure-data` after confirming completeness.

Run services separately when needed:

```bash
# Backend API and /docs
uv run python -m terrai_spatial api --port 8000

# Frontend; defaults to http://127.0.0.1:8000/api/v1
uv run python -m terrai_spatial frontend --port 4176
```

Common engineering commands:

```bash
uv run python -m terrai_spatial validate
uv run python -m terrai_spatial data status
uv run python -m terrai_spatial data ensure
uv run python -m terrai_spatial data update
uv run python -m terrai_spatial data update --only tiles
uv run python -m terrai_spatial data update --only embedding
uv run python -m terrai_spatial data update --only grid
uv run python -m terrai_spatial build
uv run python -m terrai_spatial build --only joint
```

`uv.lock` pins FastAPI, Uvicorn, and the Python environment. The `remote` optional dependencies are installed only when Satellite Embedding is fetched again.

## FastAPI

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | Service and 18 file-backed dataset readiness |
| `GET /api/v1/catalog` | File catalog, type, record count, and update time |
| `GET /api/v1/bootstrap` | Complete first-load exhibition contract |
| `GET /api/v1/datasets/{key}` | Read one JSON/GeoJSON by stable key |
| `GET /api/v1/features/{key}` | Query GeoJSON by field, range, bbox, sort, and limit |
| `GET /api/v1/recommendations/{analysis}` | Python-ranked action queue |
| `/api/v1/assets/*` | Local tiles and remote-sensing images |

The frontend never reads `data/` directly. File locations, caching, filtering, aggregation, and ranking stay in Python. See [the call sequence diagrams](../architecture/FRONTEND_BACKEND.en.md).

Data tasks are also directly executable:

```bash
uv run python scripts/ensure_data.py status
uv run python scripts/ensure_data.py ensure
uv run python scripts/ensure_data.py update --only joint
uv run python scripts/build_joint_analysis.py
uv run python scripts/build_multiscale_evidence.py
uv run python scripts/fetch_visual_tiles.py
uv run --extra remote python scripts/fetch_google_satellite_embedding.py
uv run python scripts/fetch_tepco_grid.py
uv run python scripts/update_tepco_grid.py
uv run python scripts/parse_tepco_grid.py
```

### Automatic-repair boundaries

- `bootstrap`: atomically restore missing/corrupt base GeoJSON/CSV/JSON via `git show HEAD:<path>`; source archives fall back to GitHub and private repositories require `GITHUB_TOKEN`.
- `tiles`, `embedding`: startup downloads only when cache is missing; `data update` forces refresh.
- `joint`, `evidence`: rebuild when output is missing/corrupt or older than scripts/inputs.
- `grid`: first online startup downloads the official TEPCO ZIP, validates and extracts only two expected CSVs, and rebuilds the summary. Raw ZIP/CSV and hash/time metadata are Git-ignored. `data update --only grid`, `fetch tepco`, and `build --only grid` refresh deliberately.
- `--offline`: forbids network. A committed screening summary can run without raw CSV; an existing ZIP/CSV cache can rebuild. Otherwise startup stops explicitly.
- Failed repair never starts with a partial dataset; it reports the task, missing input, and recovery action.

## Auditable values and trilingual UI

- Dashed values in metric cards, descriptions, action queues, scores, and popups open one audit drawer.
- **Observed data** shows publisher, source field, snapshot, local evidence file, and limitations.
- **Model output** shows model/version, inputs/outputs, uncertainty, and local validation status. Google AEF has no pixel-level confidence interval here and is explicitly “uncalibrated.”
- **Calculated data** shows formula, substituted object values, result, and lineage. Risk, suitability, and joint scores are heuristics, not probabilities.
- The “中 / 日 / EN” switch updates immediately; language persists locally and in `?lang=zh|ja|en`.

## Internal product architecture (not customer navigation)

| Layer | Responsibility | Current state |
|---|---|---|
| **FL · Foundation Data Layer** | Authorized real evidence and deterministic transformations, preserving missingness, time, resolution, and license | Six public/official source groups and local derivatives integrated |
| **SL · Synthetic Data Layer** | Non-destructive scenario-model augmentation of predictable missingness with uncertainty, model identity, lineage, and abstention | Concept defined; **zero** surface imputations in Yokohama/Mobara |
| **AL · Application Layer** | Scenario rules, ranking, review, and action over qualified FL/SL | Slope, road, facility, and solar Demos integrated |

Google Satellite Embedding is external FL, not TerrAI SL. Capacity proxies and risk/suitability scores are transparent AL calculations. Ownership, permission, formal grid access, and structural safety remain unknown until authoritative data or due diligence.

- [Concept architecture](../architecture/FL_SL_AL_CONCEPT.en.md)
- [Refactor background and rationale](../refactor/fl-sl-al-platform/00-overview.md)
- [This PR's staged plan](../refactor/fl-sl-al-platform/01-concept-layers-pr1a.md)
- [Frontend–backend call sequences](../architecture/FRONTEND_BACKEND.en.md)

FastAPI v1 establishes only the minimal read/query/rank boundary. Formal schemas, model registry, orchestration, database, tenancy, and deployment remain later development.

### Current cost conclusion

- **Paid runtime data/analysis services: zero.** All modules can be shown offline.
- **Core regeneration needs no database purchase or Earth Engine.** Satellite Embedding reads a public COG mirror; other sources use public downloads/APIs and local compute.
- Free access is not unrestricted commercial reuse: GSI has attribution/processing/Survey Act/third-party limits; OSM has ODbL; TEPCO CSV is free to read but not open-licensed and requires rights review before republication.
- Per-dataset notes for integrated data are in [`docs/data`](../data/README.en.md); candidate evaluations are in [`open-data-landscape.en.md`](open-data-landscape.en.md).

### Six external source groups used by the Demo

| Source | Use | Access/runtime cost | Commercial constraints |
|---|---|---|---|
| GSI DEM5A and map/imagery/relief/slope tiles | Terrain and visual review | Free; locally cached | GSI attribution and processing notice; possible Survey Act and third-party limits |
| Google Satellite Embedding V1 mirror | 2023→2024 change, similarity, future few-label transfer | Free public COG; no Google account | CC BY 4.0 specified attribution; 64-D axes are not land classes |
| OpenStreetMap | Buildings, roads, water, land use, transmission | Free; local GeoJSON | ODbL attribution/share-alike; no completeness guarantee |
| Yokohama Open Data | Official regional disaster bases | Free CSV | Default CC BY 4.0; attribution/change notice/third-party rights |
| NASA POWER | Mobara solar climate | Free API; cached | Credit/no implied endorsement; not site-level yield |
| TEPCO public system information | Regional grid-capacity screen | Free ZIP/CSV; automatic local download | **Not open-licensed**, redistribution prohibited, not a connection commitment |

## Eight customer entry points

1. **Decision overview**: switch between Yokohama resilience and Mobara renewable development.
2. **Urban resilience projects**: community solar-storage nodes and compound inspection corridors.
3. **Solar development readiness**: deliverable candidates, rule conflicts, and public TEPCO capacity signal.
4. **Building slope risk**: terrain-exposure screen for 2,128 Hodogaya buildings.
5. **Road continuity**: inspection/community-impact priority for 272 road segments.
6. **Public facility upgrades**: opportunity queue for two official Yokohama disaster bases.
7. **Solar candidates**: suitability screen for 70 Mobara cells.
8. **Evidence and reliability**: 10 m annual embedding change, similarity, and item-level audit.

## Google remote-sensing choice

### Satellite Embedding V1: integrated

- Public Source Cooperative COG mirror, CC BY 4.0; produced by Google and Google DeepMind.
- 7,820 valid 10 m pixels in Yokohama and 19,877 in Mobara.
- 2023 and 2024 annual embeddings.
- 64-D cosine change, similarity, and future few-label transfer; no land-class interpretation or current score input.

```bash
uv run --extra remote python -m terrai_spatial fetch embedding
```

### Dynamic World: removed

Although CC BY 4.0, its official access path depends on Earth Engine and commercial use incurs usage charges. Under the no-added-database/service-purchase constraint, UI, metadata, registry, and adapters were removed. Evaluate direct-download ESA WorldCover for interpretable land cover or locally processed Sentinel-2 L2A for current spectral evidence.

## FL multiscale foundation and SL plan

| Scale | Data | Demo role |
|---|---|---|
| 5–10 m raster | GSI DEM, Satellite Embedding | Terrain, change, similarity evidence |
| Object | Buildings, roads, official facilities, solar grid | Actionable assets |
| 100–300 m neighborhood | Service area, road influence, evidence zones | Demand, accessibility, facility gaps |
| Region/portfolio | Grid gate, project queue, evidence coverage | Investment ranking and stop conditions |

The `geo_pfn` Haneda experiment supplies mechanism evidence for SL in the medium-sparse 25–50 complete-context-hole regime, but dense-best and extreme-sparse-best models differ, and point prediction, uncertainty, and sample-error ranking require separate validation. SL therefore uses model portfolios, density-dependent selection, calibration, and abstention—not one model filling every map. It is not claimed as Yokohama/Mobara surface accuracy.

## Four visual evidence layers

- **Standard**: GSI standard map.
- **Imagery**: latest seamless orthophotography, mainly aerial at high zoom with some satellite coverage.
- **Relief**: hillshade derived from DEM5A/5B/10B.
- **Slope**: slope map from the same elevation evidence.

All pilot tiles are cached locally. Refresh with:

```bash
uv run python -m terrai_spatial fetch tiles
```

## How 1 + 1 + 1 > 3

- **Community solar-storage resilience hubs**: low-slope, high roof-capacity proxy, close to important roads, serving nearby high-risk buildings.
- **Official facility upgrade projects**: apply the same logic first to real Yokohama disaster bases, keeping official identity separate from model-discovered supplemental nodes.
- **Compound intervention corridors**: combine high-priority roads, exposed-building density, and mean building risk for packageable drainage, slope, and inspection projects.
- **Deliverable solar cells (Mobara)**: strengthen road logistics, earthwork slope, and transmission-distance factors to narrow “suitable” into “inspect first.” This remains a separate Mobara product, not a spatial join with Yokohama.

Rebuild joint evidence:

```bash
uv run python -m terrai_spatial build --only joint
uv run python -m terrai_spatial build --only evidence
```

Outputs: `resilience_hubs.geojson`, `compound_corridors.geojson`, `solar_delivery_cells.geojson`, and `joint_summary.json` under `data/joint/`.

## Public grid-capacity screen

TEPCO Chiba “Expected Power Flows, etc.” is integrated. Git stores only the standardized screen, not redistribution-prohibited ZIP/CSV or local hash metadata. Snapshot date comes from HTTP `Last-Modified`; retrieval time and SHA-256 remain in local audit metadata.

- Chiba table: 175 transmission-line and 201 transformer records.
- Mobara match: four related lines and one Mobara distribution substation.
- Mobara substation: 5 MW local spare-capacity proxy, 0 MW after upstream constraints, with possible normal-operation output control.

```bash
uv run python -m terrai_spatial fetch tepco
uv run python -m terrai_spatial data update --only grid
uv run python scripts/update_tepco_grid.py --force
uv run python scripts/update_tepco_grid.py --offline
uv run python -m terrai_spatial build --only grid
```

Output: `data/mobara/tepco_grid_screen.json`. Download automation does not change TEPCO rights. Values rank regional discovery/pre-consultation only, not formal connection studies, and CSV geometry cannot allocate capacity to each cell. See [`tepco-grid.en.md`](../data/tepco-grid.en.md).

## Important boundaries

All scores are transparent relative heuristics. They are not:

- building structural safety or confirmed hazard;
- actual usable roof area, generation, or storage design;
- road-failure probability or emergency-passability guarantee;
- ownership, environmental permission, geohazard compliance, grid capacity, or connection commitment.

Before a pilot, prioritize:

- Yokohama: public building attributes, real roof data, official hazard depths/zones, and distribution constraints.
- Mobara: registry parcels, MAFF 2026 field polygons, prices/planning/protected areas, and project-level grid consultation.

Confirmed no-purchase candidates include ESA WorldCover, Sentinel-2 L2A, GSI Hazard Map open layers, MAFF field polygons, registry maps, MLIT real estate API, National Land/Environmental GIS, and METI FIT/FIP. Dynamic World remains only in the “excluded after evaluation” record. See [`open-data-landscape.en.md`](open-data-landscape.en.md).

## Original Demos

- `../terrai_slope_screen_poc`
- `../terrai_resilience_road_poc`
- `../terrai_solar_site_screen_poc`

They remain for method/data-generation traceability.

## Project structure

```text
terrai-spatial-intelligence/
├── pyproject.toml              # uv project and optional remote dependencies
├── uv.lock                     # reproducible environment lock
├── terrai_spatial/             # FastAPI backend and unified CLI
│   ├── api.py                  # health/catalog/data/query/recommendations
│   ├── data_service.py         # file cache, query, aggregation, ranking
│   └── data_tasks.py           # shared startup/manual task registry
├── frontend/                   # independent static customer frontend
│   ├── index.html              # exhibition information architecture
│   ├── app.js                  # API loading, map, interactions
│   ├── audit.js                # observed/model/calculation audit
│   ├── i18n.js                 # Chinese/Japanese/English UI dictionary
│   └── styles.css              # map, queue, drawer, responsive UI
├── scripts/                   # directly executable acquisition/rebuild pipelines
├── docs/                      # architecture/data/summary are trilingual; refactor is English
│   ├── architecture/          # current concepts and frontend/backend call sequences
│   ├── data/                  # integrated FL dataset cards and license cautions
│   ├── refactor/              # English refactor overviews and PR-stage plans
│   ├── summary/               # evaluations, validation, and project decisions
│   └── others/                # uncategorized documentation of last resort
└── data/                      # FL snapshots and results; no database yet
```
