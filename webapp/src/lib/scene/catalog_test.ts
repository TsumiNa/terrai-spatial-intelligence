import { expect, it } from "vitest";

import { matchScene, sceneExtent, type SceneEntry } from "./catalog";

const nihonbashi = {
  scene_id: "nihonbashi-utilities",
  owner_dataset_key: "uc24_16_nihonbashi",
  geographic_extent_degrees_and_metres: [139.767, 35.6809, 139.7803, 35.6917, 2.4, 15.8],
} as SceneEntry;

const sapporo = {
  scene_id: "sapporo-station-underground",
  owner_dataset_key: "uc24_13_sapporo",
  geographic_extent_degrees_and_metres: [141.3496, 43.0549, 141.3569, 43.071, 35.4, 57.9],
} as SceneEntry;

const scenes = [nihonbashi, sapporo];

it("matches a box drawn inside a scene extent", () => {
  expect(matchScene([139.77, 35.685, 139.775, 35.688], scenes)?.scene_id).toBe("nihonbashi-utilities");
  expect(matchScene([141.35, 43.06, 141.355, 43.065], scenes)?.scene_id).toBe("sapporo-station-underground");
});

it("matches a box that merely intersects an edge", () => {
  expect(matchScene([139.78, 35.691, 139.79, 35.7], scenes)?.scene_id).toBe("nihonbashi-utilities");
});

it("returns null where no catalogued scene exists", () => {
  // Yokohama: exhibition territory, no underground scene.
  expect(matchScene([139.5835, 35.4426, 139.5935, 35.4504], scenes)).toBeNull();
});

it("never unions the geographically disjoint scenes", () => {
  // Even an absurd box spanning both cities selects exactly one scene.
  const spanning = matchScene([139.0, 35.0, 142.0, 44.0], scenes);
  expect(spanning?.scene_id).toBe("nihonbashi-utilities");
});

it("exposes the horizontal extent for camera framing", () => {
  expect(sceneExtent(nihonbashi)).toEqual([139.767, 35.6809, 139.7803, 35.6917]);
});
