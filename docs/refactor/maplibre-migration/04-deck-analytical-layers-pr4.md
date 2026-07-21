# PR4 Plan: deck.gl Analytical Layers

- Status: Completed
- Refactor: `maplibre-migration`
- PR: #15

## Goal

Render every analytical layer the current exhibition has, through deck.gl, wired to the audit drawer. This is the stage that reaches parity.

## Scope

1. Layers for each module: slope exposure buildings, road priority, official facilities, solar site cells, resilience hubs, compound corridors, solar delivery cells, and embedding evidence.
2. Picking wired to the audit drawer, so clicking a feature opens the record it opens today.
3. Queue-to-map interaction: selecting a queue item highlights and frames its feature.
4. Colour and threshold definitions expressed as data, not embedded in code, so analytical thresholds can change without a code edit.

## Non-goals

No underground layers. No terrain. No new analyses; this stage reproduces existing behaviour.

## Implementation notes

- Build extrusions from the `elevation_m` already present in the data rather than sampling terrain. The evaluation showed absolute heights avoid the expensive clamp path entirely.
- Batch aggressively. One layer per feature class, not one object per feature.
- `HexagonLayer` aggregation is available and has no equivalent in the previous stack. It is not required for parity; if it is added, add it as a distinct view rather than changing an existing one.

## Acceptance

- Every module renders the same features as the current exhibition, with the same colours and rankings.
- Clicking any feature opens the same audit record as today, with source, formula and limitation intact.
- Selecting a queue item frames the corresponding feature.
- Playwright covers one feature click per module.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
