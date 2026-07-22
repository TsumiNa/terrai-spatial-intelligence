/**
 * Pure map configuration: cameras, raster cache ceilings and style
 * composition. The imperative wrapper in ./map.ts is the only consumer.
 *
 * Raster maximum levels are the measured GSI source ceilings (see
 * docs/summary/render-stack-evaluation): slopemap z15, hillshademap z16,
 * imagery z18. The local cache mirrors exactly those levels, so declaring
 * them here means MapLibre overscales instead of requesting tiles that
 * would 404.
 */

import type { StyleSpecification, LayerSpecification, SourceSpecification } from "maplibre-gl";

import type { RegionKey } from "../modules";
import type { BasemapKey } from "../state.svelte";

export const VECTOR_STYLE_URL = "https://gsi-cyberjapan.github.io/gsivectortile-mapbox-gl-js/std.json";

/** MapLibre zooms are 512px-tile zooms: one less than the Leaflet values the
 * old exhibition used with 256px GSI tiles. Nihonbashi's camera frames the
 * UC24-16 manifest extent. */
export const REGION_CAMERAS: Record<RegionKey, { center: [number, number]; zoom: number; bounds: [number, number, number, number] }> = {
  yokohama: { center: [139.5885, 35.4465], zoom: 16, bounds: [139.5835, 35.4426, 139.5935, 35.4504] },
  mobara: { center: [140.2835, 35.445], zoom: 15, bounds: [140.2757, 35.4387, 140.2913, 35.4513] },
  nihonbashi: { center: [139.7737, 35.6863], zoom: 14.4, bounds: [139.767, 35.6809, 139.7803, 35.6917] },
};

export const REGION_KEYS = Object.keys(REGION_CAMERAS) as RegionKey[];

export type RasterKind = Exclude<BasemapKey, "standard">;

export const RASTER_KINDS: RasterKind[] = ["photo", "hillshade", "slope"];

/** The live nationwide GSI raster layers. The zoom bounds are the sources'
 * published ranges; beyond maxzoom MapLibre overscales instead of requesting
 * tiles that would 404. The per-region tile cache died with the demo-scope
 * framing: the vector basemap has always streamed from GSI, and the rasters
 * now follow the same dependency to the same host. */
export const RASTER_SOURCES: Record<RasterKind, { url: string; minzoom: number; maxzoom: number }> = {
  photo: { url: "https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg", minzoom: 2, maxzoom: 18 },
  hillshade: { url: "https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{z}/{x}/{y}.png", minzoom: 2, maxzoom: 16 },
  slope: { url: "https://cyberjapandata.gsi.go.jp/xyz/slopemap/{z}/{x}/{y}.png", minzoom: 3, maxzoom: 15 },
};

export const GSI_ATTRIBUTION =
  '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル (GSI)</a>';

/** The floor fits the whole mainland-Kanto acquisition window (2.3 degrees
 * of longitude) into a 1600 px viewport: 512·2⁹/360 ≈ 728 px per degree.
 * Below their own measured floors the windowed foundation layers say
 * "zoom in" instead of loading, so zooming out degrades nothing but tile
 * detail. */
export const MIN_ZOOM = 9;
export const MAX_ZOOM = 18;
export const MAX_PITCH = 85;

export function rasterId(kind: RasterKind): string {
  return `terrai-${kind}`;
}

/**
 * The vector style's own building layers. Analytical scores live in the
 * exhibition's GeoJSON, not in the vector tiles, so a building-level analysis
 * cannot recolor these — it hides them and draws the analysis color as the
 * only building color instead.
 */
export function vectorBuildingLayerIds(style: StyleSpecification): string[] {
  return style.layers
    .filter((layer) => "source-layer" in layer && layer["source-layer"] === "building")
    .map((layer) => layer.id);
}

/**
 * Append the three nationwide raster basemaps to the GSI vector style, all
 * hidden. The active one is a visibility toggle, so switching basemaps never
 * rebuilds the style and never moves the camera.
 */
export function composeStyle(vectorStyle: StyleSpecification): StyleSpecification {
  const sources: Record<string, SourceSpecification> = { ...vectorStyle.sources };
  const layers: LayerSpecification[] = [...vectorStyle.layers];
  for (const kind of RASTER_KINDS) {
    const id = rasterId(kind);
    const { url, minzoom, maxzoom } = RASTER_SOURCES[kind];
    sources[id] = {
      type: "raster",
      tiles: [url],
      tileSize: 256,
      minzoom,
      maxzoom,
      attribution: GSI_ATTRIBUTION,
    };
    layers.push({ id, type: "raster", source: id, layout: { visibility: "none" } });
  }
  return { ...vectorStyle, sources, layers };
}
