/**
 * Underground observation domain: the UC24-16 Nihonbashi manifest and audit
 * index, and the pure summaries the module builds from them.
 *
 * Everything here is observed foundation data. Missing attributes stay
 * missing (`uro:mesureType` is absent on access structures, depths only exist
 * where published), the upstream misspellings (`uro:outerDiamiter`,
 * `uro:mesureType`) are the real keys, and nothing invents a value the source
 * does not carry.
 */

import { palette } from "./theme";

/** Underground utility classes coloured APWA-style, from the palette only so
 * this module stays cycle-free (modules → underground → theme). The class
 * split doubles as the measurement-class split: every network feature carries
 * `uro:mesureType: "2"` while access structures publish none. */
export const UNDERGROUND_STYLE = {
  classColors: {
    water_pipe: palette.blue,
    sewer_pipe: palette.green,
    gas_pipe: palette.amber,
    communications_cable: palette.comms,
    power_cable: palette.red,
    sewer_manhole: palette.gray,
    power_manhole: palette.gray,
    communications_manhole: palette.gray,
    communications_handhole: palette.gray,
  } as Record<string, string>,
  opacity: 0.9,
} as const;

export interface UndergroundResource {
  resource_id: string;
  slug: string;
  utility_class: string;
  name: string;
  feature_count: number;
  gltf_count: number;
  tileset_url: string;
  /** 3D Tiles region: [west, south, east, north] in radians + [minH, maxH] metres. */
  bounding_region: number[];
  retrieved_at?: string;
}

export interface UndergroundManifest {
  dataset_id: string;
  scene_id: string;
  package_page: string;
  retrieved_at: string;
  license: string;
  license_url: string;
  vertical_datum: string;
  height_reference?: string;
  depth_semantics?: string;
  extent_degrees_and_metres: number[];
  feature_count: number;
  resource_count: number;
  resources: UndergroundResource[];
  limitations: string[];
}

export interface UndergroundFeature {
  record_id: string;
  source_feature_id: string;
  source_resource_id: string;
  source_asset: string;
  utility_class: string;
  attributes: Record<string, string>;
}

export interface UndergroundAuditIndex {
  dataset_id: string;
  feature_count: number;
  attribute_units: Record<string, string | null>;
  features: UndergroundFeature[];
}

export type UndergroundFamily = "networks" | "access";

/** The underground module's on-demand data lifecycle: `unknown` until first
 * entry, `unavailable` when /catalog reports the cache absent, `ready` once
 * the manifest and audit index are loaded. */
export type UndergroundStatus = "unknown" | "loading" | "unavailable" | "ready" | "error";

export interface UndergroundState {
  status: UndergroundStatus;
  manifest: UndergroundManifest | null;
  auditIndex: UndergroundAuditIndex | null;
}

export const NETWORK_CLASSES = [
  "water_pipe",
  "sewer_pipe",
  "gas_pipe",
  "communications_cable",
  "power_cable",
] as const;

export const ACCESS_CLASSES = [
  "sewer_manhole",
  "power_manhole",
  "communications_manhole",
  "communications_handhole",
] as const;

export function resourceFamily(utilityClass: string): UndergroundFamily {
  return (NETWORK_CLASSES as readonly string[]).includes(utilityClass) ? "networks" : "access";
}

/**
 * i-UR `UtilityNetworkElement_material` codelist, fetched from the published
 * source (geospatial.jp/iur/codelists/3.2). Official Japanese labels are data,
 * not interface chrome, so they render as published in every UI language.
 */
export const MATERIAL_CODELIST: Record<string, string> = {
  "1": "金属",
  "2": "合成樹脂",
  "3": "陶器：CP",
  "4": "その他",
  "101": "鉄筋コンクリート：RC",
  "102": "遠心力鉄筋コンクリート（ヒューム管）：HP",
  "103": "ガラス繊維鉄筋コンクリート",
  "104": "コンクリート製セグメント",
  "105": "鋼製セグメント",
  "106": "ミニシールド用鉄筋コンクリートセグメント",
  "107": "ダグタイル鋳鉄管：DIP",
  "108": "硬質塩化ビニル（薄肉管）：VU",
  "109": "硬質塩化ビニル（厚肉管）：VP",
  "110": "高剛性硬質塩化ビニル",
  "111": "強化プラスチック複合管：FRPM",
  "112": "ポリエチレン：PE",
  "113": "レジンコンクリート",
  "115": "プレキャストコンクリート",
  "116": "現場打鉄筋コンクリート",
  "99": "不明",
};

/** A material code with its official label, or the bare code when the
 * codelist does not define it. Never a guess. */
export function materialLabel(code: string): string {
  const label = MATERIAL_CODELIST[code];
  return label ? `${code} ${label}` : code;
}

/** 3D Tiles bounding region (radians) → [west, south, east, north] degrees. */
export function regionToDegrees(region: number[]): [number, number, number, number] {
  const d = 180 / Math.PI;
  return [region[0] * d, region[1] * d, region[2] * d, region[3] * d];
}

export interface AssetSummary {
  assetPath: string;
  utilityClass: string;
  features: UndergroundFeature[];
  /** [shallowest published minDepth, deepest published maxDepth], if any. */
  depthRange: [number, number] | null;
  /** Distinct `uro:outerDiamiter` values as published (units unknown upstream). */
  diameters: string[];
  /** Distinct material codes as published. */
  materialCodes: string[];
  /** Distinct `uro:mesureType` codes; features without one contribute nothing. */
  mesureTypes: string[];
  /** Distinct `gml:name` values. */
  names: string[];
}

export function indexByAsset(index: UndergroundAuditIndex): Map<string, UndergroundFeature[]> {
  const byAsset = new Map<string, UndergroundFeature[]>();
  for (const feature of index.features) {
    const key = `${feature.source_resource_id}:${feature.source_asset}`;
    const bucket = byAsset.get(key);
    if (bucket) bucket.push(feature);
    else byAsset.set(key, [feature]);
  }
  return byAsset;
}

export function summarizeAsset(features: UndergroundFeature[]): AssetSummary {
  const distinct = (key: string) =>
    [...new Set(features.map((f) => f.attributes[key]).filter((v): v is string => v !== undefined))].sort();
  const finite = (key: string) =>
    features
      .map((f) => f.attributes[key])
      // Number("") is 0, so an empty string must count as missing, not zero.
      .filter((v): v is string => v !== undefined && v.trim() !== "")
      .map(Number)
      .filter((v) => Number.isFinite(v));
  const minDepths = finite("uro:minDepth");
  const maxDepths = finite("uro:maxDepth");
  return {
    assetPath: features[0]?.source_asset ?? "",
    utilityClass: features[0]?.utility_class ?? "",
    features,
    depthRange: minDepths.length && maxDepths.length ? [Math.min(...minDepths), Math.max(...maxDepths)] : null,
    diameters: distinct("uro:outerDiamiter"),
    materialCodes: distinct("uro:material"),
    mesureTypes: distinct("uro:mesureType"),
    names: distinct("gml:name"),
  };
}

/** Manifest resources in published order, filtered to one family. */
export function familyResources(manifest: UndergroundManifest, family: UndergroundFamily): UndergroundResource[] {
  return manifest.resources.filter((resource) => resourceFamily(resource.utility_class) === family);
}
