/**
 * deck.gl analytical layers and their popup wiring, per module and view.
 *
 * Ported from the Leaflet layer halves of the `render*` functions in
 * `frontend/app.js`: layer order (bottom→top), styling and the popup each
 * feature class binds. Colors and thresholds come from ./style-rules.ts as
 * data. Layers are rebuilt only when (module, view, data) change — never on
 * a language switch or unrelated state.
 */

import { GeoJsonLayer, BitmapLayer } from "@deck.gl/layers";
import { PathStyleExtension } from "@deck.gl/extensions";
import type { Layer } from "@deck.gl/core";

import type { Bootstrap, Feature, FeatureCollection } from "../api/types";
import type { FieldKey, ModuleName } from "../audit";
import type { MessageKey, MessageParams } from "../i18n/i18n.svelte";
import {
  BUILDING_OVERLAYS,
  CONSTRAINT_STYLE,
  CONTEXT_STYLES,
  CORRIDOR_STYLES,
  DELIVERY_STYLE,
  EVIDENCE_CHANGE,
  FACILITY_MARKERS,
  HUB_STYLES,
  OVERLAY_OPACITY,
  RISK_BANDS,
  ROAD_OPACITY,
  ROAD_THRESHOLDS,
  SOLAR_STATUS,
  WINDOWED_STYLE,
  ZONE_STYLE,
  rgba,
} from "./style-rules";

type P = Record<string, any>;
type Translate = (key: MessageKey, params?: MessageParams) => string;

export interface PopupField {
  key: FieldKey;
  value: (props: P, t: Translate) => string | number;
}

export interface PopupSpec {
  eyebrow: MessageKey;
  title: (props: P, t: Translate) => string;
  fields: PopupField[];
}

export interface PickHandlers {
  onFeature(spec: PopupSpec, feature: Feature, coordinate: [number, number]): void;
}

const named = (props: P, t: Translate) => (props.name ? String(props.name) : t("common.unnamedRoad"));
const byCell = (props: P) => String(props.cell_id);

/** Repository-relative `data/…` paths resolve on the API asset mount. */
export function assetUrl(path: string, assetBase: string): string {
  return path.startsWith("data/") ? `${assetBase}/${path.slice(5)}` : path;
}

/**
 * The windowed foundation layer, rendered minimally: geometry only, palette
 * colours, drawn beneath the analytical layers and never picked. Styling is
 * the overlay stage's scope; this proves the delivery path.
 */
export function buildWindowedFeatureLayer(key: string, features: Feature[]): Layer {
  return new GeoJsonLayer({
    id: `windowed-${key}`,
    data: features as unknown as GeoJSON.Feature[],
    stroked: true,
    filled: true,
    pickable: false,
    lineWidthUnits: "pixels",
    getLineWidth: WINDOWED_STYLE.width,
    getLineColor: WINDOWED_STYLE.line,
    getFillColor: WINDOWED_STYLE.fill,
    pointRadiusUnits: "pixels",
    getPointRadius: 4,
  } as never);
}

