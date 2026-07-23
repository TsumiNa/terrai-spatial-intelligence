# PR3 Plan: The Zoom-threshold Handover

- Status: Planned
- Refactor: `osm-highzoom-detail`

## Goal

Past the handover zoom the city fabric is data: the GSI basemap's gray building
texture yields to the windowed OSM building layer, every footprint is clickable to
a raw audit record, and attribution states ODbL alongside GSI.

## Scope

- Registry entry for `osmBuildings` (extents = the Kanto acquisition window,
  `minZoom` = the measured handover threshold from PR2, attribution
  "© OpenStreetMap contributors", ODbL licence, extract-date vintage, limitations
  copy on community completeness).
- The layer is part of the basemap experience, not a toggle in the foundation
  list: it activates with the standard basemap at `zoom ≥ threshold`, rendered
  through the existing windowed client and a quiet building style from the
  palette; the GSI building layers hide above the threshold (a `maxzoom` clamp in
  `composeStyle`), so exactly one building inventory shows at any zoom.
- Modules that draw their own analysis buildings keep suppressing everything else,
  this layer included — the analysis remains the only building color there.
- Clicking a footprint opens the raw-kind audit record (osm_id, type, tags,
  extract date, licence), reusing the foundation popup machinery.
- e2e: handover visibility flips across the threshold; a click opens the record;
  attribution contains both GSI and ODbL notices. Visual baselines per the
  platform-split procedure if anything outside the map mask moves.

## Non-goals

- No change to windowed-layer status copy or the foundation layer list UI beyond
  what the new entry needs; no roads/POI.

## Acceptance

- `npm run build` (which runs svelte-check), `npm run test` and
  `npx playwright test` green in fixture scope; screenshots across the threshold
  at a dense ward and a sparse suburb recorded in the completion note.
