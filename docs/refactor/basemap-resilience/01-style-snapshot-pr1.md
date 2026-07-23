# PR1 Plan: Pinned Style Snapshot

- Status: Planned
- Refactor: `basemap-resilience`

## Goal

The map constructs from a style file the repository owns: a pinned `std.json`
snapshot served with the app, with upstream refresh as a deliberate, tested
act.

## Scope

- Vendor the current `std.json` (~200 KB) into the webapp source (imported or
  static-served); `createExhibitionMap` loads it instead of fetching the
  experimental GitHub Pages URL. The GSI attribution stays as required.
- A small fetch task/script refreshes the snapshot on demand and prints a diff
  summary; the three style transforms' unit tests run against the vendored
  file, so a refresh that breaks their assumptions fails visibly in CI rather
  than silently in production.
- Record the snapshot's retrieval date beside it (the FL provenance habit,
  applied to a rendering asset).

## Implementation steps

1. Fetch today's `std.json`, commit it under the webapp source with its
   retrieval date recorded beside it.
2. Point `createExhibitionMap` at the vendored file; delete the runtime fetch
   and its failure path.
3. Add the refresh script (fetch → diff summary → overwrite) and register it
   as an opt-in task.
4. Run the style-transform unit tests against the vendored file; add one that
   fails if the file loses the members the transforms rely on
   (`source-layer: building`, the z17/z18 layer bands).
5. Verify boot with `gsi-cyberjapan.github.io` blocked; confirm visual
   baselines are byte-stable.

## Non-goals

- No change to which tiles the style points at (still `experimental_bvmap` —
  PR2 owns tile-failure handling); no visual change of any kind.

## Acceptance

- The app boots and renders identically with the network blocked to
  `gsi-cyberjapan.github.io` (tiles still flow from `cyberjapandata`).
- Visual baselines byte-stable; the refresh script round-trips and reports no
  diff against the freshly vendored copy.
