# PR2 Plan: Basemap Integration

- Status: Planned
- Refactor: `osm-basemap-tiles`

## Goal

The wide view renders dense OSM building fabric at every zoom from the
self-built tiles, replacing GSI's building texture below the z16 handover,
while the windowed clickable OSM objects continue above it — one seamless
building experience, available offline.

## Scope

- Serve the PMTiles (static file + HTTP range, optionally behind a CDN) and add
  it to the map style as a vector source; its building layer takes the place of
  the neutralized GSI building texture below the handover, in the same gray so
  crossing z16 to the windowed objects reads as continuity.
- Keep clickability: `osm_id` baked into tile features resolves the audit record
  without an API call.
- Attribution: ODbL "© OpenStreetMap contributors" wherever the fabric renders.
- Offline proof: with the GSI vector-tile host blocked, the wide-view building
  fabric still renders from the local tiles.

## Non-goals

- No change to imagery/hillshade/slope (live GSI). No roads/water/labels yet.
- No removal of the windowed z16+ layer; it stays for the clickable detail.

## Acceptance

- `cd webapp && npm run build && npm run test` and the Playwright suites pass;
  survey-zoom screenshots show dense city fabric where it was sparse before.
- Blocking the GSI vector host leaves the building fabric intact; attribution
  present; `terrai validate` green.
