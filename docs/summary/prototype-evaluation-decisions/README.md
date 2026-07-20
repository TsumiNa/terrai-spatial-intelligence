# TerrAI Refactor Decision Record

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## FL → SL → AL conceptual architecture (2026-07-20)

TerrAI's shared foundation is divided into Foundation Data Layer (FL), Synthetic Data Layer (SL), and Application Layer (AL). Public/official observations and deterministic transformations that preserve meaning belong to FL. Future sparse imputations that pass held-out, calibration, and applicability gates belong to SL. Current slope, road-resilience, solar-siting, and joint scores belong to AL.

The first stage was a Factor of Concept and did not define schemas, databases, or orchestration. The later exhibition refactor added a minimal read-only API without changing the three-layer boundary. See [`FL_SL_AL_CONCEPT.md`](../../architecture/FL_SL_AL_CONCEPT.md); rationale is retained in [`fl-sl-al-platform/00-overview.md`](../../refactor/fl-sl-al-platform/00-overview.md).

## Customer exhibition UI and minimal FastAPI separation (2026-07-20)

- Remove FL/SL/AL maturity and internal experiments from customer navigation; lead with functions, result interpretation, reliability, and item-level audit.
- Move the static frontend to `frontend/` and load data only through `/api/v1`.
- Let FastAPI handle caching, health, catalog, GeoJSON query, aggregation, and recommendation ranking; keep rebuilds in Python scripts and the task registry.
- Keep independent JSON/GeoJSON files and use stable dataset keys as the isolation boundary for a future SQLite migration.
- See [`FRONTEND_BACKEND.md`](../../architecture/FRONTEND_BACKEND.md).

## What was retained from the three Claude Demos

| Claude Demo | Retained | Rejected or rewritten |
|---|---|---|
| A1 Hodogaya risk overview | Region overview → object drill-down; 100–300 m decision zones; source/method boundaries | Interpolating 91 elevation points into a 60 m surface and presenting sparse interpolation as DEM accuracy |
| A3 facility resilience | Real public facilities as commercial action objects; facility portfolio queue | Cross-region Bunkyo samples, hard-coded elevations, and calling another facility mean “TPI”; replaced with 2026 Yokohama official sites and same-area joins |
| B1 solar asset exposure | Investment/operations queue, portfolio view, discovery-to-due-diligence language | Obsolete WRI 324-station inventory, 20-station sample, three points per site, and `<5 m` lowland rule; METI/TEPCO direction retained instead |

## Google data choice

- **Satellite Embedding**: annual 64-D cross-sensor representation for change, similarity, and future few-label transfer. The PoC uses a public COG mirror and does not require Earth Engine.
- **Dynamic World**: open data, but commercial Earth Engine access incurs compute charges. Removed from the Demo and integration queue under the zero-paid-service constraint; evaluate ESA WorldCover or locally processed Sentinel-2 instead.

## Multiscale data contract

1. 5–10 m surface evidence: GSI DEM and Satellite Embedding; later Sentinel-2/ESA WorldCover.
2. Object assets: buildings, roads, official facilities, solar grids.
3. 100–300 m neighborhoods: service demand, road influence, facility gaps, evidence support.
4. Regional/portfolio gates: grid constraints, permission-data gaps, and project queues.

Every output should carry at least `evidence_status`, time, spatial support, score participation, and limitations.

## Relation to the `geo_pfn` sparse-context experiment

The current experiment fixes 48 query boreholes and samples 3–192 complete context holes from 192 candidates. With coordinate+depth features, geo-PFN reaches roughly 20 RMSE at 25–50 holes, around 3–6 lower than TabICL. It has no stable point-prediction advantage at extreme sparsity, while HGBT/TabICL remain strong dense baselines. Later training corrected the earlier claim that real features inherently hurt: 2M LCSG improved from about 22.9 to 17.7 with more training tables, and 17M reached about 19.0 LCSG at N=25. Remaining gaps concern feature uptake, sparse-target training, interval sharpness, and cross-site validation.

The platform therefore adopts four mechanisms only: complete coherent contexts, model selection by density and scenario, uncertainty on every inference, and abstention. The subsurface Su experiment is not presented as proof of surface or remote-sensing accuracy.

## Demo → PoC → MVP validation gates

| Stage | Allowed | Must not claim |
|---|---|---|
| Demo | Data fusion, evidence status, action queues, offline reproducibility | Disaster probability, energy yield, grid commitment, formal facility-upgrade benefit |
| PoC | Small customer label set; held-out, cross-area, and ablation comparisons against HGBT/spatial baselines; uncertainty calibration | Engineering applicability without independent validation |
| MVP | Permissions, versions, audit, monitoring, human review, and validated features in scoring | Replacing statutory review or engineering judgment with a black-box score |
