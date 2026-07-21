/**
 * Color and threshold definitions for every analytical layer, expressed as
 * data. Ported one-to-one from the Leaflet style callbacks in
 * `frontend/app.js`; an analytical threshold change is an edit here, not in
 * layer code.
 */

import { palette } from "../theme";
import { colors } from "../modules";

export type RGBA = [number, number, number, number];

export function rgba(hex: string, alpha = 1): RGBA {
  const value = hex.replace("#", "");
  const full = value.length === 3 ? value.split("").map((c) => c + c).join("") : value;
  return [
    parseInt(full.slice(0, 2), 16),
    parseInt(full.slice(2, 4), 16),
    parseInt(full.slice(4, 6), 16),
    Math.round(alpha * 255),
  ];
}

/** Buildings drawn as context under other analytical layers. */
export const BUILDING_OVERLAYS = {
  overview: { line: rgba(palette.exposureOutline), width: 0.4, fill: rgba(colors.red, 0.2) },
  facilities: { line: rgba(colors.red), width: 0.25, fill: rgba(colors.red, 0.12) },
  joint: { line: rgba(colors.red), width: 0.35, fill: rgba(colors.red, 0.18) },
} as const;

/** Building slope-exposure bands (slope module). */
export const RISK_BANDS = {
  field: "risk_band",
  colors: { high: colors.red, medium: colors.amber, low: colors.green } as Record<string, string>,
  fillOpacity: { high: 0.72, other: 0.42 },
  lineWidth: 0.55,
} as const;

/** Road inspection-priority thresholds (roads module). */
export const ROAD_THRESHOLDS = [
  { min: 70, color: colors.red, width: 4 },
  { min: 45, color: colors.amber, width: 2.2 },
  { min: 0, color: colors.green, width: 2.2 },
] as const;

export const ROAD_OPACITY = 0.85;

/** Compound corridors in their three visual contexts. */
export const CORRIDOR_STYLES = {
  overview: { priority: { color: colors.red, width: 4 }, other: { color: colors.amber, width: 2.2 }, opacity: 0.65 },
  network: { priority: { color: colors.red, width: 3.2 }, other: { color: colors.amber, width: 3.2 }, opacity: 0.55 },
  focus: { priority: { color: colors.red, width: 4.5 }, other: { color: colors.amber, width: 2.5 }, opacity: 0.85 },
} as const;

/** Resilience hubs in their three visual contexts. */
export const HUB_STYLES = {
  overview: { line: rgba(palette.corridorOutline), width: 1.2, fill: () => rgba(colors.lime, 0.9) },
  banded: {
    line: rgba(palette.zoneOutline),
    width: 1.1,
    fill: (band: unknown) => rgba(band === "priority" ? colors.lime : colors.green, 0.9),
  },
  network: { line: rgba(colors.green), width: 0.7, fill: () => rgba(colors.lime, 0.35) },
} as const;

/** Delivery-ready solar cells (overview renewable + development delivery). */
export const DELIVERY_STYLE = {
  line: rgba(palette.white),
  width: 1,
  colors: { priority: colors.blue, other: colors.green },
  fillOpacity: { overview: 0.76, development: 0.78 },
} as const;

/** Solar siting status bands (solar module). */
export const SOLAR_STATUS = {
  line: rgba(palette.white),
  width: 0.65,
  colors: { preferred: colors.green, conditional: colors.amber, reject: colors.gray } as Record<string, string>,
  fillOpacity: { reject: 0.34, other: 0.72 },
} as const;

/** Site-context linework (power / water / building / other), per module. */
export const CONTEXT_STYLES = {
  overviewRenewable: {
    power: { color: palette.transmission, width: 3.5, opacity: 1, dash: [5, 5] as [number, number] },
    water: { color: colors.blue, width: 1.4, opacity: 1 },
    building: { color: palette.buildingOutline, width: 0.8, opacity: 1 },
    other: { color: palette.buildingOutline, width: 0.8, opacity: 1 },
  },
  solar: {
    power: { color: palette.transmission, width: 3.5, opacity: 0.8, dash: [5, 5] as [number, number] },
    water: { color: colors.blue, width: 2, opacity: 0.75 },
    building: { color: palette.buildingOutlineSoft, width: 0.5, opacity: 1, fill: rgba(palette.buildingFill, 0.45) },
    other: { color: palette.buildingOutline, width: 1.2, opacity: 0.7 },
  },
  development: {
    power: { color: palette.transmission, width: 3.5, opacity: 0.85, dash: [5, 5] as [number, number] },
    water: { color: colors.blue, width: 1.5, opacity: 0.75 },
    building: { color: palette.buildingOutline, width: 1, opacity: 0.55 },
    other: { color: palette.buildingOutline, width: 1, opacity: 0.55 },
  },
} as const;

/** Satellite-embedding change bands (evidence module). */
export const EVIDENCE_CHANGE = {
  thresholds: [
    { min: 75, color: colors.red },
    { min: 45, color: colors.amber },
    { min: 0, color: colors.forest },
  ],
  fillOpacity: 0.08,
} as const;

/** Multi-scale decision zones (evidence module). */
export const ZONE_STYLE = {
  line: rgba(palette.white),
  width: 1.1,
  dash: [4, 4] as [number, number],
  fill: rgba(colors.forest, 0.04),
} as const;

/** Official facility markers. */
export const FACILITY_MARKERS = {
  official: { radius: 9, stroke: rgba(palette.white), strokeWidth: 2.2, highScore: 80, high: colors.green, other: colors.blue, fillOpacity: 0.95 },
  joint: { radius: 8, stroke: rgba(palette.white), strokeWidth: 2, fill: colors.blue, fillOpacity: 0.95 },
} as const;

/** Rule-exclusion cells (development constraints). */
export const CONSTRAINT_STYLE = {
  line: rgba(palette.white),
  width: 0.7,
  multiple: colors.red,
  single: colors.amber,
  fillOpacity: 0.72,
} as const;

/** Image overlay opacities (evidence module). */
export const OVERLAY_OPACITY = { change: 0.82, latent: 0.74 } as const;
