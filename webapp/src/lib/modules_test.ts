import { beforeEach, expect, it } from "vitest";

import { buildModuleVM, normalizeView } from "./modules";
import { i18n } from "./i18n/i18n.svelte";
import type { Bootstrap, Feature, FeatureCollection } from "./api/types";

function collection(features: Feature[]): FeatureCollection {
  return { type: "FeatureCollection", features };
}

function feature(id: string, properties: Record<string, unknown>): Feature {
  return { type: "Feature", id, properties, geometry: null };
}

function fixtureBootstrap(): Bootstrap {
  const empty = collection([]);
  return {
    buildings: empty,
    buildingSummary: { building_count: 2128, counts: { high: 128, medium: 402, low: 1598 }, mean_score: 31 },
    roads: empty,
    roadSummary: { road_count: 272, total_km: 48.5, high_queue: 24, exposed_buildings: 1236, mean_score: 38 },
    solar: empty,
    solarContext: empty,
    solarSummary: { cell_count: 154, counts: { preferred: 70, conditional: 41, reject: 43 }, shortlist_area_ha: 156.8, annual_ghi_kwh_m2: 1350 },
    hubs: empty,
    corridors: empty,
    delivery: empty,
    jointSummary: {
      resilience_hubs: { count: 30, priority_count: 9, pv_capacity_proxy_kwp: 5120 },
      compound_corridors: { count: 41, road_length_km: 9.7 },
      solar_delivery_cells: { count: 21, area_ha: 47.1 },
    },
    gridScreen: {
      mobara_screen: { spare_own_mw: 30, spare_with_upstream_mw: 20 },
      source_file_last_modified_at: "2026-06-30",
    },
    gsiEvacuation: empty,
    facilities: empty,
    embeddingEvidence: empty,
    embeddingSummary: {
      regions: {
        yokohama: { pixel_count: 51342, valid_pct: 98.4, mean_cosine_change: 0.089, p95_cosine_change: 0.21 },
        mobara: { pixel_count: 30712, valid_pct: 97.2, mean_cosine_change: 0.083, p95_cosine_change: 0.19 },
      },
      overlays: {
        yokohama: { change_image: "a.png", latent_image: "b.png", bounds: [[35, 139], [36, 140]] },
        mobara: { change_image: "c.png", latent_image: "d.png", bounds: [[35, 140], [36, 141]] },
      },
    },
    yokohamaZones: collection([feature("z1", {}), feature("z2", {})]),
    mobaraZones: collection([feature("z3", {})]),
    multiscaleSummary: {},
    facilitySummary: { count: 2, pv_kwp_proxy: 118, served_high_risk_buildings: 37, mean_resilience_score: 78 },
    recommendations: {
      slope: empty,
      roads: empty,
      solar: empty,
      facilities: empty,
      // Server order deliberately not sorted by score: the client must not re-sort.
      hubs: collection([
        feature("h2", { name: "枢纽B", pv_kwp_proxy: 80, served_high_risk_buildings: 5, hub_score: 61 }),
        feature("h1", { name: "枢纽A", pv_kwp_proxy: 120, served_high_risk_buildings: 9, hub_score: 88 }),
      ]),
      corridors: empty,
      delivery: empty,
      constraints: collection([
        feature("c1", { cell_id: "M-12", reject_reasons: ["坡度", "水体"], slope_deg: 21, distance_water_m: 12 }),
      ]),
      embedding: empty,
      embeddingYokohama: collection([
        feature("e1", { cell_id: "Y-3", year_pair: "2023→2024", valid_pixels: 96, support_pct: 98, change_score: 81, cosine_change: 0.3 }),
      ]),
      embeddingMobara: empty,
    },
    meta: {
      status: "ready",
      datasets_ready: 18,
      datasets_total: 18,
      source_groups: 7,
      traceability: "",
      checked_at: "",
      source_catalog: [],
      data_model: "",
      api_version: "v1",
    },
  };
}

beforeEach(() => {
  i18n.lang = "zh";
});

it("falls back to the module default view for unknown views", () => {
  expect(normalizeView("overview", "bogus")).toBe("urban");
  expect(normalizeView("evidence", null)).toBe("yokohama_change");
  expect(normalizeView("development", "constraints")).toBe("constraints");
});

it("renders the overview metrics from the bootstrap payload", () => {
  const vm = buildModuleVM("overview", "urban", fixtureBootstrap());
  expect(vm.metrics.map((m) => m.value)).toEqual(["2,128", "272", "70", "82,054"]);
  expect(vm.metrics[1].note).toBe("48.5 km 韧性分析");
  expect(vm.region).toBe("yokohama");
});

it("keeps the server queue order without re-sorting", () => {
  const vm = buildModuleVM("overview", "urban", fixtureBootstrap());
  expect(vm.queueItems.map((item) => item.title)).toEqual(["枢纽B", "枢纽A"]);
  expect(vm.queueItems[0].score).toBe(61);
});

it("wires every queue item to a score and a detail audit record", () => {
  const vm = buildModuleVM("overview", "urban", fixtureBootstrap());
  for (const item of vm.queueItems) {
    expect(item.scoreAudit.sections.length).toBeGreaterThan(0);
    expect(item.detailAudit.kind).toBe("calculation");
  }
});

