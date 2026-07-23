# PR2 Plan: Interactive AL Recombination (frontend)

- Status: Planned
- Refactor: `interactive-al-compute`

## Goal

An AL metric is computed live in the browser as a recombination of the FL
materials, so a user can tune its coefficients and see the result update
instantly — with the formula and each input's provenance preserved, and the
observed/synthetic distinction intact.

## Scope

- A frontend AL framework where a metric is declared as a formula over named FL
  materials (e.g. `score = w_slope·slope + w_relief·relief + w_low·low_point`,
  weights user-adjustable). The client fetches the materials (PR1) for the current
  window and evaluates the formula per feature — closed-form, single-pass, on data
  already in hand, so it is instant with no backend round-trip.
- Coefficient controls per module (sliders/inputs) that re-evaluate on change;
  bands/thresholds also client-side.
- A default-weight product is baked/served for **first paint**, so the map shows a
  score immediately before any interaction; interaction then recomputes on the
  client.
- Auditability preserved: the popup/inspector shows the **formula, the current
  coefficients, and each material's source/vintage**, so an interactive score
  still traces to source + formula + limitation.
- Observed/synthetic preserved: a score from FL materials is marked
  observed-derived; if an SL prediction is later folded in, it is marked
  synthetic-derived and styled distinctly.

## Non-goals

- No SL simulation (separate compute service; named, not built here).
- No heavy/iterative computation on the client — only closed-form recombination
  of delivered materials (boundary rule in the overview).
- No change to the FL materials pipeline (PR1) or the basemap tiles.

## Implementation steps

1. Add the metric-definition layer (formula over named materials + adjustable
   coefficients) and the per-feature client evaluation over fetched materials.
2. Add the per-module coefficient controls and live re-evaluation.
3. Serve/bake a default-weight product for first paint; swap to client compute on
   interaction.
4. Extend the inspector to render formula + coefficients + material provenance;
   enforce the observed/synthetic marking. Add e2e for "adjust weight → colours
   update, provenance still shown".

## Acceptance

- Adjusting a coefficient re-colours the buildings instantly with no
  `/api/v1/features` request beyond the already-fetched materials.
- First paint shows the default-weight score before any interaction.
- The inspector shows the formula, current coefficients, and each material's
  source; observed-derived vs synthetic-derived is visually distinct.
- `cd webapp && npm run build && npm run test`, the Playwright suites, and
  `uv run python -m terrai_spatial validate` pass.
