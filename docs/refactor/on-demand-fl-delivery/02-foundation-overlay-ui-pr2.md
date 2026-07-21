# PR2 Plan: Foundation Layers as Auditable Overlays

- Status: In progress
- Refactor: `on-demand-fl-delivery`
- Depends on: PR1 merged

## Goal

Make the integrated foundation layers visible in the product, as overlays a user can turn on over
any module, with the same provenance guarantee every analytical value already carries.

## Scope

1. A foundation-layer registry describing each available key: display name in three languages,
   geometry family, default styling, minimum zoom, source attribution, and use restrictions.
2. A layer control that lists the available foundation layers and toggles them independently of
   the module and view selection.
3. Rendering through `buildAnalyticalLayers`' existing conventions — colours from
   `style-rules.ts`, which draws from the locked palette — placed beneath analytical layers so an
   analysis is never obscured by context.
4. Audit records for foundation features, of `raw` kind: what the source is, when it was
   retrieved, what the source's own timestamp says, and what it is not suitable for.
5. On-screen attribution and licence notice for any visible foundation layer, driven by the
   registry rather than hard-coded.
6. Foundation layer visibility as explicit application state that survives module, view, region
   and language switches.

## Non-goals

No foundation data entering any score, ranking, or recommendation. No new analysis. No editing,
filtering, or querying of foundation attributes beyond display. No changes to the analytical
layers' own styling. No 3D scene datasets: `uc24_16_nihonbashi` and `uc24_13_sapporo` are asset
manifests over 3D Tiles, not feature collections — they belong to the underground rendering
stages, not to this overlay registry. `osmSapporoUndergroundAccess` is a feature collection and
does qualify.

## Contract decisions

- A foundation layer is **evidence shown**, never evidence scored. If a later application needs
  one of these layers as an input, that is an AL change with its own validation and audit design,
  not a side effect of making it visible.
- Attribution is not optional and not deferred. Several MLIT sources require attribution, prohibit
  unchanged redistribution, or carry Survey Act considerations, and OSM is ODbL. A layer whose
  registry entry lacks attribution must not render.
- Source timestamps are shown as the source states them. A 2021 land-use mesh drawn over a 2024
  basemap must say 2021 on screen, because the overlay invites exactly the comparison that
  mismatch invalidates.
- The palette guard applies. No colour literal enters any file but `theme.ts`.

## Implementation notes

- Seventeen source layers inside one archive is a display problem, not only a delivery problem.
  Decide whether a dataset key presents as one toggle or several, and base that on how the source
  actually separates its layers rather than on what is convenient to render.
- Foundation geometry is context, so it should read as context: lower opacity, thinner strokes,
  no picking priority over analytical features. Where a foundation layer and an analytical layer
  both claim a click, the analytical layer wins.
- `drawsOwnBuildings` already exists for the case where an analysis owns building colour. A
  foundation layer that also colours buildings needs the same treatment or the two will fight.
- Trilingual names belong in the compile-checked catalog, so a missing Japanese or Chinese entry
  fails the build rather than shipping an English string into a Japanese UI.
- The registry is data. Adding a foundation layer should be a registry entry plus a data card,
  not a code change in the layer builder.

## Acceptance

- Every integrated foundation layer can be toggled on over any module, and its features render
  within their source extent.
- Clicking a foundation feature opens an audit record naming its source, retrieval time, source
  time, licence, and stated limitations.
- Attribution for every visible foundation layer is on screen, and a registry entry without
  attribution fails a test rather than rendering.
- Layer visibility survives module, view, region and language switches.
- No foundation value appears in any score, queue, or recommendation.
- Colours come from the palette; `palette_guard` passes.
- The trilingual catalogs are complete; `npm run build` fails if one is not.
- Playwright covers toggling one layer on, clicking a feature, and confirming the audit record.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, `npm run build`, the Playwright
  suite, and `git diff --check` pass.
