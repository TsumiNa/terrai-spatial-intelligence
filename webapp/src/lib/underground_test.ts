import { expect, it } from "vitest";

import {
  ACCESS_CLASSES,
  NETWORK_CLASSES,
  UNDERGROUND_STYLE,
  familyResources,
  materialLabel,
  regionToDegrees,
  resourceFamily,
  summarizeAsset,
  type UndergroundFeature,
  type UndergroundManifest,
} from "./underground";

function feature(overrides: Partial<UndergroundFeature> & { attributes?: Record<string, string> }): UndergroundFeature {
  return {
    record_id: "r:asset:0:0",
    source_feature_id: "{id}",
    source_resource_id: "res-1",
    source_asset: "data/a.gltf",
    utility_class: "water_pipe",
    attributes: {},
    ...overrides,
  };
}

it("splits utility classes into the two published families", () => {
  for (const cls of NETWORK_CLASSES) expect(resourceFamily(cls)).toBe("networks");
  for (const cls of ACCESS_CLASSES) expect(resourceFamily(cls)).toBe("access");
});

it("colours every published utility class from the palette", () => {
  for (const cls of [...NETWORK_CLASSES, ...ACCESS_CLASSES]) {
    expect(UNDERGROUND_STYLE.classColors[cls], cls).toMatch(/^#/);
  }
});

it("labels material codes from the i-UR codelist and leaves unknown codes as codes", () => {
  expect(materialLabel("109")).toBe("109 硬質塩化ビニル（厚肉管）：VP");
  expect(materialLabel("99")).toBe("99 不明");
  expect(materialLabel("777")).toBe("777");
});

it("converts 3D Tiles regions from radians to degrees", () => {
  const [west, south, east, north] = regionToDegrees([Math.PI / 6, Math.PI / 12, Math.PI / 3, Math.PI / 4, 0, 10]);
  expect(west).toBeCloseTo(30);
  expect(south).toBeCloseTo(15);
  expect(east).toBeCloseTo(60);
  expect(north).toBeCloseTo(45);
});

it("summarizes an asset without inventing missing attributes", () => {
  const summary = summarizeAsset([
    feature({ attributes: { "uro:minDepth": "1.2", "uro:maxDepth": "2.4", "uro:material": "109", "uro:mesureType": "2", "gml:name": "上水道管" } }),
    feature({ attributes: { "uro:minDepth": "-0.5", "uro:maxDepth": "3.1", "uro:material": "107", "uro:mesureType": "2", "gml:name": "上水道管" } }),
    // A manhole-style feature that publishes none of the depth attributes.
    feature({ utility_class: "sewer_manhole", attributes: { "gml:name": "マンホール" } }),
  ]);
  expect(summary.depthRange).toEqual([-0.5, 3.1]);
  expect(summary.materialCodes).toEqual(["107", "109"]);
  expect(summary.mesureTypes).toEqual(["2"]);
  expect(summary.names).toEqual(["マンホール", "上水道管"]);
});

it("summarizes an all-unknown asset as empty, not zero", () => {
  const summary = summarizeAsset([feature({ attributes: {} })]);
  expect(summary.depthRange).toBeNull();
  expect(summary.diameters).toEqual([]);
  expect(summary.materialCodes).toEqual([]);
  expect(summary.mesureTypes).toEqual([]);
});

it("filters manifest resources by family in published order", () => {
  const manifest = {
    resources: [
      { slug: "water-pipe", utility_class: "water_pipe" },
      { slug: "sewer-manhole", utility_class: "sewer_manhole" },
      { slug: "gas-pipe", utility_class: "gas_pipe" },
    ],
  } as unknown as UndergroundManifest;
  expect(familyResources(manifest, "networks").map((r) => r.slug)).toEqual(["water-pipe", "gas-pipe"]);
  expect(familyResources(manifest, "access").map((r) => r.slug)).toEqual(["sewer-manhole"]);
});
