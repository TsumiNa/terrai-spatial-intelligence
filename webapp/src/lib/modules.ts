/**
 * Per-module view models for the exhibition panels.
 *
 * Port of the panel halves of the eight `render*` functions in
 * `frontend/app.js`: header, status chips, metrics, tabs, legend, queue,
 * method card and map note. Map layers stay out until the deck.gl stage.
 * All text is resolved through `i18n.t` at build time, so a view model is a
 * pure function of (module, view, data, language).
 */

import { field, metric, queueScore, type AuditRecord, type ModuleName } from "./audit";
import { i18n } from "./i18n/i18n.svelte";
import type { Bootstrap, Feature } from "./api/types";

export const colors = {
  red: "#d75b4c",
  amber: "#e2a43c",
  green: "#1f7a58",
  lime: "#8fc85a",
  blue: "#397ca3",
  forest: "#164d3b",
  gray: "#a9b5af",
} as const;

export type RegionKey = "yokohama" | "mobara";

export const MODULES: ModuleName[] = [
  "overview",
  "evidence",
  "slope",
  "roads",
  "facilities",
  "solar",
  "joint",
  "development",
];

export const MODULE_VIEWS: Record<ModuleName, string[]> = {
  overview: ["urban", "renewable"],
  evidence: ["yokohama_change", "yokohama_latent", "mobara_change", "mobara_latent"],
  slope: ["all", "high"],
  roads: ["all", "high"],
  facilities: ["official", "network"],
  solar: ["all", "preferred"],
  joint: ["hubs", "corridors"],
  development: ["delivery", "constraints"],
};

export function normalizeView(module: ModuleName, view: string | null): string {
  const views = MODULE_VIEWS[module];
  return view && views.includes(view) ? view : views[0];
}

export interface FormulaVM {
  parts: { label: string; strong?: boolean }[];
  ops: string[];
}

export interface StatusChipVM {
  kind: "observed" | "proxy" | "pending";
  label: string;
  detail?: string;
}

export interface MetricVM {
  label: string;
  value: string;
  unit: string;
  note: string;
  color: string;
  audit: AuditRecord;
}

export interface QueueItemVM {
  title: string;
  detail: string;
  score: string | number;
  scoreLabel: string;
  color: string;
  scoreAudit: AuditRecord;
  detailAudit: AuditRecord;
  /** The underlying server-ranked feature, for queue-to-map framing. */
  feature: Feature;
}

export interface ModuleVM {
  region: RegionKey;
  eyebrow: string;
  title: string;
  kicker: string;
  heroTitle: string;
  description: string;
  formula: FormulaVM | null;
  chips: StatusChipVM[];
  metrics: MetricVM[];
  tabs: { view: string; label: string }[];
  activeView: string;
  legend: { label: string; color: string }[];
  queueEyebrow: string;
  queueTitle: string;
  queueExplanation: string;
  queueCount: number;
  queueItems: QueueItemVM[];
  methodTitle: string;
  methodBody: string;
  mapNote: string;
}

type P = Record<string, any>;

const QUEUE_LIMIT = 18;

const defaultChips = (): StatusChipVM[] => [
  { kind: "observed", label: i18n.t("status.dataChecked") },
  { kind: "proxy", label: i18n.t("status.traceable") },
];

function queueItems(
  module: ModuleName,
  view: string,
  features: Feature[],
  formatter: (props: P) => { title: string; detail: string; score: string | number; color: string; scoreLabel?: string },
): QueueItemVM[] {
  return features.slice(0, QUEUE_LIMIT).map((feature) => {
    const props = feature.properties as P;
    const item = formatter(props);
    return {
      title: item.title,
      detail: item.detail,
      score: item.score,
      scoreLabel: item.scoreLabel ?? "SCORE",
      color: item.color,
      scoreAudit: queueScore(module, view, item.score, props),
      detailAudit: field("field.queueDetail", item.detail, props),
      feature,
    };
  });
}

