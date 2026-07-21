import { expect, it } from "vitest";

import { applyRowMajor, ecefToGeographic, geographicToEcef } from "./frame";

// The published Nihonbashi handoff's own origin, used as test vectors: the
// scene contract says these two triples are the same point in both systems.
const ORIGIN_GEOGRAPHIC: [number, number, number] = [139.77367254514985, 35.6863162629256, 9.08196062016552];
const ORIGIN_ECEF: [number, number, number] = [-3959803.08579172, 3349413.1893692957, 3699983.177290261];

it("converts the handoff origin between EPSG:4979 and EPSG:4978 exactly", () => {
  const ecef = geographicToEcef(ORIGIN_GEOGRAPHIC);
  expect(ecef[0]).toBeCloseTo(ORIGIN_ECEF[0], 3);
  expect(ecef[1]).toBeCloseTo(ORIGIN_ECEF[1], 3);
  expect(ecef[2]).toBeCloseTo(ORIGIN_ECEF[2], 3);

  const [lon, lat, height] = ecefToGeographic(ORIGIN_ECEF);
  // The handoff's own round-trip tolerance: 1e-8 degrees, 1e-4 metres.
  expect(Math.abs(lon - ORIGIN_GEOGRAPHIC[0])).toBeLessThan(1e-8);
  expect(Math.abs(lat - ORIGIN_GEOGRAPHIC[1])).toBeLessThan(1e-8);
  expect(Math.abs(height - ORIGIN_GEOGRAPHIC[2])).toBeLessThan(1e-4);
});

it("round-trips arbitrary points within the handoff tolerance", () => {
  for (const point of [
    [139.77, 35.686, -12.5],
    [141.3533, 43.0629, 46.6],
    [140.2835, 35.445, 3.2],
  ] as [number, number, number][]) {
    const [lon, lat, height] = ecefToGeographic(geographicToEcef(point));
    expect(Math.abs(lon - point[0])).toBeLessThan(1e-8);
    expect(Math.abs(lat - point[1])).toBeLessThan(1e-8);
    expect(Math.abs(height - point[2])).toBeLessThan(1e-4);
  }
});

it("applies row-major matrices the way the handoff publishes them", () => {
  // Translation by (10, 20, 30) in row-major layout.
  const translate = [1, 0, 0, 10, 0, 1, 0, 20, 0, 0, 1, 30, 0, 0, 0, 1];
  expect(applyRowMajor(translate, [1, 2, 3])).toEqual([11, 22, 33]);
  // 90° rotation about z: x→y.
  const rotate = [0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const [x, y, z] = applyRowMajor(rotate, [1, 0, 0]);
  expect(x).toBeCloseTo(0);
  expect(y).toBeCloseTo(1);
  expect(z).toBeCloseTo(0);
});
