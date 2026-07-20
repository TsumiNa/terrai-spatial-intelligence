# FL → SL → AL Factor of Concept Refactor Record

- Status: Completed — merged as PR #1
- Date: 2026-07-20
- Branch: `refactor/fl-sl-al-concept`
- Baseline: `main` / `4ceb7ba`
- Type: conceptual refactor first; minimal frontend/backend separation added in the same PR's customer-exhibition stage

## 1. Why

The Prototype shared a map, data, and audit foundation but was narrated as three application Demos. It did not explain multiscale missingness as a cross-application capability and could mix observations, deterministic processing, proxies, heuristics, and future imputations.

The refactor defines TerrAI as accumulative data infrastructure plus application outputs:

1. **FL** accumulates public, commercial, and customer-authorized evidence while preserving multiscale missingness.
2. **SL** uses locally validated scenario model portfolios to non-destructively augment predictable missingness with uncertainty and abstention.
3. **AL** turns qualified FL/SL evidence into slope, road, solar, and other business outputs.

This preserves commercial readability and gives sparse-context prediction such as `geo_pfn` the correct architectural position.

## 2. Evidence reviewed

- `TerrAI_Narrative_Product_Strategy_Update_v4.docx` §4 and §6–7: sparse subsurface prediction is an entry proof; reusable engine/delivery and controlled applications are the long-term assets.
- `TsumiNa/geo_pfn` commit `07c7ee0`, `stage-report.html`, and `sparse-context-results.html`: model ranking changes with density, features, and training volume; interval coverage and row-level error ranking are distinct.
- Current Prototype lineage: six external source groups form FL; current scores are transparent AL rules; no Yokohama/Mobara surface SL has passed held-out, calibration, and cross-area validation.

Later `geo_pfn` training corrected the early overstatement that real features hurt; under-training was the main cause. The architecture therefore binds to model selection by scenario and sparsity, strong baselines, uncertainty, and abstention—not one fixed model or feature set.

## 2.1 Decision, alternatives, and consequences

Adopt FL → SL → AL instead of keeping an ambiguous “unified data foundation” or allowing every application to maintain its own imputation model. The unified label is simple but continues to mix facts, proxies, and predictions. Per-application models may ship quickly but trap customer learning, calibration, and audit inside one project instead of creating shared assets.

The accepted structure keeps observed and synthetic evidence distinguishable, gives model portfolios/applicability/abstention explicit positions, and lets new applications reuse validated SL. The cost is accepting that some areas remain unknown and later implementing versioning, permissions, model selection, and lineage. Ownership, statutory permission, formal grid access, and structural safety must never be model-imputed.

## 3. Implementation steps and commit intent

### Commit 1: `docs: define FL SL AL conceptual architecture`

- Canonical three-layer definition, multiscale missingness, and observed/synthetic/unresolved boundaries.
- Decision rationale, alternatives, consequences, and non-goals.
- Corrected `geo_pfn` interpretation.

### Commit 2: `feat: add FL SL AL architecture lens`

- Added the first internal architecture view and trilingual explanation.
- Showed FL live, surface SL zero, and AL live.
- Connected maturity and calibration evidence to the audit drawer without changing application results.

### Commit 3: `docs: map prototype maturity and validate concept`

- Connected README, concept, decision rationale, and refactor record.
- Added concept contracts preventing AL heuristics from being relabeled as SL.
- Recorded review and Factor of Develop boundaries.

### Commit 4: `feat: rebuild exhibition demo with FastAPI backend`

- Customer navigation now exposes business entry points, results, reliability, and audit instead of internal maturity.
- Static files moved to `frontend/`; one `/api/v1/bootstrap` contract loads exhibition data.
- Python data service handles caching, query, aggregation, regional filtering, and action-queue ranking.
- Independent JSON/GeoJSON remains current FL storage; no ORM, schema, write API, or database.
- Added API and customer-boundary tests.

### Commit 5: `docs: record customer exhibition service boundary`

- Updated startup, independent services, API, and customer entry documentation.
- Recorded frontend/FastAPI/pipeline boundaries and SQLite triggers.
- Corrected the review path for customer and internal audiences.

Exact hashes and diffs remain in Git and the PR Commits page; this record preserves product intent.

## 4. Current asset mapping

| Asset | Layer | Reason |
|---|---|---|
| GSI, OSM, Yokohama open data, NASA POWER, TEPCO CSV | FL | Published/observed evidence and local snapshots |
| Google Satellite Embedding | FL | Google-produced external representation, not TerrAI imputation |
| DEM slope, coordinate conversion, spatial aggregation | FL | Deterministic transformations preserving observational meaning |
| Risk/suitability/joint scores and capacity proxies | AL | Transparent business rules and proxies |
| `geo_pfn` Haneda experiment | SL mechanism evidence | Candidate mechanism in a sparse regime, not surface accuracy |
| Yokohama/Mobara surface sparse imputation | Absent | No local targets, held-out, calibration, or cross-area validation |

## 5. PR review order

1. Start the Demo and confirm the landing page immediately explains Yokohama resilience and Mobara renewable development.
2. Review portfolio and specialist analyses: map, action queue, and one-line interpretation.
3. Click dashed metrics, queue scores, and popup fields to inspect source, formula, uncertainty, and limitations.
4. Switch Chinese, Japanese, and English; verify a narrow viewport.
5. Open FastAPI `/docs` and inspect health, catalog, data, GeoJSON query, and recommendation routes.
6. Read `docs/architecture/FL_SL_AL_CONCEPT.md` and confirm the runtime never labels AL rules as SL.
7. Run automated validation for concept, API, data tasks, and assets.

## 6. Reserved for Factor of Develop

- FL/SL/AL objects, fields, tables, and file schemas;
- inter-layer APIs, orchestration, model registry, versioning, and rollback;
- customer imports, permissions, tenant isolation, and cross-customer learning;
- the first surface target, labels, missingness mechanism, and model portfolio;
- SL held-out, calibration, time/area validation, and AL admission thresholds;
- databases, feature stores, object stores, online inference, and deployment topology.

These choices must be constrained by the first customer PoC's target, risk tolerance, and data authorization.

## 7. Acceptance commands

```bash
node --check frontend/app.js
node --check frontend/audit.js
node --check frontend/i18n.js
uv run pytest
uvx ruff check .
uv run python -m terrai_spatial validate
git diff --check
```

## 8. Customer exhibition and FastAPI follow-up

The first concept UI was useful internally but unsuitable for an exhibition. The same PR therefore:

1. kept FL/SL/AL in internal documents, not customer navigation;
2. changed the landing page to opportunity, four metrics, map, queue, and plain-language result;
3. removed internal experiment, Claude comparison, and model-shell explanation from runtime;
4. moved static files to `frontend/` and loaded data only through FastAPI;
5. added Python JSON/GeoJSON cache, query, aggregation, and ranking;
6. kept file storage behind stable dataset keys for later SQLite migration.

See `docs/architecture/FRONTEND_BACKEND.md`.
