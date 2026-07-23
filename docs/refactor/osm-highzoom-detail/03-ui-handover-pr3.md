# PR3 Plan: The Zoom-threshold Handover

- Status: Completed
- Refactor: `osm-highzoom-detail`
- PR: #67

## Completion record

- The handover is exactly one building inventory at any zoom: GSI's neutralized
  texture below z16 (a `maxzoom` clamp in `composeStyle`), the windowed OSM data
  objects at and above it, auto-managed with the standard basemap and suppressed
  wherever a module draws its own buildings.
- Real windows busted the assumed budget immediately: a quantized z16 window over
  the default view matched 5,642 footprints and dense central-Tokyo fabric reaches
  ~10k, so the server limit ceiling rose to 20,000 and the registry gained a
  per-layer `windowLimit` (15,000 here) — the budget is feature count, not the
  tessellation weight the old land-history bound guarded against.
- A latent popup bug surfaced and is fixed: the layer-rebuild effect closed the
  active popup on every windowed-overlay state change (any window arrival killed
  queue popups once the detail layer was live in most modules). Popup lifecycle
  now has its own effect keyed only on module/view/data.
- The detail style needed one revision: the "continuity" pale fill vanished
  against the 宅地 background the clamped texture leaves behind; the shipped
  style is neutral mid-gray, clearly structure, far from any analysis color.

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
