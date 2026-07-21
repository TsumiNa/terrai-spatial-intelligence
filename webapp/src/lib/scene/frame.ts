/**
 * The scene's local frame, exactly as the handoff publishes it.
 *
 * Every transform here comes from the selected scene handoff — the
 * `EPSG:4979 → EPSG:4978 ECEF → local ENU metres` contract — never from a
 * hard-coded origin. The audit chain depends on the inverse: a point picked
 * in the scene resolves back through `local_to_world` and ECEF → geographic
 * to real coordinates against the WGS 84 ellipsoid.
 *
 * Pure array math, deliberately free of Three.js so the round trip is
 * testable against the handoff's own origin vectors.
 */

export interface LocalFrame {
  source_crs: string;
  world_crs: string;
  local_unit: string;
  local_axis_convention: { x: string; y: string; z: string };
  geographic_extent_degrees_and_metres: number[];
  origin_geographic_degrees_and_metres: [number, number, number];
  origin_world_ecef_metres: [number, number, number];
  world_to_local_matrix_row_major: number[];
  local_to_world_matrix_row_major: number[];
  height_reference: string;
  vertical_datum: string;
  orthometric_vertical_datum: string;
  round_trip_tolerance: { longitude_latitude_degrees: number; height_metres: number };
}

/** WGS 84 ellipsoid. */
const A = 6378137;
const F = 1 / 298.257223563;
const E2 = F * (2 - F);

const RAD = Math.PI / 180;

/** EPSG:4979 (lon, lat in degrees; ellipsoid height in metres) → EPSG:4978. */
export function geographicToEcef([lon, lat, height]: [number, number, number]): [number, number, number] {
  const phi = lat * RAD;
  const lambda = lon * RAD;
  const sinPhi = Math.sin(phi);
  const n = A / Math.sqrt(1 - E2 * sinPhi * sinPhi);
  return [
    (n + height) * Math.cos(phi) * Math.cos(lambda),
    (n + height) * Math.cos(phi) * Math.sin(lambda),
    (n * (1 - E2) + height) * sinPhi,
  ];
}

/** EPSG:4978 → EPSG:4979, iteratively (converges to sub-millimetre fast). */
export function ecefToGeographic([x, y, z]: [number, number, number]): [number, number, number] {
  const lambda = Math.atan2(y, x);
  const p = Math.hypot(x, y);
  let phi = Math.atan2(z, p * (1 - E2));
  let n = A;
  let height = 0;
  for (let iteration = 0; iteration < 8; iteration += 1) {
    const sinPhi = Math.sin(phi);
    n = A / Math.sqrt(1 - E2 * sinPhi * sinPhi);
    height = p / Math.cos(phi) - n;
    phi = Math.atan2(z, p * (1 - (E2 * n) / (n + height)));
  }
  return [lambda / RAD, phi / RAD, height];
}

/** Apply a row-major 4×4 to a point (w = 1). */
export function applyRowMajor(matrix: number[], [x, y, z]: [number, number, number]): [number, number, number] {
  return [
    matrix[0] * x + matrix[1] * y + matrix[2] * z + matrix[3],
    matrix[4] * x + matrix[5] * y + matrix[6] * z + matrix[7],
    matrix[8] * x + matrix[9] * y + matrix[10] * z + matrix[11],
  ];
}

/** A picked local point resolved to real coordinates through the handoff. */
export function localToGeographic(frame: LocalFrame, local: [number, number, number]): [number, number, number] {
  return ecefToGeographic(applyRowMajor(frame.local_to_world_matrix_row_major, local));
}

/** A geographic point placed into the scene's local metres. */
export function geographicToLocal(frame: LocalFrame, geographic: [number, number, number]): [number, number, number] {
  return applyRowMajor(frame.world_to_local_matrix_row_major, geographicToEcef(geographic));
}
