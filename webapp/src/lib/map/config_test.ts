import { readFileSync } from "node:fs";

import { expect, it } from "vitest";

import type { StyleSpecification } from "maplibre-gl";

import { BASEMAP_BUILDING_FILL, BUILDING_EXTRUSION_LAYER_ID, BUILDING_TILES_ATTRIBUTION, BUILDING_TILES_LAYER_ID, BUILDING_TILES_MIN_ZOOM, BUILDING_TILES_SOURCE_ID, BUILDING_TILES_SOURCE_LAYER, FALLBACK_RASTER_LAYER_ID, FALLBACK_RASTER_SOURCE_ID, FALLBACK_STD_RASTER_URL, LOCAL_SPRITE_URL, RASTER_KINDS, RASTER_SOURCES, RELIEF_TINT_FADE_END_ZOOM, RELIEF_TINT_LAYER_ID, RELIEF_TINT_MAX_OPACITY, RELIEF_TINT_SOURCE_ID, RELIEF_TINT_START_ZOOM, RELIEF_TINT_URL, TERRAIN_SOURCE_ID, buildingTilesUrl, composeStyle, freezeHighZoomCartography, neutralizeBasemapBuildings, rasterId } from "./config";
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

it("declares the published GSI zoom range, not deeper", () => {
  expect(RASTER_SOURCES.photo.maxzoom).toBe(18);
});

