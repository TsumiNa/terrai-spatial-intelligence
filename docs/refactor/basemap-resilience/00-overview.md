# Basemap Resilience

- Status: Planned

## Context

The wide-view basemap depends on two experimental GSI resources, fetched live at
every page load:

1. **The style definition** — `std.json` from
   `gsi-cyberjapan.github.io/gsivectortile-mapbox-gl-js/`, a GitHub Pages file of
   an experimental repository. If this URL dies, `createExhibitionMap` throws and
   **the map never constructs at all**.
2. **The vector tiles** — `cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/…`,
   explicitly 提供実験: GSI states the URL and data structure may change without
   notice and accepts no liability. If it breaks, the app runs over a blank
   basemap.

There is a third, quieter exposure: the three compose-time style transforms
(z16 cartography freeze, building neutralization, handover clamp) encode
assumptions about today's `std.json` — layer zoom ranges and
`source-layer: "building"`. A silent upstream style update could invalidate them
without any error.

Commercial terms are already confirmed (free, attribution-only, no application);
this refactor addresses **operational** risk only. The z16+ building experience
is already self-hosted (the OSM detail layer), so a basemap failure no longer
touches the core "buildings as data" capability — this plan shrinks the
remaining blast radius: the wide view.

## Decision (proposed — awaiting owner evaluation)

Two independent, small measures:

1. **Style snapshot** (`01-style-snapshot-pr1.md`): vendor a pinned `std.json`
   into the repository and load it locally instead of fetching GitHub Pages at
   runtime. The style transforms then run against a known input forever;
   upstream style refresh becomes a deliberate task (fetch → diff → test →
   commit), like every other acquisition.
2. **Raster fallback** (`02-raster-fallback-pr2.md`): a switchable plan B for
   the tiles themselves — GSI's **production** raster 標準地図
   (`/xyz/std/{z}/{x}/{y}.png`, z0–18, non-experimental, same terms) wired as a
   hidden basemap through the existing raster plumbing, promoted either by an
   ops flag or automatically on repeated vector-tile failures.

Degradation cost when the fallback is active: no vector features in the wide
view (labels raster-baked, no building texture below the handover), while the
OSM detail layer, all foundation overlays and every analysis layer continue
unchanged — they are our data.

Alternatives considered:

- *Do nothing* — free until the day it is not; a boot-time hard failure on a
  commercial exhibition is not an acceptable failure mode, and the fix costs
  an afternoon.
- *Self-host the vector tiles* — removes the dependency entirely but means
  owning a nationwide tile pyramid build; rejected earlier at the basemap
  level by the owner (「通用的信息就直接用」), and out of proportion to the
  risk now that the building experience is already self-hosted.
- *Switch the wide view to a non-GSI basemap (OSM-based, commercial provider)*
  — trades a no-SLA free official source for either a paid SLA or a
  self-hosting burden, and loses the GSI cartography the exhibition's
  Japanese audience reads natively. Kept as the eventual escape hatch if GSI
  discontinues the experiment outright.

## Non-goals

- No self-hosting of any tile pyramid; no change to the confirmed live-GSI
  posture for imagery/hillshade/slope (production endpoints already).
- No style redesign — the snapshot is byte-for-byte what GSI publishes today.

## Planned PRs

1. `01-style-snapshot-pr1.md` — vendor and locally serve the pinned style, plus
   the refresh task.
2. `02-raster-fallback-pr2.md` — the production-raster fallback and its
   activation path.
