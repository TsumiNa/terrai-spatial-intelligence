# PR2 Plan: Store and Service Registration

- Status: Completed
- Refactor: `osm-highzoom-detail`
- PR: #66

## Completion record

- Store: **8,072,460 features / 7.0 GB / 3m26s** with `osmBuildings` ingested
  through the streaming path; `terrai validate` green against it.
- The handover measurements PR3 cites: a Shinjuku z16-scale window
  (0.01°×0.008°) holds **1,857 buildings / 1.1 MB raw**; the same area at
  z15 scale is 7,101 / 4.2 MB; Koenji dense residential 3,668 / 2.2 MB —
  z16 is the comfortable floor, matching the existing windowed discipline.
- The OSM product is an order denser than any MLIT layer: the shared fixture
  windows produced a 97 MB fixture, so it keeps its own two tight windows
  (the Playwright handover viewport and the identity Tokyo window) —
  **18,151 buildings / 11 MB committed**.
- The fixture builder was renamed to `build_ci_fixture.py` (task `ci_fixture`)
  now that it derives fixtures for both acquisitions; every literal reference
  moved in the same change.

## Goal

`osmBuildings` becomes a served foundation collection: ingested by the streaming
store build, delivered through the windowed endpoint, honest in health and catalog,
present in CI through fixture windows, and documented as a dataset card.

## Scope

- `data_service.py`: `osmBuildings` joins `FOUNDATION_DATASETS`
  (`data/osm/kanto_buildings/buildings.geojson`) with tier `FL, observed`; store
  inputs and staleness follow automatically.
- CI fixture: `build_mlit_fixture.py` grows to clip this product through the same
  suite windows (renamed accordingly if its name stops being true), keeping the
  committed fixture small; the fixture manifest records the derivation.
- Identity suite: the collection exceeds the size threshold, so it is covered by
  the envelope/count/window identity path; a windowed query joins the matrix.
- Docs: a dataset card under `docs/data/` (trilingual) for the Kanto building
  extract — ODbL, share-alike cautions, completeness honesty (OSM coverage varies
  by area; an absent building is not proof of absence), and the pinned extract
  date as the vintage.
- Measurements recorded: store build time and size deltas, densest-window feature
  count and payload at the intended handover zoom — the number PR3's threshold
  decision cites.

## Non-goals

- No UI change (PR3). No bootstrap participation — windowed delivery only.

## Acceptance

- `uv run pytest` green in fixture scope and against the full local product;
  `terrai validate` green; store rebuild wall-clock recorded.
- A z16 window over dense Tokyo returns its buildings through
  `GET /api/v1/features/osmBuildings` within the existing payload discipline.
