# Interactive AL Compute (FL materials + live analysis)

- Status: Planned

## Context

The exhibition demo precomputes every analytical metric offline and only for the
Yokohama study area: each building's `risk_score` (`data/yokohama/building_risk.geojson`),
road `priority_score`, corridor `compound_score`, and so on are baked by the
pipeline, and the read API only **filters and sorts** those frozen values. So
dragging the map never computes anything new — the risk colouring exists only
where it was pre-baked, and only for the demo region. That is correct for a
fixed demonstration; it is wrong for the real product.

The real product must let each module be **configured and corrected at runtime**:
tune the coefficients in a scoring formula, insert temporary data, hand-correct a
value, run a what-if. Results that depend on runtime user input are, by
definition, **not precomputable**. The current "precompute the product, then
filter" architecture cannot express interactivity.

This refactor changes what is computed where, along the project's FL → SL → AL
layers. It sits **after** `osm-basemap-tiles` and `local-3d-work-mode` (those are
the data and rendering foundation); this is the analysis layer on top.

## The division of labour (FL / AL / SL)

- **FL materials → backend, precomputed, served.** The invariant, expensive,
  shared denominators — DEM-derived `slope`, `relief`, `low_point`, `aspect`,
  `curvature`, distance-to-water, and the like — are computed once, offline,
  region-wide, and stored as FL (observed) materials keyed by `feature_id`, with
  provenance. They do not change when a user tweaks a formula, so they are never
  recomputed per request. The read API serves them; it does not compute them.
- **AL analysis → frontend, live.** An AL metric is a **recombination** of FL (and
  SL) materials: a weighted sum, a threshold, a ranking, a small closed-form
  model. With the materials already delivered, the browser recomputes the score
  instantly as the user changes coefficients — no backend round-trip. (The demo's
  `risk_score = 0.55·slope + 0.30·relief + 0.15·low_point` over already-baked
  `slope_component`/`relief_component`/`low_point_component` is exactly this shape;
  today the weights are frozen, tomorrow they are a slider.)
- **SL simulation → its own compute service, on demand.** Heavy, iterative,
  not-frontend-able modelling (flood, evacuation, prediction) runs in a separate
  backend compute service invoked in work mode. This is where the Python-vs-Rust
  question actually lives (see `rust-api-backend`); it is named here as the
  boundary but its build-out is out of this refactor's core scope.

Frontend/backend boundary rule: **closed-form / single-pass / data-in-hand →
frontend** (including small ONNX/WASM models); **iterative / large / needs raw
source → backend**.

## Two disciplines that must survive the move

- **Auditability.** When AL recombination runs on the client, the result must
  still carry its **formula and each input material's provenance**, so an
  interactive score traces to source + formula + limitation. Interactivity must
  not turn a displayed value into a black-box client number.
- **Observed / synthetic / unresolved.** A score built from FL materials is
  observed-derived; one that folds in an SL prediction is synthetic-derived. The
  distinction stays visually and semantically intact after client recombination —
  a simulated value never reads as measured.

## Coverage strategy: region-wide batch, never lazy fill-on-read

Materials are precomputed for the **whole target region** in a deterministic
offline batch — the same discipline as every other acquisition. This is a
deliberate rejection of a read-through cache that computes a missing chunk on
request and writes it back, because that pattern:

- turns the thin, read-only, cacheable, cold-start-safe API into a stateful
  read-write path with transactions and concurrency (two clients panning into the
  same fresh chunk race);
- gives the first visitor to any area a user-facing latency spike;
- creates two code paths producing "the same" data, breaking the byte-identity
  validation the store relies on;
- leaves a per-request "is this chunk ready?" branch on the **hot path** that, as
  coverage saturates, becomes permanent dead weight guarding a case that almost
  never fires.

Because the region is computed uniformly, that readiness check never exists.
Adding coverage for a new region is a one-time full precompute — an acceptable
one-off cost for per-feature scalars. Adding a **new material** is: extend the
pipeline, re-run the batch, atomically swap the store, re-validate. Expansion
beyond the core region, if ever needed, uses **explicit, idempotent, batch
localisation jobs** (the telemetry-driven pattern in `local-3d-work-mode`), never
a read-time write-back.

## Decision

Split analysis into precomputed FL materials, live frontend AL recombination, and
an on-demand SL compute service. Precompute the terrain-derivative material set
region-wide into the store as FL materials keyed by `feature_id`; recombine them
into AL metrics on the client with tunable coefficients while preserving formula
provenance and the observed/synthetic distinction; retire the frozen AL products
as the source of truth (keep a default-weight product only for first paint).
Route heavy SL simulation to a separate compute service.

Alternatives considered:

- *Keep precomputing AL products* — cannot express runtime configuration,
  correction, or what-if; the demo limitation made permanent.
- *Recompute AL on the backend per request* — needless round-trips for what is
  cheap client arithmetic over materials already delivered; hurts interactivity
  and reloads the API.
- *Lazy fill-on-read cache for materials* — rejected above (statefulness, races,
  latency spikes, dual code paths, hot-path dead code).
- *Bake materials into the basemap tiles* — wrong coupling; tiles are a
  rarely-rebuilt render artifact (see the `osm-basemap-tiles` render/analyse
  boundary).

## Non-goals

- No change to the basemap tiles — they carry render/identity only
  (`osm-basemap-tiles`); materials live in the store.
- No build-out of the SL compute service here — its boundary is named; the heavy
  compute and any language decision are `rust-api-backend` territory.
- No new SL models or AL formulas invented here — this is the placement and
  plumbing; specific modules bring their own formulas.
- No change to the FL → SL → AL data model or the observed/synthetic/unresolved
  commitment; this refactor presents them, it does not redefine them.

## Planned PRs

1. `01-fl-materials-precompute-pr1.md` — the region-wide FL material-primitives
   pipeline (terrain derivatives per feature, keyed by `feature_id`, with
   provenance), generalising today's Yokohama-only `building_risk` computation
   into a served FL materials layer.
2. `02-interactive-al-recombination-pr2.md` — the frontend AL framework: fetch
   materials, recombine into a metric with tunable coefficients, preserve formula
   + provenance and the observed/synthetic distinction, bake a default-weight
   product for first paint.
3. `03-retire-precomputed-al-products-pr3.md` — make materials the served source
   of truth and the frozen AL products derived/default-only, so analysis is live;
   the SL compute-service boundary is documented as the next step.
