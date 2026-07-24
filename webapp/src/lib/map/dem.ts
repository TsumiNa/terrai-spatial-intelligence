/**
 * GSI elevation-tile transcoding for MapLibre terrain and computed hillshade.
 *
 * GSI's 標高PNGタイル encode elevation in their own RGB scheme, which MapLibre's
 * raster-dem source does not speak. A custom tile protocol re-encodes each tile
 * to the Mapbox terrain-RGB scheme on the fly, with **no server-side processing**.
 *
 * It also resolves the source per tile from a resolution chain — DEM1A (1 m,
 * ~z17, LiDAR-surveyed areas), DEM5A (5 m, z15), DEM10B (10 m, z14) — so the
 * finest data available drives both the 2.5D surface and the computed hillshade:
 * sharp where 1 m LiDAR exists, degrading gracefully elsewhere. Where a source
 * only reaches a lower zoom, its parent tile is upsampled by interpolating the
 * **decoded elevations** (interpolating the encoded RGB would corrupt them).
 *
 * GSI scheme:  x = R·2¹⁶ + G·2⁸ + B; elevation = 0.01x m for x < 2²³,
 *              0.01·(x − 2²⁴) m for x > 2²³, and x = 2²³ means "no data"
 *              (sea) — treated as 0 m so the ocean stays flat.
 * Mapbox scheme: elevation = −10000 + 0.1·(R·2¹⁶ + G·2⁸ + B).
 */

import type * as maplibregl from "maplibre-gl";

const GSI_INVALID = 8388608; // 2^23
const GSI_WRAP = 16777216; // 2^24
const TILE = 256;

/** The elevation-tile chain, finest first. `maxNative` is the deepest zoom the
 * source serves real tiles at (its resolution ceiling); deeper requests reuse a
 * parent tile. DEM1A is patchy (LiDAR only), so it is tried only where its
 * resolution beats DEM5A (see the protocol). */
export const DEM_CHAIN: { base: string; maxNative: number }[] = [
  { base: "https://cyberjapandata.gsi.go.jp/xyz/dem1a_png", maxNative: 17 },
  { base: "https://cyberjapandata.gsi.go.jp/xyz/dem5a_png", maxNative: 15 },
  { base: "https://cyberjapandata.gsi.go.jp/xyz/dem_png", maxNative: 14 },
];

/** The deepest zoom the chain serves; MapLibre's raster-dem `maxzoom`. */
export const DEM_MAX_ZOOM = 17;

/** Decode one GSI elevation pixel to metres (0 for the no-data sentinel). */
export function gsiElevation(r: number, g: number, b: number): number {
  const x = r * 65536 + g * 256 + b;
  if (x === GSI_INVALID) return 0;
  return (x > GSI_INVALID ? x - GSI_WRAP : x) * 0.01;
}

