import { expect, it, vi } from "vitest";

import { POPUPS, assetUrl, buildAnalyticalLayers, geometryBounds, queuePopup } from "./layers";
import { rgba } from "./style-rules";
import type { Bootstrap, Feature, FeatureCollection } from "../api/types";

const t = (key: string) => key;

function collection(features: Feature[]): FeatureCollection {
  return { type: "FeatureCollection", features };
}

function feature(id: string, properties: Record<string, unknown>, geometry: unknown = null): Feature {
  return { type: "Feature", id, properties, geometry };
}

const empty = collection([]);

function fixture(): Bootstrap {
  return {
    buildings: empty,
    roads: empty,
    solar: empty,
    solarContext: empty,
    hubs: empty,
    corridors: empty,
    delivery: empty,
    gsiEvacuation: empty,
    facilities: empty,
    embeddingEvidence: empty,
    yokohamaZones: empty,
    mobaraZones: empty,
    multiscaleSummary: {},
    buildingSummary: { building_count: 0, counts: { high: 0, medium: 0, low: 0 }, mean_score: 0 },
    roadSummary: { road_count: 0, total_km: 0, high_queue: 0, exposed_buildings: 0, mean_score: 0 },
    solarSummary: { cell_count: 0, counts: { preferred: 0, conditional: 0, reject: 0 }, shortlist_area_ha: 0, annual_ghi_kwh_m2: 0 },
    jointSummary: {
      resilience_hubs: { count: 0, priority_count: 0, pv_capacity_proxy_kwp: 0 },
      compound_corridors: { count: 0, road_length_km: 0 },
      solar_delivery_cells: { count: 0, area_ha: 0 },
    },
    gridScreen: { mobara_screen: { spare_own_mw: 0, spare_with_upstream_mw: 0 }, source_file_last_modified_at: null },
    embeddingSummary: {
      regions: {
        yokohama: { pixel_count: 0, valid_pct: 0, mean_cosine_change: 0, p95_cosine_change: 0 },
        mobara: { pixel_count: 0, valid_pct: 0, mean_cosine_change: 0, p95_cosine_change: 0 },
      },
      overlays: {
        yokohama: { change_image: "data/google/a.png", latent_image: "data/google/b.png", bounds: [[35.44, 139.58], [35.45, 139.59]] },
        mobara: { change_image: "data/google/c.png", latent_image: "data/google/d.png", bounds: [[35.43, 140.27], [35.45, 140.29]] },
      },
    },
    facilitySummary: { count: 0, pv_kwp_proxy: 0, served_high_risk_buildings: 0, mean_resilience_score: 0 },
    recommendations: {
      slope: empty,
      roads: empty,
      solar: empty,
      facilities: empty,
      hubs: empty,
      corridors: empty,
      delivery: empty,
      constraints: empty,
      embedding: empty,
      embeddingYokohama: empty,
      embeddingMobara: empty,
    },
    meta: {
      status: "ready",
      datasets_ready: 0,
      datasets_total: 0,
      source_groups: 0,
      traceability: "",
      checked_at: "",
      source_catalog: [],
      data_model: "",
      api_version: "v1",
    },
  };
}

const handlers = { onFeature: vi.fn() };

it("computes recursive geometry bounds", () => {
  expect(geometryBounds({ type: "Point", coordinates: [139.5, 35.4] })).toEqual([139.5, 35.4, 139.5, 35.4]);
  expect(
    geometryBounds({
      type: "Polygon",
      coordinates: [[[139.5, 35.4], [139.6, 35.5], [139.55, 35.45]]],
    }),
  ).toEqual([139.5, 35.4, 139.6, 35.5]);
  expect(geometryBounds(null)).toBeNull();
});

it("builds the ported layer stack per module and view (bottom to top)", () => {
  const data = fixture();
  expect(buildAnalyticalLayers("overview", "urban", data, "http://a", handlers).map((l) => l.id)).toEqual([
    "overview-buildings",
    "overview-corridors",
    "overview-hubs",
  ]);
  expect(buildAnalyticalLayers("evidence", "yokohama_change", data, "http://a", handlers).map((l) => l.id)).toEqual([
    "evidence-overlay",
    "evidence-zones",
    "evidence-cells",
  ]);
  expect(buildAnalyticalLayers("facilities", "network", data, "http://a", handlers).map((l) => l.id)).toEqual([
    "facilities-corridors",
    "facilities-hubs",
    "facilities-buildings",
    "facilities-markers",
  ]);
  expect(buildAnalyticalLayers("facilities", "official", data, "http://a", handlers).map((l) => l.id)).toEqual([
    "facilities-buildings",
    "facilities-markers",
  ]);
  expect(buildAnalyticalLayers("development", "constraints", data, "http://a", handlers).map((l) => l.id)).toEqual([
    "development-context",
    "development-constraints",
  ]);
});

it("maps the evidence overlay image onto the API asset mount", () => {
  expect(assetUrl("data/google/d.png", "http://x/api/v1/assets")).toBe("http://x/api/v1/assets/google/d.png");
  expect(assetUrl("https://elsewhere/e.png", "http://x/api/v1/assets")).toBe("https://elsewhere/e.png");
  const layers = buildAnalyticalLayers("evidence", "mobara_latent", fixture(), "http://x/api/v1/assets", handlers);
  const bitmap = layers[0] as unknown as { props: { bounds: number[] } };
  // summary bounds are [[south, west], [north, east]]; BitmapLayer wants [w, s, e, n]
  expect(bitmap.props.bounds).toEqual([140.27, 35.43, 140.29, 35.45]);
});

it("opens the same popup from the queue as from the map layer", () => {
  expect(queuePopup("overview", "urban")).toBe(POPUPS.hubOverview);
  expect(queuePopup("evidence", "yokohama_latent")).toBe(POPUPS.embeddingLatent);
  expect(queuePopup("joint", "corridors")).toBe(POPUPS.corridorFocus);
  expect(queuePopup("development", "constraints")).toBe(POPUPS.exclusionCell);
});

it("formats popup values from feature properties", () => {
  const props = { cell_id: "M-1", reject_reasons: ["坡度", "水体"], slope_deg: 12, distance_water_m: 8 };
  const spec = POPUPS.exclusionCell;
  expect(spec.title(props, t as never)).toBe("M-1");
  expect(spec.fields[0].value(props, t as never)).toBe(2);
  expect(spec.fields[1].value(props, t as never)).toBe("坡度、水体");
});

it("converts hex colours with opacity into RGBA data", () => {
  expect(rgba("#d75b4c")).toEqual([215, 91, 76, 255]);
  expect(rgba("#fff", 0.5)).toEqual([255, 255, 255, 128]);
});
