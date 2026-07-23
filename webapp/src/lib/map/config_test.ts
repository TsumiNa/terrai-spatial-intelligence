import { readFileSync } from "node:fs";

import { expect, it } from "vitest";

import type { StyleSpecification } from "maplibre-gl";

import { BASEMAP_BUILDING_FILL, BASEMAP_DETAIL_HANDOVER_ZOOM, LOCAL_SPRITE_URL, RASTER_SOURCES, TERRAIN_SOURCE_ID, clampBasemapBuildings, composeStyle, freezeHighZoomCartography, neutralizeBasemapBuildings, rasterId } from "./config";
import { palette } from "../theme";
import { rgba } from "./style-rules";

/** The pinned snapshot the webapp actually serves (basemap-resilience). Reading
 *  it here means a refresh that drops the members the transforms rely on fails in
 *  CI, not silently in production. */
const vendoredStyle = JSON.parse(
  readFileSync(new URL("../../../public/basemap/gsi-std-style.json", import.meta.url), "utf-8"),
) as StyleSpecification;

const buildingLayers = (style: StyleSpecification) =>
  style.layers.filter((l) => "source-layer" in l && (l as { "source-layer"?: string })["source-layer"] === "building");

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

it("appends three hidden nationwide raster layers and the terrain DEM source", () => {
  const composed = composeStyle(baseStyle);
  // vector + three rasters + the raster-dem terrain source (no layer of its own)
  expect(Object.keys(composed.sources)).toHaveLength(5);
  expect(composed.layers).toHaveLength(4);
  const dem = composed.sources[TERRAIN_SOURCE_ID] as { type?: string; encoding?: string; tiles?: string[] };
  expect(dem.type).toBe("raster-dem");
  expect(dem.encoding).toBe("mapbox");
  expect(dem.tiles?.[0]).toMatch(/^gsidem:\/\/https:\/\/cyberjapandata\.gsi\.go\.jp/);
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
  const paintOf = (id: string) => (byId[id] as unknown as { paint: Record<string, string> }).paint;
  expect(paintOf("bldg-fill")["fill-color"]).toBe(BASEMAP_BUILDING_FILL);
  expect(paintOf("bldg-fill")["fill-outline-color"]).toBe(palette.gray);
  // a visible gray from the palette at 0.5 alpha — not the near-invisible pale
  // that made the city look empty
  const [r, g, b] = rgba(palette.gray);
  expect(BASEMAP_BUILDING_FILL).toBe(`rgba(${r}, ${g}, ${b}, 0.5)`);
  expect(paintOf("bldg-line")["line-color"]).toBe(palette.gray);
  // everything that is not a building keeps GSI's own cartography
  expect(paintOf("road-line")["line-color"]).toBe("rgb(255,255,255)");
});

it("the vendored GSI snapshot still carries the members the transforms rely on", () => {
  // neutralize/clamp need the `building` source-layer to exist
  expect(buildingLayers(vendoredStyle).length).toBeGreaterThan(0);
  // freezeHighZoomCartography acts on layers whose maxzoom reaches the z17 switch
  expect(vendoredStyle.layers.filter((l) => (l.maxzoom ?? 0) >= 17).length).toBeGreaterThan(0);
});

it("composes the vendored snapshot, repointing the sprite off the experimental host", () => {
  const composed = composeStyle(vendoredStyle);
  // the sprite is the only other gsi-cyberjapan.github.io asset — repoint it local
  expect(composed.sprite).toBe(LOCAL_SPRITE_URL);
  // glyphs (maps.gsi.go.jp) and the vector source (cyberjapandata) are untouched
  expect(composed.glyphs).toBe(vendoredStyle.glyphs);
  // every building layer is clamped to the handover after compose
  for (const l of buildingLayers(composed)) {
    expect(l.maxzoom ?? 99).toBeLessThanOrEqual(BASEMAP_DETAIL_HANDOVER_ZOOM);
  }
});

it("clamps basemap buildings to the handover zoom and nothing else", () => {
  const style: StyleSpecification = {
    version: 8,
    sources: { v: { type: "vector", tiles: ["https://example.test/{z}/{x}/{y}.pbf"] } },
    layers: [
      { id: "bldg-early", type: "fill", source: "v", "source-layer": "building", minzoom: 13, maxzoom: 14 },
      { id: "bldg-open", type: "fill", source: "v", "source-layer": "building", minzoom: 14 },
      { id: "road", type: "line", source: "v", "source-layer": "road", minzoom: 11 },
    ],
  };
  const clamped = clampBasemapBuildings(style);
  const byId = Object.fromEntries(clamped.layers.map((layer) => [layer.id, layer]));
  expect(byId["bldg-early"].maxzoom).toBe(14); // already below the handover
  expect(byId["bldg-open"].maxzoom).toBe(BASEMAP_DETAIL_HANDOVER_ZOOM);
  expect(byId["road"].maxzoom).toBeUndefined();
});
