import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  IDLE_STATE,
  PROVING_LAYER,
  WINDOWED_MIN_ZOOM,
  WINDOW_LIMIT,
  createWindowedFeatureClient,
  intersectsAny,
  quantizeWindow,
  requestWindow,
  type Bounds,
  type WindowedState,
} from "./windowed";

const YOKOHAMA_VIEW: Bounds = [139.585, 35.443, 139.595, 35.451];
const OCEAN_VIEW: Bounds = [150.0, 20.0, 150.1, 20.1];

function feature(id: string) {
  return { type: "Feature", id, geometry: { type: "Point", coordinates: [139.59, 35.45] }, properties: {} };
}

function fakeApi(responses: Array<() => Promise<{ data?: unknown; error?: unknown }>>) {
  const calls: Array<{ query: { bbox: number[]; limit: number }; signal: AbortSignal }> = [];
  return {
    calls,
    GET: vi.fn((path: string, init: { params: { query: { bbox: number[]; limit: number } }; signal: AbortSignal }) => {
      calls.push({ query: init.params.query, signal: init.signal });
      const next = responses.shift();
      if (!next) throw new Error("unexpected request");
      return next();
    }),
  };
}

function collection(matched: number, count: number) {
  return {
    data: {
      type: "FeatureCollection",
      features: Array.from({ length: count }, (_, index) => feature(`f${index}`)),
      query: { matched, returned: count },
    },
  };
}

beforeEach(() => {
  vi.useFakeTimers();
});
afterEach(() => {
  vi.useRealTimers();
});

function harness(api: ReturnType<typeof fakeApi>) {
  const states: WindowedState[] = [];
  const client = createWindowedFeatureClient({
    api,
    datasetKey: PROVING_LAYER.key,
    extents: PROVING_LAYER.extents,
    onState: (state) => states.push(state),
  });
  return { client, states, last: () => states[states.length - 1] };
}

it("requests the settled viewport with the bbox order pinned to west,south,east,north", async () => {
  const api = fakeApi([async () => collection(2, 2)]);
  const { client, last } = harness(api);

  client.viewChanged({ bounds: YOKOHAMA_VIEW, zoom: 16 });
  await vi.runAllTimersAsync();

  expect(api.calls).toHaveLength(1);
  expect(api.calls[0].query.bbox).toEqual(quantizeWindow(YOKOHAMA_VIEW));
  const [west, south, east, north] = api.calls[0].query.bbox;
  expect(west).toBeLessThan(east);
  expect(south).toBeLessThan(north);
  expect(west).toBeCloseTo(139.58, 10);
  expect(south).toBeCloseTo(35.44, 10);
  expect(east).toBeCloseTo(139.6, 10);
  expect(north).toBeCloseTo(35.46, 10);
  expect(api.calls[0].query.limit).toBe(WINDOW_LIMIT);
  expect(last().status).toBe("ready");
  expect(last().features).toHaveLength(2);
});

it("issues no request below the zoom floor and says so", async () => {
  const api = fakeApi([]);
  const { client, last } = harness(api);

  client.viewChanged({ bounds: YOKOHAMA_VIEW, zoom: WINDOWED_MIN_ZOOM - 0.1 });
  await vi.runAllTimersAsync();

  expect(api.GET).not.toHaveBeenCalled();
  expect(last().status).toBe("belowZoom");
});

it("issues no request outside the layer's extent and says so", async () => {
  const api = fakeApi([]);
  const { client, last } = harness(api);

  client.viewChanged({ bounds: OCEAN_VIEW, zoom: 16 });
  await vi.runAllTimersAsync();

  expect(api.GET).not.toHaveBeenCalled();
  expect(last().status).toBe("outside");
});