/** Encode metres into the Mapbox terrain-RGB triple (0.1 m resolution). */
export function mapboxRgb(elevation: number): [number, number, number] {
  const v = Math.round((elevation + 10000) * 10);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

/** Rewrite a decoded RGBA buffer in place from the GSI to the Mapbox scheme. */
export function transcodePixels(pixels: Uint8ClampedArray): void {
  for (let index = 0; index < pixels.length; index += 4) {
    const [r, g, b] = mapboxRgb(gsiElevation(pixels[index], pixels[index + 1], pixels[index + 2]));
    pixels[index] = r;
    pixels[index + 1] = g;
    pixels[index + 2] = b;
    pixels[index + 3] = 255;
  }
}

export const GSI_DEM_PROTOCOL = "gsidem";

/** Parse the `gsidem://terrai-dem/{z}/{x}/{y}` tile URL. */
function parseZXY(url: string): [number, number, number] {
  const [z, x, y] = url
    .replace(`${GSI_DEM_PROTOCOL}://`, "")
    .split("/")
    .slice(-3)
    .map((part) => Number.parseInt(part, 10));
  return [z, x, y];
}

/** Encode `elev` (a TILE×TILE metres array) into `target` as Mapbox terrain-RGB. */
function encodeMapbox(elev: Float32Array, target: Uint8ClampedArray): void {
  for (let p = 0, o = 0; p < elev.length; p += 1, o += 4) {
    const [r, g, b] = mapboxRgb(elev[p]);
    target[o] = r;
    target[o + 1] = g;
    target[o + 2] = b;
    target[o + 3] = 255;
  }
}

/**
 * Register the DEM protocol once per page. Tile URLs are
 * `gsidem://terrai-dem/{z}/{x}/{y}`; the finest covering source in the chain
 * wins, overscaled from a parent where necessary, and a fully-uncovered tile
 * (open water) yields a flat sea-level tile rather than an error.
 */
export function registerGsiDemProtocol(lib: typeof maplibregl): void {
  lib.addProtocol(GSI_DEM_PROTOCOL, async (params) => {
    const [z, x, y] = parseZXY(params.url);
    const canvas = new OffscreenCanvas(TILE, TILE);
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) throw new Error("2d canvas context unavailable for DEM transcoding");
    const out = context.createImageData(TILE, TILE);

    // DEM1A only pays off past DEM5A's native ceiling; below z16 skip it so the
    // wide view does not pay an extra 404 round-trip per tile in the (common)
    // areas it does not cover.
    const chain = z >= 16 ? DEM_CHAIN : DEM_CHAIN.slice(1);
    let filled = false;

    for (const { base, maxNative } of chain) {
      const srcZ = Math.min(z, maxNative);
      const dz = z - srcZ;
      const sx = x >> dz;
      const sy = y >> dz;
      const response = await fetch(`${base}/${srcZ}/${sx}/${sy}.png`);
      if (!response.ok) continue;
      const bitmap = await createImageBitmap(await response.blob());
      context.clearRect(0, 0, TILE, TILE);
      context.drawImage(bitmap, 0, 0);
      const src = context.getImageData(0, 0, TILE, TILE).data;

      if (dz === 0) {
        // Native resolution: straight transcode.
        const image = context.getImageData(0, 0, TILE, TILE);
        transcodePixels(image.data);
        out.data.set(image.data);
      } else {
        // Overscale: interpolate the *decoded elevations* of the parent tile's
        // sub-region, then re-encode. (Interpolating the encoded RGB is invalid.)
        const elev = new Float32Array(TILE * TILE);
        for (let i = 0, p = 0; p < elev.length; i += 4, p += 1) elev[p] = gsiElevation(src[i], src[i + 1], src[i + 2]);
        const span = TILE >> dz; // the sub-region's size in source pixels
        const offX = (x - (sx << dz)) * span;
        const offY = (y - (sy << dz)) * span;
        const step = span / TILE; // source pixels per output pixel (< 1)
        const sampled = new Float32Array(TILE * TILE);
        for (let oy = 0; oy < TILE; oy += 1) {
          const fy0 = offY + oy * step;
          const y0 = Math.min(TILE - 1, Math.floor(fy0));
          const y1 = Math.min(TILE - 1, y0 + 1);
          const wy = fy0 - y0;
          for (let ox = 0; ox < TILE; ox += 1) {
            const fx0 = offX + ox * step;
            const x0 = Math.min(TILE - 1, Math.floor(fx0));
            const x1 = Math.min(TILE - 1, x0 + 1);
            const wx = fx0 - x0;
            sampled[oy * TILE + ox] =
              elev[y0 * TILE + x0] * (1 - wx) * (1 - wy) +
              elev[y0 * TILE + x1] * wx * (1 - wy) +
              elev[y1 * TILE + x0] * (1 - wx) * wy +
              elev[y1 * TILE + x1] * wx * wy;
          }
        }
        encodeMapbox(sampled, out.data);
      }
      filled = true;
      break;
    }

    if (!filled) {
      // No source covers this tile (open water): flat sea level.
      const [r, g, b] = mapboxRgb(0);
      for (let o = 0; o < out.data.length; o += 4) {
        out.data[o] = r;
        out.data[o + 1] = g;
        out.data[o + 2] = b;
        out.data[o + 3] = 255;
      }
    }

    context.putImageData(out, 0, 0);
    const blob = await canvas.convertToBlob({ type: "image/png" });
    return { data: await blob.arrayBuffer() };
  });
}
