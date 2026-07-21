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
 * old exhibition used with 256px GSI tiles. */
export const REGION_CAMERAS: Record<RegionKey, { center: [number, number]; zoom: number; bounds: [number, number, number, number] }> = {
  yokohama: { center: [139.5885, 35.4465], zoom: 16, bounds: [139.5835, 35.4426, 139.5935, 35.4504] },
  mobara: { center: [140.2835, 35.445], zoom: 15, bounds: [140.2757, 35.4387, 140.2913, 35.4513] },
};

export const REGION_KEYS = Object.keys(REGION_CAMERAS) as RegionKey[];

export type RasterKind = Exclude<BasemapKey, "standard">;

export const RASTER_KINDS: RasterKind[] = ["photo", "hillshade", "slope"];

/** extension + real maximum tile level per cached raster layer. */
export const RASTER_CEILINGS: Record<RasterKind, { extension: "jpg" | "png"; maxzoom: number }> = {
  photo: { extension: "jpg", maxzoom: 18 },
  hillshade: { extension: "png", maxzoom: 16 },
  slope: { extension: "png", maxzoom: 15 },
};

export const GSI_ATTRIBUTION =
  '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル (GSI)</a>';

export const MIN_ZOOM = 14;
export const MAX_ZOOM = 18;
export const MAX_PITCH = 85;

export function rasterId(region: RegionKey, kind: RasterKind): string {
  return `terrai-${region}-${kind}`;
}

export function rasterTileUrl(assetBase: string, region: RegionKey, kind: RasterKind): string {
  const { extension } = RASTER_CEILINGS[kind];
  return `${assetBase}/tiles/${region}/${kind}/{z}/{x}-{y}.${extension}`;
}

/**
 * Append the six cached raster basemaps (2 regions × 3 kinds) to the GSI
 * vector style, all hidden. The active one is a visibility toggle, so
 * switching basemaps never rebuilds the style and never moves the camera.
 */
export function composeStyle(vectorStyle: StyleSpecification, assetBase: string): StyleSpecification {
  const sources: Record<string, SourceSpecification> = { ...vectorStyle.sources };
  const layers: LayerSpecification[] = [...vectorStyle.layers];
  for (const region of REGION_KEYS) {
    for (const kind of RASTER_KINDS) {
      const id = rasterId(region, kind);
      sources[id] = {
        type: "raster",
        tiles: [rasterTileUrl(assetBase, region, kind)],
        tileSize: 256,
        minzoom: 15,
        maxzoom: RASTER_CEILINGS[kind].maxzoom,
        bounds: REGION_CAMERAS[region].bounds,
        attribution: GSI_ATTRIBUTION,
      };
      layers.push({ id, type: "raster", source: id, layout: { visibility: "none" } });
    }
  }
  return { ...vectorStyle, sources, layers };
}
