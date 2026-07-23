/**
 * Viewport-driven windowed feature client — the first consumer of
 * `GET /api/v1/features/{key}`.
 *
 * This module lives outside `src/lib/map/` deliberately: the map reports
 * viewport changes through its narrow interface and renders whatever layers
 * it is handed; every fetch decision (debounce, zoom floor, quantised cache,
 * cancellation, failure states) is here, and the map knows none of it.
 *
 * Cancellation matters more than caching: a drag across a region queues
 * windows that are already stale by the time they resolve, and only the last
 * one is wanted. Superseded requests are aborted, never awaited.
 */

import type { Feature } from "../api/types";

/** Below this zoom no request is issued; the state says so instead. The
 *  floor is the bound that keeps a window's response tractable: at zoom 15 a
 *  legitimate landHistory window already returns ~8.6 MB across 141 large
 *  polygons, enough to stall tessellation on software-GL hardware. */
export const WINDOWED_MIN_ZOOM = 16;
/** The viewport snaps outward to this grid (~1 km) before it becomes a cache
 *  key, so panning back into a visited neighbourhood is a hit, not a near
 *  miss, and every pixel of pan is not a distinct window. */
export const WINDOW_GRID_DEGREES = 0.01;
export const WINDOW_DEBOUNCE_MS = 250;
/** The default per-window feature budget; a truncated window is reported as
 *  oversized and renders nothing rather than silently showing a subset.
 *  Layers with denser-but-simpler features (the OSM building detail) raise
 *  it per registry entry, within the server's own ceiling. */
export const WINDOW_LIMIT = 5000;

/** `[west, south, east, north]` — the order the API's bbox parameter expects.
 *  A transposed bbox returns plausible wrong data, not an error; the request
 *  test pins this order. */
export type Bounds = [number, number, number, number];

export type WindowedStatus =
  | "idle"
  | "belowZoom"
  | "outside"
  | "loading"
  | "ready"
  | "empty"
  | "oversized"
  | "error";

export interface WindowedState {
  status: WindowedStatus;
  features: Feature[];
  matched: number;
}

export interface WindowResult {
  matched: number;
  features: Feature[];
}

interface ApiLike {
  GET(path: "/api/v1/features/{key}", init: unknown): Promise<{ data?: unknown; error?: unknown }>;
}

export function quantizeWindow(bounds: Bounds, grid: number = WINDOW_GRID_DEGREES): Bounds {
  const [west, south, east, north] = bounds;
  return [
    Math.floor(west / grid) * grid,
    Math.floor(south / grid) * grid,
    Math.ceil(east / grid) * grid,
    Math.ceil(north / grid) * grid,
  ];
}

export function intersectsAny(window: Bounds, extents: Bounds[]): boolean {
  return extents.some(
    ([west, south, east, north]) =>
      window[0] <= east && window[2] >= west && window[1] <= north && window[3] >= south,
  );
}

/** One windowed request, exactly as the endpoint expects it. */
export async function requestWindow(
  api: ApiLike,
  key: string,
  window: Bounds,
  signal: AbortSignal,
  limit: number = WINDOW_LIMIT,
): Promise<WindowResult> {
  const { data, error } = await api.GET("/api/v1/features/{key}", {
    params: { path: { key }, query: { bbox: [...window], limit } },
    signal,
  });
  if (error || !data) throw new Error(`windowed request for ${key} failed`);
  const collection = data as { features?: Feature[]; query?: { matched?: number } };
  const features = collection.features ?? [];
  return { matched: collection.query?.matched ?? features.length, features };
}

function stateOf(result: WindowResult): WindowedState {
  if (result.matched === 0) return { status: "empty", features: [], matched: 0 };
  if (result.matched > result.features.length) {
    return { status: "oversized", features: [], matched: result.matched };
  }
  return { status: "ready", features: result.features, matched: result.matched };
}

export interface WindowedFeatureClient {
  viewChanged(view: { bounds: Bounds; zoom: number }): void;
  destroy(): void;
}

export function createWindowedFeatureClient(options: {
  api: ApiLike;
  datasetKey: string;
  extents: Bounds[];
  onState: (state: WindowedState) => void;
  /** Per-layer floor from the registry; the default is the measured bound. */
  minZoom?: number;
  /** Per-layer window budget from the registry. */
  windowLimit?: number;
  debounceMs?: number;
}): WindowedFeatureClient {
  const debounceMs = options.debounceMs ?? WINDOW_DEBOUNCE_MS;
  const minZoom = options.minZoom ?? WINDOWED_MIN_ZOOM;
  const windowLimit = options.windowLimit ?? WINDOW_LIMIT;
  const cache = new Map<string, WindowResult>();
  let timer: ReturnType<typeof setTimeout> | null = null;
  let inflight: AbortController | null = null;
  let destroyed = false;

  const cancelPending = () => {
    if (timer !== null) clearTimeout(timer);
    timer = null;
    inflight?.abort();
    inflight = null;
  };

  const resolve = (window: Bounds) => {
    if (!intersectsAny(window, options.extents)) {
      cancelPending();
      options.onState({ status: "outside", features: [], matched: 0 });
      return;
    }
    const cacheKey = window.join(",");
    const cached = cache.get(cacheKey);
    if (cached) {
      cancelPending();
      options.onState(stateOf(cached));
      return;
    }
    inflight?.abort();
    const controller = new AbortController();
    inflight = controller;
    options.onState({ status: "loading", features: [], matched: 0 });
    requestWindow(options.api, options.datasetKey, window, controller.signal, windowLimit).then(
      (result) => {
        if (destroyed || controller.signal.aborted) return;
        cache.set(cacheKey, result);
        options.onState(stateOf(result));
      },
      (cause) => {
        if (destroyed || controller.signal.aborted) return;
        void cause;
        options.onState({ status: "error", features: [], matched: 0 });
      },
    );
  };

  return {
    viewChanged(view) {
      if (destroyed) return;
      if (view.zoom < minZoom) {
        cancelPending();
        options.onState({ status: "belowZoom", features: [], matched: 0 });
        return;
      }
      if (timer !== null) clearTimeout(timer);
      const window = quantizeWindow(view.bounds);
      timer = setTimeout(() => {
        timer = null;
        resolve(window);
      }, debounceMs);
    },
    destroy() {
      destroyed = true;
      cancelPending();
    },
  };
}
