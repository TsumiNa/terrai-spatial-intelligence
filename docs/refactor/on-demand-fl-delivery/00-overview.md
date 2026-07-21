# On-demand FL Delivery

- Status: In progress

## Context

Three separate pieces of work have now placed Foundation Layer data behind an on-demand
delivery boundary, and nothing on the frontend has ever crossed it.

`docs/refactor/mlit-foundation-data/00-overview.md` decided, correctly, not to add the MLIT
layers to the bootstrap payload. `terrai_spatial/data_service.py:41-42` records the intent:
"Large FL layers are queryable but deliberately excluded from the exhibition bootstrap. Clients
request only the spatial window needed by an analysis." The server side was built and tested —
`GET /api/v1/features/{key}` accepts a four-element `bbox` query, and `query_features`,
`_intersects_bbox` and `_coordinate_pairs` implement the window.

No frontend code calls it. `webapp/src` contains exactly one `client.GET`, for `/bootstrap`, and
zero references to any on-demand dataset key. `FOUNDATION_DATASETS` now holds thirteen keys: the
ten MLIT layers integrated by PR #3 — roughly 68 MB including a 23 MB land-history layer and a
20 MB land-use mesh — plus the three underground keys merged in PRs #31-#33. All of them are
reachable today only by hand-written `curl`. `docs/architecture/FRONTEND_BACKEND.md:115` states
the current behaviour plainly: "No additional API request today."

The underground refactor, now merged, continued the same pattern rather than breaking it — its
scene catalog and handoffs are on-demand and absent from bootstrap, exactly as its plan
required. It even stopped one step short of the API: `DataService.scene_catalog()` and
`scene_handoff()` exist (`data_service.py:121-133`) but no route calls them, because
`maplibre-migration` PR7 owns the endpoint shape. The delivery boundary is intact, and still
nothing consumes it.

So the gap is not that a stage forgot the UI. It is that every FL addition has deposited data
behind a channel whose frontend end was never built — and the underground addition has now
arrived, with 3D Tiles assets cached on demand and handoffs waiting for a reader. Left as is,
the rendering stages (`maplibre-migration` 06 and 07) will each invent their own loading path
under deadline, and the boundary that three plans deliberately drew will be crossed by accident.

Meanwhile the one request that is made ships uncompressed: the bootstrap assembles roughly
3.77 MB from nineteen datasets, two of which account for 74% of it, and `terrai_spatial/api.py`
installs only `CORSMiddleware`.

## Decision

Build the missing consumer before more data arrives, and prove it against data that already
exists rather than against data still being acquired.

Windowed loading becomes a first-class frontend capability: a viewport-driven client for
`GET /api/v1/features/{key}`, a way to present a foundation layer as a map overlay with the same
audit guarantees analytical layers already have, and only then the intake of whatever the
underground refactor actually produces.

The bootstrap keeps its role. It carries the analytical products that every module needs
immediately. Foundation layers stay outside it, permanently, and are requested by window.

## Alternatives considered

### Add the MLIT layers to the bootstrap payload

Rejected, again. It was rejected once in the MLIT refactor for the right reason, and the payload
has only grown since. Adding 68 MB to a 3.77 MB uncompressed response would make every page load
pay for layers no module reads.

### Wait for the underground refactor and build one loading path for everything

Rejected. It couples a channel that can be built and tested today against ten integrated layers
to a dataset that is still being acquired, and it guarantees the channel is designed under the
pressure of the stage that needs it. Building it first means the underground intake is a
consumer of something proven, not the reason it exists.

### Serve foundation layers as pre-cut vector tiles instead of windowed GeoJSON

Deferred, not rejected. Tiling is the right answer at a scale this demo has not reached, and it
would replace a bbox query that already exists and is tested. Revisit when a windowed GeoJSON
response for a real layer measurably fails, and record the measurement that triggered it.

### Let each module fetch what it needs, without a shared client

Rejected. It reproduces the state the repository is already in — several plans each assuming
someone else built the path — and it would put fetch logic inside the map module, which
`docs/refactor/maplibre-migration/00-overview.md:35` forbids.

## Scope

- A typed, viewport-driven client for the windowed feature endpoint, with cancellation and caching.
- Response compression on the API.
- Foundation layers presented as toggleable map overlays, with audit records and provenance.
- Intake of the underground scene handoff once the underground refactor lands.

## Non-goals

- No change to the bootstrap payload's contents or contract.
- No vector-tile pipeline.
- No new analysis, score, or AL module. Foundation layers are shown as evidence, not folded into
  any ranking.
- No change to the tile-serving path, which already works per viewport.
- No 3D, terrain, or Three.js work. The underground stages own that.
- No presentation of demonstration-grade underground models as operational records.

## Consequences

- The 68 MB of MLIT data integrated by PR #3 becomes visible in the product for the first time.
- The underground refactor gains a delivery path it can consume instead of inventing.
- The frontend acquires a second data-loading mode. That is a real increase in complexity, and it
  is why the windowed client is one shared module rather than per-module fetches.
- Layer visibility becomes user state that must survive module and region switches, which the
  current state model does not represent.
- Showing foundation layers raises a licensing surface the bootstrap never had. Attribution and
  use restrictions recorded in the data cards must reach the screen.

## Delivery plan

- [01-windowed-feature-client-pr1.md](01-windowed-feature-client-pr1.md): the viewport-driven
  client and API compression, proven against one existing MLIT layer.
- [02-foundation-overlay-ui-pr2.md](02-foundation-overlay-ui-pr2.md): foundation layers as
  auditable, attributable map overlays.
- [03-underground-scene-intake-pr3.md](03-underground-scene-intake-pr3.md): intake of the
  underground scene handoff, written against the underground plan and to be revised against what
  it actually delivers.
