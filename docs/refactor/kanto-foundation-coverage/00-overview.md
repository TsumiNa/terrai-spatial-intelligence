# Kanto-wide Foundation Coverage

- Status: Planned

## Context

Every MLIT foundation layer is acquired through two small demonstration windows —
Yokohama `(139.54, 35.39, 139.66, 35.515)` and Mobara `(140.22, 35.38, 140.35, 35.51)`,
about 0.03 square degrees together (`terrai_spatial/pipeline/regions.py`). Outside those
two boxes the exhibition map has nothing to show: panning anywhere in Tokyo, Saitama,
Chiba or the rest of Kanagawa returns empty windows, and the on-demand delivery
architecture built by `data-pipeline-and-store` and `on-demand-fl-delivery` — R-tree
windowing, zoom floors, viewport quantisation — serves a data extent it outgrew the day
it merged.

The request is to cover the Tokyo metropolitan area: the 23 wards and the Tama cities,
plus Kanagawa, Chiba and Saitama prefectures in full.

## The sizing facts (probed 2026-07-22, HTTP HEAD against nlftp.mlit.go.jp)

| Source | Wide-coverage archives | Zipped size |
| --- | --- | --- |
| A33-25 landslide warning (GeoJSON, per prefecture) | `_11 _12 _13 _14` | 38.2 MB |
| A56-25 embankment regulation (per prefecture) | `_11 _12 _13 _14` | ~26 MB |
| L01-26 / L02-25 land prices (per prefecture) | `_11 _12 _13 _14` each | ~9 MB |
| A53-25 multi-stage flood | `_83` (the whole Kanto bureau block; already downloaded today) | 14.7 MB |
| N02-25 railway, FC flood history | national archives (already downloaded today) | 21.8 MB |
| L03-b-21 land-use mesh (per primary mesh) | `5238 5239 5240 5338 5339 5340 5439 5440` | 137 MB |
| F3 1:50k land classification (per digitised sheet) | 15 Kanto sheets of the 98 digitised nationally | ~30 MB |
| land_history_2011 (per 1:25k sheet) | 14 Kanto sheets of the ~70 published nationally | ~50 MB |

Two consequences follow directly:

1. **The expanded products cannot be committed.** The demo-scope committed outputs are
   already 68 MB; the wide window is roughly a hundred times their area. The land-use
   mesh alone expands to an estimated 1–2 GB of GeoJSON (~2 million 100 m cells), and
   the landslide-warning output alone would cross GitHub's 100 MB single-file limit.
2. **Coverage is honest but partial for two sources.** F3 and land_history_2011 were
   digitised sheet-by-sheet upstream; only the sheets listed above exist. The other
   eight sources cover the four prefectures completely (as rectangles or per-prefecture
   files).

## Decision

Acquisition gains a second scope; nothing committed changes.

- The committed demo subsets under `data/mlit/` stay exactly as they are: they are what
  CI builds the store from offline, what the Playwright suites and visual baselines are
  pinned to, and what makes a fresh clone work without a 300 MB download session.
- A new opt-in network task downloads the wide-scope archives and writes
  `data/external/mlit_wide/*.geojson` — a **gitignored reproducible cache**, the same
  category as the TEPCO CSVs and the PLATEAU archives. One acquisition window covers
  mainland Kanto: `(138.65, 34.85, 140.95, 36.30)`, excluding the Izu/Ogasawara islands
  as requested.
- The store build resolves each MLIT dataset **per file**: the wide product when a
  non-empty one exists, the committed demo subset otherwise. The store manifest records
  which source it was built from, so `verify_store` drift detection keeps working
  unchanged. Everything downstream of the store — windowed delivery, catalog, health,
  identity oracle — follows the resolved path automatically.

Alternatives considered:

- *Commit the wide products* — infeasible (single files over GitHub's hard limit,
  gigabytes of history churn on every refresh).
- *Move all MLIT data out of git* — breaks the offline demo, hermetic CI and the visual
  baselines for no benefit; upstream refreshes would silently shift test fixtures.
- *Serve wide data from tiles or a remote store* — a different architecture; the
  windowed SQLite store was built precisely so coverage could grow without one.

Consequences to accept: the store and local test data become environment-dependent
(demo scope in CI, wide scope on machines that fetched it). The byte-identity tests
compare store against files *in the same environment*, so they remain valid in both;
they just get slower where the wide cache exists. The wide store build is a
minutes-long, RAM-hungry local operation and is documented as such.

## Non-goals

- No zoom-floor changes. The floors are measured bounds (`landHistory` at zoom 15
  already stalls software-GL tessellation); revisiting them without new measurements
  against the wide store would un-measure them. Measurement is a follow-up, not this
  sequence.
- No expansion of `gsiEvacuation`, the PLATEAU scenes, the KuniJiban boreholes, or any
  analysis (AL) product — those are Yokohama/Mobara/Nihonbashi/Sapporo-scoped by design.
- No `/api/v1` contract changes: same routes, same shapes.
- No CI acquisition of wide data, ever: CI stays offline and hermetic.

## Planned PRs

1. `01-wide-acquisition-pr1.md` — the wide-region registry entry, the wide fetch script
   (streaming writes), its data task, and the gitignore entry. Inert until run.
2. `02-store-scope-resolution-pr2.md` — per-file wide-over-demo source resolution in the
   data service; store inputs and staleness follow; a store-freshness guard in the
   identity suite.
3. `03-coverage-surfacing-pr3.md` — widen the foundation-layer registry extents in the
   webapp and update the ten MLIT data cards (trilingual) to state the two-scope
   coverage honestly, including the partial-sheet caveats.

After PR3 merges, the wide fetch and store rebuild run once on the exhibition machine
(not in a PR), and the result is verified visually across the four prefectures.
