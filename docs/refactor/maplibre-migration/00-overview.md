# Frontend Migration: Svelte + Vite, MapLibre + deck.gl

- Status: In progress — stages 01-05 reach parity, 06-07 are blocked on data
- Date: 2026-07-20
- Baseline: `main` / `d68bd1e`
- Type: frontend platform migration; the FastAPI backend and the data pipelines stay
- Evidence: [render stack evaluation](../../summary/render-stack-evaluation/README.md)

## Why

The exhibition frontend is hand-written browser JavaScript with a vendored Leaflet, served as static files with no build step. That was the right choice while the UI was being explored. Three things have now outgrown it.

**Leaflet cannot express the roadmap.** It renders 2D raster tiles and nothing else. Underground utility networks need a lowered camera and depth control; the site scene needs a 3D viewer. Neither is a Leaflet feature that is missing, they are outside what the library is.

**The contracts between frontend and backend are literal strings.** `command_validate` greps `frontend/app.js` for `state.data.recommendations.slope.features`, greps `terrai_spatial/api.py` for route paths, and greps `frontend/index.html` for `data-module="overview"`. Renaming a route or a module id breaks validation somewhere far from the edit. FastAPI already publishes an OpenAPI schema; generated types can replace most of this.

**Translation completeness is checked by grep.** `frontend/i18n.js` uses Simplified Chinese UI strings as dictionary keys, and validation looks for `"证据与可靠性"` to confirm a translation exists. A missing translation is found by a human noticing, not by the build. The repository's documentation now defaults to English while the UI source language is Chinese; the two policies have diverged.

## Decision

Migrate to **Svelte 5 + Vite + TypeScript**, with **MapLibre GL JS + deck.gl** for the map and a **standalone Three.js scene** for the site view.

The rendering stack decision, its measurements, and the alternatives considered are recorded in the [render stack evaluation](../../summary/render-stack-evaluation/README.md). In short: MapLibre wins on weight, frame rate, 2D handling and basemap sharpness; CesiumJS was excluded because the underground requirement does not have the shape that would justify it; and `flutter-maplibre-gl` keeps a native tablet client reachable later.

Svelte was chosen over React because the framework's job here is panels, queues, the audit drawer and language switching — state synchronisation, not a large component ecosystem — and the bundle budget is already spent on the map libraries. React with the same three orthogonal decisions below would also be defensible; the framework is the least consequential choice in this migration.

### Three decisions that matter more than the framework

1. **Generate TypeScript types from FastAPI's OpenAPI schema.** Dataset keys and property names stop being magic strings. A batch of the literal-string contracts in `command_validate` can then be deleted rather than maintained.
2. **Compile-time i18n with typed message identifiers.** Completeness becomes a build error instead of a grep. This is also the moment to settle whether the UI source language stays Chinese or follows the documentation to English.
3. **Playwright instead of grep for UI contracts.** `data-module="overview"` in the HTML is a proxy for "the navigation works". Test the actual flow.

### Rules that hold across every stage

- **The map stays imperative.** One module owns the MapLibre instance and its deck.gl overlay. Svelte owns panels and state. Do not wrap map layers in reactive components; a diff that rebuilds a layer on every state change reproduces exactly the stutter measured during evaluation.
- **The audit chain is not allowed to regress.** Every displayed value keeps its route back to source, formula and limitation. This is the product's core claim, and it is the thing most likely to be quietly dropped while porting panels.
- **No Cesium.** It is not a dependency of any stage.

## Non-goals

Backend rewrite; database or schema work; authentication or tenancy; the Flutter or Capacitor field client; SL model serving. Underground network rendering and the site scene are planned here but blocked on data that does not exist yet — see stages 06 and 07.

## Stage map

Stages 01–05 reach parity with today's exhibition and retire Leaflet. Stages 06–07 add capability and cannot start until their data exists.

| Stage | Plan | Purpose |
|---|---|---|
| 01 | [toolchain and typed client](01-toolchain-and-typed-client-pr1.md) | Vite, Svelte, TypeScript, OpenAPI codegen. No visible change. |
| 02 | [app shell and i18n](02-app-shell-and-i18n-pr2.md) | Panels, queues, audit drawer, compile-time translations. Map area is a placeholder. |
| 03 | [MapLibre basemaps](03-maplibre-basemap-pr3.md) | Vector and raster basemaps, region switching, camera. |
| 04 | [deck.gl analytical layers](04-deck-analytical-layers-pr4.md) | Every current module's layers and their audit wiring. Parity reached. |
| 05 | [retire the Leaflet runtime](05-retire-leaflet-runtime-pr5.md) | Delete the old frontend; replace grep contracts with types and Playwright. |
| 06 | [underground utility networks](06-underground-networks-pr6.md) | Lowered camera, translucent surface, depth-controlled network layer. |
| 07 | [site scene](07-site-scene-three-pr7.md) | Box-select into a standalone Three.js local scene. |

Each stage ships as its own pull request, states its own acceptance commands, and leaves the test suite and validation passing when it merges. A stage that only turns green after a later one is wrongly ordered — see `.github/instructions/branch-and-pr-workflow.instructions.md`.

## Consequences accepted

- **A build step becomes mandatory.** `terrai serve` must serve built output rather than raw source files, and contributors need Node installed alongside `uv`. The zero-build shortcut ends here, deliberately.
- **Two frontends coexist during stages 01–04.** The old one keeps working and stays the served default until stage 05 removes it. This is what makes each stage independently revertible.
- **`REQUIRED_FILES` and the exhibition contracts in `terrai_spatial/cli.py` change in stage 05, not before.** Moving them earlier would make earlier stages fail validation for files they have not replaced yet.
- **The site scene introduces a second coordinate system.** Local metric coordinates relative to a site origin. The origin, rotation, vertical datum and default exaggeration must come from the API as data, never hard-coded, or the audit chain breaks at the moment a user enters 3D.

## Open questions carried into implementation

1. ~~Whether the UI source language stays Simplified Chinese or moves to English.~~ **Settled in stage 02:** the message key set is defined by the English catalog (`webapp/src/lib/i18n/messages.ts`), aligning the UI source language with the documentation policy; the Chinese and Japanese catalogs are compile-checked against it, and the default *display* language remains Simplified Chinese for exhibition parity.
2. Whether MapLibre terrain from GSI elevation works outside the throwaway spike. Not required by any stage here, but wanted for surface context.
3. The output shape of `geo_pfn` subsurface prediction, which decides whether stage 07 needs volumetric ray marching or only discrete surfaces and boreholes.
