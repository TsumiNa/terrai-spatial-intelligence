import { expect, it } from "vitest";

import { gsiElevation, mapboxRgb, transcodePixels } from "./dem";

it("decodes the GSI elevation scheme, including the sentinel and negatives", () => {
  expect(gsiElevation(0, 0, 0)).toBe(0);
  expect(gsiElevation(0, 15, 24)).toBeCloseTo(38.64, 2); // 0x0F18 = 3864 → 38.64 m
  expect(gsiElevation(128, 0, 0)).toBe(0); // 2^23: no data reads as sea level
  expect(gsiElevation(255, 255, 255)).toBeCloseTo(-0.01, 2); // wrap-around negative
});

it("round-trips an elevation through the Mapbox scheme at 0.1 m resolution", () => {
  const [r, g, b] = mapboxRgb(38.6);
  expect(-10000 + 0.1 * (r * 65536 + g * 256 + b)).toBeCloseTo(38.6, 1);
  const [zr, zg, zb] = mapboxRgb(0);
  expect(-10000 + 0.1 * (zr * 65536 + zg * 256 + zb)).toBeCloseTo(0, 1);
});

it("transcodes a pixel buffer in place and forces it opaque", () => {
  // one GSI pixel at 38.64 m, one no-data pixel, both half-transparent
  const pixels = new Uint8ClampedArray([0, 15, 24, 128, 128, 0, 0, 128]);
  transcodePixels(pixels);
  const first = -10000 + 0.1 * (pixels[0] * 65536 + pixels[1] * 256 + pixels[2]);
  const second = -10000 + 0.1 * (pixels[4] * 65536 + pixels[5] * 256 + pixels[6]);
  expect(first).toBeCloseTo(38.6, 1);
  expect(second).toBeCloseTo(0, 1);
  expect(pixels[3]).toBe(255);
  expect(pixels[7]).toBe(255);
});