export const POPUPS: Record<string, PopupSpec> = {
  corridorOverview: {
    eyebrow: "popup.corridor",
    title: named,
    fields: [
      { key: "score.joint", value: (p) => p.compound_score },
      { key: "field.highRiskBuildings", value: (p, t) => `${p.joint_high_risk_buildings} ${t("unit.buildings")}` },
    ],
  },
  hubOverview: {
    eyebrow: "popup.hub",
    title: (p) => String(p.name),
    fields: [
      { key: "score.joint", value: (p) => p.hub_score },
      { key: "field.pvProxy", value: (p) => `${p.pv_kwp_proxy} kWp` },
      { key: "field.serviceDemand", value: (p, t) => `${p.served_high_risk_buildings} ${t("unit.buildings")}` },
    ],
  },
  deliveryCell: {
    eyebrow: "popup.deliveryCell",
    title: byCell,
    fields: [
      { key: "score.delivery", value: (p) => p.delivery_score },
      { key: "field.slope", value: (p) => `${p.slope_deg}°` },
      { key: "field.road", value: (p) => `${p.distance_road_m} m` },
      { key: "field.transmission", value: (p) => `${p.distance_grid_m} m` },
    ],
  },
  zone: {
    eyebrow: "popup.zone",
    title: (p) => String(p.zone_id),
    fields: [
      { key: "score.action", value: (p) => p.action_score },
      { key: "field.context", value: (p) => p.context_density },
      { key: "field.embeddingChange", value: (p) => p.embedding_change_score ?? "—" },
      { key: "field.notScored", value: (p, t) => (p.embedding_used_in_score ? t("popupValue.no") : t("popupValue.yes")) },
    ],
  },
  embeddingChange: {
    eyebrow: "popup.embeddingChange",
    title: byCell,
    fields: [
      { key: "score.changePercentile", value: (p) => p.change_score },
      { key: "field.cosineChange", value: (p) => p.cosine_change },
      { key: "field.validPixels", value: (p) => p.valid_pixels },
      { key: "field.evidenceStatus", value: (_, t) => t("popupValue.observedRepresentation") },
    ],
  },
  embeddingLatent: {
    eyebrow: "popup.embeddingLatent",
    title: byCell,
    fields: [
      { key: "field.year", value: () => "2024" },
      { key: "field.support", value: (p) => `${p.support_pct}%` },
      { key: "field.vectorPreview", value: (p) => (p.embedding_preview ?? []).slice(0, 3).join(" · ") },
      { key: "field.semanticClass", value: (_, t) => t("popupValue.notInterpretable") },
    ],
  },
  corridorNetwork: {
    eyebrow: "popup.corridor",
    title: named,
    fields: [
      { key: "score.joint", value: (p) => p.compound_score },
      { key: "field.highRiskBuildings", value: (p) => p.joint_high_risk_buildings },
    ],
  },
  hubNetwork: {
    eyebrow: "popup.candidateNode",
    title: (p) => String(p.name),
    fields: [
      { key: "score.joint", value: (p) => p.hub_score },
      { key: "field.capacityProxy", value: (p) => `${p.pv_kwp_proxy} kWp` },
    ],
  },
  facilityOfficial: {
    eyebrow: "popup.officialBase",
    title: (p) => String(p.name),
    fields: [
      { key: "score.opportunity", value: (p) => p.resilience_score },
      { key: "field.officialStatus", value: (_, t) => t("popupValue.observed") },
      { key: "field.capacityProxy", value: (p) => `${p.pv_kwp_proxy} kWp` },
      { key: "field.highRiskLinks", value: (p, t) => `${p.served_high_risk_buildings} ${t("unit.buildings")}` },
      { key: "field.roadDistance", value: (p) => `${p.nearest_road_m} m` },
      { key: "field.roofMatch", value: (p) => `${p.matched_roof_m} m` },
    ],
  },
  slopeBuilding: {
    eyebrow: "popup.slope",
    title: (p) => String(p.name),
    fields: [
      { key: "score.risk", value: (p) => p.risk_score },
      { key: "field.slope", value: (p) => `${p.slope_deg}°` },
      { key: "field.localRelief", value: (p) => `${p.local_relief_m} m` },
      { key: "field.elevation", value: (p) => `${p.elevation_m} m` },
    ],
  },
  road: {
    eyebrow: "popup.road",
    title: named,
    fields: [
      { key: "score.priority", value: (p) => p.priority_score },
      { key: "field.maxSlope", value: (p) => `${p.max_slope_deg}°` },
      { key: "field.exposedBuildings", value: (p, t) => `${p.nearby_exposed_buildings} ${t("unit.buildings")}` },
      { key: "field.length", value: (p) => `${p.length_m} m` },
    ],
  },
  siteContext: {
    eyebrow: "popup.siteContext",
    title: (p) => String(p.name ?? p.kind),
    fields: [
      { key: "field.kind", value: (p) => p.kind },
      { key: "field.class", value: (p) => p.class ?? "—" },
    ],
  },
  solarCell: {
    eyebrow: "popup.solarCell",
    title: byCell,
    fields: [
      { key: "score.suitability", value: (p) => p.score },
      { key: "field.slope", value: (p) => `${p.slope_deg}°` },
      { key: "field.distTransmission", value: (p) => `${p.distance_grid_m} m` },
      { key: "field.distRoad", value: (p) => `${p.distance_road_m} m` },
    ],
  },
  hubJoint: {
    eyebrow: "popup.hub",
    title: (p) => String(p.name),
    fields: [
      { key: "score.joint", value: (p) => p.hub_score },
      { key: "field.pvProxy", value: (p) => `${p.pv_kwp_proxy} kWp` },
      { key: "field.serviceDemand", value: (p, t) => `${p.served_high_risk_buildings} ${t("unit.buildings")}` },
      { key: "field.roadPriority", value: (p) => p.nearest_road_priority },
    ],
  },
  facilityJoint: {
    eyebrow: "popup.officialBaseShort",
    title: (p) => String(p.name),
    fields: [
      { key: "score.opportunity", value: (p) => p.resilience_score },
      { key: "field.capacityProxy", value: (p) => `${p.pv_kwp_proxy} kWp` },
    ],
  },
  corridorFocus: {
    eyebrow: "popup.corridor",
    title: named,
    fields: [
      { key: "score.joint", value: (p) => p.compound_score },
      { key: "field.highRiskBuildings", value: (p, t) => `${p.joint_high_risk_buildings} ${t("unit.buildings")}` },
      { key: "field.meanBuildingRisk", value: (p) => p.joint_average_building_risk },
      { key: "field.length", value: (p) => `${p.length_m} m` },
    ],
  },
  exclusionCell: {
    eyebrow: "popup.exclusion",
    title: byCell,
    fields: [
      { key: "score.conflicts", value: (p) => (p.reject_reasons ?? []).length },
      { key: "field.reasons", value: (p) => (p.reject_reasons ?? []).join("、") || "—" },
      { key: "field.slope", value: (p) => `${p.slope_deg}°` },
      { key: "field.distWater", value: (p) => `${p.distance_water_m} m` },
    ],
  },
};

