import { expect, it } from "vitest";

import type { StyleSpecification } from "maplibre-gl";

import { RASTER_SOURCES, composeStyle, freezeHighZoomCartography, neutralizeBasemapBuildings, rasterId, vectorBuildingLayerIds } from "./config";
import { palette } from "../theme";

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

it("freezes the z16 cartography past the vector tile ceiling", () => {
  const style: StyleSpecification = {
    version: 8,
    sources: { v: { type: "vector", tiles: ["https://example.test/{z}/{x}/{y}.pbf"], maxzoom: 16 } },
    layers: [
      { id: "mid-handoff", type: "fill", source: "v", "source-layer": "landforma", minzoom: 8, maxzoom: 14 },
      { id: "reaches-17", type: "fill", source: "v", "source-layer": "building", minzoom: 14, maxzoom: 17 },
      { id: "reaches-18", type: "line", source: "v", "source-layer": "road", minzoom: 11, maxzoom: 18 },
      { id: "large-scale-only", type: "line", source: "v", "source-layer": "road", minzoom: 17, maxzoom: 18 },
    ],
  };
  const frozen = freezeHighZoomCartography(style);
  const byId = Object.fromEntries(frozen.layers.map((layer) => [layer.id, layer]));
  // GSI's mid-zoom hand-offs stay exactly as designed…
  expect(byId["mid-handoff"].maxzoom).toBe(14);
  // …layers that reached the z17 switch overscale to the camera ceiling…
  expect("maxzoom" in byId["reaches-17"]).toBe(false);
  expect("maxzoom" in byId["reaches-18"]).toBe(false);
  // …and the large-scale edge cartography never appears.
  expect(byId["large-scale-only"]).toBeUndefined();
});

it("neutralizes the basemap's cartographic buildings to palette grays", () => {
  const style: StyleSpecification = {
    version: 8,
    sources: { v: { type: "vector", tiles: ["https://example.test/{z}/{x}/{y}.pbf"] } },
    layers: [
      { id: "bldg-fill", type: "fill", source: "v", "source-layer": "building", paint: { "fill-color": "rgba(255,119,51,1)" } },
      { id: "bldg-line", type: "line", source: "v", "source-layer": "building", paint: { "line-color": "rgba(255,119,51,1)" } },
      { id: "road-line", type: "line", source: "v", "source-layer": "road", paint: { "line-color": "rgb(255,255,255)" } },
    ],
  };
  const neutral = neutralizeBasemapBuildings(style);
  const byId = Object.fromEntries(neutral.layers.map((layer) => [layer.id, layer]));
  expect((byId["bldg-fill"] as { paint: Record<string, string> }).paint["fill-color"]).toBe(palette.line);
  expect((byId["bldg-fill"] as { paint: Record<string, string> }).paint["fill-outline-color"]).toBe(palette.gray);
  expect((byId["bldg-line"] as { paint: Record<string, string> }).paint["line-color"]).toBe(palette.gray);
  // everything that is not a building keeps GSI's own cartography
  expect((byId["road-line"] as { paint: Record<string, string> }).paint["line-color"]).toBe("rgb(255,255,255)");
});
