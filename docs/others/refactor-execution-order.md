# Refactor Execution Order (temporary working note)

> **Temporary / disposable.** A cross-refactor sequencing aid, written to plan the
> order of the currently-Planned refactors before deployment begins. It belongs in
> `others/` because it spans **all** refactors at once — it is not a single
> refactor's plan (those live in each `docs/refactor/<name>/`), nor current
> architecture, a dataset card, or an evaluation summary. Delete it once the
> sequence is underway and the per-refactor plans carry the live status.

Source of truth for each refactor's own PR steps and status stays in its folder
and in `docs/refactor/history.md`. This note only fixes the **order across**
refactors and the **dependencies between** them.

## The five Planned refactors

`osm-basemap-tiles`, `local-3d-work-mode`, `interactive-al-compute`,
`basemap-resilience`, `rust-api-backend`. (`data-pipeline-and-store` PR4/PR5 stay
Blocked on measured triggers and are out of this sequence.)

## Dependencies that force the order

- `local-3d-work-mode` reuses the **PLATEAU acquisition** that `osm-basemap-tiles`
  PR4 pins, and its unmodelled-area fallback **extrudes the merged tiles** — so it
  needs `osm-basemap-tiles` at least through PR4.
- `interactive-al-compute` joins its FL materials by **`feature_id`**, the key the
  merged tiles carry, and its overview places it **after** tiles and local-3d — so
  it comes last of the build-out work.
- `basemap-resilience` is **independent** of all of the above (it hardens the live
  GSI style JSON + non-building vector tiles). `osm-basemap-tiles` PR5 only shrinks
  one of its exposures (the GSI building layers); its core is orthogonal.
- `rust-api-backend` is **entry-condition gated** (measured throughput need +
  settled business scope + separated/embedded decision) and is the home of the SL
  compute service that `interactive-al-compute` names — so it is conditional and
  last.

## The order

### Phase 0 — Pre-flight (early, independent, before frontend integration)

Two low-risk items that are **not** multi-PR refactors but should land early,
before any frontend-heavy work in Phase 1+ builds on the map layer.

**MapLibre v6 upgrade** — maintenance, not a refactor (recorded in the
`maplibre-v6-upgrade-decision` memory, so it has no `docs/refactor/` folder). Do
it **before `osm-basemap-tiles` PR3** (basemap integration), so all downstream
frontend work targets v6 rather than being written on 5.24 and migrated later.

- **Gate first: verify WebGL2 on the exhibition/kiosk hardware** — the only real
  risk (v6 drops WebGL1). ~95% global; any modern iPad (iPadOS 15+) is fine, but
  confirm the actual display devices.
- Code change is small: bump `webapp/package.json` `maplibre-gl` `^5.24.0` → `^6`,
  then fix the two **default** imports — v6 removes the default export, so ESM
  namespace imports are required, and this hits **both** the value default import
  and the type-only default import:
  - `webapp/src/lib/map/map.ts`:
    `import maplibregl from "maplibre-gl"` → `import * as maplibregl from "maplibre-gl"`.
  - `webapp/src/lib/map/dem.ts`:
    `import type maplibregl from "maplibre-gl"` → `import type * as maplibregl from "maplibre-gl"`.
  The **named** type imports in `config.ts`
  (`import type { StyleSpecification, … } from "maplibre-gl"`) are unaffected —
  removing the default export does not touch named exports. No `addProtocol`/gsidem,
  `setData`-2nd-param, `styleimagemissing`, or Map-extends-Camera breakage. Run
  `npm run build` (let `tsc` surface any remaining default-import sites) + the
  Playwright suites.
- Not for perf/power (v6 gains are incremental and unquantified) — purely to stay
  current and let the downstream frontend target v6.

**`basemap-resilience`** — 2 PRs, ~an afternoon each. The live GSI-dependent
basemap stays the production path for the whole tiles build below, so hardening it
early protects the demo/commercial showing while the big work proceeds.

1. `01-style-snapshot-pr1.md` — vendor and locally serve the pinned `std.json`.
2. `02-raster-fallback-pr2.md` — production-raster fallback + activation.

### Phase 1 — `osm-basemap-tiles` (the foundation)

The backbone: it establishes the merged tiles, the `feature_id` contract, the
extrudable heights, and the PLATEAU acquisition everything downstream reuses. Run
its five PRs in order:

1. `01` FGD acquisition → 2. `02` merged tile generation → 3. `03` basemap
   integration → 4. `04` PLATEAU height + 2.5D extrusion → 5. `05` retire the
   windowed buildings path.

Note: `local-3d-work-mode` can start once PR4 lands (PLATEAU acquisition +
extrudable tiles exist), even before PR5.

### Phase 2 — `local-3d-work-mode` (work mode on the foundation)

Starts after `osm-basemap-tiles` PR4. Four PRs in order:

1. `01` box-select scene shell → 2. `02` on-demand PLATEAU loading (fallback to
   extruded merged tiles) → 3. `03` subsurface + SL/AL overlays → 4. `04`
   telemetry-driven selective localisation.

### Phase 3 — `interactive-al-compute` (analysis architecture on top)

Starts after tiles (needs `feature_id`) and, per its overview, after local-3d.
Three PRs in order:

1. `01` FL materials precompute (region-wide) → 2. `02` interactive frontend AL
   recombination → 3. `03` retire frozen AL products as source of truth.

### Phase 4 — `rust-api-backend` (conditional, gated)

Not scheduled. Trigger only if `interactive-al-compute`'s SL compute service (or a
measured read-throughput need) meets the three entry conditions in that folder's
overview. Its home is the SL compute service, isolated from the thin read API. Pick
per-kernel: numpy/C-backed first, compiled/Rust only for a hot kernel that cannot
vectorize and misses budget.

## One-line sequence

MapLibre v6 upgrade + `basemap-resilience` (Phase 0, early; v6 before tiles PR3) →
`osm-basemap-tiles` (1→5) → `local-3d-work-mode` (after tiles PR4) →
`interactive-al-compute` → `rust-api-backend` (only if its entry conditions are met).

## Process discipline per PR (from the repo conventions)

- Branch per PR; never develop the next stage while a PR is open.
- Copilot auto-reviews every PR; address feedback before squash-merge.
- e2e runs locally before merge (CI e2e is gated to release tags/dispatch);
  squash-merge via the REST route.
- Update the refactor's own plan status line and `history.md` in the same change
  that changes the fact.
