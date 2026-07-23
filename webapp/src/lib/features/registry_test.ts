import { expect, it } from "vitest";

import { FOUNDATION_LAYERS, foundationLayer, renderableFoundationLayers } from "./registry";

/** The on-demand foundation feature collections the service exposes. The 3D
 *  asset manifests (`uc24_16_nihonbashi`, `uc24_13_sapporo`,
 *  `kunijibanBoreholes`) are manifests, not feature collections, and no
 *  bootstrap analytical dataset may drift into the overlay registry — a
 *  foundation layer is evidence shown, never evidence scored. */
const ON_DEMAND_FEATURE_KEYS = [
  "landClassification50k",
  "floodHistory",
  "landHistory",
  "landslideWarning",
  "multistageFlood",
  "publishedLandPrice",
  "embankmentRegulation",
  "railway",
  "landUseMesh",
  "prefecturalLandPrice",
  "osmBuildings",
  "osmSapporoUndergroundAccess",
];

it("registers exactly the on-demand foundation feature collections", () => {
  expect(FOUNDATION_LAYERS.map((entry) => entry.key).sort()).toEqual([...ON_DEMAND_FEATURE_KEYS].sort());
});

it("refuses to render a layer whose registry entry lacks attribution", () => {
  expect(renderableFoundationLayers()).toHaveLength(FOUNDATION_LAYERS.length);

  const broken = [...FOUNDATION_LAYERS, { ...FOUNDATION_LAYERS[0], key: "broken", attribution: "  " }];
  const rendered = renderableFoundationLayers(broken);
  expect(rendered.some((entry) => entry.key === "broken")).toBe(false);
});

it("every entry states its licence, source timestamp and trilingual limitations", () => {
  for (const entry of FOUNDATION_LAYERS) {
    expect(entry.license.length, entry.key).toBeGreaterThan(0);
    expect(entry.sourceUpdatedAt.length, entry.key).toBeGreaterThan(0);
    expect(entry.limitations.zh.length, entry.key).toBeGreaterThan(0);
    expect(entry.limitations.ja.length, entry.key).toBeGreaterThan(0);
    expect(entry.limitations.en.length, entry.key).toBeGreaterThan(0);
    expect(entry.name.startsWith("fl."), entry.key).toBe(true);
  }
});

it("declares ordered extents and a floor within the map's zoom range", () => {
  for (const entry of FOUNDATION_LAYERS) {
    expect(entry.minZoom).toBeGreaterThanOrEqual(14);
    expect(entry.minZoom).toBeLessThanOrEqual(18);
    for (const [west, south, east, north] of entry.extents) {
      expect(west).toBeLessThan(east);
      expect(south).toBeLessThan(north);
    }
  }
});

it("looks a layer up by key", () => {
  expect(foundationLayer("railway")?.geometry).toBe("line");
  expect(foundationLayer("nope")).toBeUndefined();
});