it("aborts a superseded request instead of awaiting it", async () => {
  let resolveFirst: (value: { data?: unknown }) => void = () => {};
  const api = fakeApi([
    () => new Promise((resolve) => (resolveFirst = resolve)),
    async () => collection(1, 1),
  ]);
  const { client, last } = harness(api);

  client.viewChanged({ bounds: YOKOHAMA_VIEW, zoom: 16 });
  await vi.runAllTimersAsync();
  const shifted: Bounds = [139.62, 35.47, 139.64, 35.49];
  client.viewChanged({ bounds: shifted, zoom: 16 });
  await vi.runAllTimersAsync();

  expect(api.calls).toHaveLength(2);
  expect(api.calls[0].signal.aborted).toBe(true);
  expect(api.calls[1].signal.aborted).toBe(false);
  resolveFirst(collection(9, 9));
  await vi.runAllTimersAsync();
  expect(last().status).toBe("ready");
  expect(last().matched).toBe(1);
});

it("returns to a visited window from the cache with no request", async () => {
  const api = fakeApi([async () => collection(3, 3), async () => collection(1, 1)]);
  const { client, states } = harness(api);
  const elsewhere: Bounds = [139.62, 35.47, 139.64, 35.49];

  client.viewChanged({ bounds: YOKOHAMA_VIEW, zoom: 16 });
  await vi.runAllTimersAsync();
  client.viewChanged({ bounds: elsewhere, zoom: 16 });
  await vi.runAllTimersAsync();
  client.viewChanged({ bounds: YOKOHAMA_VIEW, zoom: 16 });
  await vi.runAllTimersAsync();

  expect(api.calls).toHaveLength(2);
  expect(states[states.length - 1].status).toBe("ready");
  expect(states[states.length - 1].matched).toBe(3);
});

it("reports an empty window, a truncated window and a failure as distinct states", async () => {
  const api = fakeApi([
    async () => collection(0, 0),
    async () => collection(WINDOW_LIMIT + 1, WINDOW_LIMIT),
    async () => ({ error: { detail: "boom" } }),
  ]);
  const { client, last } = harness(api);
  const windows: Bounds[] = [
    YOKOHAMA_VIEW,
    [139.60, 35.46, 139.62, 35.48],
    [139.62, 35.48, 139.64, 35.50],
  ];

  client.viewChanged({ bounds: windows[0], zoom: 16 });
  await vi.runAllTimersAsync();
  expect(last().status).toBe("empty");

  client.viewChanged({ bounds: windows[1], zoom: 16 });
  await vi.runAllTimersAsync();
  expect(last().status).toBe("oversized");
  expect(last().features).toHaveLength(0);

  client.viewChanged({ bounds: windows[2], zoom: 16 });
  await vi.runAllTimersAsync();
  expect(last().status).toBe("error");
});

it("emits nothing after destroy", async () => {
  const api = fakeApi([async () => collection(1, 1)]);
  const { client, states } = harness(api);

  client.viewChanged({ bounds: YOKOHAMA_VIEW, zoom: 16 });
  client.destroy();
  await vi.runAllTimersAsync();

  expect(states.every((state) => state.status !== "ready")).toBe(true);
});

describe("window helpers", () => {
  it("quantizes outward so the response covers the raw viewport", () => {
    const [west, south, east, north] = quantizeWindow([139.5851, 35.4432, 139.5949, 35.4508]);
    expect(west).toBeLessThanOrEqual(139.5851);
    expect(south).toBeLessThanOrEqual(35.4432);
    expect(east).toBeGreaterThanOrEqual(139.5949);
    expect(north).toBeGreaterThanOrEqual(35.4508);
  });

  it("treats an edge-touching window as inside the extent", () => {
    expect(intersectsAny([139.66, 35.3, 139.7, 35.39], PROVING_LAYER.extents)).toBe(true);
    expect(intersectsAny([139.67, 35.3, 139.7, 35.3899], PROVING_LAYER.extents)).toBe(false);
  });

  it("exposes an idle state constant for consumers to reset with", () => {
    expect(IDLE_STATE.status).toBe("idle");
  });
});

it("request helper propagates a server error as a thrown error", async () => {
  const api = fakeApi([async () => ({ error: { detail: "500" } })]);
  const controller = new AbortController();
  await expect(requestWindow(api, "landHistory", quantizeWindow(YOKOHAMA_VIEW), controller.signal)).rejects.toThrow(
    "windowed request for landHistory failed",
  );
});
