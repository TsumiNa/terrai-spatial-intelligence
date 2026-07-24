import { afterEach, describe, expect, it, vi } from "vitest";

import { type Bounds, buildCoverageIndex, loadCoverage, meshCell, viewportInCoverage } from "./coverage";

describe("meshCell", () => {
  it("decodes a 6-digit 2次メッシュ to its SW-corner degree bounds", () => {
    // 533914: central Kanto, lon 139.5–139.625, lat 35.4167–35.5.
    const [w, s, e, n] = meshCell("533914");
    expect(w).toBeCloseTo(139.5, 4);
    expect(s).toBeCloseTo(35.41667, 4);
    expect(e).toBeCloseTo(139.625, 4);
    expect(n).toBeCloseTo(35.5, 4);
  });

  it("places a remote-island mesh far away", () => {
    // 365337: Minamitorishima, ~154°E — never in the mainland coverage.
    const [w] = meshCell("365337");
    expect(w).toBeGreaterThan(153);
  });
});

describe("viewportInCoverage", () => {
  const index = buildCoverageIndex(["533914", "533924"]);

  it("is true when the viewport overlaps a covered cell", () => {
    const bounds: Bounds = [139.55, 35.44, 139.6, 35.48]; // inside 533914
    expect(viewportInCoverage(bounds, index)).toBe(true);
  });

  it("is true when the viewport straddles a cell edge", () => {
    const bounds: Bounds = [139.45, 35.44, 139.55, 35.48]; // straddles 533914's west edge
    expect(viewportInCoverage(bounds, index)).toBe(true);
  });

  it("is false when the viewport is wholly outside every covered cell", () => {
    const bounds: Bounds = [141.0, 36.6, 141.2, 36.8]; // north-east, no coverage
    expect(viewportInCoverage(bounds, index)).toBe(false);
  });
});

describe("loadCoverage", () => {
  afterEach(() => vi.unstubAllGlobals());
  const stubFetch = (impl: () => Promise<unknown>) => vi.stubGlobal("fetch", vi.fn(impl));

  it("indexes a valid coverage document", async () => {
    stubFetch(async () => ({ ok: true, json: async () => ({ meshes: ["533914", "533924"] }) }));
    const index = await loadCoverage("/basemap/coverage.json");
    expect(index?.cells).toHaveLength(2);
  });

  it("returns null on a non-200 response (degrades to GSI, not empty map)", async () => {
    stubFetch(async () => ({ ok: false, json: async () => ({}) }));
    expect(await loadCoverage("/x")).toBeNull();
  });

  it("returns null when the fetch rejects", async () => {
    stubFetch(async () => {
      throw new Error("network down");
    });
    expect(await loadCoverage("/x")).toBeNull();
  });

  it("returns null on malformed JSON", async () => {
    stubFetch(async () => ({
      ok: true,
      json: async () => {
        throw new SyntaxError("unexpected token");
      },
    }));
    expect(await loadCoverage("/x")).toBeNull();
  });

  it("returns null when meshes is absent or not an array of strings", async () => {
    stubFetch(async () => ({ ok: true, json: async () => ({ meshes: "nope" }) }));
    expect(await loadCoverage("/x")).toBeNull();
    stubFetch(async () => ({ ok: true, json: async () => ({ meshes: [123] }) }));
    expect(await loadCoverage("/x")).toBeNull();
  });
});
