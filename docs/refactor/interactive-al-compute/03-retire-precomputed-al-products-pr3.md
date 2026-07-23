# PR3 Plan: Retire Precomputed AL Products as the Source of Truth

- Status: Planned
- Refactor: `interactive-al-compute`

## Goal

Analysis is live: the FL materials are the served source of truth, and the frozen
AL products (`risk_score`, `compound_score`, …) are derived on the client or kept
only as a default-weight convenience — so no analytical metric is a baked,
region-locked value the user cannot influence.

## Scope

- Move the AL metrics that are pure recombinations (building slope-risk, road
  priority, and any other weighted-sum/threshold product) off their precomputed
  fields and onto the PR2 client recombination over PR1 materials.
- Keep a **default-weight** version served for first paint and for API consumers
  that want a canonical number, but mark it explicitly as the default composition,
  not the only one.
- Drop, or downgrade to default-only, the frozen product fields whose sole purpose
  was to be the source of truth; the materials + formula now are. Update the data
  cards/registry so a reader sees the metric's home is "materials + formula", not
  a frozen column.
- Document the **SL compute-service boundary** as the explicit next step: metrics
  that need iterative/simulation compute (not closed-form recombination) are
  routed to a separate on-demand service (`rust-api-backend` territory), not baked
  and not run on the client.

## Non-goals

- No removal of the FL materials (PR1) — they are now the truth.
- No build-out of the SL compute service — only its boundary is documented.
- No change to the basemap tiles.

## Implementation steps

1. Repoint each recombination-style AL metric to client compute (PR2) over
   materials (PR1); keep a default-weight product for first paint/API.
2. Remove or default-only the frozen source-of-truth fields; update data
   cards/registry and provenance to "materials + formula".
3. Write the SL compute-service boundary note (what routes there, why not baked,
   why not client).
4. Full e2e: interactive metrics across the region (not just Yokohama), provenance
   and observed/synthetic intact, no region-locked frozen colouring.

## Acceptance

- Analytical colouring responds to coefficient changes across the whole covered
  region, not only the former demo area, with provenance preserved.
- No AL metric remains a frozen, user-uninfluenceable region-locked value except
  the explicitly-labelled default-weight first-paint product.
- The SL compute-service boundary is documented and cross-referenced to
  `rust-api-backend`.
- `cd webapp && npm run build && npm run test`, the Playwright suites, the store
  build, and `uv run python -m terrai_spatial validate` pass.
