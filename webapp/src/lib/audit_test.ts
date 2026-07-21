import { expect, it } from "vitest";

import { field, localized, metric, queueScore, text, TYPE_LABELS } from "./audit";

it("keeps the three record kinds distinguishable", () => {
  expect(Object.keys(TYPE_LABELS).sort()).toEqual(["calculation", "model", "raw"]);
});

it("builds a raw record with all four provenance sections", () => {
  const record = metric("metric.annualGhi", "1350", "kWh/m²", "NASA POWER 2001–2020");
  expect(record.kind).toBe("raw");
  expect(record.sections).toHaveLength(4);
  expect(record.sections[0].url).toContain("power.larc.nasa.gov");
  expect(text(record.title, "ja")).toBe("年平均GHI");
});

it("builds a count calculation for count-style metrics", () => {
  const record = metric("metric.highExposure", 128, "栋", "进入优先核验队列");
  expect(record.kind).toBe("calculation");
  expect(record.sections.map((s) => text(s.label, "en"))).toEqual(["Formula", "Substituted inputs", "Data lineage"]);
  expect(text(record.sections[2].value, "zh")).toContain("data/yokohama/building_risk.geojson");
});

it("builds a model record with uncertainty and validation sections", () => {
  const record = metric("metric.embedding10m", "51,342", "像素", "Google AEF · 2023→2024");
  expect(record.kind).toBe("model");
  expect(record.sections.map((s) => text(s.label, "en"))).toEqual([
    "Model / version",
    "Inputs and output",
    "Uncertainty",
    "Validation status",
    "Data source",
  ]);
});

it("substitutes score components into the risk formula", () => {
  const record = field("score.risk", 88, { slope_component: 90, relief_component: 80, low_point_component: 95 });
  expect(record.kind).toBe("calculation");
  expect(text(record.sections[1].value, "zh")).toBe("0.55×90 + 0.30×80 + 0.15×95 = 88");
});

it("distinguishes hub and corridor joint scores by properties", () => {
  const hub = field("score.joint", 77, { hub_score: 77, pv_component: 1, access_component: 2, community_need_component: 3, site_safety_component: 4 });
  expect(text(hub.sections[2].value, "en")).toContain("150 m demand");
  const corridor = field("score.joint", 66, {
    compound_score: 66,
    joint_high_risk_buildings: 4,
    priority_score: 70,
    joint_average_building_risk: 55,
  });
  expect(text(corridor.sections[1].value, "zh")).toContain("0.35×50.0");
});

it("routes queue scores to the module-specific formula", () => {
  expect(text(queueScore("slope", "all", 80, { slope_component: 1, relief_component: 2, low_point_component: 3 }).title, "en")).toBe("Risk score");
  expect(text(queueScore("development", "constraints", 2, { reject_reasons: ["坡度", "水体"] }).title, "en")).toBe("Conflict count");
  expect(text(queueScore("overview", "renewable", 70, {}).title, "en")).toBe("Delivery score");
});

it("falls back to a raw property record for unknown fields", () => {
  const record = field("field.property", "值");
  expect(record.kind).toBe("raw");
  expect(record.sections).toHaveLength(4);
});

it("resolves localized titles from the message catalogs", () => {
  const title = localized("metric.spareCapacity");
  expect(title.zh).toBe("上位约束后空容量");
  expect(title.ja).toBe("上位系統考慮後空容量");
  expect(title.en).toBe("Spare capacity after upstream constraints");
});

it("keeps the TEPCO snapshot date in the spare-capacity record", () => {
  const record = metric("metric.spareCapacity", 20, "MW", "自身 30 MW", { snapshot: "2026-06-30" });
  expect(record.kind).toBe("raw");
  expect(text(record.sections[2].value, "zh")).toContain("2026-06-30");
  const missing = metric("metric.spareCapacity", 20, "MW", "自身 30 MW", {});
  expect(text(missing.sections[2].value, "zh")).toBe("source date unavailable");
});
