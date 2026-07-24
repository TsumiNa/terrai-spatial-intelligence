/**
 * The merged building tiles only cover mainland Kanto (the 180 2次メッシュ the
 * FGD acquisition kept — see data/fgd/kanto_buildings/coverage.json). When the
 * user pans the map to building zoom over an area we do not cover, the wide view
 * would otherwise read as empty; instead the map falls back to GSI's own building
 * texture there and shows an "out of service" badge. This module answers the one
 * question that drives that: does the current viewport touch our coverage?
 *
 * A 2次メッシュ (JIS secondary grid) cell is 5′ lat × 7.5′ lon; its 6-digit code
 * decodes to the SW corner (the inverse of scripts/fetch_fgd_kanto_buildings.py's
 * `mesh_cell`). The test is a cheap bbox-overlap sweep over the ~180 cells.
 */

const MESH_LAT_DEG = 1 / 12;
const MESH_LON_DEG = 1 / 8;

/** [west, south, east, north] in degrees. */
export type Bounds = [number, number, number, number];

/** The degree bounds of a 6-digit 2次メッシュ code. */
export function meshCell(code: string): Bounds {
  const latFirst = Number(code.slice(0, 2)) / 1.5;
  const lonFirst = Number(code.slice(2, 4)) + 100;
  const south = latFirst + Number(code[4]) * MESH_LAT_DEG;
  const west = lonFirst + Number(code[5]) * MESH_LON_DEG;
  return [west, south, west + MESH_LON_DEG, south + MESH_LAT_DEG];
}

/** Precomputed cell bounds for the covered meshes. */
export interface CoverageIndex {
  cells: Bounds[];
}

export function buildCoverageIndex(meshes: string[]): CoverageIndex {
  return { cells: meshes.map(meshCell) };
}

/** Whether the viewport bounds overlap any covered mesh cell. */
export function viewportInCoverage(bounds: Bounds, index: CoverageIndex): boolean {
  const [west, south, east, north] = bounds;
  for (const [cellWest, cellSouth, cellEast, cellNorth] of index.cells) {
    if (cellEast >= west && cellWest <= east && cellNorth >= south && cellSouth <= north) return true;
  }
  return false;
}

/**
 * Fetch and index the served coverage footprint. Returns ``null`` on any failure
 * so the caller degrades to "always in coverage" (tiles shown everywhere) rather
 * than falsely flagging out-of-service.
 */
export async function loadCoverage(url: string): Promise<CoverageIndex | null> {
  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    const data = (await response.json()) as { meshes?: unknown };
    if (!Array.isArray(data.meshes) || data.meshes.some((m) => typeof m !== "string")) return null;
    return buildCoverageIndex(data.meshes as string[]);
  } catch {
    return null;
  }
}
