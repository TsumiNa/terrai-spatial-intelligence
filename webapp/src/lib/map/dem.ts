/**
 * GSI elevation-tile transcoding for MapLibre terrain.
 *
 * GSI's 標高PNGタイル encode elevation in their own RGB scheme, which
 * MapLibre's raster-dem source does not speak. A custom tile protocol
 * re-encodes each tile to the Mapbox terrain-RGB scheme on the fly, so the
 * 2.5D surface is driven by GSI's DEM without any server-side processing.
 *
 * GSI scheme:  x = R·2¹⁶ + G·2⁸ + B; elevation = 0.01x m for x < 2²³,
 *              0.01·(x − 2²⁴) m for x > 2²³, and x = 2²³ means "no data"
 *              (sea) — treated as 0 m so the ocean stays flat.
 * Mapbox scheme: elevation = −10000 + 0.1·(R·2¹⁶ + G·2⁸ + B).
 */

import type * as maplibregl from "maplibre-gl";

const GSI_INVALID = 8388608; // 2^23
const GSI_WRAP = 16777216; // 2^24

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

/**
 * Register the transcoding protocol once per page. Tile URLs take the form
 * `gsidem://https://…/dem_png/{z}/{x}/{y}.png`; a GSI 404 (tiles are sparse
 * over open water) yields a flat sea-level tile rather than an error.
 */
export function registerGsiDemProtocol(lib: typeof maplibregl): void {
  lib.addProtocol(GSI_DEM_PROTOCOL, async (params) => {
    const url = params.url.replace(`${GSI_DEM_PROTOCOL}://`, "");
    const response = await fetch(url);
    const size = 256;
    const canvas = new OffscreenCanvas(size, size);
    const context = canvas.getContext("2d");
    if (!context) throw new Error("2d canvas context unavailable for DEM transcoding");
    if (response.ok) {
      const bitmap = await createImageBitmap(await response.blob());
      context.drawImage(bitmap, 0, 0);
    }
    const image = context.getImageData(0, 0, size, size);
    transcodePixels(image.data);
    context.putImageData(image, 0, 0);
    const blob = await canvas.convertToBlob({ type: "image/png" });
    return { data: await blob.arrayBuffer() };
  });
}
