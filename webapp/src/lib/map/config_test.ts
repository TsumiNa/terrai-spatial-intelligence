import { expect, it } from "vitest";

import type { StyleSpecification } from "maplibre-gl";

import { RASTER_CEILINGS, REGION_CAMERAS, composeStyle, rasterId, rasterTileUrl } from "./config";

const baseStyle: StyleSpecification = {
  version: 8,
  sources: { vector: { type: "vector", tiles: ["https://example.test/{z}/{x}/{y}.pbf"], maxzoom: 16 } },
  layers: [{ id: "background", type: "background" }],
};

it("declares the measured GSI ceilings, not deeper", () => {
  expect(RASTER_CEILINGS.photo.maxzoom).toBe(18);
  expect(RASTER_CEILINGS.hillshade.maxzoom).toBe(16);
  expect(RASTER_CEILINGS.slope.maxzoom).toBe(15);
});

it("builds per-region tile URLs against the API asset mount", () => {
  expect(rasterTileUrl("http://127.0.0.1:8000/api/v1/assets", "yokohama", "photo")).toBe(
    "http://127.0.0.1:8000/api/v1/assets/tiles/yokohama/photo/{z}/{x}-{y}.jpg",
  );
  expect(rasterTileUrl("http://127.0.0.1:8000/api/v1/assets", "mobara", "slope")).toBe(
    "http://127.0.0.1:8000/api/v1/assets/tiles/mobara/slope/{z}/{x}-{y}.png",
  );
});

it("appends six hidden raster layers on top of the vector style", () => {
  const composed = composeStyle(baseStyle, "http://x/api/v1/assets");
  expect(Object.keys(composed.sources)).toHaveLength(7);
  expect(composed.layers).toHaveLength(7);
  for (const layer of composed.layers.slice(1)) {
    expect(layer.type).toBe("raster");
    expect(layer.layout).toEqual({ visibility: "none" });
  }
  // rasters render above every vector layer so an opaque basemap covers it
  expect(composed.layers[0].id).toBe("background");
});

it("bounds every raster source to its region so panning cannot 404", () => {
  const composed = composeStyle(baseStyle, "http://x/api/v1/assets");
  const yokohama = composed.sources[rasterId("yokohama", "photo")] as { bounds?: number[] };
  expect(yokohama.bounds).toEqual([...REGION_CAMERAS.yokohama.bounds]);
  const mobara = composed.sources[rasterId("mobara", "hillshade")] as { bounds?: number[]; attribution?: string };
  expect(mobara.bounds).toEqual([...REGION_CAMERAS.mobara.bounds]);
  expect(mobara.attribution).toContain("GSI");
});

it("does not mutate the fetched vector style", () => {
  const before = JSON.stringify(baseStyle);
  composeStyle(baseStyle, "http://x/api/v1/assets");
  expect(JSON.stringify(baseStyle)).toBe(before);
});