/** Views that color building footprints themselves; the basemap's own
 * building layer hides underneath so the analysis color is the only one. */
export function drawsOwnBuildings(module: ModuleName, view: string): boolean {
  if (module === "slope" || module === "facilities") return true;
  if (module === "overview") return view === "urban";
  if (module === "joint") return view === "hubs";
  return false;
}

/** The popup the active queue's target layer binds — a queue click opens it. */
export function queuePopup(module: ModuleName, view: string): PopupSpec {
  if (module === "overview") return view === "urban" ? POPUPS.hubOverview : POPUPS.deliveryCell;
  if (module === "evidence") return view.endsWith("latent") ? POPUPS.embeddingLatent : POPUPS.embeddingChange;
  if (module === "slope") return POPUPS.slopeBuilding;
  if (module === "roads") return POPUPS.road;
  if (module === "facilities") return POPUPS.facilityOfficial;
  if (module === "solar") return POPUPS.solarCell;
  if (module === "joint") return view === "corridors" ? POPUPS.corridorFocus : POPUPS.hubJoint;
  return view === "constraints" ? POPUPS.exclusionCell : POPUPS.deliveryCell;
}

/** Recursive bbox over GeoJSON coordinates: [west, south, east, north]. */
export function geometryBounds(geometry: unknown): [number, number, number, number] | null {
  const points: [number, number][] = [];
  const walk = (value: unknown): void => {
    if (!Array.isArray(value)) return;
    if (value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") {
      points.push([value[0], value[1]]);
      return;
    }
    for (const item of value) walk(item);
  };
  walk((geometry as { coordinates?: unknown })?.coordinates);
  if (!points.length) return null;
  return [
    Math.min(...points.map(([x]) => x)),
    Math.min(...points.map(([, y]) => y)),
    Math.max(...points.map(([x]) => x)),
    Math.max(...points.map(([, y]) => y)),
  ];
}

function pickProps(spec: PopupSpec, handlers: PickHandlers) {
  return {
    pickable: true,
    onClick: (info: { object?: Feature; coordinate?: number[] }) => {
      if (!info.object || !info.coordinate) return;
      handlers.onFeature(spec, info.object, [info.coordinate[0], info.coordinate[1]]);
      return true;
    },
  };
}