it("streams the raster basemap live from the GSI tile host", () => {
  for (const { url } of Object.values(RASTER_SOURCES)) {
    expect(url).toMatch(/^https:\/\/cyberjapandata\.gsi\.go\.jp\/xyz\//);
    expect(url).toContain("{z}/{x}/{y}");
  }
});

it("appends the basemap layers and the terrain DEM source", () => {
  const composed = composeStyle(baseStyle);
  // composeStyle adds, over baseStyle: the raster-dem terrain + the hidden
  // fallback + the relief-tint sources + the photo raster source + the merged
  // building PMTiles source (hillshade is a computed layer over the terrain
  // source, so it adds no source of its own)…
  expect(Object.keys(composed.sources)).toHaveLength(Object.keys(baseStyle.sources).length + 5);
  // …and the fallback, photo, hillshade, relief-tint, building-fill and
  // building-extrusion layers (the extrusion reuses the building source).
  expect(composed.layers).toHaveLength(baseStyle.layers.length + 6);
  const dem = composed.sources[TERRAIN_SOURCE_ID] as { type?: string; encoding?: string; tiles?: string[] };
  expect(dem.type).toBe("raster-dem");
  expect(dem.encoding).toBe("mapbox");
  expect(dem.tiles?.[0]).toMatch(/^gsidem:\/\/terrai-dem\//);
  // every overlay layer starts hidden (the active basemap is a visibility toggle)
  for (const layer of composed.layers.slice(1)) {
    expect(layer.layout).toEqual({ visibility: "none" });
  }
  // hillshade is computed on the GPU from the terrain raster-dem, not a raster tile
  const hillshade = composed.layers.find((l) => l.id === rasterId("hillshade"));
  expect(hillshade?.type).toBe("hillshade");
  expect((hillshade as { source?: string }).source).toBe(TERRAIN_SOURCE_ID);
  expect(composed.layers[0].id).toBe("background");
  const photo = composed.sources[rasterId("photo")] as { bounds?: number[]; attribution?: string };
  // nationwide: no bounds clamp remains from the retired per-region cache
  expect(photo.bounds).toBeUndefined();
  expect(photo.attribution).toContain("GSI");
});

it("adds the merged building PMTiles source and a hidden fill above GSI buildings", () => {
  const composed = composeStyle(vendoredStyle, "https://cdn.example/buildings.pmtiles");
  const source = composed.sources[BUILDING_TILES_SOURCE_ID] as { type?: string; url?: string; attribution?: string };
  expect(source.type).toBe("vector");
  expect(source.url).toBe("pmtiles://https://cdn.example/buildings.pmtiles");
  expect(source.attribution).toBe(BUILDING_TILES_ATTRIBUTION);
  const fill = composed.layers.find((l) => l.id === BUILDING_TILES_LAYER_ID) as {
    type?: string;
    "source-layer"?: string;
    minzoom?: number;
    maxzoom?: number;
    layout?: unknown;
    paint?: { "fill-color"?: string };
  };
  expect(fill.type).toBe("fill");
  expect(fill["source-layer"]).toBe(BUILDING_TILES_SOURCE_LAYER);
  expect(fill.minzoom).toBe(BUILDING_TILES_MIN_ZOOM);
  // No maxzoom cap (PR5 retired the z16 handover): the tiles span all zooms.
  expect(fill.maxzoom).toBeUndefined();
  expect(fill.layout).toEqual({ visibility: "none" });
  expect(fill.paint?.["fill-color"]).toBe(BASEMAP_BUILDING_FILL);
  // Spliced above the GSI building layers, so it draws over ground / under labels.
  const buildingIdx = composed.layers.findIndex((l) => l.id === BUILDING_TILES_LAYER_ID);
  const lastGsiBuilding = composed.layers.reduce(
    (acc, l, i) => ("source-layer" in l && (l as { "source-layer"?: string })["source-layer"] === "building" && l.id !== BUILDING_TILES_LAYER_ID ? i : acc),
    -1,
  );
  expect(buildingIdx).toBe(lastGsiBuilding + 1);

  const extrusion = composed.layers.find((l) => l.id === BUILDING_EXTRUSION_LAYER_ID) as {
    type?: string;
    minzoom?: number;
    paint?: { "fill-extrusion-height"?: unknown };
  };
  expect(extrusion.type).toBe("fill-extrusion");
  expect(extrusion.minzoom).toBe(14);
  expect(extrusion.paint?.["fill-extrusion-height"]).toEqual(["get", "height"]);
});

it("resolves the building-tiles URL from ?buildings= with a default fallback", () => {
  expect(buildingTilesUrl("")).toBe("/basemap/buildings.pmtiles");
  expect(buildingTilesUrl("?buildings=https://r2.example/b.pmtiles")).toBe("https://r2.example/b.pmtiles");
});

it("appends a hidden production-raster fallback below the user rasters", () => {
  const composed = composeStyle(baseStyle);
  const src = composed.sources[FALLBACK_RASTER_SOURCE_ID] as { type?: string; tiles?: string[] };
  expect(src.type).toBe("raster");
  expect(src.tiles?.[0]).toBe(FALLBACK_STD_RASTER_URL);
  // the production std endpoint, not the experimental bvmap
  expect(FALLBACK_STD_RASTER_URL).toMatch(/^https:\/\/cyberjapandata\.gsi\.go\.jp\/xyz\/std\//);
  const fallbackLayer = composed.layers.find((l) => l.id === FALLBACK_RASTER_LAYER_ID);
  expect(fallbackLayer?.layout).toEqual({ visibility: "none" });
  // below every user raster so a selected basemap still covers it
  const idx = (id: string) => composed.layers.findIndex((l) => l.id === id);
  for (const kind of RASTER_KINDS) {
    expect(idx(FALLBACK_RASTER_LAYER_ID)).toBeLessThan(idx(rasterId(kind)));
  }
});

it("adds a hidden colour-by-height tint above the user rasters, capped past the fade", () => {
  const composed = composeStyle(baseStyle);
  const src = composed.sources[RELIEF_TINT_SOURCE_ID] as { type?: string; tiles?: string[] };
  expect(src.type).toBe("raster");
  expect(src.tiles?.[0]).toBe(RELIEF_TINT_URL);
  const tint = composed.layers.find((l) => l.id === RELIEF_TINT_LAYER_ID);
  expect(tint?.layout).toEqual({ visibility: "none" });
  // hidden at/above the fade end so no tint tiles are requested locally
  expect(tint?.maxzoom).toBe(RELIEF_TINT_FADE_END_ZOOM);
  // the opacity fades from full at the wide-view start to 0 at the fade end
  const opacity = (tint as { paint?: Record<string, unknown> }).paint?.["raster-opacity"] as unknown[];
  expect(opacity[0]).toBe("interpolate");
  expect(opacity.slice(3, 5)).toEqual([RELIEF_TINT_START_ZOOM, RELIEF_TINT_MAX_OPACITY]);
  expect(opacity.slice(-2)).toEqual([RELIEF_TINT_FADE_END_ZOOM, 0]);
  // above every user raster, so it draws over the shaded relief
  const idx = (id: string) => composed.layers.findIndex((l) => l.id === id);
  for (const kind of RASTER_KINDS) {
    expect(idx(RELIEF_TINT_LAYER_ID)).toBeGreaterThan(idx(rasterId(kind)));
  }
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
  // PR5 retired the z16 clamp: GSI's own building layers keep their native zooms
  // (they only render out of coverage, where our tiles are absent).
  expect(buildingLayers(composed).length).toBeGreaterThan(0);
});
