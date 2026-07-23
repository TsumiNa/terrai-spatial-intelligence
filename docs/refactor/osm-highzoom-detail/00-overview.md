# OSM High-zoom Detail Layer

- Status: Completed — the three-PR sequence (#65–#67) merged; the z16 windowed clickable OSM buildings ship

## Context

The basemap is the GSI vector style, streamed live — the owner has confirmed this
stays for the wide view (commercial use is free and application-free with
attribution). Its weakness is the near view, hit repeatedly in real use: the vector
tiles cap at z16, the buildings it draws are cartography — fragments without
identity, impossible to click, easily mistaken for analysis data until #63 grayed
them out — and past the zoom ceiling detail stops growing exactly where a user
expects it to grow (the Google-Maps-like expectation: zooming in reveals more).

Meanwhile the exhibition already owns the machinery this needs: a windowed store
that serves millions of features by viewport (2.7M today), a streaming ingestion
path, a CI fixture pattern, and an FL admission principle that OSM satisfies
perfectly — real GIS data, stable ids, ODbL.

## Decision

Past a zoom threshold, the city fabric itself switches from cartography to data:
a Kanto-wide OSM building layer, served through the same windowed delivery as every
foundation layer, replaces the basemap's gray building texture. Every building on
screen at high zoom becomes a clickable object with an `osm_id`, provenance and an
audit record — the same standing the analysis buildings already have (they are OSM
footprints too, so the two inventories agree by construction).

The wide view stays GSI. The handover is the boundary between "map as context" and
"map as evidence", and it lands where the windowed store already operates
comfortably (~z16 windows).

If a client later requires offline operation, self-building the basemap for that
client's region extends this same acquisition; the planned Rust backend
(docs/refactor/rust-api-backend) is the performance path if feature volume demands
it.

## Non-goals

- No self-built wide-view basemap; GSI live streaming stays (owner decision,
  commercial terms confirmed).
- No OSM roads/POI in the first pass — buildings are the pain point; other themes
  are follow-ups with their own measurements.
- No change to the analysis layers: modules that draw their own buildings keep
  hiding everything else, including this layer.
- Aerial imagery stays live GSI (no OSM equivalent; caching infeasible at scale).

## Revision (2026-07-23, after PR3 merged)

Owner direction after seeing PR3 live: the building experience is **uniform
across modules**. The inherited rule that building-drawing analyses hide the
basemap's buildings (and, in PR3, the detail layer) left the city fabric empty
everywhere outside an analysis patch. With the basemap's buildings neutral gray
and the analysis buildings being the same OSM footprints, drawing the analysis
on top of its own outline is unambiguous — so the hiding machinery is removed
outright: GSI texture below the handover, OSM data objects above it, in every
module except underground, with analysis colors layered above.

## Planned PRs

1. `01-kanto-buildings-acquisition-pr1.md` — acquire mainland-Kanto OSM building
   footprints from a pinned Geofabrik extract into the gitignored data tree, with
   per-feature `osm_id`, tags and extract-date provenance.
2. `02-store-and-service-pr2.md` — register the dataset as an FL foundation
   collection (store ingestion, windowed endpoint, health/catalog, CI fixture
   windows, trilingual data card).
3. `03-ui-handover-pr3.md` — the zoom-threshold handover in the map UI: GSI's gray
   building texture yields to the windowed OSM layer; clicks open the raw audit
   record; attribution shows ODbL alongside GSI.