export function buildModuleVM(module: ModuleName, requestedView: string | null, data: Bootstrap): ModuleVM {
  const view = normalizeView(module, requestedView);
  const t = i18n.t.bind(i18n);

  if (module === "overview") {
    const isUrban = view === "urban";
    const base = {
      region: (isUrban ? "yokohama" : "mobara") as RegionKey,
      eyebrow: t("overview.eyebrow"),
      title: t("overview.title"),
      kicker: "PORTFOLIO OPPORTUNITY",
      heroTitle: t("overview.heroTitle"),
      description: t("overview.description"),
      formula: {
        parts: [
          { label: t("overview.formulaDiscovery") },
          { label: t("overview.formulaEvidence") },
          { label: t("overview.formulaDiligence"), strong: true },
        ],
        ops: ["→", "→"],
      },
      chips: defaultChips(),
      metrics: [
        {
          label: t("metric.yokohamaBuildings"),
          value: data.buildingSummary.building_count.toLocaleString(),
          unit: t("unit.buildings"),
          note: t("metric.yokohamaBuildingsNote"),
          color: colors.red,
          audit: metric("metric.yokohamaBuildings", data.buildingSummary.building_count.toLocaleString(), t("unit.buildings"), t("metric.yokohamaBuildingsNote")),
        },
        {
          label: t("metric.yokohamaRoads"),
          value: String(data.roadSummary.road_count),
          unit: t("unit.segments"),
          note: t("metric.yokohamaRoadsNote", { km: data.roadSummary.total_km }),
          color: colors.amber,
          audit: metric("metric.yokohamaRoads", data.roadSummary.road_count, t("unit.segments"), t("metric.yokohamaRoadsNote", { km: data.roadSummary.total_km })),
        },
        {
          label: t("metric.mobaraSolar"),
          value: String(data.solarSummary.counts.preferred),
          unit: t("unit.cells"),
          note: t("metric.mobaraSolarNote", { ha: data.solarSummary.shortlist_area_ha }),
          color: colors.green,
          audit: metric("metric.mobaraSolar", data.solarSummary.counts.preferred, t("unit.cells"), t("metric.mobaraSolarNote", { ha: data.solarSummary.shortlist_area_ha })),
        },
        {
          label: t("metric.embedding10m"),
          value: (data.embeddingSummary.regions.yokohama.pixel_count + data.embeddingSummary.regions.mobara.pixel_count).toLocaleString(),
          unit: t("unit.pixels"),
          note: t("metric.embedding10mNote"),
          color: colors.blue,
          audit: metric(
            "metric.embedding10m",
            (data.embeddingSummary.regions.yokohama.pixel_count + data.embeddingSummary.regions.mobara.pixel_count).toLocaleString(),
            t("unit.pixels"),
            t("metric.embedding10mNote"),
          ),
        },
      ],
      tabs: [
        { view: "urban", label: t("overview.tabUrban") },
        { view: "renewable", label: t("overview.tabRenewable") },
      ],
      activeView: view,
    };
    if (isUrban) {
      const items = data.recommendations.hubs.features;
      return {
        ...base,
        legend: [
          { label: t("legend.hubs"), color: colors.lime },
          { label: t("legend.corridors"), color: colors.red },
          { label: t("legend.highExposureBuildings"), color: "#7b342b" },
        ],
        queueEyebrow: "YOKOHAMA URBAN RESILIENCE",
        queueTitle: t("queueTitle.overviewUrban"),
        queueExplanation: t("queueExpl.overviewUrban"),
        queueCount: items.length,
        queueItems: queueItems(module, view, items, (props) => ({
          color: colors.green,
          title: String(props.name),
          detail: t("queueDetail.hub", { kwp: props.pv_kwp_proxy, served: props.served_high_risk_buildings }),
          score: props.hub_score,
        })),
        methodTitle: t("methodCard.overviewUrbanTitle"),
        methodBody: t("methodCard.overviewUrbanBody"),
        mapNote: t("mapNote.overviewUrban"),
      };
    }
    const items = data.recommendations.delivery.features;
    return {
      ...base,
      legend: [
        { label: t("legend.highDelivery"), color: colors.blue },
        { label: t("legend.candidate"), color: colors.green },
        { label: t("legend.transmission"), color: "#8e5eaa" },
      ],
      queueEyebrow: "MOBARA SOLAR DEVELOPMENT",
      queueTitle: t("queueTitle.overviewRenewable"),
      queueExplanation: t("queueExpl.overviewRenewable"),
      queueCount: items.length,
      queueItems: queueItems(module, view, items, (props) => ({
        color: props.delivery_band === "priority" ? colors.blue : colors.green,
        title: t("common.cellTitle", { id: props.cell_id }),
        detail: t("queueDetail.solarCell", { ha: props.area_ha, slope: props.slope_deg, road: props.distance_road_m }),
        score: props.delivery_score,
      })),
      methodTitle: t("methodCard.overviewRenewableTitle"),
      methodBody: t("methodCard.overviewRenewableBody"),
      mapNote: t("mapNote.overviewRenewable"),
    };
  }

  if (module === "evidence") {
    const [region, mode] = view.split("_") as [RegionKey, "change" | "latent"];
    const summary = data.embeddingSummary.regions[region];
    const zones = (region === "yokohama" ? data.yokohamaZones : data.mobaraZones).features;
    const evidence =
      region === "yokohama" ? data.recommendations.embeddingYokohama.features : data.recommendations.embeddingMobara.features;
    return {
      region,
      eyebrow: t("nav.evidence"),
      title: t("evidence.title"),
      kicker: "EVIDENCE & RELIABILITY",
      heroTitle: mode === "change" ? t("evidence.heroTitleChange") : t("evidence.heroTitleLatent"),
      description: t("evidence.description"),
      formula: {
        parts: [
          { label: t("evidence.formulaSource") },
          { label: t("evidence.formulaCalc") },
          { label: t("evidence.formulaLimits") },
          { label: t("evidence.formulaResult"), strong: true },
        ],
        ops: ["→", "→", "→"],
      },
      chips: [
        { kind: "observed", label: t("chip.satelliteEmbedding"), detail: t("chip.satelliteEmbeddingDetail") },
        { kind: "proxy", label: t("chip.decisionZones"), detail: t("chip.heuristicAggregation") },
      ],
      metrics: [
        {
          label: t("metric.validPixels"),
          value: summary.pixel_count.toLocaleString(),
          unit: t("unit.count"),
          note: t("metric.validPixelsNote", { pct: summary.valid_pct }),
          color: colors.forest,
          audit: metric("metric.validPixels", summary.pixel_count.toLocaleString(), t("unit.count"), t("metric.validPixelsNote", { pct: summary.valid_pct })),
        },
        {
          label: t("metric.meanCosine"),
          value: String(summary.mean_cosine_change),
          unit: "",
          note: t("metric.meanCosineNote", { value: summary.p95_cosine_change }),
          color: colors.amber,
          audit: metric("metric.meanCosine", summary.mean_cosine_change, "", t("metric.meanCosineNote", { value: summary.p95_cosine_change })),
        },
        {
          label: t("metric.zones"),
          value: String(zones.length),
          unit: t("unit.zones"),
          note: t("metric.zonesNote"),
          color: colors.green,
          audit: metric("metric.zones", zones.length, t("unit.zones"), t("metric.zonesNote")),
        },
        {
          label: t("metric.paidDeps"),
          value: "0",
          unit: t("unit.items"),
          note: t("metric.paidDepsNote"),
          color: colors.green,
          audit: metric("metric.paidDeps", 0, t("unit.items"), t("metric.paidDepsNote")),
        },
      ],
      tabs: [
        { view: "yokohama_change", label: t("evidence.tabYokohamaChange") },
        { view: "yokohama_latent", label: t("evidence.tabYokohamaLatent") },
        { view: "mobara_change", label: t("evidence.tabMobaraChange") },
        { view: "mobara_latent", label: t("evidence.tabMobaraLatent") },
      ],
      activeView: view,
      legend:
        mode === "change"
          ? [
              { label: t("legend.higherChange"), color: colors.red },
              { label: t("legend.medium"), color: colors.amber },
              { label: t("legend.stable"), color: colors.forest },
            ]
          : [
              { label: t("legend.color"), color: colors.blue },
              { label: t("legend.similarity64d"), color: colors.gray },
            ],
      queueEyebrow: "CHANGE REVIEW",
      queueTitle: t("queueTitle.evidence"),
      queueExplanation: t("queueExpl.evidence"),
      queueCount: evidence.length,
      queueItems: queueItems(module, view, evidence, (props) => ({
        color: props.change_score >= 75 ? colors.red : props.change_score >= 45 ? colors.amber : colors.green,
        title: `${props.cell_id} · ${props.year_pair}`,
        detail: t("queueDetail.evidence", { pixels: props.valid_pixels, support: props.support_pct }),
        score: props.change_score,
        scoreLabel: "CHANGE",
      })),
      methodTitle: t("methodCard.evidenceTitle"),
      methodBody: t("methodCard.evidenceBody"),
      mapNote: mode === "change" ? t("mapNote.evidenceChange") : t("mapNote.evidenceLatent"),
    };
  }

  if (module === "facilities") {
    const facilities = data.recommendations.facilities.features;
    const summary = data.facilitySummary;
    return {
      region: "yokohama",
      eyebrow: t("facilities.eyebrow"),
      title: t("facilities.title"),
      kicker: "PUBLIC FACILITY RESILIENCE",
      heroTitle: t("facilities.heroTitle"),
      description: t("facilities.description"),
      formula: {
        parts: [
          { label: t("facilities.formulaOfficial") },
          { label: t("facilities.formulaRoads") },
          { label: t("facilities.formulaDemand") },
          { label: t("facilities.formulaRetrofit"), strong: true },
        ],
        ops: ["×", "×", "→"],
      },
      chips: [
        { kind: "observed", label: t("chip.facilityLocation"), detail: t("chip.facilityLocationDetail") },
        { kind: "proxy", label: t("chip.roofProxy"), detail: t("chip.fieldPending") },
      ],
      metrics: [
        {
          label: t("metric.officialBases"),
          value: String(facilities.length),
          unit: t("unit.sites"),
          note: t("metric.officialBasesNote"),
          color: colors.blue,
          audit: metric("metric.officialBases", facilities.length, t("unit.sites"), t("metric.officialBasesNote")),
        },
        {
          label: t("metric.roofCapacityProxy"),
          value: String(summary.pv_kwp_proxy),
          unit: "kWp",
          note: t("metric.roofCapacityProxyNote"),
          color: colors.green,
          audit: metric("metric.roofCapacityProxy", summary.pv_kwp_proxy, "kWp", t("metric.roofCapacityProxyNote")),
        },
        {
          label: t("metric.highRiskLinks"),
          value: String(summary.served_high_risk_buildings),
          unit: t("unit.buildingLinks"),
          note: t("metric.highRiskLinksNote"),
          color: colors.red,
          audit: metric("metric.highRiskLinks", summary.served_high_risk_buildings, t("unit.buildingLinks"), t("metric.highRiskLinksNote")),
        },
        {
          label: t("metric.meanResilienceScore"),
          value: String(summary.mean_resilience_score),
          unit: "/100",
          note: t("metric.meanResilienceScoreNote"),
          color: colors.amber,
          audit: metric("metric.meanResilienceScore", summary.mean_resilience_score, "/100", t("metric.meanResilienceScoreNote")),
        },
      ],
      tabs: [
        { view: "official", label: t("facilities.tabOfficial") },
        { view: "network", label: t("facilities.tabNetwork") },
      ],
      activeView: view,
      legend: [
        { label: t("legend.officialBases"), color: colors.blue },
        { label: t("legend.highOpportunity"), color: colors.green },
        { label: t("legend.nearbyHighExposure"), color: colors.red },
      ],
      queueEyebrow: "OFFICIAL ASSET QUEUE",
      queueTitle: t("queueTitle.facilities"),
      queueExplanation: t("queueExpl.facilities"),
      queueCount: facilities.length,
      queueItems: queueItems(module, view, facilities, (props) => ({
        color: props.resilience_score >= 80 ? colors.green : colors.blue,
        title: String(props.name),
        detail: t("queueDetail.facility", { kwp: props.pv_kwp_proxy, served: props.served_high_risk_buildings, road: props.nearest_road_m }),
        score: props.resilience_score,
      })),
      methodTitle: t("methodCard.facilitiesTitle"),
      methodBody: t("methodCard.facilitiesBody"),
      mapNote: t("mapNote.facilities"),
    };
  }

  if (module === "slope") {
    const summary = data.buildingSummary;
    const queue = data.recommendations.slope.features;
    return {
      region: "yokohama",
      eyebrow: t("slope.eyebrow"),
      title: t("slope.title"),
      kicker: "SLOPE EXPOSURE",
      heroTitle: t("slope.heroTitle"),
      description: t("slope.description"),
      formula: null,
      chips: defaultChips(),
      metrics: [
        {
          label: t("metric.buildingsAnalyzed"),
          value: summary.building_count.toLocaleString(),
          unit: t("unit.buildings"),
          note: t("metric.buildingsAnalyzedNote"),
          color: colors.forest,
          audit: metric("metric.buildingsAnalyzed", summary.building_count.toLocaleString(), t("unit.buildings"), t("metric.buildingsAnalyzedNote")),
        },
        {
          label: t("metric.highExposure"),
          value: String(summary.counts.high),
          unit: t("unit.buildings"),
          note: t("metric.highExposureNote"),
          color: colors.red,
          audit: metric("metric.highExposure", summary.counts.high, t("unit.buildings"), t("metric.highExposureNote")),
        },
        {
          label: t("metric.mediumExposure"),
          value: String(summary.counts.medium),
          unit: t("unit.buildings"),
          note: t("metric.mediumExposureNote"),
          color: colors.amber,
          audit: metric("metric.mediumExposure", summary.counts.medium, t("unit.buildings"), t("metric.mediumExposureNote")),
        },
        {
          label: t("metric.meanRiskScore"),
          value: String(summary.mean_score),
          unit: "/100",
          note: t("metric.meanRiskScoreNote"),
          color: colors.green,
          audit: metric("metric.meanRiskScore", summary.mean_score, "/100", t("metric.meanRiskScoreNote")),
        },
      ],
      tabs: [
        { view: "all", label: t("slope.tabAll") },
        { view: "high", label: t("slope.tabHigh") },
      ],
      activeView: view,
      legend: [
        { label: t("legend.high"), color: colors.red },
        { label: t("legend.mediumBand"), color: colors.amber },
        { label: t("legend.low"), color: colors.green },
      ],
      queueEyebrow: "EXPOSURE QUEUE",
      queueTitle: t("queueTitle.slope"),
      queueExplanation: t("queueExpl.slope"),
      queueCount: summary.counts.high,
      queueItems: queueItems(module, view, queue, (props) => ({
        color: colors.red,
        title: String(props.name),
        detail: t("queueDetail.slope", { slope: props.slope_deg, relief: props.local_relief_m }),
        score: props.risk_score,
      })),
      methodTitle: t("methodCard.slopeTitle"),
      methodBody: t("methodCard.slopeBody"),
      mapNote: t("mapNote.slope"),
    };
  }

  if (module === "roads") {
    const summary = data.roadSummary;
    const queue = data.recommendations.roads.features;
    return {
      region: "yokohama",
      eyebrow: t("roads.eyebrow"),
      title: t("roads.title"),
      kicker: "ROAD RESILIENCE",
      heroTitle: t("roads.heroTitle"),
      description: t("roads.description"),
      formula: null,
      chips: defaultChips(),
      metrics: [
        {
          label: t("metric.roadsAnalyzed"),
          value: String(summary.road_count),
          unit: t("unit.segments"),
          note: t("metric.roadsAnalyzedNote", { km: summary.total_km }),
          color: colors.forest,
          audit: metric("metric.roadsAnalyzed", summary.road_count, t("unit.segments"), t("metric.roadsAnalyzedNote", { km: summary.total_km })),
        },
        {
          label: t("metric.highPriorityQueue"),
          value: String(summary.high_queue),
          unit: t("unit.segments"),
          note: t("metric.highPriorityQueueNote"),
          color: colors.red,
          audit: metric("metric.highPriorityQueue", summary.high_queue, t("unit.segments"), t("metric.highPriorityQueueNote")),
        },
        {
          label: t("metric.nearbyExposedBuildings"),
          value: summary.exposed_buildings.toLocaleString(),
          unit: t("unit.buildings"),
          note: t("metric.nearbyExposedBuildingsNote"),
          color: colors.amber,
          audit: metric("metric.nearbyExposedBuildings", summary.exposed_buildings.toLocaleString(), t("unit.buildings"), t("metric.nearbyExposedBuildingsNote")),
        },
        {
          label: t("metric.meanPriorityScore"),
          value: String(summary.mean_score),
          unit: "/100",
          note: t("metric.meanPriorityScoreNote"),
          color: colors.blue,
          audit: metric("metric.meanPriorityScore", summary.mean_score, "/100", t("metric.meanPriorityScoreNote")),
        },
      ],
      tabs: [
        { view: "all", label: t("roads.tabAll") },
        { view: "high", label: t("roads.tabHigh") },
      ],
      activeView: view,
      legend: [
        { label: t("legend.highPriority70"), color: colors.red },
        { label: t("legend.watch4569"), color: colors.amber },
        { label: t("legend.low"), color: colors.green },
      ],
      queueEyebrow: "ROAD QUEUE",
      queueTitle: t("queueTitle.roads"),
      queueExplanation: t("queueExpl.roads"),
      queueCount: queue.length,
      queueItems: queueItems(module, view, queue, (props) => ({
        color: colors.red,
        title: props.name ? String(props.name) : t("common.unnamedRoad"),
        detail: t("queueDetail.road", { highway: props.highway, n: props.nearby_high_buildings }),
        score: props.priority_score,
      })),
      methodTitle: t("methodCard.roadsTitle"),
      methodBody: t("methodCard.roadsBody"),
      mapNote: t("mapNote.roads"),
    };
  }

  if (module === "solar") {
    const summary = data.solarSummary;
    const queue = data.recommendations.solar.features;
    return {
      region: "mobara",
      eyebrow: t("solar.eyebrow"),
      title: t("solar.title"),
      kicker: "SOLAR SITING",
      heroTitle: t("solar.heroTitle"),
      description: t("solar.description"),
      formula: null,
      chips: defaultChips(),
      metrics: [
        {
          label: t("metric.candidateCells"),
          value: String(summary.cell_count),
          unit: t("unit.cells"),
          note: t("metric.candidateCellsNote"),
          color: colors.forest,
          audit: metric("metric.candidateCells", summary.cell_count, t("unit.cells"), t("metric.candidateCellsNote")),
        },
        {
          label: t("metric.preferredCells"),
          value: String(summary.counts.preferred),
          unit: t("unit.cells"),
          note: t("metric.preferredCellsNote", { ha: summary.shortlist_area_ha }),
          color: colors.green,
          audit: metric("metric.preferredCells", summary.counts.preferred, t("unit.cells"), t("metric.preferredCellsNote", { ha: summary.shortlist_area_ha })),
        },
        {
          label: t("metric.conditionalCells"),
          value: String(summary.counts.conditional),
          unit: t("unit.cells"),
          note: t("metric.conditionalCellsNote"),
          color: colors.amber,
          audit: metric("metric.conditionalCells", summary.counts.conditional, t("unit.cells"), t("metric.conditionalCellsNote")),
        },
        {
          label: t("metric.annualGhi"),
          value: summary.annual_ghi_kwh_m2.toLocaleString(),
          unit: "kWh/m²",
          note: t("metric.annualGhiNote"),
          color: colors.blue,
          audit: metric("metric.annualGhi", summary.annual_ghi_kwh_m2.toLocaleString(), "kWh/m²", t("metric.annualGhiNote")),
        },
      ],
      tabs: [
        { view: "all", label: t("solar.tabAll") },
        { view: "preferred", label: t("solar.tabPreferred") },
      ],
      activeView: view,
      legend: [
        { label: t("legend.preferred"), color: colors.green },
        { label: t("legend.conditional"), color: colors.amber },
        { label: t("legend.rejected"), color: colors.gray },
      ],
      queueEyebrow: "SITE SHORTLIST",
      queueTitle: t("queueTitle.solar"),
      queueExplanation: t("queueExpl.solar"),
      queueCount: queue.length,
      queueItems: queueItems(module, view, queue, (props) => ({
        color: colors.green,
        title: t("common.cellTitle", { id: props.cell_id }),
        detail: t("queueDetail.solarCell", { ha: props.area_ha, slope: props.slope_deg, road: props.distance_road_m }),
        score: props.score,
      })),
      methodTitle: t("methodCard.solarTitle"),
      methodBody: t("methodCard.solarBody"),
      mapNote: t("mapNote.solar"),
    };
  }

  if (module === "joint") {
    const summary = data.jointSummary;
    const base = {
      region: "yokohama" as RegionKey,
      eyebrow: t("joint.eyebrow"),
      title: t("joint.title"),
      kicker: "YOKOHAMA URBAN RESILIENCE",
      heroTitle: t("joint.heroTitle"),
      description: t("joint.description"),
      formula: {
        parts: [
          { label: t("joint.formulaSlope") },
          { label: t("joint.formulaAccess") },
          { label: t("joint.formulaPv") },
          { label: t("joint.formulaHubs"), strong: true },
        ],
        ops: ["×", "×", "→"],
      },
      chips: [
        { kind: "observed", label: t("chip.officialDemOsm") },
        { kind: "proxy", label: t("chip.riskCapacityService") },
        { kind: "observed", label: t("chip.aefChange"), detail: t("chip.aefChangeDetail") },
      ] as StatusChipVM[],
      metrics: [
        {
          label: t("metric.resilienceHubs"),
          value: String(summary.resilience_hubs.count),
          unit: t("unit.sites"),
          note: t("metric.resilienceHubsNote", { n: summary.resilience_hubs.priority_count }),
          color: colors.lime,
          audit: metric("metric.resilienceHubs", summary.resilience_hubs.count, t("unit.sites"), t("metric.resilienceHubsNote", { n: summary.resilience_hubs.priority_count })),
        },
        {
          label: t("metric.roofCapacityProxy"),
          value: summary.resilience_hubs.pv_capacity_proxy_kwp.toLocaleString(),
          unit: "kWp",
          note: t("metric.roofCapacityAreaNote"),
          color: colors.green,
          audit: metric("metric.roofCapacityProxy", summary.resilience_hubs.pv_capacity_proxy_kwp.toLocaleString(), "kWp", t("metric.roofCapacityAreaNote")),
        },
        {
          label: t("metric.compoundCorridors"),
          value: String(summary.compound_corridors.count),
          unit: t("unit.segments"),
          note: t("metric.compoundCorridorsNote", { km: summary.compound_corridors.road_length_km }),
          color: colors.red,
          audit: metric("metric.compoundCorridors", summary.compound_corridors.count, t("unit.segments"), t("metric.compoundCorridorsNote", { km: summary.compound_corridors.road_length_km })),
        },
        {
          label: t("metric.terrainLayers"),
          value: "3",
          unit: t("unit.kinds"),
          note: t("metric.terrainLayersNote"),
          color: colors.blue,
          audit: metric("metric.terrainLayers", 3, t("unit.kinds"), t("metric.terrainLayersNote")),
        },
      ],
      tabs: [
        { view: "hubs", label: t("joint.tabHubs") },
        { view: "corridors", label: t("joint.tabCorridors") },
      ],
      activeView: view,
    };
    if (view === "hubs") {
      const features = data.recommendations.hubs.features;
      return {
        ...base,
        legend: [
          { label: t("legend.priorityHubs"), color: colors.lime },
          { label: t("legend.candidate"), color: colors.green },
          { label: t("legend.highExposureDemand"), color: colors.red },
        ],
        queueEyebrow: "RESILIENCE HUBS",
        queueTitle: t("queueTitle.jointHubs"),
        queueExplanation: t("queueExpl.jointHubs"),
        queueCount: features.length,
        queueItems: queueItems(module, view, features, (props) => ({
          color: colors.green,
          title: String(props.name),
          detail: t("queueDetail.hub", { kwp: props.pv_kwp_proxy, served: props.served_high_risk_buildings }),
          score: props.hub_score,
        })),
        methodTitle: t("methodCard.jointTitle"),
        methodBody: t("methodCard.jointHubsBody"),
        mapNote: t("mapNote.jointHubs"),
      };
    }
    const features = data.recommendations.corridors.features;
    return {
      ...base,
      legend: [
        { label: t("legend.highPriority"), color: colors.red },
        { label: t("legend.watch"), color: colors.amber },
      ],
      queueEyebrow: "COMPOUND CORRIDORS",
      queueTitle: t("queueTitle.jointCorridors"),
      queueExplanation: t("queueExpl.jointCorridors"),
      queueCount: features.length,
      queueItems: queueItems(module, view, features, (props) => ({
        color: props.joint_band === "priority" ? colors.red : colors.amber,
        title: props.name ? String(props.name) : t("common.unnamedRoad"),
        detail: t("queueDetail.corridor", { n: props.joint_high_risk_buildings, len: props.length_m }),
        score: props.compound_score,
      })),
      methodTitle: t("methodCard.jointTitle"),
      methodBody: t("methodCard.jointCorridorsBody"),
      mapNote: t("mapNote.jointCorridors"),
    };
  }

  // development
  const summary = data.jointSummary;
  const grid = data.gridScreen.mobara_screen;
  const gridSnapshot = data.gridScreen.source_file_last_modified_at || "—";
  const base = {
    region: "mobara" as RegionKey,
    eyebrow: t("development.eyebrow"),
    title: t("development.title"),
    kicker: "MOBARA DEVELOPMENT READINESS",
    heroTitle: t("development.heroTitle"),
    description: t("development.description"),
    formula: {
      parts: [
        { label: t("development.formulaLand") },
        { label: t("development.formulaAccess") },
        { label: t("development.formulaGrid") },
        { label: t("development.formulaReadiness"), strong: true },
      ],
      ops: ["×", "×", "→"],
    },
    chips: defaultChips(),
    metrics: [
      {
        label: t("metric.deliveryCells"),
        value: String(summary.solar_delivery_cells.count),
        unit: t("unit.cells"),
        note: t("metric.deliveryCellsNote", { ha: summary.solar_delivery_cells.area_ha }),
        color: colors.blue,
        audit: metric("metric.deliveryCells", summary.solar_delivery_cells.count, t("unit.cells"), t("metric.deliveryCellsNote", { ha: summary.solar_delivery_cells.area_ha })),
      },
      {
        label: t("metric.ruleExclusions"),
        value: String(data.solarSummary.counts.reject),
        unit: t("unit.cells"),
        note: t("metric.ruleExclusionsNote"),
        color: colors.red,
        audit: metric("metric.ruleExclusions", data.solarSummary.counts.reject, t("unit.cells"), t("metric.ruleExclusionsNote")),
      },
      {
        label: t("metric.cachedVisualLayers"),
        value: "4",
        unit: t("unit.kinds"),
        note: t("metric.cachedVisualLayersNote"),
        color: colors.green,
        audit: metric("metric.cachedVisualLayers", 4, t("unit.kinds"), t("metric.cachedVisualLayersNote")),
      },
      {
        label: t("metric.spareCapacity"),
        value: String(grid.spare_with_upstream_mw),
        unit: "MW",
        note: t("metric.spareCapacityNote", { own: grid.spare_own_mw }),
        color: colors.red,
        audit: metric("metric.spareCapacity", grid.spare_with_upstream_mw, "MW", t("metric.spareCapacityNote", { own: grid.spare_own_mw }), {
          snapshot: data.gridScreen.source_file_last_modified_at,
        }),
      },
    ],
    tabs: [
      { view: "delivery", label: t("development.tabDelivery") },
      { view: "constraints", label: t("development.tabConstraints") },
    ],
    activeView: view,
  };
  if (view === "delivery") {
    const features = data.recommendations.delivery.features;
    return {
      ...base,
      legend: [
        { label: t("legend.highDelivery"), color: colors.blue },
        { label: t("legend.candidate"), color: colors.green },
        { label: t("legend.transmission"), color: "#8e5eaa" },
      ],
      queueEyebrow: "DELIVERY-READY SOLAR",
      queueTitle: t("queueTitle.developmentDelivery"),
      queueExplanation: t("queueExpl.developmentDelivery"),
      queueCount: features.length,
      queueItems: queueItems(module, view, features, (props) => ({
        color: props.delivery_band === "priority" ? colors.blue : colors.green,
        title: t("common.cellTitle", { id: props.cell_id }),
        detail: t("queueDetail.deliveryCell", { ha: props.area_ha, slope: props.slope_deg, grid: props.distance_grid_m }),
        score: props.delivery_score,
      })),
      methodTitle: t("methodCard.developmentDeliveryTitle"),
      methodBody: t("methodCard.developmentDeliveryBody", {
        snapshot: gridSnapshot,
        own: grid.spare_own_mw,
        withUpstream: grid.spare_with_upstream_mw,
      }),
      mapNote: t("mapNote.developmentDelivery"),
    };
  }
  const features = data.recommendations.constraints.features;
  return {
    ...base,
    legend: [
      { label: t("legend.multipleConflicts"), color: colors.red },
      { label: t("legend.singleConflict"), color: colors.amber },
      { label: t("legend.water"), color: colors.blue },
    ],
    queueEyebrow: "CURRENT EXCLUSIONS",
    queueTitle: t("queueTitle.developmentConstraints"),
    queueExplanation: t("queueExpl.developmentConstraints"),
    queueCount: features.length,
    queueItems: queueItems(module, view, features, (props) => ({
      color: (props.reject_reasons?.length ?? 0) > 1 ? colors.red : colors.amber,
      title: t("common.cellTitle", { id: props.cell_id }),
      detail: (props.reject_reasons ?? []).join(" · ") || t("common.ruleConflicts"),
      score: props.reject_reasons?.length ?? 0,
      scoreLabel: "RULES",
    })),
    methodTitle: t("methodCard.developmentConstraintsTitle"),
    methodBody: t("methodCard.developmentConstraintsBody"),
    mapNote: t("mapNote.developmentConstraints"),
  };
}
