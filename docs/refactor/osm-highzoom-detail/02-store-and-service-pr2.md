# PR2 Plan: Store and Service Registration

- Status: Planned
- Refactor: `osm-highzoom-detail`

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