it("rebuilds text in the active language", () => {
  i18n.lang = "en";
  const vm = buildModuleVM("overview", "urban", fixtureBootstrap());
  expect(vm.metrics[0].label).toBe("Yokohama buildings");
  expect(vm.queueItems[0].detail).toBe("80 kWp · serves 5 buildings");
});

it("substitutes the TEPCO snapshot into the development method card", () => {
  const vm = buildModuleVM("development", "delivery", fixtureBootstrap());
  expect(vm.methodBody).toContain("2026-06-30");
  expect(vm.methodBody).toContain("30 MW");
  expect(vm.methodBody).toContain("20 MW");
});

it("summarizes constraint queue items by conflict count", () => {
  const vm = buildModuleVM("development", "constraints", fixtureBootstrap());
  expect(vm.queueItems[0].score).toBe(2);
  expect(vm.queueItems[0].scoreLabel).toBe("RULES");
  expect(vm.queueItems[0].detail).toBe("坡度 · 水体");
});

it("switches evidence hero and notes between change and latent views", () => {
  const data = fixtureBootstrap();
  const change = buildModuleVM("evidence", "yokohama_change", data);
  const latent = buildModuleVM("evidence", "yokohama_latent", data);
  expect(change.heroTitle).not.toBe(latent.heroTitle);
  expect(change.mapNote).not.toBe(latent.mapNote);
  expect(change.queueItems[0].scoreLabel).toBe("CHANGE");
});

it("renders the underground module honestly while its cache is absent", () => {
  const unavailable = buildModuleVM("underground", null, fixtureBootstrap(), {
    status: "unavailable",
    manifest: null,
    auditIndex: null,
  });
  expect(unavailable.region).toBe("nihonbashi");
  expect(unavailable.metrics).toEqual([]);
  expect(unavailable.queueItems).toEqual([]);
  expect(unavailable.notice?.title).toBe("尚未下载 3D 资产缓存");
  expect(unavailable.notice?.body).toContain("terrai_spatial fetch underground_utilities");
});

function undergroundManifestFixture() {
  return {
    dataset_id: "plateau_uc24_16_nihonbashi",
    scene_id: "nihonbashi-utilities",
    package_page: "https://www.geospatial.jp/ckan/dataset/plateau-uc24-16",
    retrieved_at: "2026-07-21T12:39:12Z",
    license: "PLATEAU Site Policy",
    license_url: "https://www.mlit.go.jp/plateau/site-policy/",
    vertical_datum: "WGS 84 ellipsoid (not an orthometric survey datum)",
    extent_degrees_and_metres: [139.767, 35.6809, 139.7803, 35.6917, 2.4, 15.8],
    feature_count: 1121,
    resource_count: 3,
    resources: [
      { resource_id: "a", slug: "water-pipe", utility_class: "water_pipe", name: "上水道", feature_count: 162, gltf_count: 9, tileset_url: "/api/v1/assets/external/plateau_uc24_16/assets/water-pipe/tileset.json", bounding_region: [2.4394, 0.6227, 2.4396, 0.6229, 2.4, 15.8] },
      { resource_id: "b", slug: "gas-pipe", utility_class: "gas_pipe", name: "ガス", feature_count: 162, gltf_count: 9, tileset_url: "/api/v1/assets/external/plateau_uc24_16/assets/gas-pipe/tileset.json", bounding_region: [2.4394, 0.6227, 2.4396, 0.6229, 2.4, 15.8] },
      { resource_id: "c", slug: "sewer-manhole", utility_class: "sewer_manhole", name: "下水道マンホール", feature_count: 92, gltf_count: 9, tileset_url: "/api/v1/assets/external/plateau_uc24_16/assets/sewer-manhole/tileset.json", bounding_region: [2.4394, 0.6227, 2.4396, 0.6229, 2.4, 15.8] },
    ],
    limitations: [],
  };
}

it("builds underground metrics and the asset inventory from the manifest", () => {
  const vm = buildModuleVM("underground", "networks", fixtureBootstrap(), {
    status: "ready",
    manifest: undergroundManifestFixture() as never,
    auditIndex: { dataset_id: "x", feature_count: 416, attribute_units: {}, features: [] },
  });
  expect(vm.notice).toBeUndefined();
  expect(vm.metrics.map((m) => m.value)).toEqual(["3", "324", "92", "2026-07-21"]);
  // Networks view lists only network resources, in published order.
  expect(vm.queueItems.map((item) => item.score)).toEqual([162, 162]);
  expect(vm.queueItems[0].scoreLabel).toBe("FEATURES");
  expect(vm.queueItems[0].feature.geometry).toMatchObject({ type: "Polygon" });
  const access = buildModuleVM("underground", "access", fixtureBootstrap(), {
    status: "ready",
    manifest: undergroundManifestFixture() as never,
    auditIndex: { dataset_id: "x", feature_count: 416, attribute_units: {}, features: [] },
  });
  expect(access.queueItems.map((item) => item.score)).toEqual([92]);
});
