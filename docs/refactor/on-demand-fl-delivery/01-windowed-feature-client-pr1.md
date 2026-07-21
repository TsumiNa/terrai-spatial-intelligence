# PR1 Plan: Viewport-driven Feature Client

- Status: Planned
- Refactor: `on-demand-fl-delivery`

## Goal

Give the frontend its first consumer of `GET /api/v1/features/{key}`, driven by the map viewport,
and compress the API's responses. Prove both against a foundation layer that is already
integrated.

## Scope

1. One shared client module that requests a dataset key for a bounding box, cancels a request
   superseded by a later viewport, and caches by key and window so panning back is free.
2. A debounce and a minimum-zoom floor, so a request is issued for a settled viewport at a scale
   where the window is bounded, not on every camera frame.
3. Wiring from the MapLibre instance's `moveend` to the client, without putting fetch logic inside
   the map module or map internals into reactive state.
4. A declared, tested behaviour for the response being too large, the request failing, and the
   viewport being outside the layer's extent. Each is a distinct state the user can see.
5. `GZipMiddleware` on the FastAPI app.
6. One existing MLIT layer chosen as the proving consumer, rendered minimally — geometry only,
   palette colours, no styling work. Presentation is PR2.

## Non-goals

No overlay UI, legend, layer switcher, or per-layer styling. No new endpoint or change to the
existing endpoint's contract. No bootstrap change. No tiling. No underground data.

## Implementation notes

- Choose the proving layer for difficulty, not convenience. `landHistory` at 23 MB with 3,780
  features across seventeen and twelve source layers per archive is the honest test; a small layer
  would pass while proving nothing.
- The bbox parameter is already constrained server-side to exactly four elements
  (`min_length=4, max_length=4`). Send `[west, south, east, north]` and add a test that pins the
  order, because a transposed bbox returns plausible wrong data rather than an error.
- Cache on the rounded window, not the raw viewport, or every pixel of pan is a cache miss.
- Cancellation matters more than caching here. A user dragging across a region can queue a dozen
  requests for windows already stale; only the last is wanted.
- `deck.gl` layer identity must stay stable as data arrives. Replacing the whole layer array on
  every response is the pattern the map module already uses; keep it, and let `id` drive the diff.
- Compression is one middleware line, but confirm it applies to the `StaticFiles` mount as well as
  the JSON routes, and that tile responses are not double-compressed.

## Acceptance

- Panning and zooming the map issues windowed requests for the proving layer, and superseded
  requests are cancelled rather than awaited.
- Returning to a previously visited window issues no request.
- Below the minimum zoom, no request is issued and the state is visible to the user.
- Request failure, empty window, and oversized response are each distinguishable on screen and
  each covered by a test.
- The bootstrap response is served compressed, and its transferred size is recorded in the PR
  description alongside the uncompressed figure.
- Playwright covers one pan that loads features and one that hits the cache.
- No fetch logic inside `webapp/src/lib/map/`, and no map object in reactive state.
- `uv run pytest`, `uv run python -m terrai_spatial validate`, `npm run build`, the Playwright
  suite, Ruff for changed Python, and `git diff --check` pass.

## Handoff

PR2 consumes this client. If the proving layer exposes a limit in the endpoint itself — an
unacceptable response size for a legitimate window, or a bbox filter too coarse to be useful —
record it here as a measured fact before PR2 designs around it.
