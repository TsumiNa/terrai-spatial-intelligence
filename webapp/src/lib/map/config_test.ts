import { expect, it } from "vitest";

import type { StyleSpecification } from "maplibre-gl";

import { RASTER_SOURCES, composeStyle, rasterId, vectorBuildingLayerIds } from "./config";

const baseStyle: StyleSpecification = {
  version: 8,
  sources: { vector: { type: "vector", tiles: ["https://example.test/{z}/{x}/{y}.pbf"], maxzoom: 16 } },
  layers: [{ id: "background", type: "background" }],
};

it("declares the published GSI zoom ranges, not deeper", () => {
  expect(RASTER_SOURCES.photo.maxzoom).toBe(18);
  expect(RASTER_SOURCES.hillshade.maxzoom).toBe(16);
  expect(RASTER_SOURCES.slope.maxzoom).toBe(15);
  expect(RASTER_SOURCES.slope.minzoom).toBe(3);
});

it("streams every raster basemap live from the GSI tile host", () => {
  for (const { url } of Object.values(RASTER_SOURCES)) {
    expect(url).toMatch(/^https:\/\/cyberjapandata\.gsi\.go\.jp\/xyz\//);
    expect(url).toContain("{z}/{x}/{y}");
  }
});

it("appends three hidden nationwide raster layers on top of the vector style", () => {
  const composed = composeStyle(baseStyle);
  expect(Object.keys(composed.sources)).toHaveLength(4);
  expect(composed.layers).toHaveLength(4);
  for (const layer of composed.layers.slice(1)) {
    expect(layer.type).toBe("raster");
    expect(layer.layout).toEqual({ visibility: "none" });
  }
  // rasters render above every vector layer so an opaque basemap covers it
  expect(composed.layers[0].id).toBe("background");
  const photo = composed.sources[rasterId("photo")] as { bounds?: number[]; attribution?: string };
  // nationwide: no bounds clamp remains from the retired per-region cache
  expect(photo.bounds).toBeUndefined();
  expect(photo.attribution).toContain("GSI");
});

it("identifies the vector style's building layers by source-layer", () => {
  const style: StyleSpecification = {
    version: 8,
    sources: { v: { type: "vector", tiles: ["https://example.test/{z}/{x}/{y}.pbf"] } },
    layers: [
      { id: "background", type: "background" },
      { id: "bldg-1", type: "fill", source: "v", "source-layer": "building" },
      { id: "road-1", type: "line", source: "v", "source-layer": "road" },
      { id: "bldg-2", type: "line", source: "v", "source-layer": "building" },
    ],
  };
  expect(vectorBuildingLayerIds(style)).toEqual(["bldg-1", "bldg-2"]);
});

it("does not mutate the fetched vector style", () => {
  const before = JSON.stringify(baseStyle);
  composeStyle(baseStyle);
  expect(JSON.stringify(baseStyle)).toBe(before);
});