function geo(id: string, data: FeatureCollection, props: Record<string, unknown>): Layer {
  return new GeoJsonLayer({
    id,
    data: data as unknown as GeoJSON.FeatureCollection,
    lineWidthUnits: "pixels",
    ...props,
  } as never);
}

function buildingsOverlay(id: string, data: FeatureCollection, style: (typeof BUILDING_OVERLAYS)[keyof typeof BUILDING_OVERLAYS]): Layer {
  return geo(id, data, {
    stroked: true,
    filled: true,
    getLineColor: style.line,
    getLineWidth: style.width,
    getFillColor: style.fill,
  });
}

function corridorLayer(
  id: string,
  data: FeatureCollection,
  variant: keyof typeof CORRIDOR_STYLES,
  spec: PopupSpec | null,
  handlers: PickHandlers,
): Layer {
  const style = CORRIDOR_STYLES[variant];
  return geo(id, data, {
    stroked: true,
    filled: false,
    getLineColor: (f: Feature) =>
      rgba((f.properties as P).joint_band === "priority" ? style.priority.color : style.other.color, style.opacity),
    getLineWidth: (f: Feature) => ((f.properties as P).joint_band === "priority" ? style.priority.width : style.other.width),
    ...(spec ? pickProps(spec, handlers) : {}),
  });
}

function contextLayer(
  id: string,
  data: FeatureCollection,
  variant: keyof typeof CONTEXT_STYLES,
  spec: PopupSpec | null,
  handlers: PickHandlers,
): Layer {
  const styles = CONTEXT_STYLES[variant] as Record<string, { color: string; width: number; opacity: number; dash?: [number, number]; fill?: ReturnType<typeof rgba> }>;
  const styleFor = (f: Feature) => styles[(f.properties as P).kind] ?? styles.other;
  return geo(id, data, {
    stroked: true,
    filled: true,
    getLineColor: (f: Feature) => rgba(styleFor(f).color, styleFor(f).opacity),
    getLineWidth: (f: Feature) => styleFor(f).width,
    getFillColor: (f: Feature) => styleFor(f).fill ?? [0, 0, 0, 0],
    getDashArray: (f: Feature) => styleFor(f).dash ?? [0, 0],
    extensions: [new PathStyleExtension({ dash: true })],
    ...(spec ? pickProps(spec, handlers) : {}),
  });
}

function facilityLayer(
  id: string,
  data: FeatureCollection,
  variant: keyof typeof FACILITY_MARKERS,
  spec: PopupSpec,
  handlers: PickHandlers,
): Layer {
  const style = FACILITY_MARKERS[variant];
  return geo(id, data, {
    stroked: true,
    filled: true,
    pointType: "circle",
    pointRadiusUnits: "pixels",
    getPointRadius: style.radius,
    getLineColor: style.stroke,
    getLineWidth: style.strokeWidth,
    getFillColor: (f: Feature) =>
      "high" in style
        ? rgba((f.properties as P).resilience_score >= style.highScore ? style.high : style.other, style.fillOpacity)
        : rgba((style as { fill: string }).fill, style.fillOpacity),
    ...pickProps(spec, handlers),
  });
}

