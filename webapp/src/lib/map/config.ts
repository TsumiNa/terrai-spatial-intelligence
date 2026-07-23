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
import { palette } from "../theme";
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
export const GSI_ATTRIBUTION =
  '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル (GSI)</a>';

export const RASTER_SOURCES: Record<RasterKind, { url: string; minzoom: number; maxzoom: number; attribution: string }> = {
  // seamlessphoto blends third-party imagery; GSI's tile catalog requires
  // their credits alongside the GSI one when the layer is shown.
  photo: {
    url: "https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg",
    minzoom: 2,
    maxzoom: 18,
    attribution: `${GSI_ATTRIBUTION}・Landsat 8（courtesy USGS/NASA）・GEBCO・GRUS画像（© Axelspace）`,
  },
  hillshade: { url: "https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{z}/{x}/{y}.png", minzoom: 2, maxzoom: 16, attribution: GSI_ATTRIBUTION },
  slope: { url: "https://cyberjapandata.gsi.go.jp/xyz/slopemap/{z}/{x}/{y}.png", minzoom: 3, maxzoom: 15, attribution: GSI_ATTRIBUTION },
};

/** The floor shows the mainland-Kanto acquisition window with room around
 * it (512·2⁷/360 ≈ 182 px per degree, so the 2.3-degree window is ~420 px):
 * one view for orientation, one drag to anywhere in the coverage. Below
 * their own measured floors the windowed foundation layers say "zoom in"
 * instead of loading, so zooming out degrades nothing but tile detail. */
/** The 2.5D surface under the 起伏 basemap: GSI's 10 m DEM (dem_png, z1–14)
 * through the transcoding protocol in ./dem.ts. The exaggeration is a
 * legibility choice for observation, not survey scale, and the pitch is the
 * angle the surface reads at without hiding the far half of the viewport. */
export const TERRAIN_SOURCE_ID = "terrai-terrain-dem";
export const TERRAIN_TILE_URL = "gsidem://https://cyberjapandata.gsi.go.jp/xyz/dem_png/{z}/{x}/{y}.png";
export const TERRAIN_MAXZOOM = 14;
export const TERRAIN_EXAGGERATION = 1.5;
export const TERRAIN_PITCH = 55;

export const MIN_ZOOM = 7;
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
 * The GSI standard style switches to large-scale edge-only cartography at
 * z17 and runs out of layers entirely at z18 (its tiles cap at z16), which
 * read as a sudden wireframe and then a blank map. Freeze the z16
 * cartography instead: drop the z17+ variant layers and let every layer
 * that reached z17 overscale to the camera ceiling. Mid-zoom styling
 * (including hand-offs at z14/z16) is GSI's design and stays untouched.
 */
export function freezeHighZoomCartography(style: StyleSpecification): StyleSpecification {
  const layers = style.layers
    .filter((layer) => (layer.minzoom ?? 0) < 17)
    .map((layer) => {
      if (layer.maxzoom !== undefined && layer.maxzoom >= 17) {
        const { maxzoom: _dropped, ...rest } = layer;
        return rest as LayerSpecification;
      }
      return layer;
    });
  return { ...style, layers };
}

/**
 * The GSI style paints its cartographic buildings in oranges that collide
 * with the analysis palette, and whether an orange building was data or
 * cartography could only be settled by clicking it. Neutralize the basemap's
 * buildings instead: any colored building on this map is analysis data, and
 * every gray one is basemap texture. Reuses existing palette neutrals.
 */
export function neutralizeBasemapBuildings(style: StyleSpecification): StyleSpecification {
  const layers = style.layers.map((layer): LayerSpecification => {
    if (!("source-layer" in layer) || layer["source-layer"] !== "building") return layer;
    if (layer.type === "fill") {
      return { ...layer, paint: { ...layer.paint, "fill-color": palette.line, "fill-outline-color": palette.gray } };
    }
    if (layer.type === "line") {
      return { ...layer, paint: { ...layer.paint, "line-color": palette.gray } };
    }
    return layer;
  });
  return { ...style, layers };
}

/** Past this zoom the standard basemap's building texture yields to the
 * windowed OSM building objects (the measured floor from the OSM detail
 * plan: a Shinjuku-scale z16 window is 1,857 buildings / 1.1 MB raw). */
export const BASEMAP_DETAIL_HANDOVER_ZOOM = 16;

/**
 * Clamp the basemap's building layers to the handover zoom so exactly one
 * building inventory shows at any zoom: GSI's cartographic texture below
 * it, the clickable OSM data objects at and above it.
 */
export function clampBasemapBuildings(style: StyleSpecification, handover: number = BASEMAP_DETAIL_HANDOVER_ZOOM): StyleSpecification {
  const layers = style.layers.map((layer): LayerSpecification => {
    if (!("source-layer" in layer) || layer["source-layer"] !== "building") return layer;
    return { ...layer, maxzoom: Math.min(layer.maxzoom ?? 24, handover) };
  });
  return { ...style, layers };
}

/**
 * Append the three nationwide raster basemaps to the GSI vector style, all
 * hidden. The active one is a visibility toggle, so switching basemaps never
 * rebuilds the style and never moves the camera.
 */
export function composeStyle(vectorStyle: StyleSpecification): StyleSpecification {
  const frozen = clampBasemapBuildings(neutralizeBasemapBuildings(freezeHighZoomCartography(vectorStyle)));
  const sources: Record<string, SourceSpecification> = { ...frozen.sources };
  const layers: LayerSpecification[] = [...frozen.layers];
  sources[TERRAIN_SOURCE_ID] = {
    type: "raster-dem",
    tiles: [TERRAIN_TILE_URL],
    tileSize: 256,
    maxzoom: TERRAIN_MAXZOOM,
    encoding: "mapbox",
    attribution: GSI_ATTRIBUTION,
  };
  for (const kind of RASTER_KINDS) {
    const id = rasterId(kind);
    const { url, minzoom, maxzoom, attribution } = RASTER_SOURCES[kind];
    sources[id] = {
      type: "raster",
      tiles: [url],
      tileSize: 256,
      minzoom,
      maxzoom,
      attribution,
    };
    layers.push({ id, type: "raster", source: id, layout: { visibility: "none" } });
  }
  return { ...frozen, sources, layers };
}
