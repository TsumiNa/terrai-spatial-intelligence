import { expect, it } from "vitest";

import { buildAccessOverlay, sectionPlaneConstant } from "./scene";
import type { EvidenceSource } from "./catalog";
import type { LocalFrame } from "./frame";

// A synthetic identity-ish frame around the Sapporo origin so the overlay
// math is exercised without a real handoff matrix.
const frame = {
  origin_geographic_degrees_and_metres: [141.3532530763526, 43.06294861431397, 46.626168690073996],
  world_to_local_matrix_row_major: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  local_to_world_matrix_row_major: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
} as unknown as LocalFrame;

const source = { dataset_id: "osm_sapporo_underground_access" } as EvidenceSource;

it("builds lines for ways and points for entrances, all provenance-tagged", () => {
  const group = buildAccessOverlay(
    [
      { geometry: { type: "LineString", coordinates: [[141.353, 43.062], [141.354, 43.063]] }, properties: {} },
      { geometry: { type: "Point", coordinates: [141.3535, 43.0625] }, properties: {} },
    ],
    frame,
    "access_topology",
    source,
  );
  const types = group.children.map((child) => child.type).sort();
  expect(types).toEqual(["Line", "Points"]);
  for (const child of group.children) {
    expect((child.userData.terrai as { source: EvidenceSource }).source.dataset_id).toBe(source.dataset_id);
  }
});

it("places features without a stated level at the origin reference height", () => {
  // Two identical horizontal positions, one with an explicit height: only the
  // heightless one uses the scene-origin reference; they must differ in z
  // (here z carries the raw ECEF z since the frame matrix is identity).
  const withHeight = buildAccessOverlay(
    [{ geometry: { type: "Point", coordinates: [141.3535, 43.0625, 10] }, properties: {} }],
    frame,
    "access_topology",
    source,
  );
  const withoutHeight = buildAccessOverlay(
    [{ geometry: { type: "Point", coordinates: [141.3535, 43.0625] }, properties: {} }],
    frame,
    "access_topology",
    source,
  );
  const z = (group: typeof withHeight) =>
    (group.children[0] as unknown as { geometry: { getAttribute(name: string): { getZ(i: number): number } } }).geometry
      .getAttribute("position")
      .getZ(0);
  expect(z(withHeight)).not.toBeCloseTo(z(withoutHeight), 1);
});

it("keeps the z section at the requested local height under exaggeration", () => {
  // The Copilot-flagged case: a z cut at 50 local metres with 2x exaggeration
  // must move the world-space plane to 100, not stay at 50.
  expect(sectionPlaneConstant("z", 50, 2)).toBe(100);
  expect(sectionPlaneConstant("z", -12.5, 3)).toBe(-37.5);
  expect(sectionPlaneConstant("z", 50, 1)).toBe(50);
});

it("leaves horizontal sections untouched by vertical exaggeration", () => {
  expect(sectionPlaneConstant("x", 50, 2)).toBe(50);
  expect(sectionPlaneConstant("y", -200, 3)).toBe(-200);
});