export function buildAnalyticalLayers(
  module: ModuleName,
  view: string,
  data: Bootstrap,
  assetBase: string,
  handlers: PickHandlers,
): Layer[] {
  const layers: Layer[] = [];

  if (module === "overview" && view === "urban") {
    layers.push(buildingsOverlay("overview-buildings", data.recommendations.slope, BUILDING_OVERLAYS.overview));
    layers.push(corridorLayer("overview-corridors", data.corridors, "overview", POPUPS.corridorOverview, handlers));
    layers.push(
      geo("overview-hubs", data.hubs, {
        stroked: true,
        filled: true,
        getLineColor: HUB_STYLES.overview.line,
        getLineWidth: HUB_STYLES.overview.width,
        getFillColor: HUB_STYLES.overview.fill(),
        ...pickProps(POPUPS.hubOverview, handlers),
      }),
    );
  }

  if (module === "overview" && view === "renewable") {
    layers.push(contextLayer("overview-context", data.solarContext, "overviewRenewable", null, handlers));
    layers.push(
      geo("overview-delivery", data.recommendations.delivery, {
        stroked: true,
        filled: true,
        getLineColor: DELIVERY_STYLE.line,
        getLineWidth: DELIVERY_STYLE.width,
        getFillColor: (f: Feature) =>
          rgba(
            (f.properties as P).delivery_band === "priority" ? DELIVERY_STYLE.colors.priority : DELIVERY_STYLE.colors.other,
            DELIVERY_STYLE.fillOpacity.overview,
          ),
        ...pickProps(POPUPS.deliveryCell, handlers),
      }),
    );
  }

  if (module === "evidence") {
    const [region, mode] = view.split("_") as ["yokohama" | "mobara", "change" | "latent"];
    const overlay = data.embeddingSummary.overlays[region];
    const [[south, west], [north, east]] = overlay.bounds;
    const image = mode === "change" ? overlay.change_image : overlay.latent_image;
    layers.push(
      new BitmapLayer({
        id: "evidence-overlay",
        image: assetUrl(image, assetBase),
        bounds: [west, south, east, north],
        opacity: mode === "change" ? OVERLAY_OPACITY.change : OVERLAY_OPACITY.latent,
      }),
    );
    const zones = region === "yokohama" ? data.yokohamaZones : data.mobaraZones;
    layers.push(
      geo("evidence-zones", zones, {
        stroked: true,
        filled: true,
        getLineColor: ZONE_STYLE.line,
        getLineWidth: ZONE_STYLE.width,
        getFillColor: ZONE_STYLE.fill,
        getDashArray: ZONE_STYLE.dash,
        extensions: [new PathStyleExtension({ dash: true })],
        ...pickProps(POPUPS.zone, handlers),
      }),
    );
    const evidence = region === "yokohama" ? data.recommendations.embeddingYokohama : data.recommendations.embeddingMobara;
    if (mode === "change") {
      layers.push(
        geo("evidence-cells", evidence, {
          stroked: false,
          filled: true,
          getFillColor: (f: Feature) => {
            const score = (f.properties as P).change_score;
            const band = EVIDENCE_CHANGE.thresholds.find((item) => score >= item.min) ?? EVIDENCE_CHANGE.thresholds[2];
            return rgba(band.color, EVIDENCE_CHANGE.fillOpacity);
          },
          ...pickProps(POPUPS.embeddingChange, handlers),
        }),
      );
    } else {
      layers.push(
        geo("evidence-cells", evidence, {
          stroked: false,
          filled: true,
          getFillColor: [0, 0, 0, 0],
          ...pickProps(POPUPS.embeddingLatent, handlers),
        }),
      );
    }
  }

  if (module === "facilities") {
    if (view === "network") {
      layers.push(corridorLayer("facilities-corridors", data.corridors, "network", POPUPS.corridorNetwork, handlers));
      layers.push(
        geo("facilities-hubs", data.hubs, {
          stroked: true,
          filled: true,
          getLineColor: HUB_STYLES.network.line,
          getLineWidth: HUB_STYLES.network.width,
          getFillColor: HUB_STYLES.network.fill(),
          ...pickProps(POPUPS.hubNetwork, handlers),
        }),
      );
    }
    layers.push(buildingsOverlay("facilities-buildings", data.recommendations.slope, BUILDING_OVERLAYS.facilities));
    layers.push(facilityLayer("facilities-markers", data.recommendations.facilities, "official", POPUPS.facilityOfficial, handlers));
  }

  if (module === "slope") {
    const features = view === "high" ? data.recommendations.slope : data.buildings;
    layers.push(
      geo("slope-buildings", features, {
        stroked: true,
        filled: true,
        getLineWidth: RISK_BANDS.lineWidth,
        getLineColor: (f: Feature) => rgba(RISK_BANDS.colors[(f.properties as P)[RISK_BANDS.field]] ?? RISK_BANDS.colors.low),
        getFillColor: (f: Feature) => {
          const band = (f.properties as P)[RISK_BANDS.field];
          return rgba(
            RISK_BANDS.colors[band] ?? RISK_BANDS.colors.low,
            band === "high" ? RISK_BANDS.fillOpacity.high : RISK_BANDS.fillOpacity.other,
          );
        },
        ...pickProps(POPUPS.slopeBuilding, handlers),
      }),
    );
  }

  if (module === "roads") {
    const features = view === "high" ? data.recommendations.roads : data.roads;
    const bandFor = (f: Feature) =>
      ROAD_THRESHOLDS.find((item) => (f.properties as P).priority_score >= item.min) ?? ROAD_THRESHOLDS[2];
    layers.push(
      geo("roads-lines", features, {
        stroked: true,
        filled: false,
        getLineColor: (f: Feature) => rgba(bandFor(f).color, ROAD_OPACITY),
        getLineWidth: (f: Feature) => bandFor(f).width,
        ...pickProps(POPUPS.road, handlers),
      }),
    );
  }

  if (module === "solar") {
    layers.push(contextLayer("solar-context", data.solarContext, "solar", POPUPS.siteContext, handlers));
    const features = view === "preferred" ? data.recommendations.solar : data.solar;
    layers.push(
      geo("solar-cells", features, {
        stroked: true,
        filled: true,
        getLineColor: SOLAR_STATUS.line,
        getLineWidth: SOLAR_STATUS.width,
        getFillColor: (f: Feature) => {
          const status = (f.properties as P).status;
          return rgba(
            SOLAR_STATUS.colors[status] ?? SOLAR_STATUS.colors.reject,
            status === "reject" ? SOLAR_STATUS.fillOpacity.reject : SOLAR_STATUS.fillOpacity.other,
          );
        },
        ...pickProps(POPUPS.solarCell, handlers),
      }),
    );
  }

  if (module === "joint") {
    if (view === "hubs") {
      layers.push(buildingsOverlay("joint-buildings", data.recommendations.slope, BUILDING_OVERLAYS.joint));
      layers.push(facilityLayer("joint-facilities", data.facilities, "joint", POPUPS.facilityJoint, handlers));
      layers.push(
        geo("joint-hubs", data.recommendations.hubs, {
          stroked: true,
          filled: true,
          getLineColor: HUB_STYLES.banded.line,
          getLineWidth: HUB_STYLES.banded.width,
          getFillColor: (f: Feature) => HUB_STYLES.banded.fill((f.properties as P).hub_band),
          ...pickProps(POPUPS.hubJoint, handlers),
        }),
      );
    } else {
      layers.push(corridorLayer("joint-corridors", data.recommendations.corridors, "focus", POPUPS.corridorFocus, handlers));
    }
  }

  if (module === "development") {
    layers.push(contextLayer("development-context", data.solarContext, "development", null, handlers));
    if (view === "delivery") {
      layers.push(
        geo("development-delivery", data.recommendations.delivery, {
          stroked: true,
          filled: true,
          getLineColor: DELIVERY_STYLE.line,
          getLineWidth: DELIVERY_STYLE.width,
          getFillColor: (f: Feature) =>
            rgba(
              (f.properties as P).delivery_band === "priority" ? DELIVERY_STYLE.colors.priority : DELIVERY_STYLE.colors.other,
              DELIVERY_STYLE.fillOpacity.development,
            ),
          ...pickProps(POPUPS.deliveryCell, handlers),
        }),
      );
    } else {
      layers.push(
        geo("development-constraints", data.recommendations.constraints, {
          stroked: true,
          filled: true,
          getLineColor: CONSTRAINT_STYLE.line,
          getLineWidth: CONSTRAINT_STYLE.width,
          getFillColor: (f: Feature) =>
            rgba(
              ((f.properties as P).reject_reasons ?? []).length > 1 ? CONSTRAINT_STYLE.multiple : CONSTRAINT_STYLE.single,
              CONSTRAINT_STYLE.fillOpacity,
            ),
          ...pickProps(POPUPS.exclusionCell, handlers),
        }),
      );
    }
  }

  return layers;
}
